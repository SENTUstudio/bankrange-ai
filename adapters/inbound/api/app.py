"""Backend Command & Control API for BankRange.

This Inbound Adapter wraps the core simulation engine in an asyncio loop
and exposes REST endpoints to manipulate it in real-time.
"""

import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from adapters.inbound.api.topology_mapper import (
    _to_branch_detail,
    _to_branch_summary,
    _to_network_graph,
)
from adapters.outbound.kafka_publisher import KafkaEventPublisher
from core.domain.topology_factory import TopologyFactory
from core.factories.topology_config_factory import create_topology_config
from core.use_cases.event_generator import EventGenerator

# Load .env at startup
load_dotenv()

logger = logging.getLogger("BankRange-API")

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _get_api_key() -> str | None:
    """Read API key from environment (evaluated at request time for testability)."""
    return os.getenv("BR_API_KEY")


def _check_api_key(x_api_key: str | None) -> None:
    """Raise 401 if API key is missing or wrong."""
    expected = _get_api_key()
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")



# ---------------------------------------------------------------------------
# Injectable State
# ---------------------------------------------------------------------------
@dataclass
class EngineState:
    """Holds state shared between the API endpoints and background loop."""

    is_running: bool = True
    deployed: bool = False
    multiplier_override: float = 0.0
    estimated_eps: float = 0.0
    total_workstations: int = 0

    # Internal references hold domain instances
    _generator: EventGenerator | None = None
    _publisher: KafkaEventPublisher | None = None


# ---------------------------------------------------------------------------
# DTO Models
# ---------------------------------------------------------------------------
class ControlRequest(BaseModel):
    """Payload to alter engine behavior."""

    eps_multiplier: float = Field(
        ...,
        ge=0.0,
        description="Must be >= 0. Scales the volume of logs generated.",
    )


class StatusResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str
    current_multiplier: float
    estimated_eps: float
    total_workstations: int


# ---------------------------------------------------------------------------
# EMA helper
# ---------------------------------------------------------------------------
def _compute_ema_eps(current_ema: float, new_value: float, alpha: float = 0.3) -> float:
    """Compute exponential moving average for EPS smoothing."""
    return alpha * new_value + (1.0 - alpha) * current_ema


# ---------------------------------------------------------------------------
# Background Simulation Loop
# ---------------------------------------------------------------------------
async def _run_engine_loop(engine_state: EngineState) -> None:
    """The infinite simulation loop wrapped for asyncio."""
    logger.info("Background Engine Loop Started.")
    generator = engine_state._generator
    publisher = engine_state._publisher

    if not generator or not publisher:
        logger.error("Engine missing components. Aborting loop.")
        engine_state.is_running = False
        return

    import time
    from datetime import datetime

    engine_state.is_running = True
    ticks = 0

    try:
        while engine_state.is_running:
            if engine_state.deployed:
                loop_start = time.time()
                sim_time = datetime.now(UTC)

                # Pass only the user-controlled multiplier — the temporal profile
                # is applied internally by EventGenerator.generate_tick().
                # Applying it here too would double-count it.
                generator.set_scale_multiplier(engine_state.multiplier_override)

                # Generate and publish
                generator.generate_tick(sim_time)
                ticks += 1

                # Update estimated EPS with EMA smoothing
                raw_eps = generator.estimated_eps(sim_time)
                engine_state.estimated_eps = _compute_ema_eps(
                    engine_state.estimated_eps, raw_eps
                )

                # Maintain realtime pacing without blocking asyncio thread
                processing_time = time.time() - loop_start
                sleep_time = max(0.01, 1.0 - processing_time)  # Wait 1s max
                await asyncio.sleep(sleep_time)
            else:
                await asyncio.sleep(1)  # idle when stopped

    except asyncio.CancelledError:
        logger.info("Engine Loop cancelled via application shutdown.")
    finally:
        engine_state.is_running = False
        logger.info("Flushing publisher...")
        publisher.flush(5.0)


def _start_background_engine(engine_state: EngineState) -> None:
    """Initialize domain components and fire the asyncio task."""
    logger.info("Initializing Topologies and Publishers from environment...")

    # 1. Topology Scaling
    num_branches = int(os.getenv("BR_NUM_BRANCHES", "10"))
    workstations_per_branch = int(os.getenv("BR_WORKSTATIONS_PER_BRANCH", "50"))
    employees_per_branch = int(os.getenv("BR_EMPLOYEES_PER_BRANCH", "60"))

    # 2. OS Distribution
    windows_pct = int(os.getenv("BR_WINDOWS_PCT", "80"))
    linux_pct = int(os.getenv("BR_LINUX_PCT", "15"))
    macos_pct = int(os.getenv("BR_MACOS_PCT", "5"))

    # 3. Performance
    base_eps = float(os.getenv("BR_BASE_EPS", "2.0"))

    # 4. Infrastructure
    kafka_brokers = os.getenv("BR_KAFKA_BROKERS", "localhost:9092")
    # We ignore static topic as the publisher now routes dynamically to bankrange-raw-{os}

    publisher = KafkaEventPublisher(
        bootstrap_servers=kafka_brokers,
        topic_prefix="bankrange-raw",  # Dynamic routing per OS
    )

    config = create_topology_config(
        num_branches=num_branches,
        workstations_per_branch=workstations_per_branch,
        employees_per_branch=employees_per_branch,
        windows_pct=windows_pct,
        linux_pct=linux_pct,
        macos_pct=macos_pct,
        base_eps=base_eps,
    )

    factory = TopologyFactory()
    branches = factory.create(config)

    generator = EventGenerator(branches=branches, publisher=publisher, seed=42)

    # Populate state
    engine_state._generator = generator
    engine_state._publisher = publisher
    engine_state.total_workstations = generator.total_workstations

    asyncio.create_task(_run_engine_loop(engine_state))


