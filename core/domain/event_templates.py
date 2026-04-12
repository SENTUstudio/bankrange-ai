"""Event templates — realistic log content for bank workstations.

Defines what events each combination of OS + EventType produces.
This is the "content brain" of the simulator — it knows that a
Windows PC logs Event ID 4624 for successful logins, or that
a Linux server logs sshd authentication messages.

The templates are used by the EventGenerator to produce realistic,
varied log messages that a SIEM analyst would recognize.
"""

import random
from dataclasses import dataclass

from core.domain.value_objects import EventType, OSType, Severity


@dataclass(frozen=True)
class EventTemplate:
    """A template for generating a specific type of log event.

    Each template defines the shape of one kind of event:
    what it says, how severe it is, and what metadata it carries.
    """

    event_type: EventType
    severity: Severity
    message_template: str
    metadata_keys: tuple[str, ...]


# ---------------------------------------------------------------------------
# Windows event templates
# ---------------------------------------------------------------------------

WINDOWS_TEMPLATES: list[EventTemplate] = [
    # Authentication events (Windows Security Log)
    EventTemplate(
        event_type=EventType.AUTHENTICATION,
        severity=Severity.INFO,
        message_template="An account was successfully logged on",
        metadata_keys=("windows_event_id", "logon_type"),
    ),
    EventTemplate(
        event_type=EventType.AUTHENTICATION,
        severity=Severity.WARNING,
        message_template="An account failed to log on",
        metadata_keys=("windows_event_id", "failure_reason"),
    ),
    EventTemplate(
        event_type=EventType.AUTHENTICATION,
        severity=Severity.INFO,
        message_template="An account was logged off",
        metadata_keys=("windows_event_id", "logon_type"),
    ),
    # Process events
    EventTemplate(
        event_type=EventType.PROCESS,
        severity=Severity.INFO,
        message_template="A new process has been created: {process_name}",
        metadata_keys=("windows_event_id", "process_name", "process_id"),
    ),
    EventTemplate(
        event_type=EventType.PROCESS,
        severity=Severity.INFO,
        message_template="A process has exited: {process_name}",
        metadata_keys=("windows_event_id", "process_name", "exit_code"),
    ),
    # Network events
    EventTemplate(
        event_type=EventType.NETWORK,
        severity=Severity.INFO,
        message_template="Network connection established to {destination_ip}",
        metadata_keys=("destination_ip", "destination_port", "protocol"),
    ),
    # File access events
    EventTemplate(
        event_type=EventType.FILE_ACCESS,
        severity=Severity.INFO,
        message_template="A handle to an object was requested: {file_path}",
        metadata_keys=("windows_event_id", "file_path", "access_mask"),
    ),
    # System events
    EventTemplate(
        event_type=EventType.SYSTEM,
        severity=Severity.INFO,
        message_template="Windows Update check completed",
        metadata_keys=("update_status",),
    ),
    EventTemplate(
        event_type=EventType.SYSTEM,
        severity=Severity.INFO,
        message_template="System time synchronized with NTP server",
        metadata_keys=("ntp_server",),
    ),
    # Application events
    EventTemplate(
        event_type=EventType.APPLICATION,
        severity=Severity.INFO,
        message_template="Application started: {app_name}",
        metadata_keys=("app_name", "app_version"),
    ),
    EventTemplate(
        event_type=EventType.APPLICATION,
        severity=Severity.ERROR,
        message_template="Application error: {app_name} crashed",
        metadata_keys=("app_name", "error_code"),
    ),
]

# ---------------------------------------------------------------------------
# Linux event templates
# ---------------------------------------------------------------------------

LINUX_TEMPLATES: list[EventTemplate] = [
    EventTemplate(
        event_type=EventType.AUTHENTICATION,
        severity=Severity.INFO,
        message_template="sshd: Accepted publickey for {username}",
        metadata_keys=("ssh_method", "source_port"),
    ),
    EventTemplate(
        event_type=EventType.AUTHENTICATION,
        severity=Severity.WARNING,
        message_template="sshd: Failed password for {username}",
        metadata_keys=("ssh_method", "attempt_count"),
    ),
    EventTemplate(
        event_type=EventType.PROCESS,
        severity=Severity.INFO,
        message_template="systemd: Started {service_name}.service",
        metadata_keys=("service_name", "pid"),
    ),
    EventTemplate(
        event_type=EventType.NETWORK,
        severity=Severity.INFO,
        message_template="iptables: ACCEPT IN={interface} SRC={source_ip}",
        metadata_keys=("interface", "source_ip", "destination_port"),
    ),
    EventTemplate(
        event_type=EventType.SYSTEM,
        severity=Severity.INFO,
        message_template="kernel: CPU utilization at {cpu_pct}%",
        metadata_keys=("cpu_pct", "load_avg"),
    ),
    EventTemplate(
        event_type=EventType.FILE_ACCESS,
        severity=Severity.INFO,
        message_template="audit: open {file_path} by uid={uid}",
        metadata_keys=("file_path", "uid", "operation"),
    ),
]

# ---------------------------------------------------------------------------
# macOS event templates
# ---------------------------------------------------------------------------

MACOS_TEMPLATES: list[EventTemplate] = [
    EventTemplate(
        event_type=EventType.AUTHENTICATION,
        severity=Severity.INFO,
        message_template="loginwindow: Login succeeded for user {username}",
        metadata_keys=("auth_method",),
    ),
    EventTemplate(
        event_type=EventType.APPLICATION,
        severity=Severity.INFO,
        message_template="launchd: Started {app_name}",
        metadata_keys=("app_name", "bundle_id"),
    ),
    EventTemplate(
        event_type=EventType.SYSTEM,
        severity=Severity.INFO,
        message_template="kernel: Bluetooth controller power state: ON",
        metadata_keys=("device_type",),
    ),
    EventTemplate(
        event_type=EventType.NETWORK,
        severity=Severity.INFO,
        message_template="mDNSResponder: resolved {domain}",
        metadata_keys=("domain", "record_type"),
    ),
]

# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

TEMPLATES_BY_OS: dict[OSType, list[EventTemplate]] = {
    OSType.WINDOWS: WINDOWS_TEMPLATES,
    OSType.LINUX: LINUX_TEMPLATES,
    OSType.MACOS: MACOS_TEMPLATES,
}


def pick_template(os_type: OSType, rng: random.Random | None = None) -> EventTemplate:
    """Pick a random event template appropriate for the given OS.

    Uses weighted selection: authentication and system events are
    more frequent than errors or file access in normal operations.

    Args:
        os_type: The workstation's operating system.
        rng: Optional Random instance for deterministic testing.

    Returns:
        An EventTemplate matching the OS type.
    """
    templates = TEMPLATES_BY_OS[os_type]
    r = rng or random.Random()
    return r.choice(templates)
