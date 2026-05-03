"""Unit tests for the topology config factory.

Validates that create_topology_config produces a TopologyConfig identical
to the previous CLI-local implementation.
"""

from core.domain.topology_config import OSDistribution, TopologyConfig
from core.factories.topology_config_factory import create_topology_config


class TestTopologyConfigFactory:
    """The factory must build TopologyConfig without cross-adapter imports."""

    def test_factory_produces_topology_config(self) -> None:
        """Factory produces a TopologyConfig with correct field values."""
        config = create_topology_config(
            num_branches=10,
            workstations_per_branch=50,
            employees_per_branch=60,
            windows_pct=80,
            linux_pct=15,
            macos_pct=5,
            base_eps=2.0,
        )

        assert isinstance(config, TopologyConfig)
        assert config.num_branches == 10
        assert config.workstations_per_branch == 50
        assert config.employees_per_branch == 60
        assert config.os_distribution == OSDistribution(
            windows_pct=80, linux_pct=15, macos_pct=5
        )
        assert config.base_eps == 2.0
        assert len(config.segment_templates) == 2
        assert config.segment_templates[0].name_prefix == "teller-vlan"
        assert config.segment_templates[1].name_prefix == "server-vlan"

    def test_factory_is_importable_from_core(self) -> None:
        """API adapter must be able to import factory from core, not CLI."""
        import adapters.inbound.api.app as app_module

        # Verify the app imports create_topology_config from core.factories
        assert hasattr(app_module, "create_topology_config")
        # Check the module origin
        origin = app_module.create_topology_config.__module__
        assert origin == "core.factories.topology_config_factory"
