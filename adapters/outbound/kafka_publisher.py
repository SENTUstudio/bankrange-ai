"""KafkaEventPublisher adapter.

Implements the EventPublisher port to send LogEvents to an Apache Kafka
cluster. Uses confluent-kafka (librdkafka C extension) for maximum
throughput, which is essential for handling 4000+ EPS.
"""

import json
from typing import Any

from confluent_kafka import KafkaException, Producer

from core.domain.log_event import LogEvent
from core.ports.event_publisher import EventPublisher


class KafkaEventPublisher(EventPublisher):
    """Publishes log events to a Kafka topic.

    This adapter acts as a protective boundary around the confluent_kafka
    Producer. It serializes domain events to their chaotic raw string format
    and handles batching and error checking.
    """

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        producer_config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the Kafka publisher.

        Args:
            bootstrap_servers: Comma-separated list of Kafka brokers.
            topic: The Kafka topic to publish events to.
            producer_config: Optional additional config for librdkafka.
        """
        self._topic = topic
        
        # Base config optimized for high throughput
        config = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "bankrange-simulator",
            # Batch tuning for 4000+ EPS
            "queue.buffering.max.messages": 100000,
            "linger.ms": 50,  # Wait up to 50ms to batch messages
            "compression.type": "lz4",  # High throughput compression
        }
        
        if producer_config:
            config.update(producer_config)
            
        self._producer = Producer(config)

    def publish(self, event: LogEvent) -> None:
        """Publish a single event to Kafka."""
        try:
            payload = event.to_raw_format().encode("utf-8")
            
            # Use event_id as the routing key to ensure ordering/partitioning
            # if needed, though for pure logging, random partitioning is fine.
            self._producer.produce(
                topic=self._topic,
                key=str(event.event_id).encode("utf-8"),
                value=payload,
                on_delivery=self._delivery_report,
            )
            # Try to handle callbacks, non-blocking
            self._producer.poll(0)
            
        except KafkaException as e:
            # Wrap infrastructure exceptions in generic runtime errors
            # so the domain doesn't need to know about KafkaException
            raise RuntimeError(f"Failed to publish event to Kafka: {e}") from e

    def publish_batch(self, events: list[LogEvent]) -> None:
        """Publish a batch of events efficiently."""
        try:
            for event in events:
                payload = event.to_raw_format().encode("utf-8")
                self._producer.produce(
                    topic=self._topic,
                    key=str(event.event_id).encode("utf-8"),
                    value=payload,
                    # For batches, we skip the callback to reduce overhead
                    # or point it to a lightweight error-only handler
                )
            # Service delivery reports
            self._producer.poll(0)
            
        except KafkaException as e:
            raise RuntimeError(f"Failed to publish batch to Kafka: {e}") from e
        except BufferError as e: # Catch librdkafka local queue full
            # If the queue is full, flush and try to poll to free space
            self._producer.poll(1.0)
            raise RuntimeError(f"Kafka producer queue full: {e}") from e

    def flush(self, timeout_secs: float = 10.0) -> None:
        """Ensure all buffered messages are sent to the broker."""
        self._producer.flush(timeout_secs)

    @staticmethod
    def _delivery_report(err: Any, msg: Any) -> None:
        """Callback for message delivery confirmation.
        
        In a production scenario, you might log failures here,
        but for a load generator, we want minimal overhead. We only
        print out serious errors.
        """
        if err is not None:
            print(f"Message delivery failed: {err}")
