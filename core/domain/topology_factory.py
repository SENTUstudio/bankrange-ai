"""TopologyFactory — Domain Service for building bank topology.

This is a pure domain service with ZERO infrastructure dependencies.
It takes a TopologyConfig and produces a list of fully-configured
Branch entities, each with its network segments, workstations,
and employees.

The factory is deterministic given the same config — this is
intentional so simulations are reproducible.
"""

from core.domain.entities import Branch, Employee, NetworkSegment, Workstation
from core.domain.topology_config import TopologyConfig
from core.domain.value_objects import MacAddress, OSType


class TopologyFactory:
    """Builds a complete bank topology from configuration.

    The factory encapsulates the complex logic of:
    - Distributing OS types according to the configured percentages.
    - Assigning IPs from network segments (CIDR-based allocation).
    - Generating consistent hostnames, employee codes, and MACs.
    - Respecting branch capacity constraints.

    Usage:
        config = TopologyConfig(...)
        factory = TopologyFactory()
        branches = factory.create(config)
    """

    def create(self, config: TopologyConfig) -> list[Branch]:
        """Build the full topology from configuration.

        Returns:
            A list of Branch entities, each fully populated with
            segments, workstations, and employees.
        """
        branches: list[Branch] = []

        for branch_idx in range(config.num_branches):
            branch_code = f"SUC{branch_idx + 1:03d}"
            branch_name = f"Sucursal {branch_idx + 1:03d}"

            # Build network segments from templates
            segments = self._create_segments(config, branch_idx)

            # Build workstations with proper OS distribution and IP allocation
            workstations = self._create_workstations(config, branch_code, segments, branch_idx)

            # Build employees and assign them to workstations
            employees = self._create_employees(config, workstations, branch_idx)

            branch = Branch(
                code=branch_code,
                name=branch_name,
                city=self._city_for_branch(branch_idx),
                max_workstations=config.workstations_per_branch,
                network_segments=segments,
                workstations=workstations,
                employees=employees,
            )
            branches.append(branch)

        return branches

    def _create_segments(self, config: TopologyConfig, branch_idx: int) -> list[NetworkSegment]:
        """Create network segments for a branch from templates."""
        segments: list[NetworkSegment] = []

        for template in config.segment_templates:
            cidr = template.cidr_prefix.replace("{branch_idx}", str(branch_idx + 1))
            segment = NetworkSegment(
                name=f"{template.name_prefix}-{branch_idx + 1:03d}",
                cidr=cidr,
                vlan_id=template.vlan_id,
            )
            segments.append(segment)

        return segments

    def _create_workstations(
        self,
        config: TopologyConfig,
        branch_code: str,
        segments: list[NetworkSegment],
        branch_idx: int,
    ) -> list[Workstation]:
        """Create workstations with OS distribution and IP allocation.

        Workstations are distributed across segments by OS type:
        - Linux → last segment (server-vlan / DMZ)
        - Windows / macOS → first segment (teller-vlan / corporate)

        If only one segment exists, all workstations go there.
        """
        workstations: list[Workstation] = []
        os_sequence = self._build_os_sequence(config)

        import random

        rng = random.Random(config.num_branches + branch_idx)  # Stable seed
        rng.shuffle(os_sequence)

        # Segment routing: Linux → server segment, others → teller segment
        teller_segment = segments[0]
        server_segment = segments[-1]  # Same as teller if only one segment

        # Per-segment IP offset counters
        ip_offsets: dict[int, int] = {}

        for ws_idx in range(config.workstations_per_branch):
            os_type = os_sequence[ws_idx % len(os_sequence)]
            segment = server_segment if os_type == OSType.LINUX else teller_segment

            offset = ip_offsets.get(segment.vlan_id, 0)
            ip = segment.allocate_ip(offset)
            ip_offsets[segment.vlan_id] = offset + 1

            mac = self._generate_mac(branch_idx, ws_idx)
            type_code = self._os_type_code(os_type)

            workstation = Workstation(
                hostname=f"{branch_code}-{type_code}-{ws_idx + 1:03d}",
                os_type=os_type,
                ip_address=ip,
                mac_address=mac,
                eps=config.base_eps,
            )
            workstations.append(workstation)

        return workstations

    def _create_employees(
        self,
        config: TopologyConfig,
        workstations: list[Workstation],
        branch_idx: int,
    ) -> list[Employee]:
        """Create employees and assign them to workstations."""
        employees: list[Employee] = []
        departments = [
            "operations",
            "treasury",
            "compliance",
            "customer_service",
            "it_support",
            "management",
        ]

        for emp_idx in range(config.employees_per_branch):
            # Assign to workstation if available (round-robin)
            ws_id = None
            if emp_idx < len(workstations):
                ws_id = workstations[emp_idx].id

            employee = Employee(
                employee_code=f"EM{branch_idx * 10000 + emp_idx + 1:06d}",
                full_name=f"Employee {branch_idx + 1:03d}-{emp_idx + 1:04d}",
                department=departments[emp_idx % len(departments)],
                workstation_id=ws_id,
            )
            employees.append(employee)

        return employees

    @staticmethod
    def _build_os_sequence(config: TopologyConfig) -> list[OSType]:
        """Build a repeating OS sequence based on distribution percentages.

        For a distribution of windows=80, linux=15, macos=5:
        Returns [WINDOWS]*80 + [LINUX]*15 + [MACOS]*5
        This is then indexed modulo 100 for each workstation.
        """
        sequence: list[OSType] = []
        sequence.extend([OSType.WINDOWS] * config.os_distribution.windows_pct)
        sequence.extend([OSType.LINUX] * config.os_distribution.linux_pct)
        sequence.extend([OSType.MACOS] * config.os_distribution.macos_pct)
        return sequence

    @staticmethod
    def _generate_mac(branch_idx: int, ws_idx: int) -> MacAddress:
        """Generate a deterministic MAC address from branch and workstation indices.

        Format: 02:BR:BR:WS:WS:WS
        - 02: locally administered unicast
        - BR:BR: branch index as 2 hex bytes
        - WS:WS:WS: workstation index as 3 hex bytes
        """
        branch_hex = f"{branch_idx:04X}"
        ws_hex = f"{ws_idx:06X}"
        mac_str = f"02:{branch_hex[:2]}:{branch_hex[2:4]}:{ws_hex[:2]}:{ws_hex[2:4]}:{ws_hex[4:6]}"
        return MacAddress(value=mac_str)

    @staticmethod
    def _os_type_code(os_type: OSType) -> str:
        """Map OS type to a short hostname component."""
        mapping = {
            OSType.WINDOWS: "PC",
            OSType.LINUX: "LX",
            OSType.MACOS: "MC",
        }
        return mapping[os_type]

    @staticmethod
    def _city_for_branch(branch_idx: int) -> str:
        """Assign city based on branch index (round-robin)."""
        cities = [
            "Buenos Aires",
            "Córdoba",
            "Rosario",
            "Mendoza",
            "Tucumán",
            "La Plata",
            "Mar del Plata",
            "Salta",
        ]
        return cities[branch_idx % len(cities)]
