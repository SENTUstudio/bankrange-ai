"""Topology DTOs for the tactical map API.

These Pydantic models define the API contract for topology endpoints.
They are pure data schemas with no business logic.
"""

from pydantic import BaseModel, Field


class CoordinatesDTO(BaseModel):
    """Geographic and SVG coordinates for a branch."""

    x: float = Field(description="SVG x coordinate (0-1000)")
    y: float = Field(description="SVG y coordinate (0-1000)")
    lat: float = Field(description="Real-world latitude")
    lng: float = Field(description="Real-world longitude")


class BranchSummaryDTO(BaseModel):
    """Summary information for a branch on the map."""

    code: str = Field(description="Branch code (e.g., 'SUC001')")
    name: str = Field(description="Branch display name")
    city: str = Field(description="City where the branch is located")
    coordinates: CoordinatesDTO = Field(description="Geographic and SVG coordinates")
    workstation_count: int = Field(ge=0, description="Number of workstations")
    employee_count: int = Field(ge=0, description="Number of employees")
    status: str = Field(description="Branch status: online, degraded, offline")


class NetworkSegmentDTO(BaseModel):
    """Network segment information."""

    name: str = Field(description="Segment name (e.g., 'teller-vlan-001')")
    cidr: str = Field(description="CIDR block (e.g., '10.1.1.0/24')")
    vlan_id: int = Field(ge=1, le=4094, description="IEEE 802.1Q VLAN identifier")


class WorkstationDTO(BaseModel):
    """Workstation information for branch detail."""

    id: str = Field(description="Workstation identifier")
    hostname: str = Field(description="Hostname (e.g., 'SUC001-PC-001')")
    os_type: str = Field(description="Operating system type")
    ip_address: str = Field(description="IPv4 address")
    eps: float = Field(ge=0.0, description="Events per second baseline rate")


class BranchDetailDTO(BaseModel):
    """Detailed information for a single branch."""

    code: str = Field(description="Branch code")
    name: str = Field(description="Branch display name")
    city: str = Field(description="City where the branch is located")
    coordinates: CoordinatesDTO = Field(description="Geographic and SVG coordinates")
    segments: list[NetworkSegmentDTO] = Field(description="Network segments")
    workstations: list[WorkstationDTO] = Field(description="Workstations")


class GraphNodeDTO(BaseModel):
    """Node in a network graph."""

    id: str = Field(description="Unique node identifier")
    label: str = Field(description="Human-readable label")
    type: str = Field(description="Node type: router, switch, workstation, segment")
    x: float | None = Field(default=None, description="Optional pre-computed x position")
    y: float | None = Field(default=None, description="Optional pre-computed y position")


class GraphEdgeDTO(BaseModel):
    """Edge connecting two nodes in a network graph."""

    source: str = Field(description="Source node id")
    target: str = Field(description="Target node id")
    type: str = Field(description="Edge type: eth, wifi, vlan")


class NetworkGraphDTO(BaseModel):
    """Complete network graph for D3-force rendering."""

    nodes: list[GraphNodeDTO] = Field(description="Graph nodes")
    edges: list[GraphEdgeDTO] = Field(description="Graph edges")
