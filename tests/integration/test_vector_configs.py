"""Integration tests for Vector configuration files.

Validates that YAML configs meet expected structure and behavior.
"""

from pathlib import Path

import yaml


class TestVectorConfigs:
    """Vector configs must preserve fields and parse correctly."""

    def test_macos_config_preserves_message_field(self) -> None:
        """The macOS transform must NOT delete .message after parsing."""
        config_path = Path("config/vector/macos.yaml")
        assert config_path.exists()

        with open(config_path) as f:
            config = yaml.safe_load(f)

        transforms = config.get("transforms", {})
        process_macos = transforms.get("process_macos", {})
        source = process_macos.get("source", "")

        assert "del(.message)" not in source
        assert ".message = parts[6]" in source or "parts[6]" in source

    def test_linux_config_extracts_branch_via_regex(self) -> None:
        """The Linux transform must extract branch from message, not hardcode it."""
        config_path = Path("config/vector/linux.yaml")
        assert config_path.exists()

        with open(config_path) as f:
            config = yaml.safe_load(f)

        transforms = config.get("transforms", {})
        process_linux = transforms.get("process_linux", {})
        source = process_linux.get("source", "")

        assert '.branch = "SUC001"' not in source
        assert "branch=" in source

    def test_linux_config_fallbacks_to_unknown_when_no_branch(self) -> None:
        """When regex fails, branch must fallback to 'unknown', not crash."""
        config_path = Path("config/vector/linux.yaml")
        assert config_path.exists()

        with open(config_path) as f:
            config = yaml.safe_load(f)

        transforms = config.get("transforms", {})
        process_linux = transforms.get("process_linux", {})
        source = process_linux.get("source", "")

        assert '.branch = "unknown"' in source
        assert "if err != null" in source

    def test_windows_config_uses_named_elements(self) -> None:
        """Windows transform must access fixed fields by name, not array index."""
        config_path = Path("config/vector/windows.yaml")
        assert config_path.exists()

        with open(config_path) as f:
            config = yaml.safe_load(f)

        transforms = config.get("transforms", {})
        process_windows = transforms.get("process_windows", {})
        source = process_windows.get("source", "")

        assert "Data[0]" not in source
        assert "Data[1]" not in source
        assert "Data[2]" not in source
        assert "Data[3]" not in source
        assert 'Message."#text"' in source
        assert 'Level."#text"' in source
        assert 'IP."#text"' in source
        assert 'Branch."#text"' in source
