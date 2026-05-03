"""Unit tests for the BankRange CLI Runner.

Tests validate argument parsing and correct invocation of domain factories.
"""

import sys
from unittest.mock import MagicMock, patch

from adapters.inbound.cli.runner import create_topology_config
from core.domain.topology_config import TopologyConfig


class TestCLIRunner:
    """CLI is the primary inbound adapter for the simulator."""

    def test_create_topology_config_accepts_base_eps_and_employees_per_branch(self) -> None:
        """The factory must be callable with the corrected parameter names."""
        config = create_topology_config(
            num_branches=2,
            workstations_per_branch=10,
            employees_per_branch=80,
            windows_pct=80,
            linux_pct=15,
            macos_pct=5,
            base_eps=2.5,
        )
        assert isinstance(config, TopologyConfig)
        assert config.employees_per_branch == 80
        assert config.base_eps == 2.5

    def test_main_parses_employees_per_branch_and_passes_base_eps(self) -> None:
        """main() must parse --employees-per-branch and use base_eps in factory call."""
        from adapters.inbound.cli.runner import main

        with (
            patch.object(
                sys, "argv", ["runner", "--employees-per-branch", "75", "--eps-scale", "3.0"]
            ),
            patch("adapters.inbound.cli.runner.KafkaEventPublisher") as mock_pub,
            patch("adapters.inbound.cli.runner.create_topology_config") as mock_factory,
            patch("adapters.inbound.cli.runner.TopologyFactory.create", return_value=[]),  # type: ignore[misc]
            patch("adapters.inbound.cli.runner.sys.exit"),
            patch("adapters.inbound.cli.runner.time.sleep", side_effect=KeyboardInterrupt),
        ):
            mock_factory.return_value = MagicMock()
            mock_pub.return_value = MagicMock()

            main()

            mock_factory.assert_called_once()
            call_kwargs = mock_factory.call_args.kwargs
            assert call_kwargs["base_eps"] == 3.0
            assert call_kwargs["employees_per_branch"] == 75

    def test_main_defaults_employees_per_branch_to_60(self) -> None:
        """When --employees-per-branch is omitted, default to 60."""
        from adapters.inbound.cli.runner import main

        def _fake_getenv(key: str, default: str | None = None) -> str | None:
            if key == "BR_EMPLOYEES_PER_BRANCH":
                return default
            return default

        with (
            patch.object(sys, "argv", ["runner"]),
            patch("adapters.inbound.cli.runner.KafkaEventPublisher") as mock_pub,
            patch("adapters.inbound.cli.runner.create_topology_config") as mock_factory,
            patch("adapters.inbound.cli.runner.TopologyFactory.create", return_value=[]),  # type: ignore[misc]
            patch("adapters.inbound.cli.runner.sys.exit"),
            patch("adapters.inbound.cli.runner.time.sleep", side_effect=KeyboardInterrupt),
            patch("adapters.inbound.cli.runner.os.getenv", side_effect=_fake_getenv),
        ):
            mock_factory.return_value = MagicMock()
            mock_pub.return_value = MagicMock()

            main()

            mock_factory.assert_called_once()
            call_kwargs = mock_factory.call_args.kwargs
            assert call_kwargs["employees_per_branch"] == 60
