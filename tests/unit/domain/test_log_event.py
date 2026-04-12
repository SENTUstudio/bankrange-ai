"""Unit tests for LogEvent entity.

Tests validate the PRD acceptance criteria (Section 5):
all required fields are present and correctly typed.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from core.domain.log_event import LogEvent
from core.domain.value_objects import EventType, OSType, Severity


class TestLogEvent:
    """LogEvent is the atomic output of the simulator."""

    def test_valid_log_event_is_created(self) -> None:
        """A log event with all required fields is accepted."""
        event = LogEvent(
            hostname="SUC001-PC-001",
            ip_address="10.1.1.10",
            os_type=OSType.WINDOWS,
            username="EM001234",
            branch_code="SUC001",
            event_type=EventType.AUTHENTICATION,
            severity=Severity.INFO,
            message="User login successful",
        )
        assert event.hostname == "SUC001-PC-001"
        assert event.ip_address == "10.1.1.10"
        assert event.os_type == OSType.WINDOWS
        assert event.username == "EM001234"
        assert event.event_type == EventType.AUTHENTICATION
        assert event.severity == Severity.INFO

    def test_event_id_is_auto_generated(self) -> None:
        """Each event gets a unique UUID automatically."""
        event1 = LogEvent(
            hostname="SUC001-PC-001",
            ip_address="10.1.1.10",
            os_type=OSType.WINDOWS,
            username="EM001234",
            branch_code="SUC001",
            event_type=EventType.SYSTEM,
            message="System boot",
        )
        event2 = LogEvent(
            hostname="SUC001-PC-001",
            ip_address="10.1.1.10",
            os_type=OSType.WINDOWS,
            username="EM001234",
            branch_code="SUC001",
            event_type=EventType.SYSTEM,
            message="System boot",
        )
        assert event1.event_id != event2.event_id

    def test_timestamp_defaults_to_utc(self) -> None:
        """Timestamps must be timezone-aware in UTC."""
        event = LogEvent(
            hostname="SUC001-PC-001",
            ip_address="10.1.1.10",
            os_type=OSType.WINDOWS,
            username="EM001234",
            branch_code="SUC001",
            event_type=EventType.NETWORK,
            message="DNS query",
        )
        assert event.timestamp.tzinfo is not None
        assert event.timestamp.tzinfo == timezone.utc

    def test_default_severity_is_info(self) -> None:
        """Baseline events default to INFO severity."""
        event = LogEvent(
            hostname="SUC001-PC-001",
            ip_address="10.1.1.10",
            os_type=OSType.WINDOWS,
            username="SYSTEM",
            branch_code="SUC001",
            event_type=EventType.SYSTEM,
            message="Heartbeat",
        )
        assert event.severity == Severity.INFO

    def test_log_event_is_immutable(self) -> None:
        """Log events must not be modified after creation."""
        event = LogEvent(
            hostname="SUC001-PC-001",
            ip_address="10.1.1.10",
            os_type=OSType.WINDOWS,
            username="EM001234",
            branch_code="SUC001",
            event_type=EventType.AUTHENTICATION,
            message="Login",
        )
        with pytest.raises(ValidationError):
            event.hostname = "TAMPERED"  # type: ignore[misc]

    def test_invalid_branch_code_is_rejected(self) -> None:
        """Branch code must follow the bank convention."""
        with pytest.raises(ValidationError, match="branch_code"):
            LogEvent(
                hostname="SUC001-PC-001",
                ip_address="10.1.1.10",
                os_type=OSType.WINDOWS,
                username="EM001234",
                branch_code="invalid",
                event_type=EventType.AUTHENTICATION,
                message="Login",
            )

    def test_to_raw_format_incorporates_os_mutations(self) -> None:
        """The entity must emit diverse chaotic string formats by OS."""
        ts = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        
        base_kwargs = {
            "timestamp": ts,
            "hostname": "SUC001-PC-001",
            "ip_address": "10.1.1.10",
            "username": "EM001234",
            "branch_code": "SUC001",
            "event_type": EventType.AUTHENTICATION,
            "severity": Severity.WARNING,
            "message": "Failed login attempt",
            "metadata": {},
        }
        
        # Test Windows XML-like
        windows_event = LogEvent(os_type=OSType.WINDOWS, **base_kwargs)
        win_str = windows_event.to_raw_format()
        assert "<Event><System>" in win_str
        assert "SUC001-PC-001" in win_str
        
        # Test Linux Syslog-like
        linux_event = LogEvent(os_type=OSType.LINUX, **base_kwargs)
        lin_str = linux_event.to_raw_format()
        assert "<134>Jan 15 10:30:00 SUC001-PC-001" in lin_str
        assert "WARNING - Failed login attempt" in lin_str
        
        # Test macOS tabulated
        mac_event = LogEvent(os_type=OSType.MACOS, **base_kwargs)
        mac_str = mac_event.to_raw_format()
        assert "2026-01-15T10:30:00+00:00\tSUC001-PC-001" in mac_str

    def test_empty_message_is_rejected(self) -> None:
        """Every log event must have a meaningful message."""
        with pytest.raises(ValidationError, match="message"):
            LogEvent(
                hostname="SUC001-PC-001",
                ip_address="10.1.1.10",
                os_type=OSType.WINDOWS,
                username="EM001234",
                branch_code="SUC001",
                event_type=EventType.SYSTEM,
                message="",
            )
