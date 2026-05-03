# Explore Report: orchestration-v1

## Goal
Explore the current state of the project and identify requirements for:
1. Dockerizing the API and UI.
2. Updating `docker-compose.yml`.
3. Auto-provisioning Kafka topics.
4. Simplifying the `Makefile`.

## Current State
- **API**: FastAPI, runs on 8000. Uses `BR_BRANCHES`, `BR_WORKSTATIONS`, `BR_KAFKA_BROKERS`, `BR_KAFKA_TOPIC`.
- **UI**: Streamlit, runs on 8501. Uses `BR_API_URL`.
- **Infrastructure**: Kafka, Loki, Grafana, Vector already defined in `docker-compose.yml`.
- **Makefile**: Has manual commands for running API, UI, and creating Kafka topics.
- **Dependencies**: Managed by `uv`.

## Requirements
- `Dockerfile.api`: Use `uv` for minimal image size.
- `Dockerfile.ui`: Use `uv` for minimal image size.
- `docker-compose.yml`:
  - Add `bankrange-api` and `bankrange-ui`.
  - Add healthchecks for `bankrange-api`.
  - Add `init-kafka` for topic provisioning.
  - Set dependencies using `depends_on`.
- `Makefile`:
  - Update `up` to include API and UI.
  - Remove manual `topic-create` if auto-provisioned.
