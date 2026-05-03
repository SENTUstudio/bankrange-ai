"""Unit tests for domain Entities.

Tests validate the business rules and invariants of Branch,
NetworkSegment, Workstation, and Employee as defined by the
BankRange domain model.
"""

import uuid

import pytest
from pydantic import ValidationError

from core.domain.entities import Branch, Employee, NetworkSegment, Workstation
from core.domain.exceptions import SegmentCapacityExceededError, WorkstationLimitExceededError
from core.domain.value_objects import IPAddress, MacAddress, OSType


class TestNetworkSegment:
    """A network segment defines CIDR bounds for workstation IPs."""

    def test_valid_segment_is_created(self, sample_segment: NetworkSegment) -> None:
        """A segment with valid private CIDR and VLAN is accepted."""
        assert sample_segment.name == "teller-vlan"
        assert sample_segment.cidr == "10.1.1.0/24"
        assert sample_segment.vlan_id == 100

    def test_segment_capacity_for_slash_24(self) -> None:
        """A /24 CIDR block has 254 usable host addresses."""
        segment = NetworkSegment(
            name="test-segment",
            cidr="10.0.0.0/24",
            vlan_id=10,
        )
        assert segment.capacity == 254

    def test_public_cidr_is_rejected(self) -> None:
        """Network segments must use private address space."""
        with pytest.raises(ValueError, match="private CIDR"):
            NetworkSegment(
                name="invalid-segment",
                cidr="8.8.8.0/24",
                vlan_id=10,
            )

    def test_allocate_ip_returns_correct_address(self) -> None:
        """IP allocation returns the Nth usable host in the CIDR."""
        segment = NetworkSegment(
            name="test-segment",
            cidr="10.1.1.0/24",
            vlan_id=10,
        )
        ip = segment.allocate_ip(0)
        assert ip.value == "10.1.1.1"

        ip = segment.allocate_ip(9)
        assert ip.value == "10.1.1.10"

    def test_allocate_ip_beyond_capacity_raises(self) -> None:
        """Cannot allocate more IPs than the segment supports."""
        segment = NetworkSegment(
            name="tiny-segment",
            cidr="10.1.1.0/30",  # Only 2 usable IPs
            vlan_id=10,
        )
        assert segment.capacity == 2

        with pytest.raises(SegmentCapacityExceededError, match="capacity of 2"):
            segment.allocate_ip(2)


class TestWorkstation:
    """A workstation generates log events at a given EPS rate."""

    def test_valid_workstation_is_created(self, sample_workstation: Workstation) -> None:
        """Workstation with valid hostname, IP, MAC, and OS is accepted."""
        assert sample_workstation.hostname == "SUC001-PC-001"
        assert sample_workstation.os_type == OSType.WINDOWS
        assert sample_workstation.eps == 2.0

    def test_hostname_must_follow_bank_convention(self) -> None:
        """Hostnames must match BRANCH-TYPE-SEQ pattern."""
        with pytest.raises(ValidationError, match="hostname"):
            Workstation(
                hostname="my-laptop",  # Invalid: no bank convention
                os_type=OSType.WINDOWS,
                ip_address=IPAddress(value="10.1.1.10"),
                mac_address=MacAddress(value="AA:BB:CC:DD:EE:01"),
            )

    def test_eps_must_be_positive(self) -> None:
        """Events per second must be greater than zero."""
        with pytest.raises(ValidationError, match="eps"):
            Workstation(
                hostname="SUC001-PC-001",
                os_type=OSType.WINDOWS,
                ip_address=IPAddress(value="10.1.1.10"),
                mac_address=MacAddress(value="AA:BB:CC:DD:EE:01"),
                eps=0,
            )


class TestEmployee:
    """An employee is a bank staff member assigned to a workstation."""

    def test_valid_employee_is_created(self, sample_employee: Employee) -> None:
        """Employee with valid code, name, and department is accepted."""
        assert sample_employee.employee_code == "EM001234"
        assert sample_employee.full_name == "María García López"
        assert sample_employee.department == "operations"
        assert sample_employee.workstation_id is None

    def test_employee_code_must_follow_format(self) -> None:
        """Employee code must be 2 uppercase letters + 4-8 digits."""
        with pytest.raises(ValidationError, match="employee_code"):
            Employee(
                employee_code="invalid",
                full_name="Test User",
                department="operations",
            )

    def test_employee_can_be_assigned_to_workstation(self) -> None:
        """An employee may be assigned to a specific workstation."""
        ws_id = uuid.uuid4()
        employee = Employee(
            employee_code="EM005678",
            full_name="Juan Pérez",
            department="treasury",
            workstation_id=ws_id,
        )
        assert employee.workstation_id == ws_id


class TestBranch:
    """A branch is the aggregate root of the banking topology."""

    def test_valid_branch_is_created(self, sample_branch: Branch) -> None:
        """Branch with valid code, name, city, and segments is accepted."""
        assert sample_branch.code == "SUC001"
        assert sample_branch.name == "Sucursal Centro"
        assert sample_branch.city == "Buenos Aires"
        assert len(sample_branch.network_segments) == 1

    def test_branch_code_must_follow_convention(self) -> None:
        """Branch code must be 3 uppercase letters + 3-4 digits."""
        with pytest.raises(ValidationError, match="code"):
            Branch(
                code="invalid",
                name="Test Branch",
                city="Test City",
                max_workstations=10,
            )

    def test_exceeding_workstation_capacity_raises(self) -> None:
        """A branch cannot have more workstations than its capacity."""
        workstations = [
            Workstation(
                hostname=f"SUC001-PC-{i:03d}",
                os_type=OSType.WINDOWS,
                ip_address=IPAddress(value=f"10.1.1.{i + 1}"),
                mac_address=MacAddress(value=f"AA:BB:CC:DD:EE:{i:02X}"),
            )
            for i in range(3)
        ]

        with pytest.raises(
            WorkstationLimitExceededError,
            match="max capacity is 2",
        ):
            Branch(
                code="SUC001",
                name="Tiny Branch",
                city="Test City",
                max_workstations=2,  # Only 2 allowed
                workstations=workstations,  # But we send 3
            )
