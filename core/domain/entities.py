"""Domain Entities for BankRange.

Entities are objects with a distinct identity that persists over time.
In BankRange's ubiquitous language:

- A **Branch** is a physical bank location (sucursal) with employees
  and workstations connected through one or more network segments.
- A **NetworkSegment** defines a CIDR block within a branch,
  representing a logical network partition (e.g., teller VLAN,
  corporate VLAN, ATM network).
- A **Workstation** is a computing device (PC, server, ATM terminal)
  that generates log events. It has an IP within its segment and runs
  a specific OS.
- An **Employee** is a bank staff member assigned to a workstation
  during business hours. Employees generate user-level events
  (login, file access, email).
"""

import uuid
from ipaddress import IPv4Network
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from core.domain.exceptions import SegmentCapacityExceededError
from core.domain.value_objects import IPAddress, MacAddress, OSType


class NetworkSegment(BaseModel):
    """A logical network partition within a branch.

    Defines the CIDR block that constrains which IPs workstations can
    receive. A branch may have multiple segments (e.g., 'teller-vlan',
    'server-dmz', 'guest-wifi').

    Business rules:
    - CIDR must be a valid private IPv4 network.
    - The segment name must follow the ubiquitous language of banking IT.
    """

    id: Annotated[
        uuid.UUID,
        Field(default_factory=uuid.uuid4, description="Unique segment identifier"),
    ]
    name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description="Segment name (e.g., 'teller-vlan', 'server-dmz')",
        ),
    ]
    cidr: Annotated[
        str,
        Field(description="CIDR block (e.g., '10.1.1.0/24')"),
    ]
    vlan_id: Annotated[
        int,
        Field(ge=1, le=4094, description="IEEE 802.1Q VLAN identifier"),
    ]

    @model_validator(mode="after")
    def validate_cidr_is_private(self) -> "NetworkSegment":
        """Ensure the CIDR block is a valid private network."""
        try:
            network = IPv4Network(self.cidr, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR block: {self.cidr}") from e

        if not network.is_private:
            raise ValueError(f"Network segment must use private CIDR (RFC 1918), got: {self.cidr}")
        return self

    @property
    def capacity(self) -> int:
        """Number of usable host IPs in this segment."""
        network = IPv4Network(self.cidr, strict=False)
        # Subtract network and broadcast addresses
        return max(network.num_addresses - 2, 0)

    def allocate_ip(self, offset: int) -> IPAddress:
        """Allocate the Nth usable IP from this segment.

        Args:
            offset: Zero-based offset into the usable host range.

        Returns:
            An IPAddress value object within this segment.

        Raises:
            SegmentCapacityExceededError: If offset exceeds capacity.
        """
        if offset < 0 or offset >= self.capacity:
            raise SegmentCapacityExceededError(
                f"Offset {offset} exceeds segment '{self.name}' capacity of {self.capacity} hosts"
            )
        network = IPv4Network(self.cidr, strict=False)
        # +1 to skip the network address
        host_ip = network.network_address + offset + 1
        return IPAddress(value=str(host_ip))


class Workstation(BaseModel):
    """A computing device within the bank's network.

    Each workstation is assigned to a network segment and runs
    a specific operating system. It generates log events at a
    configurable rate (EPS).

    Business rules:
    - Hostname must follow bank naming convention: {branch_code}-{type}-{seq}
    - IP must belong to the workstation's assigned network segment.
    - Each workstation has a unique MAC address.
    """

    id: Annotated[
        uuid.UUID,
        Field(default_factory=uuid.uuid4, description="Unique workstation identifier"),
    ]
    hostname: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            pattern=r"^[A-Z0-9]+-[A-Z]+-\d{3,4}$",
            description="Hostname following bank convention: BRANCH-TYPE-SEQ",
        ),
    ]
    os_type: Annotated[
        OSType,
        Field(description="Operating system type"),
    ]
    ip_address: Annotated[
        IPAddress,
        Field(description="Assigned IPv4 address"),
    ]
    mac_address: Annotated[
        MacAddress,
        Field(description="Network interface MAC address"),
    ]
    eps: Annotated[
        float,
        Field(
            default=2.0,
            gt=0,
            le=100,
            description="Events per second baseline rate",
        ),
    ]


class Employee(BaseModel):
    """A bank staff member who operates a workstation.

    Employees generate user-level events: authentication, file access,
    email, application usage. Their role determines what kind of events
    they produce.

    Business rules:
    - Employee ID follows internal bank format (alphanumeric).
    - Department must be a recognized bank department.
    - An employee can be assigned to at most one workstation at a time.
    """

    id: Annotated[
        uuid.UUID,
        Field(default_factory=uuid.uuid4, description="Unique employee identifier"),
    ]
    employee_code: Annotated[
        str,
        Field(
            min_length=3,
            max_length=10,
            pattern=r"^[A-Z]{2}\d{4,8}$",
            description="Internal employee code (e.g., 'EM001234')",
        ),
    ]
    full_name: Annotated[
        str,
        Field(
            min_length=2,
            max_length=128,
            description="Employee full name",
        ),
    ]
    department: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            description="Bank department (e.g., 'operations', 'treasury')",
        ),
    ]
    workstation_id: Annotated[
        uuid.UUID | None,
        Field(
            default=None,
            description="Currently assigned workstation (None if unassigned)",
        ),
    ]


class Branch(BaseModel):
    """A physical bank location (sucursal).

    A branch aggregates workstations, employees, and network segments.
    It defines the organizational and network topology for log generation.

    Business rules:
    - Branch code must follow banking convention (3-letter prefix + number).
    - A branch must have at least one network segment.
    - Total workstations cannot exceed max_workstations capacity.
    """

    id: Annotated[
        uuid.UUID,
        Field(default_factory=uuid.uuid4, description="Unique branch identifier"),
    ]
    code: Annotated[
        str,
        Field(
            pattern=r"^[A-Z]{3}\d{3,4}$",
            description="Branch code (e.g., 'SUC001', 'COR001')",
        ),
    ]
    name: Annotated[
        str,
        Field(
            min_length=2,
            max_length=128,
            description="Branch display name",
        ),
    ]
    city: Annotated[
        str,
        Field(
            min_length=2,
            max_length=64,
            description="City where the branch is located",
        ),
    ]
    max_workstations: Annotated[
        int,
        Field(
            gt=0,
            le=500,
            description="Maximum workstation capacity for this branch",
        ),
    ]
    network_segments: Annotated[
        list[NetworkSegment],
        Field(
            default_factory=list,
            description="Network segments in this branch",
        ),
    ]
    workstations: Annotated[
        list[Workstation],
        Field(
            default_factory=list,
            description="Workstations deployed in this branch",
        ),
    ]
    employees: Annotated[
        list[Employee],
        Field(
            default_factory=list,
            description="Employees assigned to this branch",
        ),
    ]

    @model_validator(mode="after")
    def validate_workstation_capacity(self) -> "Branch":
        """Ensure workstation count does not exceed branch capacity."""
        if len(self.workstations) > self.max_workstations:
            from core.domain.exceptions import WorkstationLimitExceededError

            raise WorkstationLimitExceededError(
                f"Branch '{self.code}' has {len(self.workstations)} workstations "
                f"but max capacity is {self.max_workstations}"
            )
        return self
