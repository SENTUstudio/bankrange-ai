import os

import yaml


def test_dockerfile_api_exists():
    assert os.path.exists("Dockerfile.api"), "Dockerfile.api must exist"


def test_dockerfile_api_base_image():
    with open("Dockerfile.api") as f:
        content = f.read()
    assert "FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim" in content, (
        "Dockerfile.api must use uv base image"
    )


def test_dockerfile_ui_exists():
    assert os.path.exists("Dockerfile.ui"), "Dockerfile.ui must exist"


def test_dockerfile_ui_base_image():
    with open("Dockerfile.ui") as f:
        content = f.read()
    assert "FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim" in content, (
        "Dockerfile.ui must use uv base image"
    )


def test_docker_compose_services_exist():
    with open("docker-compose.yml") as f:
        config = yaml.safe_load(f)

    services = config.get("services", {})
    assert "kafka-init" in services, "kafka-init service must exist in docker-compose"
    assert "bankrange-api" in services, "bankrange-api service must exist in docker-compose"
    assert "bankrange-ui" in services, "bankrange-ui service must exist in docker-compose"


def test_docker_compose_dependencies():
    with open("docker-compose.yml") as f:
        config = yaml.safe_load(f)

    services = config.get("services", {})
    api = services.get("bankrange-api", {})
    ui = services.get("bankrange-ui", {})

    # API depends on kafka-init completed
    api_depends_on = api.get("depends_on", {})
    assert "kafka-init" in api_depends_on
    assert api_depends_on["kafka-init"]["condition"] == "service_completed_successfully"

    # UI depends on API healthy
    ui_depends_on = ui.get("depends_on", {})
    assert "bankrange-api" in ui_depends_on
    assert ui_depends_on["bankrange-api"]["condition"] == "service_healthy"
