"""Backend Command & Control API for BankRange.

This Inbound Adapter wraps the core simulation engine in an asyncio loop
and exposes REST endpoints to manipulate it in real-time.
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from adapters.inbound.api.topology_mapper import (
    _to_branch_detail,
    _to_branch_summary,
    _to_network_graph,
)
from adapters.outbound.kafka_publisher import KafkaEventPublisher
from core.domain.temporal import BANK_WORKDAY_PROFILE
from core.domain.topology_factory import TopologyFactory
from core.factories.topology_config_factory import create_topology_config
from core.use_cases.event_generator import EventGenerator

# Load .env at startup
load_dotenv()

logger = logging.getLogger("BankRange-API")


# ---------------------------------------------------------------------------
# Injectable State
# ---------------------------------------------------------------------------
@dataclass
class EngineState:
    """Holds state shared between the API endpoints and background loop."""

    is_running: bool = False
    multiplier_override: float = 1.0
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
        return

    import time
    from datetime import datetime

    engine_state.is_running = True
    ticks = 0

    try:
        while engine_state.is_running:
            loop_start = time.time()
            sim_time = datetime.now(UTC)

            # Important: we inject the dynamic scale before generating
            base_multi = BANK_WORKDAY_PROFILE.get_multiplier(sim_time)
            effective_multi = base_multi * engine_state.multiplier_override

            generator.set_scale_multiplier(effective_multi)

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
        topic="bankrange-raw-windows",  # Dummy default, dynamic used
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
@asynccontextmanager
async def lifespan(app: FastAPI):
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

# Enable CORS for Streamlit
_allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501")
_allowed_origins = [origin.strip() for origin in _allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/status", response_model=StatusResponse)
async def get_status() -> dict[str, Any]:
    """Retrieve the real-time operational status of the simulator."""
    engine_state = app.state.engine
    return {
        "status": "running" if engine_state.is_running else "stopped",
        "current_multiplier": engine_state.multiplier_override,
        "estimated_eps": engine_state.estimated_eps,
        "total_workstations": engine_state.total_workstations,
    }


@app.post("/control")
async def control_engine(req: ControlRequest) -> dict[str, Any]:
    """Manipulate the volume of the synthetic traffic."""
    app.state.engine.multiplier_override = req.eps_multiplier
    logger.info(f"Engine scale updated by API -> {req.eps_multiplier}x")

    return {
        "message": "Success",
        "new_multiplier": req.eps_multiplier,
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


async def _sse_generator():
    """Async generator yielding SSE-formatted engine state updates."""
    engine = app.state.engine
    heartbeat_counter = 0
    while True:
        payload = {
            "status": "running" if engine.is_running else "stopped",
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
