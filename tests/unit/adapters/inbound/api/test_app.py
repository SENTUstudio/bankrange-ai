"""Unit tests for the FastAPI C&C Inbound Adapter.

Tests the HTTP layer mapping to the Domain engine.
"""

import pytest
from fastapi.testclient import TestClient

import adapters.inbound.api.app as app_module
from adapters.inbound.api.app import EngineState


@pytest.fixture
def client(monkeypatch):
    """Provide a TestClient with background engine disabled and test state injected."""
    monkeypatch.setattr(app_module, "_start_background_engine", lambda state: None)
    with TestClient(app_module.app) as test_client:
        # Inject a fresh test state after lifespan startup
        app_module.app.state.engine = EngineState(
            is_running=True,
            multiplier_override=1.0,
            estimated_eps=0.0,
            total_workstations=100,
        )
        yield test_client


class TestEngineState:
    def test_engine_state_instances_are_independent(self) -> None:
        """Instance mutation must not leak to other instances."""
        state_a = EngineState()
        state_b = EngineState()
        state_a.is_running = True
        assert state_b.is_running is False


class TestEmaEps:
    def test_compute_ema_eps_first_sample(self) -> None:
        """EMA with alpha=0.3 on first sample should be 30% of value."""
        from adapters.inbound.api.app import _compute_ema_eps

        assert _compute_ema_eps(0.0, 100.0) == 30.0

    def test_compute_ema_eps_converges(self) -> None:
        """EMA should smooth toward the target value over iterations."""
        from adapters.inbound.api.app import _compute_ema_eps

        ema = 0.0
        ema = _compute_ema_eps(ema, 100.0)
        ema = _compute_ema_eps(ema, 100.0)
        assert ema == 51.0

    def test_status_returns_real_estimated_eps_not_tick_count(self, client) -> None:
        """GET /status must return EMA-calculated EPS, not last tick event count."""
        engine = app_module.app.state.engine
        engine.is_running = True
        engine.estimated_eps = 150.0  # Simulated EMA value

        response = client.get("/status")
        data = response.json()
        assert data["estimated_eps"] == 150.0

    def test_status_no_cached_eps_field(self, client) -> None:
        """cached_eps must no longer appear in the status response."""
        response = client.get("/status")
        assert "cached_eps" not in response.json()


class TestFastAPIApp:
    def test_status_endpoint_returns_engine_metadata(self, client) -> None:
        """GET /status should return 200 with engine metrics."""
        engine = app_module.app.state.engine
        engine.multiplier_override = 2.5
        engine.estimated_eps = 4500.5
        engine.total_workstations = 500

        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["current_multiplier"] == 2.5
        assert data["estimated_eps"] == 4500.5
        assert data["total_workstations"] == 500

    def test_control_endpoint_updates_multiplier(self, client) -> None:
        """POST /control should change the injected state multiplier."""
        engine = app_module.app.state.engine
        assert engine.multiplier_override == 1.0

        response = client.post("/control", json={"eps_multiplier": 5.0})

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Success"
        assert data["new_multiplier"] == 5.0

        # Verify the memory state actually changed
        assert engine.multiplier_override == 5.0

    def test_control_endpoint_rejects_negative_multiplier(self, client) -> None:
        """Input validation: negative EPS multipliers are impossible."""
        engine = app_module.app.state.engine
        response = client.post("/control", json={"eps_multiplier": -1.5})

        # 422 Unprocessable Entity generated natively by Pydantic/FastAPI
        assert response.status_code == 422

        # State should remain untouched
        assert engine.multiplier_override == 1.0

    def test_cors_rejects_untrusted_origin(self, client) -> None:
        """Untrusted origins must not receive CORS reflection headers."""
        response = client.get(
            "/status",
            headers={"Origin": "https://evil.com"},
        )
        assert response.status_code == 200
        # FastAPI CORSMiddleware does NOT reflect wildcard when origins is a list
        allow_origin = response.headers.get("access-control-allow-origin")
        assert allow_origin != "https://evil.com"

    def test_cors_allows_default_origin(self, client) -> None:
        """The default Streamlit origin must be permitted."""
        response = client.get(
            "/status",
            headers={"Origin": "http://localhost:8501"},
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:8501"

    def test_cors_allows_multiple_origins_from_env(self, monkeypatch) -> None:
        """ALLOWED_ORIGINS env var can specify multiple comma-separated origins."""
        import importlib

        monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:8501,https://app.example.com")
        importlib.reload(app_module)

        monkeypatch.setattr(app_module, "_start_background_engine", lambda state: None)
        with TestClient(app_module.app) as test_client:
            test_client.app.state.engine = EngineState(is_running=True, total_workstations=100)

            # First origin
            response = test_client.get("/status", headers={"Origin": "https://app.example.com"})
            assert response.status_code == 200
            assert response.headers.get("access-control-allow-origin") == "https://app.example.com"

            # Second origin (default)
            response = test_client.get("/status", headers={"Origin": "http://localhost:8501"})
            assert response.status_code == 200
            assert response.headers.get("access-control-allow-origin") == "http://localhost:8501"

    def test_lifespan_injects_engine_state(self, monkeypatch) -> None:
        """Lifespan must create an EngineState and attach it to app.state."""
        import importlib

        fresh_module = importlib.reload(app_module)
        monkeypatch.setattr(fresh_module, "_start_background_engine", lambda state: None)

        with TestClient(fresh_module.app) as test_client:
            assert hasattr(test_client.app.state, "engine")
            assert isinstance(test_client.app.state.engine, fresh_module.EngineState)
