"""EventGenerator — the core use case of BankRange Phase 1.

This is the heart of the simulator. It takes a topology (branches
with workstations) and produces a continuous stream of LogEvents,
pushing them through the EventPublisher port.

Architecture:
    TopologyFactory  →  [Branch/Workstation]
                              ↓
    EventGenerator  ←  TemporalProfile (EPS modulation)
         ↓              ←  EventTemplates (content)
    EventPublisher  →  (Kafka / File / Memory)

The generator is a PURE USE CASE — it depends only on:
- Domain entities (Branch, Workstation, LogEvent)
- Domain services (TemporalProfile, EventTemplates)
- Output port interface (EventPublisher)

It does NOT know about Kafka, files, or any infrastructure.
"""

import random
from datetime import UTC, datetime

from core.domain.entities import Branch, Employee, Workstation
from core.domain.event_templates import EventTemplate, pick_template
from core.domain.log_event import LogEvent
from core.domain.temporal import BANK_WORKDAY_PROFILE, TemporalProfile
from core.ports.event_publisher import EventPublisher


class EventGenerator:
    """Generates realistic log events for a bank topology.

    The generator produces one "tick" worth of events for all
    workstations across all branches. Each tick represents one
    second of simulated time.

    Usage:
        generator = EventGenerator(
            branches=topology,
            publisher=kafka_publisher,
        )
        events = generator.generate_tick(current_time)
    """

    def __init__(
        self,
        branches: list[Branch],
        publisher: EventPublisher,
        temporal_profile: TemporalProfile | None = None,
        seed: int | None = None,
    ) -> None:
        """Initialize the event generator.

        Args:
            branches: The bank topology (from TopologyFactory).
            publisher: Output port for publishing events.
            temporal_profile: EPS modulation profile. Defaults to
                BANK_WORKDAY_PROFILE.
            seed: Random seed for reproducible event generation.
        """
        self._branches = branches
        self._publisher = publisher
        self._profile = temporal_profile or BANK_WORKDAY_PROFILE
        self._rng = random.Random(seed)
        self._scale_multiplier: float = 1.0

        # Pre-compute the flat list of (workstation, branch_code) for speed
        self._workstation_registry: list[tuple[Workstation, str]] = []
        for branch in branches:
            for ws in branch.workstations:
                self._workstation_registry.append((ws, branch.code))

        # Map workstation_id → Employee for username resolution
        self._employee_map: dict[str, Employee] = {}
        for branch in branches:
            for emp in branch.employees:
                if emp.workstation_id is not None:
                    self._employee_map[str(emp.workstation_id)] = emp

    @property
    def branches(self) -> list[Branch]:
        """The bank topology branches."""
        return self._branches

    @property
    def total_workstations(self) -> int:
        """Total number of workstations in the topology."""
        return len(self._workstation_registry)

    def set_scale_multiplier(self, multiplier: float) -> None:
        """Apply a runtime volume scaling factor.

        Args:
            multiplier: Scale factor. Must be >= 0.

        Raises:
            ValueError: If multiplier is negative.
        """
        if multiplier < 0:
            raise ValueError("Scale multiplier must be >= 0")
        self._scale_multiplier = multiplier

    def estimated_eps(self, dt: datetime) -> float:
        """Estimate total EPS for the topology at a given time.

        This is useful for dashboards and capacity planning.

        Args:
            dt: The datetime to calculate EPS for.

        Returns:
            Estimated total events per second across all workstations.
        """
        multiplier = self._profile.get_multiplier(dt)
        return sum(ws.eps * multiplier for ws, _ in self._workstation_registry) * self._scale_multiplier

    def generate_tick(self, tick_time: datetime | None = None) -> list[LogEvent]:
        """Generate one second worth of events for all workstations.

        For each workstation, the number of events generated depends on:
        - base EPS (workstation.eps)
        - temporal multiplier (based on hour of day)
        - randomness (Poisson-like variation)

        Events are published through the EventPublisher port AND
        returned for inspection/testing.

        Args:
            tick_time: The simulated timestamp. Defaults to now(UTC).

        Returns:
            List of generated LogEvents.
        """
        tick_time = tick_time or datetime.now(UTC)
        multiplier = self._profile.get_multiplier(tick_time)
        events: list[LogEvent] = []

        for ws, branch_code in self._workstation_registry:
            effective_eps = ws.eps * multiplier * self._scale_multiplier
            # Determine how many events this workstation produces this tick
            num_events = self._poisson_count(effective_eps)

            for _ in range(num_events):
                template = pick_template(ws.os_type, self._rng)
                event = self._create_event(ws, branch_code, template, tick_time)
                events.append(event)

        # Publish the batch
        if events:
            self._publisher.publish_batch(events)

        return events

    def _create_event(
        self,
        ws: Workstation,
        branch_code: str,
        template: EventTemplate,
        timestamp: datetime,
    ) -> LogEvent:
        """Create a LogEvent from a workstation and template."""
        hour = timestamp.hour
        username = self._get_username(ws, hour)
        metadata = self._generate_metadata(template)
        message = template.message_template.format_map({**metadata, "username": username})

        return LogEvent(
            timestamp=timestamp,
            hostname=ws.hostname,
            ip_address=ws.ip_address.value,
            os_type=ws.os_type,
            username=username,
            branch_code=branch_code,
            event_type=template.event_type,
            severity=template.severity,
            message=message,
            metadata=metadata,
        )

    def _poisson_count(self, rate: float) -> int:
        """Generate a Poisson-distributed count for event generation.

        This gives realistic variation: sometimes 0 events, sometimes
        3-4 events, averaging around the effective EPS rate.
        """
        if rate <= 0:
            return 0
        # Use the random module's approach for Poisson
        # For small rates, this is efficient enough
        count = 0
        p = 1.0
        l_val = 2.71828 ** (-rate)  # e^(-rate)
        while True:
            count += 1
            p *= self._rng.random()
            if p < l_val:
                break
        return count - 1

    def _get_username(self, ws: Workstation, hour: int = 9) -> str:
        """Get the username for a workstation's events.

        Returns the assigned employee's username if they are on shift,
        otherwise 'SYSTEM' (batch jobs, security scans, etc.).
        """
        emp = self._employee_map.get(str(ws.id))
        if emp is not None and emp.is_on_shift(hour):
            # Derive a login-style username from full name: "Maria González" → "m.gonzalez"
            parts = emp.full_name.lower().split()
            return f"{parts[0][0]}.{parts[-1]}" if len(parts) >= 2 else parts[0]
        return "SYSTEM"

    def _generate_metadata(self, template: EventTemplate) -> dict:
        """Generate realistic metadata values for an event template."""
        metadata: dict = {}

        for key in template.metadata_keys:
            metadata[key] = self._metadata_value_for(key)

        return metadata

    def _metadata_value_for(self, key: str) -> str | int:
        """Generate a plausible value for a metadata field."""
        generators: dict = {
            # Windows-specific
            "windows_event_id": lambda: self._rng.choice(
                [4624, 4625, 4634, 4688, 4689, 4663, 1102]
            ),
            "logon_type": lambda: self._rng.choice([2, 3, 7, 10]),
            "failure_reason": lambda: self._rng.choice(
                ["bad_password", "account_locked", "expired_password"]
            ),
            "process_name": lambda: self._rng.choice(
                [
                    "explorer.exe",
                    "chrome.exe",
                    "outlook.exe",
                    "excel.exe",
                    "svchost.exe",
                    "notepad.exe",
                ]
            ),
            "process_id": lambda: self._rng.randint(1000, 65535),
            "exit_code": lambda: self._rng.choice([0, 0, 0, 1, -1]),
            "access_mask": lambda: self._rng.choice(["0x1", "0x2", "0x4", "0x20"]),
            "update_status": lambda: self._rng.choice(
                ["no_updates", "updates_available", "installing"]
            ),
            # Network
            "destination_ip": lambda: (
                f"10.{self._rng.randint(1, 10)}."
                f"{self._rng.randint(1, 254)}.{self._rng.randint(1, 254)}"
            ),
            "destination_port": lambda: self._rng.choice([80, 443, 8080, 3389, 22, 53, 389, 636]),
            "source_port": lambda: self._rng.randint(49152, 65535),
            "source_ip": lambda: (
                f"10.{self._rng.randint(1, 10)}."
                f"{self._rng.randint(1, 254)}.{self._rng.randint(1, 254)}"
            ),
            "protocol": lambda: self._rng.choice(["TCP", "UDP", "TLS"]),
            "interface": lambda: self._rng.choice(["eth0", "eth1", "bond0"]),
            "domain": lambda: self._rng.choice(
                [
                    "bank-intranet.local",
                    "mail.bank.local",
                    "updates.microsoft.com",
                    "ntp.ubuntu.com",
                ]
            ),
            "record_type": lambda: self._rng.choice(["A", "AAAA", "CNAME"]),
            # Linux
            "ssh_method": lambda: self._rng.choice(["publickey", "password"]),
            "service_name": lambda: self._rng.choice(
                ["nginx", "postgresql", "redis", "sshd", "cron"]
            ),
            "pid": lambda: self._rng.randint(1, 32768),
            "cpu_pct": lambda: self._rng.randint(5, 95),
            "load_avg": lambda: round(self._rng.uniform(0.1, 4.0), 2),
            "uid": lambda: self._rng.choice([0, 1000, 1001, 33, 65534]),
            "operation": lambda: self._rng.choice(["read", "write", "execute"]),
            "attempt_count": lambda: self._rng.randint(1, 5),
            # File
            "file_path": lambda: self._rng.choice(
                [
                    "C:\\Users\\employee\\Documents\\report.xlsx",
                    "C:\\Program Files\\BankApp\\config.ini",
                    "/var/log/syslog",
                    "/etc/passwd",
                    "/home/admin/.ssh/authorized_keys",
                    "C:\\Windows\\System32\\cmd.exe",
                ]
            ),
            # Application
            "app_name": lambda: self._rng.choice(
                [
                    "BankCoreApp",
                    "OutlookDesktop",
                    "ChromeBrowser",
                    "ExcelReporting",
                    "VPNClient",
                    "AntivirusEngine",
                ]
            ),
            "app_version": lambda: (
                f"{self._rng.randint(1, 5)}.{self._rng.randint(0, 9)}.{self._rng.randint(0, 99)}"
            ),
            "bundle_id": lambda: "com.bank.app",
            "error_code": lambda: self._rng.choice(
                ["E_TIMEOUT", "E_MEMORY", "E_NETWORK", "E_CONFIG"]
            ),
            "ntp_server": lambda: self._rng.choice(
                ["time.windows.com", "pool.ntp.org", "ntp.ubuntu.com"]
            ),
            "device_type": lambda: "bluetooth_controller",
            "auth_method": lambda: self._rng.choice(["password", "touchid", "smartcard"]),
        }

        generator = generators.get(key)
        if generator:
            return generator()  # type: ignore[no-any-return]
        return f"unknown_{key}"
