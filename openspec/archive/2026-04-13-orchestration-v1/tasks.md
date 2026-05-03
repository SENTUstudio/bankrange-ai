# Tasks: orchestration-v1

## Implementation Checklist
- [x] **Dockerization**
  - [x] Create `Dockerfile.api` based on `uv`.
  - [x] Create `Dockerfile.ui` based on `uv`.
  - [x] Test local builds for both.
- [x] **Orchestration**
  - [x] Update `docker-compose.yml` with `kafka-init` service.
  - [x] Add `bankrange-api` service with healthcheck.
  - [x] Add `bankrange-ui` service.
  - [x] Configure environment variables for internal networking.
  - [x] Update `vector` to depend on `kafka-init`.
- [x] **Developer Experience**
  - [x] Update `Makefile`: Simplify `up`, `down`, and `clean`.
  - [x] Remove manual topic creation steps.
- [x] **Verification**
  - [x] Execute `make up` and verify all services start correctly.
  - [x] Verify `kafka-init` logs show topic creation.
  - [x] Access API on `http://localhost:8000/status`.
  - [x] Access UI on `http://localhost:8501`.
  - [x] Verify Vector is transmitting data (check logs).
  - [x] Check Grafana dashboards.
