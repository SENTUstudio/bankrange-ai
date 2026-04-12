"""Unit tests for the FastAPI C&C Inbound Adapter.

Tests the HTTP layer mapping to the Domain engine.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# We patch the background task start so that importing app
# inside the test doesn't actually kick off an infinite loop.
with patch("adapters.inbound.api.app._start_background_engine"):
    from adapters.inbound.api.app import app, EngineState

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_engine_state() -> None:
    """Reset the global singleton state before each test."""
    EngineState.multiplier_override = 1.0
    EngineState.is_running = True
    EngineState.cached_eps = 0.0
    EngineState.total_workstations = 100


class TestFastAPIApp:
    def test_status_endpoint_returns_engine_metadata(self) -> None:
        """GET /status should return 200 with engine metrics."""
        EngineState.multiplier_override = 2.5
        EngineState.cached_eps = 4500.5
        EngineState.total_workstations = 500

        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["current_multiplier"] == 2.5
        assert data["estimated_eps"] == 4500.5
        assert data["total_workstations"] == 500

    def test_control_endpoint_updates_multiplier(self) -> None:
        """POST /control should change the global state multiplier."""
        assert EngineState.multiplier_override == 1.0

        response = client.post(
            "/control", 
            json={"eps_multiplier": 5.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Success"
        assert data["new_multiplier"] == 5.0

        # Verify the memory state actually changed
        assert EngineState.multiplier_override == 5.0

    def test_control_endpoint_rejects_negative_multiplier(self) -> None:
        """Input validation: negative EPS multipliers are impossible."""
        response = client.post(
            "/control", 
            json={"eps_multiplier": -1.5}
        )

        # 422 Unprocessable Entity generated natively by Pydantic/FastAPI
        assert response.status_code == 422
        
        # State should remain untouched
        assert EngineState.multiplier_override == 1.0
