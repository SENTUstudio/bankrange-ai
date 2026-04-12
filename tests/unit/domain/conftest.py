"""Shared fixtures for domain unit tests."""

import uuid

import pytest

from core.domain.entities import Branch, Employee, NetworkSegment, Workstation
from core.domain.log_event import LogEvent
from core.domain.value_objects import IPAddress, MacAddress, OSType
from core.ports.event_publisher import EventPublisher


class InMemoryEventPublisher(EventPublisher):
    """An event publisher that stores events in memory for testing."""

    def __init__(self) -> None:
        self.published_events: list[LogEvent] = []
        self.flushed = False

    def publish(self, event: LogEvent) -> None:
        self.published_events.append(event)

    def publish_batch(self, events: list[LogEvent]) -> None:
        self.published_events.extend(events)

    def flush(self) -> None:
        self.flushed = True

    def clear(self) -> None:
        self.published_events.clear()
        self.flushed = False


@pytest.fixture
def mock_publisher() -> InMemoryEventPublisher:
    """Fixture to provide a clean in-memory publisher for each test."""
    return InMemoryEventPublisher()


@pytest.fixture
def sample_segment() -> NetworkSegment:
    """A typical teller VLAN network segment."""
    return NetworkSegment(
        name="teller-vlan",
        cidr="10.1.1.0/24",
        vlan_id=100,
    )


@pytest.fixture
def sample_ip() -> IPAddress:
    """A valid private IP address."""
    return IPAddress(value="10.1.1.10")


@pytest.fixture
def sample_mac() -> MacAddress:
    """A valid MAC address."""
    return MacAddress(value="AA:BB:CC:DD:EE:01")


@pytest.fixture
def sample_workstation(sample_ip: IPAddress, sample_mac: MacAddress) -> Workstation:
    """A typical Windows teller workstation."""
    return Workstation(
        hostname="SUC001-PC-001",
        os_type=OSType.WINDOWS,
        ip_address=sample_ip,
        mac_address=sample_mac,
        eps=2.0,
    )


@pytest.fixture
def sample_employee() -> Employee:
    """A bank operations employee."""
    return Employee(
        employee_code="EM001234",
        full_name="María García López",
        department="operations",
    )


@pytest.fixture
def sample_branch(sample_segment: NetworkSegment) -> Branch:
    """A branch office with one network segment."""
    return Branch(
        code="SUC001",
        name="Sucursal Centro",
        city="Buenos Aires",
        max_workstations=50,
        network_segments=[sample_segment],
    )
