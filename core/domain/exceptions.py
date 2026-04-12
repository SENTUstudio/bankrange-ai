"""Domain-specific exceptions for BankRange.

All domain errors derive from BankRangeDomainError so adapters can
catch domain exceptions at a single boundary.
"""


class BankRangeDomainError(Exception):
    """Base exception for all domain errors."""


class InvalidTopologyError(BankRangeDomainError):
    """Raised when the network topology is inconsistent.

    Examples: a workstation assigned to a non-existent segment,
    or a branch with no network segments.
    """


class WorkstationLimitExceededError(BankRangeDomainError):
    """Raised when a branch exceeds its workstation capacity.

    Each branch has a physical capacity constraint derived from
    its type (branch office vs. corporate headquarters).
    """


class SegmentCapacityExceededError(BankRangeDomainError):
    """Raised when a network segment runs out of available IPs.

    For example, a /24 CIDR block can only hold 254 usable IPs.
    """
