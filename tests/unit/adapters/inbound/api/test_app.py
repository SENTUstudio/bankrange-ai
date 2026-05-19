"""Unit tests for the FastAPI C&C Inbound Adapter.

Tests the HTTP layer mapping to the Domain engine.
"""

import contextlib

import pytest
from fastapi.middleware.cors import CORSMiddleware
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
            deployed=False,
            multiplier_override=0.0,
            estimated_eps=0.0,
            total_workstations=100,
        )
        yield test_client


class TestEngineState:
    def test_engine_state_instances_are_independent(self) -> None:
        """Instance mutation must not leak to other instances."""
        state_a = EngineState()
        state_b = EngineState()
        state_a.deployed = True
        assert state_b.deployed is False


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
    def test_status_endpoint_returns_stopped_when_not_deployed(self, client) -> None:
        """GET /status should return 'stopped' when engine is not deployed."""
        engine = app_module.app.state.engine
        engine.deployed = False
        engine.multiplier_override = 0.0
        engine.estimated_eps = 0.0
        engine.total_workstations = 500

        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"
        assert data["current_multiplier"] == 0.0
        assert data["estimated_eps"] == 0.0
        assert data["total_workstations"] == 500

    def test_status_endpoint_returns_running_when_deployed(self, client) -> None:
        """GET /status should return 'running' when engine is deployed."""
        engine = app_module.app.state.engine
        engine.deployed = True
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

    def test_control_endpoint_deploys_engine(self, client) -> None:
        """POST /control with eps_multiplier > 0 should deploy the engine."""
        engine = app_module.app.state.engine
        engine.deployed = False
        engine.multiplier_override = 0.0

        response = client.post("/control", json={"eps_multiplier": 5.0})

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Engine deployed"
        assert data["new_multiplier"] == 5.0

        # Verify the memory state actually changed
        assert engine.deployed is True
        assert engine.multiplier_override == 5.0

    def test_control_endpoint_stops_engine(self, client) -> None:
        """POST /control with eps_multiplier == 0 should stop the engine."""
        engine = app_module.app.state.engine
        engine.deployed = True
        engine.multiplier_override = 5.0

        response = client.post("/control", json={"eps_multiplier": 0.0})

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Engine stopped"
        assert data["new_multiplier"] == 0.0

        # Verify the memory state actually changed
        assert engine.deployed is False
        assert engine.multiplier_override == 0.0

    def test_control_endpoint_rejects_negative_multiplier(self, client) -> None:
        """Input validation: negative EPS multipliers are impossible."""
        engine = app_module.app.state.engine
        engine.multiplier_override = 2.0
        response = client.post("/control", json={"eps_multiplier": -1.5})

        # 422 Unprocessable Entity generated natively by Pydantic/FastAPI
        assert response.status_code == 422

        # State should remain untouched
        assert engine.multiplier_override == 2.0

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
        """The default UI origin must be permitted."""
        response = client.get(
            "/status",
            headers={"Origin": "http://localhost:8080"},
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:8080"

    def test_cors_allows_multiple_origins_from_env(self, monkeypatch) -> None:
        """ALLOWED_ORIGINS env var can specify multiple comma-separated origins."""
        import importlib

        monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:8080,https://app.example.com")
        importlib.reload(app_module)

        monkeypatch.setattr(app_module, "_start_background_engine", lambda state: None)
        with TestClient(app_module.app) as test_client:
            test_client.app.state.engine = EngineState(is_running=True, deployed=False, multiplier_override=0.0, total_workstations=100)

            # First origin
            response = test_client.get("/status", headers={"Origin": "https://app.example.com"})
            assert response.status_code == 200
            assert response.headers.get("access-control-allow-origin") == "https://app.example.com"

            # Second origin (default)
            response = test_client.get("/status", headers={"Origin": "http://localhost:8080"})
            assert response.status_code == 200
            assert response.headers.get("access-control-allow-origin") == "http://localhost:8080"

    def test_lifespan_injects_engine_state(self, monkeypatch) -> None:
        """Lifespan must create an EngineState and attach it to app.state."""
        import importlib

        fresh_module = importlib.reload(app_module)
        monkeypatch.setattr(fresh_module, "_start_background_engine", lambda state: None)

        with TestClient(fresh_module.app) as test_client:
            assert hasattr(test_client.app.state, "engine")
            assert isinstance(test_client.app.state.engine, fresh_module.EngineState)


class TestTopologyEndpoints:
    def test_list_branches_returns_empty_when_no_generator(self, client) -> None:
        """GET /topology/branches should return [] when generator is None."""
        app_module.app.state.engine._generator = None

        response = client.get("/topology/branches")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_branch_raises_404_when_no_generator(self, client) -> None:
        """GET /topology/branches/{code} should 404 when generator is None."""
        app_module.app.state.engine._generator = None

        response = client.get("/topology/branches/SUC001")
        assert response.status_code == 404
        assert response.json()["detail"] == "Branch not found"

    def test_get_branch_network_raises_404_when_no_generator(self, client) -> None:
        """GET /topology/branches/{code}/network should 404 when generator is None."""
        app_module.app.state.engine._generator = None

        response = client.get("/topology/branches/SUC001/network")
        assert response.status_code == 404
        assert response.json()["detail"] == "Branch not found"

    def test_get_branch_raises_404_for_unknown_branch(self, client) -> None:
        """GET /topology/branches/{code} should 404 for non-existent branch."""
        from unittest.mock import MagicMock

        mock_generator = MagicMock()
        mock_generator.branches = []
        app_module.app.state.engine._generator = mock_generator

        response = client.get("/topology/branches/UNKNOWN")
        assert response.status_code == 404
        assert response.json()["detail"] == "Branch not found"

    def test_get_branch_network_raises_404_for_unknown_branch(self, client) -> None:
        """GET /topology/branches/{code}/network should 404 for non-existent branch."""
        from unittest.mock import MagicMock

        mock_generator = MagicMock()
        mock_generator.branches = []
        app_module.app.state.engine._generator = mock_generator

        response = client.get("/topology/branches/UNKNOWN/network")
        assert response.status_code == 404
        assert response.json()["detail"] == "Branch not found"


class TestSseGenerator:
    def test_sse_generator_yields_running_when_deployed(self) -> None:
        """_sse_generator should yield 'running' when engine is deployed."""
        import asyncio

        from adapters.inbound.api.app import EngineState, _sse_generator

        engine = EngineState(is_running=True, deployed=True, multiplier_override=1.5, estimated_eps=100.0, total_workstations=50)
        app_module.app.state.engine = engine

        async def collect() -> list[str]:
            chunks: list[str] = []
            gen = _sse_generator()
            for _ in range(3):
                chunks.append(await gen.__anext__())
            return chunks

        chunks = asyncio.run(collect())
        assert len(chunks) == 3
        for chunk in chunks:
            assert chunk.startswith("data: ")
            assert "running" in chunk

    def test_sse_generator_yields_stopped_when_not_deployed(self) -> None:
        """_sse_generator should yield 'stopped' when engine is not deployed."""
        import asyncio

        from adapters.inbound.api.app import EngineState, _sse_generator

        engine = EngineState(is_running=True, deployed=False, multiplier_override=0.0, estimated_eps=0.0, total_workstations=50)
        app_module.app.state.engine = engine

        async def collect() -> list[str]:
            chunks: list[str] = []
            gen = _sse_generator()
            for _ in range(3):
                chunks.append(await gen.__anext__())
            return chunks

        chunks = asyncio.run(collect())
        assert len(chunks) == 3
        for chunk in chunks:
            assert chunk.startswith("data: ")
            assert "stopped" in chunk

    def test_sse_generator_heartbeat_every_15(self) -> None:
        """_sse_generator should yield a heartbeat every 15 iterations."""
        import asyncio

        from adapters.inbound.api.app import EngineState, _sse_generator

        engine = EngineState(is_running=True, deployed=True, multiplier_override=1.5, estimated_eps=100.0, total_workstations=50)
        app_module.app.state.engine = engine

        async def collect() -> list[str]:
            chunks: list[str] = []
            gen = _sse_generator()
            for _ in range(16):
                chunks.append(await gen.__anext__())
            return chunks

        chunks = asyncio.run(collect())
        assert any(":heartbeat" in c for c in chunks)

    # ── #26: SSE disconnect handling ──

    def test_sse_generator_handles_cancelled_error(self) -> None:
        """_sse_generator must clean up when task is cancelled."""
        import asyncio

        from adapters.inbound.api.app import EngineState, _sse_generator

        engine = EngineState(is_running=True, deployed=True, multiplier_override=1.0, estimated_eps=100.0, total_workstations=50)
        app_module.app.state.engine = engine

        async def run_and_cancel():
            gen = _sse_generator()
            # Advance once to enter the try block
            await gen.__anext__()
            # Cancel via aclose — simulates client disconnect
            await gen.aclose()

        # Should not raise — cleaned up silently
        asyncio.run(run_and_cancel())

    def test_sse_generator_handles_generator_exit(self) -> None:
        """_sse_generator must handle GeneratorExit (aclose) cleanly."""
        import asyncio

        from adapters.inbound.api.app import EngineState, _sse_generator

        engine = EngineState(is_running=True, deployed=True, multiplier_override=1.0, estimated_eps=100.0, total_workstations=50)
        app_module.app.state.engine = engine

        async def run_and_close():
            gen = _sse_generator()
            # Collect a few chunks then close
            await gen.__anext__()
            await gen.__anext__()
            await gen.aclose()

        # Should not raise
        asyncio.run(run_and_close())

    def test_sse_generator_continues_after_heartbeat(self, monkeypatch) -> None:
        """Regression: try/except must not break normal heartbeat streaming."""
        import asyncio

        from adapters.inbound.api.app import EngineState, _sse_generator

        engine = EngineState(is_running=True, deployed=True, multiplier_override=1.0, estimated_eps=100.0, total_workstations=50)
        app_module.app.state.engine = engine

        # Patch asyncio.sleep to avoid real 1s waits
        async def fake_sleep(_seconds: float) -> None:
            pass

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        async def collect(n: int) -> list[str]:
            chunks: list[str] = []
            gen = _sse_generator()
            for _ in range(n):
                chunks.append(await gen.__anext__())
            await gen.aclose()
            return chunks

        chunks = asyncio.run(collect(30))
        # Heartbeat should appear at least once in 30 iterations (every 15)
        assert any(":heartbeat" in c for c in chunks), "Heartbeat missing after 30 iterations"
        # Data chunks should still be flowing
        data_chunks = [c for c in chunks if c.startswith("data: ")]
        assert len(data_chunks) >= 28, f"Expected >=28 data chunks, got {len(data_chunks)}"

    def test_sse_generator_has_try_except_for_disconnect(self) -> None:
        """_sse_generator source must contain try/except for disconnect exceptions."""
        import inspect

        from adapters.inbound.api.app import _sse_generator

        source = inspect.getsource(_sse_generator)
        assert "try:" in source, "_sse_generator must have try/except for disconnect handling"
        assert "CancelledError" in source or "GeneratorExit" in source, (
            "_sse_generator must catch CancelledError or GeneratorExit"
        )


class TestHealthEndpoint:
    """Tests for the #27 /health endpoint."""

    def test_health_returns_503_when_generator_is_none(self, client) -> None:
        """GET /health must return 503 when engine._generator is None."""
        engine = app_module.app.state.engine
        engine._generator = None

        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unavailable"

    def test_health_returns_200_when_generator_initialized(self, client) -> None:
        """GET /health must return 200 when engine._generator is set."""
        from unittest.mock import MagicMock

        engine = app_module.app.state.engine
        mock_gen = MagicMock()
        engine._generator = mock_gen

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_transitions_503_to_200(self, client) -> None:
        """GET /health must transition from 503 → 200 when generator is injected."""
        from unittest.mock import MagicMock

        engine = app_module.app.state.engine
        engine._generator = None

        # Initially 503
        response = client.get("/health")
        assert response.status_code == 503

        # Inject generator → 200
        mock_gen = MagicMock()
        engine._generator = mock_gen
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_status_endpoint_unchanged(self, client) -> None:
        """GET /status must preserve its backward-compatible behavior."""
        engine = app_module.app.state.engine
        engine.deployed = True
        engine.multiplier_override = 2.0
        engine.estimated_eps = 100.0
        engine.total_workstations = 50

        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["current_multiplier"] == 2.0
        assert data["estimated_eps"] == 100.0
        assert data["total_workstations"] == 50


class TestRunEngineLoop:
    def test_run_engine_loop_missing_components_returns_early(self) -> None:
        """_run_engine_loop should return early if generator or publisher is None."""
        import asyncio

        from adapters.inbound.api.app import EngineState, _run_engine_loop

        state = EngineState()
        state._generator = None
        state._publisher = None
        state.is_running = True

        asyncio.run(_run_engine_loop(state))
        assert state.is_running is False

    def test_run_engine_loop_runs_and_stops(self) -> None:
        """_run_engine_loop should process ticks while is_running is True."""
        import asyncio
        from unittest.mock import MagicMock

        from adapters.inbound.api.app import EngineState, _run_engine_loop

        mock_generator = MagicMock()
        mock_generator.estimated_eps.return_value = 100.0
        mock_generator.generate_tick.return_value = []
        mock_generator.set_scale_multiplier = MagicMock()

        mock_publisher = MagicMock()
        mock_publisher.flush = MagicMock()

        state = EngineState()
        state._generator = mock_generator
        state._publisher = mock_publisher
        state.is_running = True
        state.deployed = True

        async def run_once() -> None:
            # Stop after first iteration
            async def stop_after() -> None:
                await asyncio.sleep(0.05)
                state.is_running = False

            await asyncio.gather(_run_engine_loop(state), stop_after())

        asyncio.run(run_once())
        assert state.is_running is False
        mock_publisher.flush.assert_called_once_with(5.0)

    def test_run_engine_loop_skips_generation_when_not_deployed(self) -> None:
        """_run_engine_loop should skip generation when deployed=False."""
        import asyncio
        from unittest.mock import MagicMock

        from adapters.inbound.api.app import EngineState, _run_engine_loop

        mock_generator = MagicMock()
        mock_generator.estimated_eps.return_value = 100.0
        mock_generator.generate_tick.return_value = []
        mock_generator.set_scale_multiplier = MagicMock()

        mock_publisher = MagicMock()
        mock_publisher.flush = MagicMock()

        state = EngineState()
        state._generator = mock_generator
        state._publisher = mock_publisher
        state.is_running = True
        state.deployed = False

        async def run_once() -> None:
            async def stop_after() -> None:
                await asyncio.sleep(0.05)
                state.is_running = False

            await asyncio.gather(_run_engine_loop(state), stop_after())

        asyncio.run(run_once())
        assert state.is_running is False
        mock_generator.generate_tick.assert_not_called()
        mock_publisher.flush.assert_called_once_with(5.0)

    def test_run_engine_loop_generates_when_deployed(self) -> None:
        """_run_engine_loop should generate events when deployed=True."""
        import asyncio
        from unittest.mock import MagicMock

        from adapters.inbound.api.app import EngineState, _run_engine_loop

        mock_generator = MagicMock()
        mock_generator.estimated_eps.return_value = 100.0
        mock_generator.generate_tick.return_value = []
        mock_generator.set_scale_multiplier = MagicMock()

        mock_publisher = MagicMock()
        mock_publisher.flush = MagicMock()

        state = EngineState()
        state._generator = mock_generator
        state._publisher = mock_publisher
        state.is_running = True
        state.deployed = True

        async def run_once() -> None:
            async def stop_after() -> None:
                await asyncio.sleep(0.05)
                state.is_running = False

            await asyncio.gather(_run_engine_loop(state), stop_after())

        asyncio.run(run_once())
        assert state.is_running is False
        mock_generator.generate_tick.assert_called()
        mock_publisher.flush.assert_called_once_with(5.0)

    def test_run_engine_loop_cancelled_error(self) -> None:
        """_run_engine_loop should handle CancelledError gracefully."""
        import asyncio
        from unittest.mock import MagicMock

        from adapters.inbound.api.app import EngineState, _run_engine_loop

        mock_generator = MagicMock()
        mock_generator.estimated_eps.return_value = 100.0
        mock_generator.generate_tick.return_value = []
        mock_generator.set_scale_multiplier = MagicMock()

        mock_publisher = MagicMock()
        mock_publisher.flush = MagicMock()

        state = EngineState()
        state._generator = mock_generator
        state._publisher = mock_publisher
        state.is_running = True

        async def run_and_cancel() -> None:
            task = asyncio.create_task(_run_engine_loop(state))
            await asyncio.sleep(0.01)
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        asyncio.run(run_and_cancel())
        assert state.is_running is False


# ---------------------------------------------------------------------------
# CORS Security Tests (Issue #4)
# ---------------------------------------------------------------------------


class TestCorsSecurity:
    """Verify CORS middleware is configured securely."""

    def test_cors_allow_credentials_is_false(self, client) -> None:
        """allow_credentials must be False — no credentialed requests in this app."""
        cors_middleware = None
        for mw in app_module.app.user_middleware:
            if hasattr(mw, "cls") and mw.cls == CORSMiddleware:
                cors_middleware = mw
                break
        assert cors_middleware is not None, "CORS middleware not found"
        assert cors_middleware.kwargs.get("allow_credentials") is False

    def test_cors_preflight_returns_ok(self, client) -> None:
        """OPTIONS preflight must succeed for allowed origin."""
        response = client.options(
            "/status",
            headers={
                "Origin": "http://localhost:8080",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Auth & Rate Limit Tests (Issue #19)
# ---------------------------------------------------------------------------


class TestApiKeyAuth:
    """Verify X-API-Key auth protects POST /control only."""

    @pytest.fixture(autouse=True)
    def _set_api_key(self, monkeypatch) -> None:
        """Set a test API key for all auth tests."""
        monkeypatch.setenv("BR_API_KEY", "test-secret-key")
        # Reload the env-dependent module-level constants
        import importlib

        importlib.reload(app_module)

    def test_control_returns_401_without_api_key(self, client) -> None:
        """POST /control without X-API-Key header must return 401."""
        response = client.post(
            "/control",
            json={"eps_multiplier": 1.0},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_control_returns_401_with_wrong_api_key(self, client) -> None:
        """POST /control with wrong X-API-Key header must return 401."""
        response = client.post(
            "/control",
            json={"eps_multiplier": 1.0},
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401

    def test_control_returns_200_with_valid_api_key(self, client) -> None:
        """POST /control with correct X-API-Key must return 200."""
        response = client.post(
            "/control",
            json={"eps_multiplier": 1.0},
            headers={"X-API-Key": "test-secret-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Engine deployed"

    def test_health_remains_public(self, client) -> None:
        """GET /health must remain public (no API key required)."""
        response = client.get("/health")
        # Should be 503 (engine not initialized) or 200 — NOT 401
        assert response.status_code in (200, 503)
        assert response.status_code != 401

    def test_status_remains_public(self, client) -> None:
        """GET /status must remain public (no API key required)."""
        response = client.get("/status")
        assert response.status_code == 200
        assert response.status_code != 401

    def test_topology_endpoints_remain_public(self, client) -> None:
        """GET /topology/branches must remain public."""
        response = client.get("/topology/branches")
        assert response.status_code != 401


class TestRateLimiter:
    """Verify rate limiting on POST /control."""

    @pytest.fixture(autouse=True)
    def _set_api_key(self, monkeypatch) -> None:
        """Set a test API key for all rate limit tests."""
        monkeypatch.setenv("BR_API_KEY", "test-secret-key")
        import importlib

        importlib.reload(app_module)

    def test_control_allows_up_to_five_requests_per_window(self, client) -> None:
        """First 5 requests within a 60s window must succeed."""
        for i in range(5):
            response = client.post(
                "/control",
                json={"eps_multiplier": 1.0},
                headers={"X-API-Key": "test-secret-key"},
            )
            assert response.status_code == 200, f"Request {i + 1} expected 200, got {response.status_code}"

    def test_control_returns_429_when_rate_limited(self, client) -> None:
        """6th request within 60s must return 429 Too Many Requests."""
        # Exhaust the rate limit (5 requests)
        for _ in range(5):
            client.post(
                "/control",
                json={"eps_multiplier": 1.0},
                headers={"X-API-Key": "test-secret-key"},
            )
        # 6th should be blocked
        response = client.post(
            "/control",
            json={"eps_multiplier": 1.0},
            headers={"X-API-Key": "test-secret-key"},
        )
        assert response.status_code == 429
        assert "Retry-After" in response.headers
