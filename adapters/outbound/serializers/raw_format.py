"""Raw format serializer for LogEvent.

Serialization is an infrastructure concern — it belongs in the adapter
layer, not in the domain entity. This module converts LogEvents to the
OS-specific chaotic string formats that Vector/Loki pipelines consume.
"""

import html
from typing import Any

from core.domain.log_event import LogEvent
from core.domain.value_objects import OSType

# English month abbreviations for locale-independent syslog timestamps.
_SYSLOG_MONTH_ABBR = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def to_raw_format(event: LogEvent) -> str:
    """Serialize a LogEvent to an OS-specific raw string format.

    - Linux  → Syslog RFC 3164
    - Windows → Flattened XML (Windows Event Log style)
    - macOS  → Tab-separated values (ASL dump style)
    """
    ts_syslog = (
        f"{_SYSLOG_MONTH_ABBR[event.timestamp.month]} "
        f"{event.timestamp.day:02d} "
        f"{event.timestamp.strftime('%H:%M:%S')}"
    )
    ts_iso = event.timestamp.isoformat()
    meta_kv = " ".join(f"{k}={v}" for k, v in event.metadata.items())
    meta_tsv = "\t".join(str(v) for v in event.metadata.values())

    if event.os_type == OSType.LINUX:
        return (
            f"<134>{ts_syslog} {event.hostname} {event.event_type.value}"
            f"[{event.event_id.hex[:8]}]: {event.username} - {event.severity.value.upper()} "
            f"- {event.message} (src={event.ip_address} branch={event.branch_code} {meta_kv})"
        )

    if event.os_type == OSType.WINDOWS:
        def _escape(value: Any) -> str:
            return html.escape(value, quote=True) if isinstance(value, str) else str(value)

        meta_xml = "".join(f'<Data Name="{k}">{_escape(v)}</Data>' for k, v in event.metadata.items())
        return (
            f'<Event><System><Provider Name="{event.event_type.value}"/>'
            f'<TimeCreated SystemTime="{ts_iso}"/>'
            f"<Computer>{html.escape(event.hostname, quote=True)}</Computer>"
            f'<Security UserID="{html.escape(event.username, quote=True)}"/></System>'
            f'<EventData><Message>{html.escape(event.message, quote=True)}</Message>'
            f'<Level>{event.severity.value}</Level>'
            f'<IP>{event.ip_address}</IP><Branch>{event.branch_code}</Branch>'
            f"{meta_xml}</EventData></Event>"
        )

    if event.os_type == OSType.MACOS:
        base = (
            f"{ts_iso}\t{event.hostname}\t{event.username}\t{event.os_type.value}"
            f"\t{event.event_type.value}\t{event.severity.value}\t{event.message}"
            f"\t{event.ip_address}\t{event.branch_code}"
        )
        return f"{base}\t{meta_tsv}" if meta_tsv else base

    return str(event.model_dump())
