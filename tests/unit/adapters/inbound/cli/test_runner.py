"""Unit tests for the BankRange CLI Runner.

Tests validate argument parsing and correct invocation of domain factories.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

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

    def test_main_kafka_init_failure_exits(self) -> None:
        """If KafkaEventPublisher raises, main should log error and exit."""
        from adapters.inbound.cli.runner import main

        with (
            patch.object(sys, "argv", ["runner"]),
            patch(
                "adapters.inbound.cli.runner.KafkaEventPublisher",
                side_effect=Exception("kafka connection failed"),
            ) as _mock_pub,
            patch("adapters.inbound.cli.runner.sys.exit", side_effect=SystemExit(1)) as mock_exit,
            patch("adapters.inbound.cli.runner.logger") as mock_logger,
        ):
            with pytest.raises(SystemExit):
                main()

            mock_logger.error.assert_called_once()
            assert "Failed to initialize Kafka Publisher" in mock_logger.error.call_args[0][0]
            mock_exit.assert_called_once_with(1)

    def test_main_logs_stats_every_5_ticks(self) -> None:
        """The main loop should log stats every 5 ticks."""
        from adapters.inbound.cli.runner import main

        sleep_call_count = 0

        def _sleep_side_effect(_duration: float) -> None:
            nonlocal sleep_call_count
            sleep_call_count += 1
            if sleep_call_count >= 6:
                raise KeyboardInterrupt

        with (
            patch.object(sys, "argv", ["runner"]),
            patch("adapters.inbound.cli.runner.KafkaEventPublisher") as mock_pub,
            patch("adapters.inbound.cli.runner.create_topology_config") as mock_factory,
            patch("adapters.inbound.cli.runner.TopologyFactory.create", return_value=[]),  # type: ignore[misc]
            patch("adapters.inbound.cli.runner.sys.exit"),
            patch("adapters.inbound.cli.runner.time.sleep", side_effect=_sleep_side_effect),
            patch("adapters.inbound.cli.runner.logger") as mock_logger,
        ):
            mock_factory.return_value = MagicMock()
            mock_pub.return_value = MagicMock()

            main()

            # Should have at least one info log with stats after 5+ ticks
            info_calls = [c for c in mock_logger.info.call_args_list if "Tick:" in str(c)]
            assert len(info_calls) >= 1

    def test_main_handles_exception_in_loop(self) -> None:
        """Unhandled exceptions in the main loop should be logged."""
        from adapters.inbound.cli.runner import main

        with (
            patch.object(sys, "argv", ["runner"]),
            patch("adapters.inbound.cli.runner.KafkaEventPublisher") as mock_pub,
            patch("adapters.inbound.cli.runner.create_topology_config") as mock_factory,
            patch("adapters.inbound.cli.runner.TopologyFactory.create", return_value=[]),  # type: ignore[misc]
            patch("adapters.inbound.cli.runner.sys.exit"),
            patch(
                "adapters.inbound.cli.runner.time.sleep",
                side_effect=RuntimeError("unexpected error"),
            ),
            patch("adapters.inbound.cli.runner.logger") as mock_logger,
        ):
            mock_factory.return_value = MagicMock()
            mock_pub.return_value = MagicMock()

            main()

            mock_logger.error.assert_called_once()
            assert "Unhandled exception" in mock_logger.error.call_args[0][0]

    def test_main_keyboard_interrupt_cleanup(self) -> None:
        """KeyboardInterrupt should trigger graceful shutdown with flush."""
        from adapters.inbound.cli.runner import main

        mock_publisher_instance = MagicMock()

        with (
            patch.object(sys, "argv", ["runner"]),
            patch(
                "adapters.inbound.cli.runner.KafkaEventPublisher", return_value=mock_publisher_instance
            ),
            patch("adapters.inbound.cli.runner.create_topology_config") as mock_factory,
            patch("adapters.inbound.cli.runner.TopologyFactory.create", return_value=[]),  # type: ignore[misc]
            patch("adapters.inbound.cli.runner.sys.exit"),
            patch("adapters.inbound.cli.runner.time.sleep", side_effect=KeyboardInterrupt),
            patch("adapters.inbound.cli.runner.logger") as mock_logger,
        ):
            mock_factory.return_value = MagicMock()

            main()

            mock_publisher_instance.flush.assert_called_once_with(timeout_secs=5.0)
            mock_logger.info.assert_any_call("🛑 Simulation stopped by user.")
