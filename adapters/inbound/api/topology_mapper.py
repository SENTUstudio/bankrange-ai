"""Topology Mapper — Adapter layer coordinate mapping and DTO conversion.

This module lives in the adapter layer (infrastructure concern).
It maps domain entities to presentation DTOs and adds geographic
coordinates that are NOT part of the domain model.
"""

from core.domain.entities import Branch

# Real lat/lng and artistic SVG coordinates for 8 Argentine cities.
# Coordinates are presentation concerns and belong in the adapter layer.
_CITY_COORDINATES: dict[str, dict[str, float]] = {
    "Buenos Aires": {
        "lat": -34.6037,
        "lng": -58.3816,
        "x": 620.0,
        "y": 620.0,
    },
    "Córdoba": {
        "lat": -31.4201,
        "lng": -64.1888,
        "x": 480.0,
        "y": 450.0,
    },
    "Rosario": {
        "lat": -32.9442,
        "lng": -60.6505,
        "x": 550.0,
        "y": 520.0,
    },
    "Mendoza": {
        "lat": -32.8895,
        "lng": -68.8458,
        "x": 320.0,
        "y": 480.0,
    },
    "Tucumán": {
        "lat": -26.8083,
        "lng": -65.2176,
        "x": 420.0,
        "y": 280.0,
    },
    "La Plata": {
        "lat": -34.9215,
        "lng": -57.9545,
        "x": 670.0,
        "y": 650.0,
    },
    "Mar del Plata": {
        "lat": -38.0055,
        "lng": -57.5426,
        "x": 700.0,
        "y": 740.0,
    },
    "Salta": {
        "lat": -24.7821,
        "lng": -65.4232,
        "x": 380.0,
        "y": 220.0,
    },
}


def get_city_coordinates(city: str) -> dict[str, float]:
    """Return coordinates for a given city.

    Args:
        city: City name as assigned by TopologyFactory.

    Returns:
        dict with lat, lng, x, y. Returns zeros for unknown cities.
    """
    return _CITY_COORDINATES.get(city, {"lat": 0.0, "lng": 0.0, "x": 0.0, "y": 0.0})


def _to_branch_summary(branch: Branch) -> dict:
    """Convert a Branch domain entity to a BranchSummaryDTO dict.

    Args:
        branch: Domain entity from TopologyFactory.

    Returns:
        dict matching BranchSummaryDTO schema.
    """
    coords = get_city_coordinates(branch.city)
    return {
        "code": branch.code,
        "name": branch.name,
        "city": branch.city,
        "coordinates": coords,
        "workstation_count": len(branch.workstations),
        "employee_count": len(branch.employees),
        "status": "online",
    }


def _to_branch_detail(branch: Branch) -> dict:
    """Convert a Branch domain entity to a BranchDetailDTO dict.

    Args:
        branch: Domain entity from TopologyFactory.

    Returns:
        dict matching BranchDetailDTO schema.
    """
    coords = get_city_coordinates(branch.city)
    return {
        "code": branch.code,
        "name": branch.name,
        "city": branch.city,
        "coordinates": coords,
        "segments": [
            {
                "name": seg.name,
                "cidr": seg.cidr,
                "vlan_id": seg.vlan_id,
            }
            for seg in branch.network_segments
        ],
        "workstations": [
            {
                "id": str(ws.id),
                "hostname": ws.hostname,
                "os_type": ws.os_type.value,
                "ip_address": ws.ip_address.value,
                "eps": ws.eps,
            }
            for ws in branch.workstations
        ],
        "employees": [
            {
                "id": str(emp.id),
                "employee_code": emp.employee_code,
                "full_name": emp.full_name,
                "department": emp.department,
                "workstation_id": str(emp.workstation_id) if emp.workstation_id else None,
            }
            for emp in branch.employees
        ],
    }


def _to_network_graph(branch: Branch) -> dict:
    """Convert a Branch domain entity to a NetworkGraphDTO dict.

    Creates nodes for router, segments, and workstations.
    Creates edges connecting router → segments → workstations.

    Args:
        branch: Domain entity from TopologyFactory.

    Returns:
        dict matching NetworkGraphDTO schema.
    """
    nodes: list[dict] = []
    edges: list[dict] = []

    # Router node
    router_id = f"{branch.code}-router"
    nodes.append({
        "id": router_id,
        "label": f"Router {branch.code}",
        "type": "router",
    })

    # Segment nodes and router → segment edges
    for seg in branch.network_segments:
        seg_id = f"{branch.code}-seg-{seg.vlan_id}"
        nodes.append({
            "id": seg_id,
            "label": seg.name,
            "type": "segment",
        })
        edges.append({
            "source": router_id,
            "target": seg_id,
            "type": "eth",
        })

    # Workstation nodes and segment → workstation edges
    for ws in branch.workstations:
        ws_id = f"{branch.code}-ws-{ws.hostname}"
        nodes.append({
            "id": ws_id,
            "label": ws.hostname,
            "type": "workstation",
        })
        # Connect to first segment (primary segment for workstations)
        if branch.network_segments:
            seg_id = f"{branch.code}-seg-{branch.network_segments[0].vlan_id}"
            edges.append({
                "source": seg_id,
                "target": ws_id,
                "type": "eth",
            })

    return {"nodes": nodes, "edges": edges}