# ---------------------------------------------------------------------------
# FastAPI Lifespan & App
# ---------------------------------------------------------------------------
@asynccontextmanager  # type: ignore[arg-type]
async def lifespan(app: FastAPI) -> None:  # type: ignore[override, misc]
    # Startup behavior
    engine_state = EngineState()
    app.state.engine = engine_state
    _start_background_engine(engine_state)
    yield
    # Shutdown behavior
    app.state.engine.is_running = False


app = FastAPI(
    title="BankRange C&C API",
    description="Command and Control panel for log simulation generator",
    lifespan=lifespan,
)

# Enable CORS for local dev (Nginx proxy makes this optional in production)
_allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080")
_allowed_origins = [origin.strip() for origin in _allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/status", response_model=StatusResponse)
async def get_status() -> dict[str, Any]:
    """Retrieve the real-time operational status of the simulator."""
    engine_state = app.state.engine
    return {
        "status": "running" if engine_state.deployed else "stopped",
        "current_multiplier": engine_state.multiplier_override,
        "estimated_eps": engine_state.estimated_eps,
        "total_workstations": engine_state.total_workstations,
    }


@app.get("/health")
async def health_check() -> Any:
    """Operational health check for Docker and orchestrators.

    Returns HTTP 200 when the simulation engine is initialized and ready.
    Returns HTTP 503 when the engine has not been started or failed to init.
    """
    engine = app.state.engine
    if engine._generator is not None:
        return {"status": "healthy"}
    return JSONResponse(
        status_code=503,
        content={"status": "unavailable", "detail": "Engine not initialized"},
    )


@app.post("/control")
async def control_engine(
    req: ControlRequest,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    """Manipulate the volume of the synthetic traffic."""
    _check_api_key(x_api_key)
    engine_state = app.state.engine
    if req.eps_multiplier > 0:
        engine_state.deployed = True
        engine_state.multiplier_override = req.eps_multiplier
        logger.info(f"Engine deployed by API -> {req.eps_multiplier}x")
        message = "Engine deployed"
    else:
        engine_state.deployed = False
        engine_state.multiplier_override = 0.0
        logger.info("Engine stopped by API")
        message = "Engine stopped"

    if engine_state._generator:
        engine_state._generator.set_scale_multiplier(engine_state.multiplier_override)

    return {
        "message": message,
        "new_multiplier": engine_state.multiplier_override,
    }


# ---------------------------------------------------------------------------
# Topology Endpoints
# ---------------------------------------------------------------------------


@app.get("/topology/branches")
async def list_branches() -> list[dict]:
    """Return all branches with coordinates and summary stats."""
    engine = app.state.engine
    generator = engine._generator
    if not generator:
        return []
    return [_to_branch_summary(b) for b in generator.branches]


@app.get("/topology/branches/{branch_code}")
async def get_branch(branch_code: str) -> dict:
    """Return full branch detail including segments and workstations."""
    engine = app.state.engine
    generator = engine._generator
    if not generator:
        raise HTTPException(status_code=404, detail="Branch not found")

    for branch in generator.branches:
        if branch.code == branch_code:
            return _to_branch_detail(branch)

    raise HTTPException(status_code=404, detail="Branch not found")


@app.get("/topology/branches/{branch_code}/network")
async def get_branch_network(branch_code: str) -> dict:
    """Return graph nodes and edges for D3-force rendering."""
    engine = app.state.engine
    generator = engine._generator
    if not generator:
        raise HTTPException(status_code=404, detail="Branch not found")

    for branch in generator.branches:
        if branch.code == branch_code:
            return _to_network_graph(branch)

    raise HTTPException(status_code=404, detail="Branch not found")


# ---------------------------------------------------------------------------
# SSE Endpoint
# ---------------------------------------------------------------------------


async def _sse_generator() -> AsyncGenerator[str]:  # type: ignore[misc, arg-type]
    """Async generator yielding SSE-formatted engine state updates."""
    engine = app.state.engine
    heartbeat_counter = 0
    while True:
        try:
            payload = {
                "status": "running" if engine.deployed else "stopped",
                "current_multiplier": engine.multiplier_override,
                "estimated_eps": engine.estimated_eps,
                "total_workstations": engine.total_workstations,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            yield f"data: {json.dumps(payload)}\n\n"

            # Heartbeat every 15 seconds to keep proxies alive
            heartbeat_counter += 1
            if heartbeat_counter >= 15:
                yield ":heartbeat\n\n"
                heartbeat_counter = 0

            await asyncio.sleep(1)
        except (asyncio.CancelledError, GeneratorExit):
            logger.debug("SSE client disconnected")
            break
        except RuntimeError:
            logger.debug("SSE transport closed")
            break


@app.get("/events/stream")
async def event_stream() -> StreamingResponse:
    """SSE stream of engine state updates (1 Hz)."""
    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
