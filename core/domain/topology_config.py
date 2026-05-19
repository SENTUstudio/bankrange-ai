"""Topology configuration for bank simulation.

Defines the parameters that shape the simulated bank topology:
how many branches, workstations per branch, OS distribution, etc.

This is a Value Object — immutable configuration that the
TopologyFactory consumes to produce the full entity graph.
"""

from ipaddress import IPv4Network
from typing import Annotated

from pydantic import BaseModel, Field, model_validator


class OSDistribution(BaseModel):
    """Percentage distribution of operating systems across workstations.

    Typical banking environments are Windows-heavy (80-90%) with
    Linux servers and a few macOS stations for executives.

    Business rule: percentages must sum to exactly 100.
    """

    model_config = {"frozen": True}

    windows_pct: Annotated[
        int,
        Field(ge=0, le=100, description="Percentage of Windows workstations"),
    ]
    linux_pct: Annotated[
        int,
        Field(ge=0, le=100, description="Percentage of Linux workstations"),
    ]
    macos_pct: Annotated[
        int,
        Field(ge=0, le=100, description="Percentage of macOS workstations"),
    ]

    @model_validator(mode="after")
    def validate_distribution_sums_to_100(self) -> "OSDistribution":
        """OS distribution percentages must total exactly 100%."""
        total = self.windows_pct + self.linux_pct + self.macos_pct
        if total != 100:
            raise ValueError(
                f"OS distribution must sum to 100%, got {total}% "
                f"(windows={self.windows_pct}, linux={self.linux_pct}, "
                f"macos={self.macos_pct})"
            )
        return self


class SegmentTemplate(BaseModel):
    """Template for a network segment to be created in each branch.

    The TopologyFactory uses these templates to generate concrete
    NetworkSegment entities with proper CIDR allocation.
    """

    model_config = {"frozen": True}

    name_prefix: Annotated[
        str,
        Field(
            min_length=1,
            max_length=32,
            description="Prefix for segment name (e.g., 'teller', 'server')",
        ),
    ]
    vlan_id: Annotated[
        int,
        Field(ge=1, le=4094, description="VLAN ID for this segment type"),
    ]
    cidr_prefix: Annotated[
        str,
        Field(
            description=(
                "CIDR prefix template. The factory replaces {branch_idx} "
                "with the branch index. E.g., '10.{branch_idx}.1.0/24'"
            ),
        ),
    ]


class TopologyConfig(BaseModel):
    """Complete configuration for generating a bank topology.

    This is the single input to TopologyFactory.create().
    It defines the size, shape, and characteristics of the
    simulated bank network.

    Business rules:
    - Must have at least 1 branch.
    - Workstations per branch must be > 0.
    - Must have at least 1 segment template.
    - employees_per_branch >= workstations_per_branch (every PC has a user).
    """

    model_config = {"frozen": True}

    num_branches: Annotated[
        int,
        Field(
            gt=0,
            le=200,
            description="Number of bank branches to simulate",
        ),
    ]
    workstations_per_branch: Annotated[
        int,
        Field(
            gt=0,
            le=500,
            description="Number of workstations per branch",
        ),
    ]
    employees_per_branch: Annotated[
        int,
        Field(
            gt=0,
            le=1000,
            description="Number of employees per branch",
        ),
    ]
    os_distribution: Annotated[
        OSDistribution,
        Field(description="OS type distribution across workstations"),
    ]
    segment_templates: Annotated[
        list[SegmentTemplate],
        Field(
            min_length=1,
            description="Network segment templates for each branch",
        ),
    ]
    base_eps: Annotated[
        float,
        Field(
            default=2.0,
            gt=0,
            le=100,
            description="Baseline events per second per workstation",
        ),
    ]

    @model_validator(mode="after")
    def validate_employees_gte_workstations(self) -> "TopologyConfig":
        """Every workstation should have at least one employee."""
        if self.employees_per_branch < self.workstations_per_branch:
            raise ValueError(
                f"employees_per_branch ({self.employees_per_branch}) must be >= "
                f"workstations_per_branch ({self.workstations_per_branch}). "
                f"Every PC needs at least one operator."
            )
        return self

    @model_validator(mode="after")
    def validate_no_cidr_overlap(self) -> "TopologyConfig":
        """Segment templates must not produce overlapping CIDRs within a branch.

        Checks using branch_idx=1 as a representative sample — if templates
        overlap for one branch they overlap for all.
        """
        networks: list[tuple[IPv4Network, str]] = []
        for template in self.segment_templates:
            cidr = template.cidr_prefix.replace("{branch_idx}", "1")
            try:
                net = IPv4Network(cidr, strict=False)
            except ValueError as e:
                raise ValueError(f"Invalid CIDR in template '{template.name_prefix}': {cidr}") from e
            for existing_net, existing_name in networks:
                if net.overlaps(existing_net):
                    raise ValueError(
                        f"CIDR overlap detected: '{template.name_prefix}' ({cidr}) "
                        f"overlaps with '{existing_name}' ({existing_net})"
                    )
            networks.append((net, template.name_prefix))
        return self
