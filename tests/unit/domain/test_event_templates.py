"""Unit tests for Event Templates.

Validates that random template selection maps correctly to the OS.
"""

import random

from core.domain.event_templates import TEMPLATES_BY_OS, pick_template
from core.domain.value_objects import OSType


class TestEventTemplates:
    def test_pick_template_returns_os_specific_template(self) -> None:
        """A picked template must belong to the correct OS repository."""
        # Windows
        win_template = pick_template(OSType.WINDOWS)
        assert win_template in TEMPLATES_BY_OS[OSType.WINDOWS]
        
        # Linux
        linux_template = pick_template(OSType.LINUX)
        assert linux_template in TEMPLATES_BY_OS[OSType.LINUX]
        
        # macOS
        macos_template = pick_template(OSType.MACOS)
        assert macos_template in TEMPLATES_BY_OS[OSType.MACOS]

    def test_pick_template_is_deterministic_with_seed(self) -> None:
        """RNG seeding must produce the same template sequence."""
        seed = 42
        
        # Run 1
        rng1 = random.Random(seed)
        seq1 = [pick_template(OSType.WINDOWS, rng1) for _ in range(5)]
        
        # Run 2
        rng2 = random.Random(seed)
        seq2 = [pick_template(OSType.WINDOWS, rng2) for _ in range(5)]
        
        assert seq1 == seq2
