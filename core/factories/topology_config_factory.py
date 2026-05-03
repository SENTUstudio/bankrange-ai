"""Factory for building TopologyConfig instances.

This factory centralizes topology configuration creation in the core layer,
eliminating the inverted dependency where API adapters imported from CLI adapters.
"""

from core.domain.topology_config import OSDistribution, SegmentTemplate, TopologyConfig


def create_topology_config(
    num_branches: int,
    workstations_per_branch: int,
    employees_per_branch: int,
    windows_pct: int,
    linux_pct: int,
    macos_pct: int,
    base_eps: float,
) -> TopologyConfig:
    """Build the configuration object for the bank using injected parameters."""
    return TopologyConfig(
        num_branches=num_branches,
        workstations_per_branch=workstations_per_branch,
        employees_per_branch=employees_per_branch,
        os_distribution=OSDistribution(
            windows_pct=windows_pct, linux_pct=linux_pct, macos_pct=macos_pct
        ),
        segment_templates=[
            SegmentTemplate(
                name_prefix="teller-vlan",
                vlan_id=100,
                cidr_prefix="10.{branch_idx}.1.0/24",
            ),
            SegmentTemplate(
                name_prefix="server-vlan",
                vlan_id=200,
                cidr_prefix="10.{branch_idx}.2.0/24",
            ),
        ],
        base_eps=base_eps,
    )
