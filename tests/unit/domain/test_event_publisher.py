"""Tests for EventPublisher protocol and InMemoryEventPublisher."""

from datetime import UTC, datetime

from core.domain.log_event import LogEvent
from core.domain.value_objects import EventType, OSType
from tests.unit.domain.conftest import InMemoryEventPublisher


def _make_event() -> LogEvent:
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


class TestInMemoryEventPublisher:
    """Tests for the in-memory implementation of EventPublisher."""

    def test_flush_with_timeout_accepts_parameter(self) -> None:
        """flush must accept a timeout_secs parameter without raising TypeError."""
        publisher = InMemoryEventPublisher()
        publisher.publish(_make_event())

        # This should not raise TypeError
        publisher.flush(timeout_secs=5.0)

        assert publisher.flushed is True

    def test_flush_with_default_timeout(self) -> None:
        """flush must work when called without arguments (default timeout)."""
        publisher = InMemoryEventPublisher()
        publisher.publish(_make_event())

        publisher.flush()

        assert publisher.flushed is True
