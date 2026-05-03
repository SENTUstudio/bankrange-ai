"""Unit tests for KafkaEventPublisher adapter."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from adapters.outbound.kafka_publisher import KafkaEventPublisher
from core.domain.log_event import LogEvent
from core.domain.value_objects import EventType, OSType


@pytest.fixture
def sample_event() -> LogEvent:
    return LogEvent(
        timestamp=datetime(2026, 1, 15, 10, 30, tzinfo=UTC),
        hostname="SUC001-PC-001",
        ip_address="10.1.1.10",
        os_type=OSType.WINDOWS,
        username="EM001234",
        branch_code="SUC001",
        event_type=EventType.AUTHENTICATION,
        message="Test login",
        metadata={"key": "value"},
    )


class TestKafkaEventPublisherTopicPrefix:
    """Tests for topic_prefix routing behavior."""

    @patch("adapters.outbound.kafka_publisher.Producer")
    def test_topic_prefix_dynamic(self, mock_producer_class: MagicMock, sample_event: LogEvent) -> None:
        """Given topic_prefix='bankrange-raw', publish windows event → topic 'bankrange-raw-windows'."""
        mock_producer_instance = mock_producer_class.return_value

        publisher = KafkaEventPublisher(
            bootstrap_servers="localhost:9092",
            topic_prefix="bankrange-raw",
        )

        publisher.publish(sample_event)

        mock_producer_instance.produce.assert_called_once()
        _, kwargs = mock_producer_instance.produce.call_args
        assert kwargs.get("topic") == "bankrange-raw-windows"

    @patch("adapters.outbound.kafka_publisher.Producer")
    def test_topic_prefix_custom(self, mock_producer_class: MagicMock, sample_event: LogEvent) -> None:
        """Given a custom topic_prefix, the generated topic must start with that prefix."""
        mock_producer_instance = mock_producer_class.return_value

        publisher = KafkaEventPublisher(
            bootstrap_servers="localhost:9092",
            topic_prefix="custom",
        )

        publisher.publish(sample_event)

        _, kwargs = mock_producer_instance.produce.call_args
        assert kwargs.get("topic") == "custom-windows"


class TestKafkaEventPublisherOnDelivery:
    """Tests for on_delivery callback in batch publishing."""

    @patch("adapters.outbound.kafka_publisher.Producer")
    def test_publish_batch_passes_on_delivery(self, mock_producer_class: MagicMock, sample_event: LogEvent) -> None:
        """Every produce() call inside publish_batch must include on_delivery kwarg."""
        mock_producer_instance = mock_producer_class.return_value

        publisher = KafkaEventPublisher(
            bootstrap_servers="localhost:9092",
            topic_prefix="bankrange-raw",
        )

        events = [sample_event, sample_event, sample_event]
        publisher.publish_batch(events)

        assert mock_producer_instance.produce.call_count == 3
        for call in mock_producer_instance.produce.call_args_list:
            _, kwargs = call
            assert "on_delivery" in kwargs
            assert kwargs["on_delivery"] == publisher._delivery_report

    @patch("adapters.outbound.kafka_publisher.Producer")
    def test_publish_passes_on_delivery(self, mock_producer_class: MagicMock, sample_event: LogEvent) -> None:
        """Single publish must also pass on_delivery kwarg."""
        mock_producer_instance = mock_producer_class.return_value

        publisher = KafkaEventPublisher(
            bootstrap_servers="localhost:9092",
            topic_prefix="bankrange-raw",
        )

        publisher.publish(sample_event)

        mock_producer_instance.produce.assert_called_once()
        _, kwargs = mock_producer_instance.produce.call_args
        assert "on_delivery" in kwargs
        assert kwargs["on_delivery"] == publisher._delivery_report


class TestKafkaEventPublisherRetry:
    """Tests for BufferError retry logic in publish_batch."""

    @patch("adapters.outbound.kafka_publisher.Producer")
    def test_publish_batch_retries_buffer_error(
        self,
        mock_producer_class: MagicMock,
        sample_event: LogEvent,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Second event fails once with BufferError, then succeeds on retry."""
        monkeypatch.setattr("time.sleep", lambda _: None)
        mock_producer_instance = mock_producer_class.return_value
        # First event OK, second fails once, third OK
        call_count = 0

        def side_effect(*args: Any, **kwargs: Any) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise BufferError("queue full")

        mock_producer_instance.produce.side_effect = side_effect

        publisher = KafkaEventPublisher(
            bootstrap_servers="localhost:9092",
            topic_prefix="bankrange-raw",
        )

        events = [sample_event, sample_event, sample_event]
        publisher.publish_batch(events)

        # 4 total calls: 1st ok, 2nd fails, 2nd retry ok, 3rd ok
        assert mock_producer_instance.produce.call_count == 4

    @patch("adapters.outbound.kafka_publisher.Producer")
    def test_publish_batch_raises_after_retries(
        self,
        mock_producer_class: MagicMock,
        sample_event: LogEvent,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Third event always fails with BufferError; RuntimeError raised after 3 attempts."""
        monkeypatch.setattr("time.sleep", lambda _: None)
        mock_producer_instance = mock_producer_class.return_value
        call_count = 0

        def side_effect(*args: Any, **kwargs: Any) -> None:
            nonlocal call_count
            call_count += 1
            # Fail on calls 3, 4, 5 (third event, 3 attempts)
            if call_count in (3, 4, 5):
                raise BufferError("queue full")

        mock_producer_instance.produce.side_effect = side_effect

        publisher = KafkaEventPublisher(
            bootstrap_servers="localhost:9092",
            topic_prefix="bankrange-raw",
        )

        events = [sample_event, sample_event, sample_event]
        with pytest.raises(RuntimeError) as exc_info:
            publisher.publish_batch(events)

        assert exc_info.value.args[0] == 1

    @patch("adapters.outbound.kafka_publisher.Producer")
    def test_publish_batch_multiple_failures(
        self,
        mock_producer_class: MagicMock,
        sample_event: LogEvent,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """All events fail with BufferError; RuntimeError reports the total failed count."""
        monkeypatch.setattr("time.sleep", lambda _: None)
        mock_producer_instance = mock_producer_class.return_value
        mock_producer_instance.produce.side_effect = BufferError("queue full")

        publisher = KafkaEventPublisher(
            bootstrap_servers="localhost:9092",
            topic_prefix="bankrange-raw",
        )

        events = [sample_event, sample_event]
        with pytest.raises(RuntimeError) as exc_info:
            publisher.publish_batch(events)

        assert exc_info.value.args[0] == 2
        assert mock_producer_instance.produce.call_count == 6  # 2 events × 3 attempts
