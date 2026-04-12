"""Unit tests for domain Value Objects.

Tests validate the invariants of IPAddress, MacAddress, and OSType
as defined in the ubiquitous language of BankRange.
"""

import pytest
from pydantic import ValidationError

from core.domain.value_objects import IPAddress, MacAddress, OSType


class TestIPAddress:
    """An IP address must be a valid, private IPv4 address."""

    def test_valid_private_ip_is_accepted(self) -> None:
        """Bank workstations use RFC 1918 private addresses."""
        ip = IPAddress(value="10.1.1.10")
        assert ip.value == "10.1.1.10"

    def test_public_ip_is_rejected(self) -> None:
        """Public IPs must never be assigned to bank workstations."""
        with pytest.raises(ValueError, match="private IPs"):
            IPAddress(value="8.8.8.8")

    def test_invalid_ip_format_is_rejected(self) -> None:
        """Garbage strings are not valid IP addresses."""
        with pytest.raises(ValueError, match="Invalid IPv4"):
            IPAddress(value="not-an-ip")

    def test_ip_is_immutable(self) -> None:
        """Value objects must be frozen (immutable)."""
        ip = IPAddress(value="10.0.0.1")
        with pytest.raises(ValidationError):
            ip.value = "10.0.0.2"  # type: ignore[misc]


class TestMacAddress:
    """A MAC address must follow colon-separated hex format."""

    def test_valid_mac_is_accepted(self) -> None:
        mac = MacAddress(value="AA:BB:CC:DD:EE:FF")
        assert mac.value == "AA:BB:CC:DD:EE:FF"

    def test_lowercase_mac_is_normalized_to_uppercase(self) -> None:
        """MAC addresses are stored in uppercase for consistency."""
        mac = MacAddress(value="aa:bb:cc:dd:ee:ff")
        assert mac.value == "AA:BB:CC:DD:EE:FF"

    def test_invalid_mac_format_is_rejected(self) -> None:
        """Only colon-separated hex pairs are accepted."""
        with pytest.raises(ValidationError):
            MacAddress(value="AABBCCDDEEFF")  # No separators


class TestOSType:
    """Operating system types in a banking environment."""

    def test_valid_os_types(self) -> None:
        """Banks typically run Windows, Linux, and macOS."""
        assert OSType.WINDOWS == "windows"
        assert OSType.LINUX == "linux"
        assert OSType.MACOS == "macos"

    def test_os_type_is_string_enum(self) -> None:
        """OSType must be usable as a plain string for serialization."""
        assert isinstance(OSType.WINDOWS, str)
        assert f"OS: {OSType.WINDOWS}" == "OS: windows"
