"""KafkaEventPublisher adapter.

Implements the EventPublisher port to send LogEvents to an Apache Kafka
cluster. Uses confluent-kafka (librdkafka C extension) for maximum
throughput, which is essential for handling 4000+ EPS.
"""

import time
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
        topic_prefix: str = "bankrange-raw",
        producer_config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the Kafka publisher.

        Args:
            bootstrap_servers: Comma-separated list of Kafka brokers.
            topic_prefix: Prefix for dynamically built Kafka topics.
            producer_config: Optional additional config for librdkafka.
        """
        self._topic_prefix = topic_prefix

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
        """Publish a single event to its OS-specific topic."""
        target_topic = f"{self._topic_prefix}-{event.os_type.value}"
        try:
            payload = event.to_raw_format().encode("utf-8")
            self._producer.produce(
                topic=target_topic,
                key=str(event.event_id).encode("utf-8"),
                value=payload,
                on_delivery=self._delivery_report,
            )
            self._producer.poll(0)
        except KafkaException as e:
            raise RuntimeError(f"Failed to publish event to {target_topic}: {e}") from e

    def publish_batch(self, events: list[LogEvent]) -> None:
        """Publish a batch of events efficiently to their OS-specific topics."""
        failed_count = 0
        for event in events:
            if not self._produce_with_retry(event):
                failed_count += 1
        self._producer.poll(0)
        if failed_count:
            raise RuntimeError(failed_count)

    def _produce_with_retry(self, event: LogEvent) -> bool:
        """Send a single event, retrying on BufferError with exponential backoff."""
        target_topic = f"{self._topic_prefix}-{event.os_type.value}"
        payload = event.to_raw_format().encode("utf-8")
        backoff_delays = [0.1, 0.5, 1.0]

        for attempt in range(len(backoff_delays)):
            try:
                self._producer.produce(
                    topic=target_topic,
                    key=str(event.event_id).encode("utf-8"),
                    value=payload,
                    on_delivery=self._delivery_report,
                )
                return True
            except BufferError:
                time.sleep(backoff_delays[attempt])
                self._producer.poll(0)
        return False

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
