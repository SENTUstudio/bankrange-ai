# Spec: orchestration-v1

## Functional Requirements
1. **API Dockerization**:
   - Must run the FastAPI application.
   - Must expose port 8000.
   - Must be configurable via environment variables.
2. **UI Dockerization**:
   - Must run the Streamlit dashboard.
   - Must expose port 8501.
   - Must connect to the `bankrange-api` container via internal networking.
3. **Automated Provisioning**:
   - Kafka topics `bankrange-raw` and `bankrange-clean` must be created automatically.
   - Topics must have 3 partitions and 1 replication factor.
4. **Developer Workflow**:
   - `make up` must start all components.
   - `make down` must clean up all resources.

## Scenarios
- **Scenario 1: Fresh Start**
  - Given the environment is clean.
  - When `make up` is executed.
  - Then Kafka starts, then `kafka-init` creates topics, then API starts, then UI starts.
  - And all services are accessible.
- **Scenario 2: Service Recovery**
  - Given the stack is running.
  - When the API container is restarted.
  - Then it must reconnect to Kafka and continue functioning.
- **Scenario 3: Volume Persistence**
  - Given the stack is running and data has been produced.
  - When `make down` is executed WITHOUT `-v`.
  - Then Kafka data must persist on next `make up`. (Note: Currently `make down` uses `-v`, so this depends on how we simplify it).

## Non-Functional Requirements
- **Build Speed**: Docker images must use `uv` and be cached efficiently.
- **Reliability**: Use healthchecks to prevent service failures during startup.
- **Portability**: The setup must work on any machine with Docker and `uv` (optional if using Docker only).
