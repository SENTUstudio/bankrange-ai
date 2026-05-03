"""BankRange CLI Runner.

This script acts as the main execution entrypoint (Inbound Adapter).
It wires together the Core Domain components, injects the infrastructure
(Kafka Publisher), and runs the continuous log generation loop.
"""

import argparse
import logging
import os
import sys
import time
from datetime import UTC, datetime

from adapters.outbound.kafka_publisher import KafkaEventPublisher
from core.domain.temporal import BANK_WORKDAY_PROFILE
from core.domain.topology_factory import TopologyFactory
from core.factories.topology_config_factory import create_topology_config
from core.use_cases.event_generator import EventGenerator

# Minimal logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("BankRange-CLI")


def main() -> None:
    """Main execution loop for BankRange simulation."""
    parser = argparse.ArgumentParser(description="BankRange Cyber Log Simulator")
    parser.add_argument(
        "--branches",
        type=int,
        default=int(os.getenv("BR_BRANCHES", "10")),
        help="Number of branches",
    )
    parser.add_argument(
        "--workstations",
        type=int,
        default=int(os.getenv("BR_WORKSTATIONS", "50")),
        help="PCs per branch",
    )
    parser.add_argument(
        "--eps-scale",
        type=float,
        default=float(os.getenv("BR_EPS_SCALE", "1.0")),
        help="Base EPS multiplier",
    )
    parser.add_argument(
        "--employees-per-branch",
        type=int,
        default=int(os.getenv("BR_EMPLOYEES_PER_BRANCH", "60")),
        help="Employees per branch",
    )
    parser.add_argument(
        "--kafka-brokers",
        type=str,
        default=os.getenv("BR_KAFKA_BROKERS", "localhost:9092"),
        help="Kafka bootstrap servers",
    )
    parser.add_argument(
        "--kafka-topic",
        type=str,
        default=os.getenv("BR_KAFKA_TOPIC", "bankrange-raw"),
        help="Target Kafka topic",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for deterministic topologies"
    )
    args = parser.parse_args()

    logger.info("🛡️  Initializing BankRange Cyber Log Simulator...")
    logger.info(f"Targeting Kafka cluster at {args.kafka_brokers}")

    # 1. Initialize Infrastructure Adapter
    try:
        publisher = KafkaEventPublisher(
            bootstrap_servers=args.kafka_brokers,
            topic=args.kafka_topic,
        )
        logger.info(f"Kafka Publisher initialized (Topic: {args.kafka_topic})")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka Publisher: {e}")
        sys.exit(1)

    # 2. Setup the Domain Config
    config = create_topology_config(
        num_branches=args.branches,
        workstations_per_branch=args.workstations,
        employees_per_branch=args.employees_per_branch,
        windows_pct=80,
        linux_pct=15,
        macos_pct=5,
        base_eps=args.eps_scale,
    )

    # 3. Create Topology
    factory = TopologyFactory()
    branches = factory.create(config)
    total_workstations = sum(len(b.workstations) for b in branches)

    logger.info(
        f"Topology built: {args.branches} branches, {total_workstations} workstations mapped."
    )

    # 4. Instantiate the Core Use Case
    generator = EventGenerator(
        branches=branches,
        publisher=publisher,
        temporal_profile=BANK_WORKDAY_PROFILE,
        seed=args.seed,
    )

    # 5. Continuous Execution Loop
    logger.info("🚀 Starting simulation engine. Press Ctrl+C to stop.")

    try:
        ticks = 0
        total_events = 0
        start_time = time.time()

        while True:
            # We generate one simulated second of events
            sim_time = datetime.now(UTC)

            loop_start = time.time()
            events_generated = generator.generate_tick(sim_time)
            loop_end = time.time()

            total_events += len(events_generated)
            ticks += 1

            # Print stats every 5 seconds
            if ticks % 5 == 0:
                elapsed = time.time() - start_time
                avg_eps = total_events / elapsed
                expected_eps = generator.estimated_eps(sim_time)

                logger.info(
                    f"Tick: {ticks:04d} | "
                    f"Generated: {len(events_generated):04d} events | "
                    f"Avg EPS: {avg_eps:.1f} (Target: {expected_eps:.1f})"
                )

            # Wait for the remainder of the 1-second tick to maintain realtime pacing
            processing_time = loop_end - loop_start
            sleep_time = max(0, 1.0 - processing_time)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("🛑 Simulation stopped by user.")
    except Exception as e:
        logger.error(f"❌ Unhandled exception during simulation: {e}")
    finally:
        logger.info("Flushing pending events to Kafka...")
        publisher.flush(timeout_secs=5.0)
        logger.info(f"Shutdown complete. Total events dispatched: {total_events}")


if __name__ == "__main__":
    main()
