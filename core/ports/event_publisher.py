"""Output ports — interfaces for infrastructure adapters.

These are the contracts that the domain defines for communication
with the outside world. The domain NEVER imports infrastructure;
infrastructure imports and implements these ports.

In Hexagonal Architecture terms, these are "driven ports" — the
domain drives them, and adapters provide the implementation.
"""

from typing import Protocol

from core.domain.log_event import LogEvent


class EventPublisher(Protocol):
    """Port for publishing log events to an external sink.

    Implementations:
    - KafkaEventPublisher (production): sends to Kafka topic
    - FileEventPublisher (development): writes to JSON file
    - InMemoryEventPublisher (testing): collects in a list

    The domain calls publish() without knowing where events go.
    This is the CORE of hexagonal architecture — dependency inversion.
    """

    def publish(self, event: LogEvent) -> None:
        """Publish a single log event.

        Args:
            event: The LogEvent to publish.

        Raises:
            EventPublishError: If the event cannot be published
                (connection lost, buffer full, etc.)
        """
        ...

    def publish_batch(self, events: list[LogEvent]) -> None:
        """Publish a batch of log events.

        Batching is critical for performance when generating
        4000+ EPS. Implementations should optimize for throughput.

        Args:
            events: List of LogEvents to publish.

        Raises:
            EventPublishError: If the batch cannot be published.
        """
        ...

    def flush(self) -> None:
        """Ensure all buffered events are sent.

        Call this at the end of a simulation cycle or on shutdown
        to guarantee delivery of all pending events.
        """
        ...
