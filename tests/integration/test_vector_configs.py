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

    # ── #25: Loki healthcheck & Vector sink reliability ──

    @staticmethod
    def _load_docker_compose() -> dict:
        """Load and return the docker-compose.yml as a dict."""
        compose_path = Path("docker-compose.yml")
        assert compose_path.exists(), "docker-compose.yml not found"
        with open(compose_path) as f:
            return yaml.safe_load(f)

    def test_loki_has_healthcheck_block(self) -> None:
        """Loki service must have a healthcheck block targeting /ready."""
        compose = self._load_docker_compose()
        loki = compose["services"]["loki"]
        assert "healthcheck" in loki, "Loki service must have a healthcheck block"
        hc = loki["healthcheck"]
        assert "test" in hc, "Healthcheck must include a 'test' command"
        test_cmd = hc["test"]
        # The test command must reference /ready somewhere
        test_str = " ".join(str(p) for p in test_cmd)
        assert "/ready" in test_str, (
            f"Healthcheck test must target Loki /ready endpoint, got: {test_str}"
        )

    def test_vector_services_depend_on_loki_service_healthy(self) -> None:
        """All three Vector services must declare loki: condition: service_healthy."""
        compose = self._load_docker_compose()
        for svc_name in ("vector-windows", "vector-linux", "vector-macos"):
            svc = compose["services"][svc_name]
            deps = svc.get("depends_on", {})
            assert "loki" in deps, f"{svc_name} must depend on loki"
            loki_dep = deps["loki"]
            if isinstance(loki_dep, dict):
                assert loki_dep.get("condition") == "service_healthy", (
                    f"{svc_name} must use loki: condition: service_healthy, "
                    f"got: {loki_dep.get('condition')}"
                )
            else:
                raise AssertionError(
                    f"{svc_name} loki dependency must include condition: service_healthy"
                )

    def test_windows_sink_healthcheck_enabled(self) -> None:
        """Windows Vector Loki sink must have healthcheck.enabled: true."""
        config_path = Path("config/vector/windows.yaml")
        assert config_path.exists()
        with open(config_path) as f:
            config = yaml.safe_load(f)
        sinks = config.get("sinks", {})
        out_loki = sinks.get("out_loki", {})
        hc = out_loki.get("healthcheck", {})
        assert hc.get("enabled") is True, (
            f"Windows sink healthcheck must be enabled=true, got: {hc.get('enabled')}"
        )

    def test_linux_sink_healthcheck_enabled(self) -> None:
        """Linux Vector Loki sink must have healthcheck.enabled: true."""
        config_path = Path("config/vector/linux.yaml")
        assert config_path.exists()
        with open(config_path) as f:
            config = yaml.safe_load(f)
        sinks = config.get("sinks", {})
        out_loki = sinks.get("out_loki", {})
        hc = out_loki.get("healthcheck", {})
        assert hc.get("enabled") is True, (
            f"Linux sink healthcheck must be enabled=true, got: {hc.get('enabled')}"
        )

    def test_macos_sink_healthcheck_enabled(self) -> None:
        """macOS Vector Loki sink must have healthcheck.enabled: true."""
        config_path = Path("config/vector/macos.yaml")
        assert config_path.exists()
        with open(config_path) as f:
            config = yaml.safe_load(f)
        sinks = config.get("sinks", {})
        out_loki = sinks.get("out_loki", {})
        hc = out_loki.get("healthcheck", {})
        assert hc.get("enabled") is True, (
            f"macOS sink healthcheck must be enabled=true, got: {hc.get('enabled')}"
        )
