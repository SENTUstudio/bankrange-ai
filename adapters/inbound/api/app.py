"""Backend Command & Control API for BankRange.

This Inbound Adapter wraps the core simulation engine in an asyncio loop
and exposes REST endpoints to manipulate it in real-time.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from adapters.inbound.cli.runner import create_topology_config
from adapters.outbound.kafka_publisher import KafkaEventPublisher
from core.domain.temporal import BANK_WORKDAY_PROFILE
from core.domain.topology_factory import TopologyFactory
from core.use_cases.event_generator import EventGenerator

logger = logging.getLogger("BankRange-API")


# ---------------------------------------------------------------------------
# Global Thread-Safe State
# ---------------------------------------------------------------------------
class EngineState:
    """Holds global state shared between the API endpoints and background loop."""
    is_running: bool = False
    multiplier_override: float = 1.0
    cached_eps: float = 0.0
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
# Background Simulation Loop
# ---------------------------------------------------------------------------
async def _run_engine_loop() -> None:
    """The infinite simulation loop wrapped for asyncio."""
    logger.info("Background Engine Loop Started.")
    generator = EngineState._generator
    publisher = EngineState._publisher
    
    if not generator or not publisher:
        logger.error("Engine missing components. Aborting loop.")
        return

    import time
    from datetime import datetime, timezone

    EngineState.is_running = True
    ticks = 0

    try:
        while EngineState.is_running:
            loop_start = time.time()
            sim_time = datetime.now(timezone.utc)
            
            # Important: we inject the dynamic scale before generating
            # In Phase 1 MVP, we intercept the multiplier directly.
            # In Phase 2, this will be handled via a command pattern natively.
            base_multi = BANK_WORKDAY_PROFILE.get_multiplier(sim_time)
            effective_multi = base_multi * EngineState.multiplier_override
            
            # Temporary override of the internal generator scaling
            # (Note: In a pure OOP way, we'd add `set_scale` to EventGenerator).
            generator._profile = type(
                "DynamicProfile", (), {"get_multiplier": lambda self, t: effective_multi}
            )() 

            # Generate and publish
            events_generated = generator.generate_tick(sim_time)
            ticks += 1

            # Update cache for UI visualization
            EngineState.cached_eps = float(len(events_generated))

            # Maintain realtime pacing without blocking asyncio thread
            processing_time = time.time() - loop_start
            sleep_time = max(0.01, 1.0 - processing_time)  # Wait 1s max
            await asyncio.sleep(sleep_time)
            
    except asyncio.CancelledError:
        logger.info("Engine Loop cancelled via application shutdown.")
    finally:
        EngineState.is_running = False
        logger.info("Flushing publisher...")
        publisher.flush(5.0)


def _start_background_engine() -> None:
    """Initialize domain components and fire the asyncio task."""
    logger.info("Initializing Topologies and Publishers...")
    
    branches_count = int(os.getenv("BR_BRANCHES", "10"))
    workstations_count = int(os.getenv("BR_WORKSTATIONS", "50"))
    kafka_brokers = os.getenv("BR_KAFKA_BROKERS", "localhost:9092")
    kafka_topic = os.getenv("BR_KAFKA_TOPIC", "bankrange-raw")

    publisher = KafkaEventPublisher(
        bootstrap_servers=kafka_brokers, topic=kafka_topic
    )
    
    config = create_topology_config(
        num_branches=branches_count,
        workstations_per_branch=workstations_count,
        eps_multiplier=1.0,  # Controlled by EngineState instead
    )
    
    factory = TopologyFactory()
    branches = factory.create(config)
    
    generator = EventGenerator(
        branches=branches, publisher=publisher, seed=42
    )

    # Populate state
    EngineState._generator = generator
    EngineState._publisher = publisher
    EngineState.total_workstations = generator.total_workstations

    asyncio.create_task(_run_engine_loop())


# ---------------------------------------------------------------------------
# FastAPI Lifespan & App
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup behavior
    _start_background_engine()
    yield
    # Shutdown behavior
    EngineState.is_running = False


app = FastAPI(
    title="BankRange C&C API",
    description="Command and Control panel for log simulation generator",
    lifespan=lifespan,
)

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/status", response_model=StatusResponse)
async def get_status() -> dict[str, Any]:
    """Retrieve the real-time operational status of the simulator."""
    return {
        "status": "running" if EngineState.is_running else "stopped",
        "current_multiplier": EngineState.multiplier_override,
        "estimated_eps": EngineState.cached_eps,
        "total_workstations": EngineState.total_workstations,
    }


@app.post("/control")
async def control_engine(req: ControlRequest) -> dict[str, Any]:
    """Manipulate the volume of the synthetic traffic."""
    EngineState.multiplier_override = req.eps_multiplier
    logger.info(f"Engine scale updated by API -> {req.eps_multiplier}x")
    
    return {
        "message": "Success",
        "new_multiplier": req.eps_multiplier,
    }
