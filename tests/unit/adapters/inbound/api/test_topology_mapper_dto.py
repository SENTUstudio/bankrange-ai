"""Tests for adapter topology mapper functions.

Validates domain entity → DTO transformations.
"""

import pytest

from adapters.inbound.api.topology_mapper import (
    _to_branch_summary,
    _to_branch_detail,
    _to_network_graph,
)
from core.domain.entities import Branch, Employee, NetworkSegment, Workstation
from core.domain.value_objects import IPAddress, MacAddress, OSType


@pytest.fixture
def sample_branch() -> Branch:
    """Provide a minimal branch for mapper tests."""
    segment = NetworkSegment(name="teller-vlan-001", cidr="10.1.1.0/24", vlan_id=100)
    ws = Workstation(
        hostname="SUC001-PC-001",
        os_type=OSType.WINDOWS,
        ip_address=IPAddress(value="10.1.1.1"),
        mac_address=MacAddress(value="02:00:00:00:00:01"),
        eps=2.0,
    )
    emp = Employee(
        employee_code="EM000001",
        full_name="Employee 001-0001",
        department="operations",
        workstation_id=ws.id,
    )
    return Branch(
        code="SUC001",
        name="Sucursal 001",
        city="Buenos Aires",
        max_workstations=50,
        network_segments=[segment],
        workstations=[ws],
        employees=[emp],
    )


class TestToBranchSummary:
    def test_maps_basic_fields(self, sample_branch: Branch) -> None:
        """_to_branch_summary maps code, name, city correctly."""
        result = _to_branch_summary(sample_branch)
        assert result["code"] == "SUC001"
        assert result["name"] == "Sucursal 001"
        assert result["city"] == "Buenos Aires"

    def test_adds_coordinates(self, sample_branch: Branch) -> None:
        """Coordinates are added from the adapter mapper, not the domain."""
        result = _to_branch_summary(sample_branch)
        coords = result["coordinates"]
        assert coords["lat"] == pytest.approx(-34.6037, abs=0.0001)
        assert coords["lng"] == pytest.approx(-58.3816, abs=0.0001)
        assert coords["x"] == pytest.approx(620.0, abs=0.1)

    def test_counts_workstations_and_employees(self, sample_branch: Branch) -> None:
        """Counts are derived from branch collections."""
        result = _to_branch_summary(sample_branch)
        assert result["workstation_count"] == 1
        assert result["employee_count"] == 1

    def test_status_is_online(self, sample_branch: Branch) -> None:
        """Status defaults to online for now."""
        result = _to_branch_summary(sample_branch)
        assert result["status"] == "online"

    def test_unknown_city_returns_zero_coords(self, sample_branch: Branch) -> None:
        """Branches with unknown cities get zero coordinates."""
        branch = sample_branch.model_copy(update={"city": "Atlantis"})
        result = _to_branch_summary(branch)
        coords = result["coordinates"]
        assert coords["lat"] == 0.0
        assert coords["lng"] == 0.0
        assert coords["x"] == 0.0
        assert coords["y"] == 0.0


class TestToBranchDetail:
    def test_maps_segments(self, sample_branch: Branch) -> None:
        """_to_branch_detail includes network segments."""
        result = _to_branch_detail(sample_branch)
        assert len(result["segments"]) == 1
        assert result["segments"][0]["name"] == "teller-vlan-001"
        assert result["segments"][0]["cidr"] == "10.1.1.0/24"
        assert result["segments"][0]["vlan_id"] == 100

    def test_maps_workstations(self, sample_branch: Branch) -> None:
        """_to_branch_detail includes workstation details."""
        result = _to_branch_detail(sample_branch)
        assert len(result["workstations"]) == 1
        ws = result["workstations"][0]
        assert ws["hostname"] == "SUC001-PC-001"
        assert ws["os_type"] == "windows"
        assert ws["ip_address"] == "10.1.1.1"
        assert ws["eps"] == 2.0

    def test_includes_coordinates(self, sample_branch: Branch) -> None:
        """Branch detail also includes geographic coordinates."""
        result = _to_branch_detail(sample_branch)
        assert result["coordinates"]["lat"] == pytest.approx(-34.6037, abs=0.0001)


class TestToNetworkGraph:
    def test_creates_router_node(self, sample_branch: Branch) -> None:
        """Network graph includes a router node."""
        result = _to_network_graph(sample_branch)
        router_nodes = [n for n in result["nodes"] if n["type"] == "router"]
        assert len(router_nodes) == 1
        assert router_nodes[0]["id"] == "SUC001-router"

    def test_creates_workstation_nodes(self, sample_branch: Branch) -> None:
        """Network graph includes workstation nodes."""
        result = _to_network_graph(sample_branch)
        ws_nodes = [n for n in result["nodes"] if n["type"] == "workstation"]
        assert len(ws_nodes) == 1
        assert ws_nodes[0]["label"] == "SUC001-PC-001"

    def test_creates_segment_nodes(self, sample_branch: Branch) -> None:
        """Network graph includes segment nodes."""
        result = _to_network_graph(sample_branch)
        seg_nodes = [n for n in result["nodes"] if n["type"] == "segment"]
        assert len(seg_nodes) == 1

    def test_edges_connect_router_to_segments(self, sample_branch: Branch) -> None:
        """Edges connect router to network segments."""
        result = _to_network_graph(sample_branch)
        router_to_seg = [
            e for e in result["edges"]
            if e["source"] == "SUC001-router" and e["target"].startswith("SUC001-seg-")
        ]
        assert len(router_to_seg) == 1

    def test_edges_connect_segments_to_workstations(self, sample_branch: Branch) -> None:
        """Edges connect segments to workstations."""
        result = _to_network_graph(sample_branch)
        seg_to_ws = [
            e for e in result["edges"]
            if e["source"].startswith("SUC001-seg-") and e["target"].startswith("SUC001-ws-")
        ]
        assert len(seg_to_ws) == 1
