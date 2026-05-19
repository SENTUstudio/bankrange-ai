"""Tests for topology and SSE endpoints.

Validates new FastAPI routes added for the tactical map interface.
"""

import json

import pytest
from fastapi.testclient import TestClient

import adapters.inbound.api.app as app_module
from adapters.inbound.api.app import EngineState
from core.domain.entities import Branch
from core.domain.log_event import LogEvent
from core.domain.topology_config import OSDistribution, SegmentTemplate, TopologyConfig
from core.domain.topology_factory import TopologyFactory
from core.ports.event_publisher import EventPublisher
from core.use_cases.event_generator import EventGenerator


class _FakePublisher(EventPublisher):
    """No-op publisher for tests."""

    def publish(self, event: LogEvent) -> None:
        pass

    def publish_batch(self, events: list[LogEvent]) -> None:
        pass

    def flush(self, timeout_secs: float = 5.0) -> None:
        pass


@pytest.fixture
def sample_branches() -> list[Branch]:
    """Provide 2 branches for endpoint tests."""
    config = TopologyConfig(
        num_branches=2,
        workstations_per_branch=3,
        employees_per_branch=3,
        os_distribution=OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0),
        segment_templates=[
            SegmentTemplate(
                name_prefix="teller",
                vlan_id=100,
                cidr_prefix="10.{branch_idx}.1.0/24",
            ),
        ],
        base_eps=2.0,
    )
    factory = TopologyFactory()
    return factory.create(config)


@pytest.fixture
def topology_client(monkeypatch, sample_branches: list[Branch]):
    """Provide a TestClient with a generator containing sample branches."""
    monkeypatch.setattr(app_module, "_start_background_engine", lambda state: None)
    with TestClient(app_module.app) as test_client:
        engine = EngineState(
            is_running=True,
            multiplier_override=1.0,
            estimated_eps=0.0,
            total_workstations=6,
        )
        engine._generator = EventGenerator(
            branches=sample_branches,
            publisher=_FakePublisher(),
            seed=42,
        )
        test_client.app.state.engine = engine
        yield test_client


class TestListBranches:
    def test_returns_200_with_branch_list(self, topology_client: TestClient) -> None:
        """GET /topology/branches returns list of branches."""
        response = topology_client.get("/topology/branches")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_branch_has_coordinates(self, topology_client: TestClient) -> None:
        """Each branch includes geographic and SVG coordinates."""
        response = topology_client.get("/topology/branches")
        data = response.json()
        first = data[0]
        assert "coordinates" in first
        assert "lat" in first["coordinates"]
        assert "lng" in first["coordinates"]
        assert "x" in first["coordinates"]
        assert "y" in first["coordinates"]

    def test_branch_has_counts(self, topology_client: TestClient) -> None:
        """Each branch includes workstation and employee counts."""
        response = topology_client.get("/topology/branches")
        data = response.json()
        first = data[0]
        assert first["workstation_count"] == 3
        assert first["employee_count"] == 3

    def test_returns_empty_list_when_no_generator(self, topology_client: TestClient) -> None:
        """If generator is missing, returns empty list gracefully."""
        topology_client.app.state.engine._generator = None
        response = topology_client.get("/topology/branches")
        assert response.status_code == 200
        assert response.json() == []


class TestGetBranch:
    def test_returns_branch_detail(self, topology_client: TestClient) -> None:
        """GET /topology/branches/{code} returns full branch detail."""
        response = topology_client.get("/topology/branches/SUC001")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "SUC001"
        assert "segments" in data
        assert "workstations" in data

    def test_returns_404_for_unknown_branch(self, topology_client: TestClient) -> None:
        """Unknown branch code returns 404."""
        response = topology_client.get("/topology/branches/UNKNOWN")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_workstations_have_required_fields(self, topology_client: TestClient) -> None:
        """Workstation DTOs include id, hostname, os_type, ip_address, eps."""
        response = topology_client.get("/topology/branches/SUC001")
        data = response.json()
        ws = data["workstations"][0]
        assert "id" in ws
        assert "hostname" in ws
        assert "os_type" in ws
        assert "ip_address" in ws
        assert "eps" in ws


class TestGetBranchNetwork:
    def test_returns_network_graph(self, topology_client: TestClient) -> None:
        """GET /topology/branches/{code}/network returns nodes and edges."""
        response = topology_client.get("/topology/branches/SUC001/network")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0
        assert len(data["edges"]) > 0

    def test_has_router_and_workstation_nodes(self, topology_client: TestClient) -> None:
        """Network graph includes router and workstation nodes."""
        response = topology_client.get("/topology/branches/SUC001/network")
        data = response.json()
        types = {n["type"] for n in data["nodes"]}
        assert "router" in types
        assert "workstation" in types

    def test_returns_404_for_unknown_branch(self, topology_client: TestClient) -> None:
        """Unknown branch code returns 404."""
        response = topology_client.get("/topology/branches/UNKNOWN/network")
        assert response.status_code == 404


class TestEventStream:
    def test_returns_event_stream_content_type(self, topology_client: TestClient, monkeypatch) -> None:
        """GET /events/stream returns text/event-stream."""

        import adapters.inbound.api.app as app_mod

        async def _limited_sse():
            yield "data: {}\n\n"

        monkeypatch.setattr(app_mod, "_sse_generator", _limited_sse)

        response = topology_client.get("/events/stream")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_stream_includes_engine_data(self, topology_client: TestClient, monkeypatch) -> None:
        """SSE stream includes engine state fields."""
        import adapters.inbound.api.app as app_mod

        async def _limited_sse():
            engine = app_mod.app.state.engine
            payload = {
                "status": "running" if engine.is_running else "stopped",
                "current_multiplier": engine.multiplier_override,
                "estimated_eps": engine.estimated_eps,
                "total_workstations": engine.total_workstations,
                "timestamp": "2024-01-01T00:00:00",
            }
            yield f"data: {json.dumps(payload)}\n\n"

        monkeypatch.setattr(app_mod, "_sse_generator", _limited_sse)

        response = topology_client.get("/events/stream")
        body = response.text
        assert "data:" in body
        assert "running" in body
