"""Tests for Topology DTOs.

Validates Pydantic DTO schemas for the tactical map interface.
"""

import pytest
from pydantic import ValidationError

from adapters.inbound.api.dtos import (
    CoordinatesDTO,
    BranchSummaryDTO,
    BranchDetailDTO,
    WorkstationDTO,
    NetworkSegmentDTO,
    GraphNodeDTO,
    GraphEdgeDTO,
    NetworkGraphDTO,
)


class TestCoordinatesDTO:
    def test_valid_coordinates(self) -> None:
        """CoordinatesDTO accepts valid lat/lng and SVG x,y."""
        dto = CoordinatesDTO(x=620.0, y=620.0, lat=-34.6037, lng=-58.3816)
        assert dto.x == 620.0
        assert dto.y == 620.0
        assert dto.lat == -34.6037
        assert dto.lng == -58.3816


class TestBranchSummaryDTO:
    def test_valid_summary(self) -> None:
        """BranchSummaryDTO accepts valid branch summary data."""
        dto = BranchSummaryDTO(
            code="SUC001",
            name="Sucursal 001",
            city="Buenos Aires",
            coordinates=CoordinatesDTO(x=620.0, y=620.0, lat=-34.6037, lng=-58.3816),
            workstation_count=50,
            employee_count=60,
            status="online",
        )
        assert dto.code == "SUC001"
        assert dto.city == "Buenos Aires"
        assert dto.workstation_count == 50


class TestNetworkSegmentDTO:
    def test_valid_segment(self) -> None:
        """NetworkSegmentDTO accepts valid segment data."""
        dto = NetworkSegmentDTO(name="teller-vlan-001", cidr="10.1.1.0/24", vlan_id=10)
        assert dto.name == "teller-vlan-001"
        assert dto.cidr == "10.1.1.0/24"
        assert dto.vlan_id == 10


class TestWorkstationDTO:
    def test_valid_workstation(self) -> None:
        """WorkstationDTO accepts valid workstation data."""
        dto = WorkstationDTO(
            id="ws-1",
            hostname="SUC001-PC-001",
            os_type="windows",
            ip_address="10.1.1.1",
            eps=2.0,
        )
        assert dto.hostname == "SUC001-PC-001"
        assert dto.os_type == "windows"
        assert dto.eps == 2.0


class TestBranchDetailDTO:
    def test_valid_detail(self) -> None:
        """BranchDetailDTO accepts valid branch detail data."""
        dto = BranchDetailDTO(
            code="SUC001",
            name="Sucursal 001",
            city="Buenos Aires",
            coordinates=CoordinatesDTO(x=620.0, y=620.0, lat=-34.6037, lng=-58.3816),
            segments=[
                NetworkSegmentDTO(name="teller-vlan-001", cidr="10.1.1.0/24", vlan_id=10),
            ],
            workstations=[
                WorkstationDTO(
                    id="ws-1",
                    hostname="SUC001-PC-001",
                    os_type="windows",
                    ip_address="10.1.1.1",
                    eps=2.0,
                ),
            ],
        )
        assert dto.code == "SUC001"
        assert len(dto.segments) == 1
        assert len(dto.workstations) == 1


class TestGraphNodeDTO:
    def test_valid_node(self) -> None:
        """GraphNodeDTO accepts valid node data."""
        dto = GraphNodeDTO(id="router-1", label="Router", type="router", x=100.0, y=100.0)
        assert dto.id == "router-1"
        assert dto.type == "router"
        assert dto.x == 100.0
        assert dto.y == 100.0

    def test_node_without_position(self) -> None:
        """GraphNodeDTO allows optional x,y coordinates."""
        dto = GraphNodeDTO(id="switch-1", label="Switch", type="switch")
        assert dto.x is None
        assert dto.y is None


class TestGraphEdgeDTO:
    def test_valid_edge(self) -> None:
        """GraphEdgeDTO accepts valid edge data."""
        dto = GraphEdgeDTO(source="router-1", target="switch-1", type="eth")
        assert dto.source == "router-1"
        assert dto.target == "switch-1"
        assert dto.type == "eth"


class TestNetworkGraphDTO:
    def test_valid_graph(self) -> None:
        """NetworkGraphDTO accepts valid graph data."""
        dto = NetworkGraphDTO(
            nodes=[
                GraphNodeDTO(id="router-1", label="Router", type="router"),
                GraphNodeDTO(id="ws-1", label="WS", type="workstation"),
            ],
            edges=[GraphEdgeDTO(source="router-1", target="ws-1", type="eth")],
        )
        assert len(dto.nodes) == 2
        assert len(dto.edges) == 1


class TestDTOValidationErrors:
    def test_workstation_eps_must_be_non_negative(self) -> None:
        """WorkstationDTO rejects negative EPS."""
        with pytest.raises(ValidationError):
            WorkstationDTO(
                id="ws-1",
                hostname="SUC001-PC-001",
                os_type="windows",
                ip_address="10.1.1.1",
                eps=-1.0,
            )

    def test_branch_summary_workstation_count_must_be_positive(self) -> None:
        """BranchSummaryDTO rejects negative workstation count."""
        with pytest.raises(ValidationError):
            BranchSummaryDTO(
                code="SUC001",
                name="Sucursal 001",
                city="Buenos Aires",
                coordinates=CoordinatesDTO(x=0, y=0, lat=0, lng=0),
                workstation_count=-1,
                employee_count=0,
                status="online",
            )

    def test_graph_edge_requires_source_and_target(self) -> None:
        """GraphEdgeDTO requires both source and target."""
        with pytest.raises(ValidationError):
            GraphEdgeDTO(source="router-1", type="eth")

    def test_network_graph_allows_empty(self) -> None:
        """NetworkGraphDTO allows empty nodes and edges."""
        dto = NetworkGraphDTO(nodes=[], edges=[])
        assert dto.nodes == []
        assert dto.edges == []

    def test_segment_vlan_out_of_range(self) -> None:
        """NetworkSegmentDTO rejects invalid VLAN IDs."""
        with pytest.raises(ValidationError):
            NetworkSegmentDTO(name="test", cidr="10.1.1.0/24", vlan_id=5000)
