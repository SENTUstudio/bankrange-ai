"""Integration tests for KafkaEventPublisher adapter.

These tests use unittest.mock to verify the interaction with the
confluent_kafka Producer without requiring a real Kafka cluster
running during the standard CI/CD pipeline.
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from confluent_kafka import KafkaException

from adapters.outbound.kafka_publisher import KafkaEventPublisher
from core.domain.log_event import LogEvent
from core.domain.value_objects import EventType, OSType


@pytest.fixture
def sample_event() -> LogEvent:
    """A valid LogEvent for testing the publisher."""
    return LogEvent(
        timestamp=datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc),
        hostname="SUC001-PC-001",
        ip_address="10.1.1.10",
        os_type=OSType.WINDOWS,
        username="EM001234",
        branch_code="SUC001",
        event_type=EventType.AUTHENTICATION,
        message="Test login",
        metadata={"key": "value"},
    )


class TestKafkaEventPublisher:
    """Tests that the Kafka adapter correctly maps domain events to infrastructure."""

    @patch("adapters.outbound.kafka_publisher.Producer")
    def test_publish_sends_raw_string_to_correct_topic(
        self, mock_producer_class: MagicMock, sample_event: LogEvent
    ) -> None:
        """Events must be serialized to chaotic raw strings and sent to the configured topic."""
        mock_producer_instance = mock_producer_class.return_value
        
        publisher = KafkaEventPublisher(
            bootstrap_servers="localhost:9092",
            topic="bankrange-logs",
        )
        
        publisher.publish(sample_event)
        
        # Verify the producer was called once
        mock_producer_instance.produce.assert_called_once()
        
        # Extract arguments passed to Produce
        args, kwargs = mock_producer_instance.produce.call_args
        
        # Topic should be the first positional arg or kwarg
        topic = kwargs.get("topic") if not args else args[0]
        assert topic == "bankrange-logs"
        
        # Determine the payload
        payload = kwargs.get("value")
        if payload is None and len(args) > 1:
            payload = args[1]
            
        assert payload is not None
        
        # Payload must be a valid UTF-8 decoded string that mirrors to_raw_format()
        if isinstance(payload, bytes):
            payload_str = payload.decode("utf-8")
        else:
            payload_str = payload
            
        assert "SUC001-PC-001" in payload_str
        assert "EventData" in payload_str  # Windows dummy schema verification

    @patch("adapters.outbound.kafka_publisher.Producer")
    def test_publish_batch_produces_multiple_events_and_polls(
        self, mock_producer_class: MagicMock, sample_event: LogEvent
    ) -> None:
        """publish_batch should call produce multiple times and then poll()."""
        mock_producer_instance = mock_producer_class.return_value
        
        publisher = KafkaEventPublisher(
            bootstrap_servers="localhost:9092",
            topic="bankrange-logs",
        )
        
        events = [sample_event, sample_event, sample_event]
        publisher.publish_batch(events)
        
        # Produce called 3 times
        assert mock_producer_instance.produce.call_count == 3
        # Poll should be called to handle delivery callbacks
        mock_producer_instance.poll.assert_called_once_with(0)

    @patch("adapters.outbound.kafka_publisher.Producer")
    def test_flush_calls_producer_flush(
        self, mock_producer_class: MagicMock
    ) -> None:
        """The domain flush method must map to the infrastructure flush."""
        mock_producer_instance = mock_producer_class.return_value
        
        publisher = KafkaEventPublisher(
            bootstrap_servers="localhost:9092",
            topic="bankrange-logs",
        )
        
        publisher.flush()
        
        mock_producer_instance.flush.assert_called_once()

    @patch("adapters.outbound.kafka_publisher.Producer")
    def test_kafka_exceptions_are_wrapped_in_domain_exceptions(
        self, mock_producer_class: MagicMock, sample_event: LogEvent
    ) -> None:
        """Infrastructure exceptions shouldn't leak directly; they should be handled."""
        mock_producer_instance = mock_producer_class.return_value
        # Simulate a buffer overflow or connection error raised by confluent_kafka
        mock_producer_instance.produce.side_effect = KafkaException("Buffer full")
        
        publisher = KafkaEventPublisher(
            bootstrap_servers="localhost:9092",
            topic="bankrange-logs",
        )
        
        with pytest.raises(RuntimeError, match="Failed to publish event to Kafka"):
            publisher.publish(sample_event)
