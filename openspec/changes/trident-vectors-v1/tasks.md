# Tasks: Trident of Vectors Architecture (v1)

## Phase 1: Vector Specialist Configurations

- [x] 1.1 Create `config/vector/windows.yaml` with XML parsing VRL, dual sinks, and lag calculation.
- [x] 1.2 Create `config/vector/linux.yaml` with Syslog regex VRL, dual sinks, and lag calculation.
- [x] 1.3 Create `config/vector/macos.yaml` with Tabular/Split VRL, dual sinks, and lag calculation.
- [x] 1.4 Verify VRL syntax for each specialist using `vector validate` (if available).

## Phase 2: Infrastructure and Orchestration

- [x] 2.1 Update `kafka-init` in `docker-compose.yml` to create `bankrange-clean-windows`, `bankrange-clean-linux`, and `bankrange-clean-macos`.
- [x] 2.2 Modify `docker-compose.yml`: Remove `vector` service and add `bankrange-vector-windows`, `bankrange-vector-linux`, `bankrange-vector-macos`.
- [x] 2.3 Configure environment variables and volume mounts for each Vector specialist in `docker-compose.yml`.

## Phase 3: Testing and Verification

- [x] 3.1 Restart the stack using `make up`.
- [x] 3.2 Verify that all 4 clean topics (3 new + legacy raw) exist using Kafka UI or CLI.
- [x] 3.3 Trigger Windows log generation and verify arrival in `bankrange-clean-windows` and Loki with `os=windows`.
- [x] 3.4 Trigger Linux log generation and verify arrival in `bankrange-clean-linux` and Loki with `os=linux`.
- [x] 3.5 Trigger macOS log generation and verify arrival in `bankrange-clean-macos` and Loki with `os=macos`.
- [x] 3.6 Verify `pipeline_lag_ms` metric is present in Loki/Grafana for each specialist.

## Phase 4: Cleanup

- [x] 4.1 Remove the legacy `config/vector.yaml` file.
- [x] 4.2 Verify that the stack remains operational after removal.
- [x] 4.3 Update README.md if necessary to reflect the new architecture.
