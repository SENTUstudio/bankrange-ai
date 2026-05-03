# Tasks: OS-Specific Raw Topics (trident-topics-v1)

## Phase 1: Outbound Adapter Update

- [ ] 1.1 Refactor `adapters/outbound/kafka_publisher.py`: Update `publish` and `publish_batch` to route events to `bankrange-raw-{os}` dynamically.
- [ ] 1.2 Add or update tests for `KafkaPublisher` to verify correct OS-specific routing.

## Phase 2: Infrastructure Update

- [ ] 2.1 Update `docker-compose.yml`: Expand `kafka-init` to create `bankrange-raw-windows`, `bankrange-raw-linux`, `bankrange-raw-macos`.
- [ ] 2.2 Update `docker-compose.yml`: Update subscriptions for `bankrange-vector-windows`, `bankrange-vector-linux`, and `bankrange-vector-macos` services to point to OS-specific topics.

## Phase 3: Vector Config Cleanup

- [ ] 3.1 Update `config/vector/windows.yaml`: Point to `bankrange-raw-windows` and remove filters.
- [ ] 3.2 Update `config/vector/linux.yaml`: Point to `bankrange-raw-linux` and remove filters.
- [ ] 3.3 Update `config/vector/macos.yaml`: Point to `bankrange-raw-macos` and remove filters.

## Phase 4: Verification and Finalization

- [ ] 4.1 Run `sdd-verify` to ensure all requirements are met.
- [ ] 4.2 Run `sdd-archive` to finalize the change.
