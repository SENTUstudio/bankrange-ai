"""BankRange C&C Streamlit Dashboard.

Visual interface to control the cyber simulation.
This dashboard issues REST requests against the local FastAPI
to manipulate engine volume iteratively.
"""

import os
import time

import httpx
import streamlit as st

# Setup Page Profile
st.set_page_config(
    page_title="BankRange C&C",
    page_icon="🛡️",
    layout="wide",
)

API_URL = os.getenv("BR_API_URL", "http://localhost:8000")


# Ensure we can talk to the backend
@st.cache_data(ttl=1)
def fetch_status() -> dict | None:
    try:
        r = httpx.get(f"{API_URL}/status", timeout=2.0)
        return r.json()
    except Exception:
        return None


def update_multiplier(new_multiplier: float) -> None:
    try:
        httpx.post(
            f"{API_URL}/control",
            json={"eps_multiplier": new_multiplier},
            timeout=2.0,
        )
        st.toast(f"Engine scale set to {new_multiplier}x", icon="🚀")
    except Exception as e:
        st.error(f"Failed to reach engine API: {e}")


# ---------------------------------------------------------------------------
# UI Layout
# ---------------------------------------------------------------------------
st.title("🛡️ BankRange C&C Control Panel")

# Poll for status
status_data = fetch_status()

if not status_data:
    st.error(f"🔌 Backend Offline. Trying to reach {API_URL}...")
    st.info("Ensure you have run: `uv run uvicorn adapters.inbound.api.app:app`")
else:
    # 1. Top Metrics row
    st.subheader("Live Simulation Status")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        label="Target Workstations",
        value=f"{status_data['total_workstations']:,}",
        help="Amount of simulated PCs generated from topology",
    )

    col2.metric(
        label="Engine Status",
        value=status_data["status"].upper(),
        delta="Active" if status_data["status"] == "running" else "Dormant",
        delta_color="normal" if status_data["status"] == "running" else "off",
    )

    current_eps = status_data["estimated_eps"]
    col3.metric(
        label="Est. EPS Transmitting",
        value=f"{current_eps:,.0f} evt/s",
        help="Estimated events per second being produced.",
    )

    # 2. Controls Segment
    st.divider()
    st.subheader("Global Control Overrides")

    scale_val = st.slider(
        "Traffic Generation Multiplier (x Base Workday EPS)",
        min_value=0.0,
        max_value=20.0,
        value=float(status_data["current_multiplier"]),
        step=0.1,
        help="0.0 stops traffic. >1.0 amplifies peak hour volume.",
    )

    # Check if user slid it
    if scale_val != status_data["current_multiplier"]:
        update_multiplier(scale_val)
        time.sleep(0.5)  # Let backend process
        st.rerun()  # Instant visualization update

    st.divider()
    st.caption("Auto-refreshing view (every 2s). Log viewing handled by Grafana.")
    time.sleep(2)
    st.rerun()
