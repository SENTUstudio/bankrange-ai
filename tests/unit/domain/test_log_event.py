"""Unit tests for LogEvent entity.

Tests validate the PRD acceptance criteria (Section 5):
all required fields are present and correctly typed.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from adapters.outbound.serializers.raw_format import to_raw_format
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
        assert event.timestamp.tzinfo == UTC

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
        """The entity must emit diverse chaotic string formats by OS including metadata."""
        ts = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)

        base_kwargs = {
            "timestamp": ts,
            "hostname": "SUC001-PC-001",
            "ip_address": "10.1.1.10",
            "username": "EM001234",
            "branch_code": "SUC001",
            "event_type": EventType.AUTHENTICATION,
            "severity": Severity.WARNING,
            "message": "Failed login attempt",
            "metadata": {"windows_event_id": 4625, "logon_type": 2},
        }

        # Test Windows XML-like
        windows_event = LogEvent(os_type=OSType.WINDOWS, **base_kwargs)
        win_str = to_raw_format(windows_event)
        assert "<Event><System>" in win_str
        assert "SUC001-PC-001" in win_str
        assert '<Data Name="windows_event_id">4625</Data>' in win_str
        assert '<Data Name="logon_type">2</Data>' in win_str

        # Test Linux Syslog-like
        linux_event = LogEvent(os_type=OSType.LINUX, **base_kwargs)
        lin_str = to_raw_format(linux_event)
        assert "<134>Jan 15 10:30:00 SUC001-PC-001" in lin_str
        assert "WARNING - Failed login attempt" in lin_str
        assert "windows_event_id=4625 logon_type=2" in lin_str

        # Test macOS tabulated
        mac_event = LogEvent(os_type=OSType.MACOS, **base_kwargs)
        mac_str = to_raw_format(mac_event)
        assert "2026-01-15T10:30:00+00:00\tSUC001-PC-001" in mac_str
        assert "\t4625\t2" in mac_str

    def test_syslog_timestamp_ignores_locale(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Linux syslog timestamp must use English months regardless of host locale."""
        monkeypatch.setenv("LC_TIME", "es_ES.UTF-8")
        # Also force Python's locale-sensitive strftime to observe the env var
        import locale

        try:
            locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
        except locale.Error:
            pytest.skip("Spanish locale not available on this system")

        ts = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)
        event = LogEvent(
            timestamp=ts,
            hostname="SUC001-PC-001",
            ip_address="10.1.1.10",
            os_type=OSType.LINUX,
            username="EM001234",
            branch_code="SUC001",
            event_type=EventType.AUTHENTICATION,
            severity=Severity.WARNING,
            message="Failed login attempt",
        )
        raw = to_raw_format(event)
        assert "<134>Jan 15 10:30:00" in raw, f"Expected English month abbreviation, got: {raw[:50]}"

    def test_syslog_timestamp_ignores_locale_for_december(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """English abbreviations must work for any month under any locale."""
        monkeypatch.setenv("LC_TIME", "fr_FR.UTF-8")
        import locale

        try:
            locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
        except locale.Error:
            pytest.skip("French locale not available on this system")

        ts = datetime(2026, 12, 25, 14, 0, 0, tzinfo=UTC)
        event = LogEvent(
            timestamp=ts,
            hostname="SUC001-PC-001",
            ip_address="10.1.1.10",
            os_type=OSType.LINUX,
            username="EM001234",
            branch_code="SUC001",
            event_type=EventType.SYSTEM,
            severity=Severity.INFO,
            message="Year-end backup",
        )
        raw = to_raw_format(event)
        assert "<134>Dec 25 14:00:00" in raw, f"Expected English month abbreviation, got: {raw[:50]}"

    def test_windows_xml_uses_named_elements_for_fixed_fields(self) -> None:
        """Fixed fields must appear as direct named children of EventData."""
        import xml.etree.ElementTree as ET

        ts = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)
        event = LogEvent(
            timestamp=ts,
            hostname="SUC001-PC-001",
            ip_address="10.1.1.10",
            os_type=OSType.WINDOWS,
            username="EM001234",
            branch_code="SUC001",
            event_type=EventType.AUTHENTICATION,
            severity=Severity.WARNING,
            message="Failed login attempt",
            metadata={"session_id": "abc123"},
        )
        raw = to_raw_format(event)
        root = ET.fromstring(raw)

        event_data = root.find("EventData")
        assert event_data is not None

        # Fixed fields as direct named children
        assert event_data.find("Message") is not None
        assert event_data.find("Message").text == "Failed login attempt"
        assert event_data.find("Level") is not None
        assert event_data.find("Level").text == "warning"
        assert event_data.find("IP") is not None
        assert event_data.find("IP").text == "10.1.1.10"
        assert event_data.find("Branch") is not None
        assert event_data.find("Branch").text == "SUC001"

        # Metadata still in Data Name="..."
        meta = event_data.find('.//*[@Name="session_id"]')
        assert meta is not None
        assert meta.text == "abc123"

    def test_to_raw_format_windows_escapes_xml_entities(self) -> None:
        """Windows events must produce well-formed XML even with special chars."""
        import xml.etree.ElementTree as ET

        ts = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)
        event = LogEvent(
            timestamp=ts,
            hostname="SUC001-PC-001",
            ip_address="10.1.1.10",
            os_type=OSType.WINDOWS,
            username="EM001234",
            branch_code="SUC001",
            event_type=EventType.AUTHENTICATION,
            severity=Severity.WARNING,
            message='<script>alert("xss")</script>',
            metadata={"reason": "A&B", "count": 5},
        )
        raw = to_raw_format(event)

        # Must be parseable XML
        root = ET.fromstring(raw)
        assert root.tag == "Event"

        # Escaped message must be present as text content in the named element
        event_data = root.find("EventData")
        assert event_data is not None
        message_el = event_data.find("Message")
        assert message_el is not None
        assert message_el.text == '<script>alert("xss")</script>'

        # Escaped metadata string must be present
        reason_data = root.find('.//*[@Name="reason"]')
        assert reason_data is not None
        assert reason_data.text == "A&B"

        # Numeric metadata must remain unescaped
        count_data = root.find('.//*[@Name="count"]')
        assert count_data is not None
        assert count_data.text == "5"

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
