"""Unit tests for TopologyConfig and TopologyFactory.

Tests validate the topology building rules and the deterministic
nature of the factory — same config, same topology.
"""

import pytest
from pydantic import ValidationError

from core.domain.topology_config import OSDistribution, SegmentTemplate, TopologyConfig
from core.domain.topology_factory import TopologyFactory
from core.domain.value_objects import OSType

# ---------------------------------------------------------------------------
# TopologyConfig validation tests
# ---------------------------------------------------------------------------


class TestOSDistribution:
    """OS distribution percentages must sum to 100%."""

    def test_valid_distribution(self) -> None:
        dist = OSDistribution(windows_pct=80, linux_pct=15, macos_pct=5)
        assert dist.windows_pct == 80

    def test_distribution_not_summing_to_100_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="sum to 100%"):
            OSDistribution(windows_pct=50, linux_pct=30, macos_pct=10)

    def test_all_windows_is_valid(self) -> None:
        dist = OSDistribution(windows_pct=100, linux_pct=0, macos_pct=0)
        assert dist.windows_pct == 100


class TestTopologyConfig:
    """TopologyConfig validates the simulation parameters."""

    def _make_config(self, **overrides) -> TopologyConfig:
        """Helper to create a config with sensible defaults."""
        defaults = {
            "num_branches": 2,
            "workstations_per_branch": 10,
            "employees_per_branch": 10,
            "os_distribution": OSDistribution(windows_pct=80, linux_pct=15, macos_pct=5),
            "segment_templates": [
                SegmentTemplate(
                    name_prefix="teller",
                    vlan_id=100,
                    cidr_prefix="10.{branch_idx}.1.0/24",
                ),
            ],
        }
        defaults.update(overrides)
        return TopologyConfig(**defaults)

    def test_valid_config_is_created(self) -> None:
        config = self._make_config()
        assert config.num_branches == 2
        assert config.workstations_per_branch == 10

    def test_employees_less_than_workstations_is_rejected(self) -> None:
        """Every workstation needs at least one operator."""
        with pytest.raises(ValueError, match="employees_per_branch"):
            self._make_config(
                workstations_per_branch=10,
                employees_per_branch=5,
            )

    def test_zero_branches_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._make_config(num_branches=0)

    def test_empty_segments_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._make_config(segment_templates=[])


# ---------------------------------------------------------------------------
# TopologyFactory tests
# ---------------------------------------------------------------------------


class TestTopologyFactory:
    """The factory builds a complete bank topology from config."""

    @pytest.fixture
    def small_config(self) -> TopologyConfig:
        """A minimal config: 2 branches, 5 workstations each."""
        return TopologyConfig(
            num_branches=2,
            workstations_per_branch=5,
            employees_per_branch=5,
            os_distribution=OSDistribution(windows_pct=80, linux_pct=20, macos_pct=0),
            segment_templates=[
                SegmentTemplate(
                    name_prefix="teller",
                    vlan_id=100,
                    cidr_prefix="10.{branch_idx}.1.0/24",
                ),
            ],
            base_eps=2.0,
        )

    def test_creates_correct_number_of_branches(self, small_config: TopologyConfig) -> None:
        factory = TopologyFactory()
        branches = factory.create(small_config)
        assert len(branches) == 2

    def test_branches_have_correct_codes(self, small_config: TopologyConfig) -> None:
        factory = TopologyFactory()
        branches = factory.create(small_config)
        assert branches[0].code == "SUC001"
        assert branches[1].code == "SUC002"

    def test_each_branch_has_correct_workstation_count(self, small_config: TopologyConfig) -> None:
        factory = TopologyFactory()
        branches = factory.create(small_config)
        for branch in branches:
            assert len(branch.workstations) == 5

    def test_workstations_have_unique_ips(self, small_config: TopologyConfig) -> None:
        """No two workstations in the same branch share an IP."""
        factory = TopologyFactory()
        branches = factory.create(small_config)
        for branch in branches:
            ips = [ws.ip_address.value for ws in branch.workstations]
            assert len(ips) == len(set(ips)), "Duplicate IPs found!"

    def test_workstations_have_unique_macs(self, small_config: TopologyConfig) -> None:
        """No two workstations in the entire topology share a MAC."""
        factory = TopologyFactory()
        branches = factory.create(small_config)
        all_macs = [ws.mac_address.value for branch in branches for ws in branch.workstations]
        assert len(all_macs) == len(set(all_macs)), "Duplicate MACs found!"

    def test_os_distribution_is_respected(self, small_config: TopologyConfig) -> None:
        """OS types are distributed according to the configuration."""
        factory = TopologyFactory()
        branches = factory.create(small_config)

        # With 5 workstations and 80/20/0 distribution:
        # Sequence is [W]*80 + [L]*20, indexed mod 100
        # So indices 0-4 → all Windows (first 5 of 80 Windows)
        for branch in branches:
            os_types = [ws.os_type for ws in branch.workstations]
            windows_count = os_types.count(OSType.WINDOWS)
            linux_count = os_types.count(OSType.LINUX)
            assert windows_count == 5  # All 5 in first block of 80
            assert linux_count == 0

    def test_employees_are_assigned_to_workstations(self, small_config: TopologyConfig) -> None:
        """Each employee gets a workstation when there are enough."""
        factory = TopologyFactory()
        branches = factory.create(small_config)
        for branch in branches:
            assigned = [e for e in branch.employees if e.workstation_id is not None]
            assert len(assigned) == 5  # 5 employees, 5 workstations

    def test_network_segments_use_branch_specific_cidrs(self, small_config: TopologyConfig) -> None:
        """Each branch gets its own CIDR block based on the template."""
        factory = TopologyFactory()
        branches = factory.create(small_config)
        assert branches[0].network_segments[0].cidr == "10.1.1.0/24"
        assert branches[1].network_segments[0].cidr == "10.2.1.0/24"

    def test_hostnames_follow_bank_convention(self, small_config: TopologyConfig) -> None:
        """Hostnames encode branch, OS type, and sequence number."""
        factory = TopologyFactory()
        branches = factory.create(small_config)
        first_ws = branches[0].workstations[0]
        assert first_ws.hostname == "SUC001-PC-001"

    def test_factory_is_deterministic(self, small_config: TopologyConfig) -> None:
        """Same config produces same topology structure (minus UUIDs)."""
        factory = TopologyFactory()
        run1 = factory.create(small_config)
        run2 = factory.create(small_config)

        for b1, b2 in zip(run1, run2, strict=True):
            assert b1.code == b2.code
            assert len(b1.workstations) == len(b2.workstations)
            for ws1, ws2 in zip(b1.workstations, b2.workstations, strict=True):
                assert ws1.hostname == ws2.hostname
                assert ws1.ip_address == ws2.ip_address
                assert ws1.mac_address == ws2.mac_address
