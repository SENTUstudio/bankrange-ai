"""Unit tests for TemporalProfile.

Validates the hourly multipliers and pre-built profiles.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from core.domain.temporal import BANK_WORKDAY_PROFILE, SERVER_24X7_PROFILE, TemporalProfile


class TestTemporalProfile:
    def test_profile_requires_exactly_24_hours(self) -> None:
        """A profile must have exactly 24 hourly multipliers."""
        with pytest.raises(ValidationError):
            TemporalProfile(hourly_multipliers=[1.0] * 23)  # Missing 1

        with pytest.raises(ValidationError):
            TemporalProfile(hourly_multipliers=[1.0] * 25)  # 1 extra

    def test_get_multiplier_returns_correct_value_for_hour(self) -> None:
        """The multiplier must match the specific hour of the datetime."""
        profile = TemporalProfile(hourly_multipliers=[0.0] * 9 + [1.5] + [0.0] * 14)

        # 09:xx should return 1.5
        dt_9am = datetime(2026, 1, 15, 9, 30)
        assert profile.get_multiplier(dt_9am) == 1.5

        # 08:xx should return 0.0
        dt_8am = datetime(2026, 1, 15, 8, 59)
        assert profile.get_multiplier(dt_8am) == 0.0

    def test_bank_workday_profile_peaks_at_9am_and_14pm(self) -> None:
        """Validate the business logic of the standard bank workday profile."""
        assert BANK_WORKDAY_PROFILE.hourly_multipliers[9] == 1.80  # Morning peak
        assert BANK_WORKDAY_PROFILE.hourly_multipliers[14] == 1.50  # Afternoon peak
        assert BANK_WORKDAY_PROFILE.hourly_multipliers[13] == 0.80  # Lunch dip
        assert BANK_WORKDAY_PROFILE.hourly_multipliers[2] == 0.05  # Deep night

    def test_server_profile_is_always_active(self) -> None:
        """Servers never sleep, their minimum multiplier should be significant."""
        min_multiplier = min(SERVER_24X7_PROFILE.hourly_multipliers)
        assert min_multiplier >= 0.80
