# Design: orchestration-v1

## Architecture Overview
The project will move to a fully dockerized environment. The API and UI will no longer require local `uv run` commands for normal development, although the local workflow will still be supported via `Makefile`.

## Docker Images
### Dockerfile.api
- **Base**: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`
- **Build**:
  - Install dependencies using `uv sync --frozen --no-dev`.
  - Copy only the required code (`core/`, `adapters/`).
- **CMD**: `uv run uvicorn adapters.inbound.api.app:app --host 0.0.0.0 --port 8000`

### Dockerfile.ui
- **Base**: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`
- **Build**: Same as API.
- **CMD**: `uv run streamlit run adapters/inbound/ui/dashboard.py --server.port 8501 --server.address 0.0.0.0`

## Orchestration (docker-compose.yml)
- **Services**:
  - `kafka`: (existing) Message broker.
  - `kafka-init`: New service to auto-create topics.
  - `bankrange-api`: New service for the FastAPI engine.
  - `bankrange-ui`: New service for the Streamlit UI.
  - `vector`, `loki`, `grafana`: (existing) Observability stack.
- **Dependencies**:
  - `kafka-init` depends on `kafka` healthy.
  - `bankrange-api` depends on `kafka-init` completed successfully and `kafka` healthy.
  - `bankrange-ui` depends on `bankrange-api` healthy.
  - `vector` depends on `kafka-init` completed and `kafka` healthy.

## Environment Variables
- `BR_API_URL`: Set to `http://bankrange-api:8000` for the UI container.
- `BR_KAFKA_BROKERS`: Set to `kafka:29092` for the API container.

## Topic Provisioning Strategy
Use a dedicated `kafka-init` service that runs once:
```yaml
kafka-init:
  image: confluentinc/cp-kafka:7.5.0
  depends_on:
    kafka:
      condition: service_healthy
  command: >
    /bin/bash -c "
    kafka-topics --create --if-not-exists --bootstrap-server kafka:29092 --topic bankrange-raw --partitions 3 --replication-factor 1 &&
    kafka-topics --create --if-not-exists --bootstrap-server kafka:29092 --topic bankrange-clean --partitions 3 --replication-factor 1
    "
```

## Makefile Simplification
- `up`: `docker-compose up -d --build`
- `down`: `docker-compose down -v`
- `logs`: `docker-compose logs -f`
- `clean`: Remove caches.
- Keep `run-api` and `run-ui` for local debugging if needed, but they are no longer the primary way to run the project.
