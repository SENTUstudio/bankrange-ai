# Proposal: orchestration-v1

## Goal
Implement a fully dockerized development environment that includes the API and UI, with automatic provisioning of Kafka topics and simplified orchestration.

## Approach
1. **Dockerization**:
   - Create two Dockerfiles (`Dockerfile.api`, `Dockerfile.ui`) based on `uv` to ensure minimal image size and fast builds.
   - API will run `uvicorn adapters.inbound.api.app:app`.
   - UI will run `streamlit run adapters/inbound/ui/dashboard.py`.
2. **Orchestration**:
   - Update `docker-compose.yml` to include `bankrange-api` and `bankrange-ui`.
   - Implement `kafka-init` service that uses `kafka-topics` to create the required topics (`bankrange-raw`, `bankrange-clean`).
   - Define service dependencies and healthchecks to ensure correct startup order.
3. **Developer Experience**:
   - Update `Makefile` to reflect the new dockerized workflow.
   - Ensure the entire stack can be started with a single `make up` command.

## Tradeoffs
- **Pros**: Consistent environment, easy setup, automated topic creation.
- **Cons**: Slightly more complex `docker-compose.yml`.

## Risks
- **Startup Latency**: Kafka can take time to be healthy. Healthchecks and `depends_on` are used to mitigate this.
