"""Temporal Engine — probabilistic behavior curves for the simulation.

Models the realistic ebb and flow of activity in a bank environment:
- Peak login at 08:30-09:30 (employees arriving)
- Steady work from 09:30-12:30
- Lunch dip from 12:30-13:30 (reduced activity)
- Afternoon steady from 13:30-17:30
- Logout peak at 17:30-18:30 (employees leaving)
- Minimal overnight activity (security systems, batch jobs)

The engine provides an EPS multiplier for any given hour of the day.
A workstation with base_eps=2.0 at a multiplier of 1.5 produces 3 EPS.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class TemporalProfile(BaseModel):
    """Hourly EPS multipliers defining a daily activity curve.

    Each entry maps an hour (0-23) to a multiplier applied to
    the workstation's base EPS rate.

    Business rules:
    - Must have exactly 24 entries (one per hour).
    - Multipliers must be >= 0 (0 means no activity).
    - At least one hour must have multiplier > 0.
    """

    model_config = {"frozen": True}

    hourly_multipliers: Annotated[
        list[float],
        Field(
            min_length=24,
            max_length=24,
            description="EPS multipliers for hours 0-23",
        ),
    ]

    def get_multiplier(self, dt: datetime) -> float:
        """Get the EPS multiplier for a given datetime.

        Args:
            dt: The datetime to query (uses the hour component).

        Returns:
            The EPS multiplier for that hour.
        """
        return self.hourly_multipliers[dt.hour]


# ---------------------------------------------------------------------------
# Pre-built profiles for common bank scenarios
# ---------------------------------------------------------------------------

BANK_WORKDAY_PROFILE = TemporalProfile(
    hourly_multipliers=[
        # 00:00-05:00 — Night: minimal (batch jobs, security scans)
        0.05,
        0.05,
        0.05,
        0.05,
        0.05,
        0.05,
        # 06:00-07:00 — Early morning: guards, IT ops arriving
        0.15,
        0.30,
        # 08:00-08:59 — Morning ramp-up: employees logging in
        1.50,
        # 09:00-09:59 — Peak activity: full operations
        1.80,
        # 10:00-11:59 — Steady high activity
        1.60,
        1.60,
        # 12:00-12:59 — Lunch dip begins
        1.00,
        # 13:00-13:59 — Lunch dip: reduced activity
        0.80,
        # 14:00-16:59 — Afternoon steady
        1.50,
        1.50,
        1.40,
        # 17:00-17:59 — End of day: logout wave starts
        1.20,
        # 18:00-18:59 — Logout peak
        0.80,
        # 19:00-20:59 — Evening: stragglers, overtime
        0.30,
        0.20,
        # 21:00-23:59 — Night: security systems only
        0.10,
        0.10,
        0.10,
    ]
)
"""Standard banking workday: peaks at 9am, dips at lunch, tapers at 6pm."""

SERVER_24X7_PROFILE = TemporalProfile(
    hourly_multipliers=[
        # Servers generate steady traffic 24/7 with slight variation
        0.80,
        0.80,
        0.90,
        0.90,
        0.80,
        0.80,  # 00-05: batch processing
        0.90,
        1.00,  # 06-07: morning prep
        1.20,
        1.50,  # 08-09: peak sync
        1.30,
        1.30,  # 10-11: steady
        1.10,
        1.00,  # 12-13: lunch
        1.30,
        1.30,
        1.20,  # 14-16: afternoon
        1.10,
        1.00,  # 17-18: EOD
        0.90,
        0.90,  # 19-20: evening
        0.80,
        0.80,
        0.80,  # 21-23: night
    ]
)
"""Server profile: steady 24/7 with slight daytime increase."""
