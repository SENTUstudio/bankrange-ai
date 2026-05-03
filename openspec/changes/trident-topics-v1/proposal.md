# Proposal: OS-Specific Raw Topics (trident-topics-v1)

## Intent

Refactor the raw data pipeline to use OS-specific Kafka topics for raw data instead of a single shared `bankrange-raw` topic. This simplifies Vector routing by allowing each specialized instance to subscribe only to its relevant data source, avoiding internal filtering and improving separation of concerns.

## Scope

### In Scope
- Refactor `KafkaPublisher` in `adapters/outbound/kafka_publisher.py` to route events to `bankrange-raw-windows`, `bankrange-raw-linux`, or `bankrange-raw-macos` based on the event's `os` field.
- Update `docker-compose.yml`:
  - Update `kafka-init` to create the 3 new raw topics (with 3 partitions, 1 replication factor).
  - Update Vector services (`bankrange-vector-windows`, `bankrange-vector-linux`, `bankrange-vector-macos`) to subscribe to their respective OS-specific topics.
- Update Vector configurations in `config/vector/*.yaml` (`windows.yaml`, `linux.yaml`, `macos.yaml`):
  - Change `source` topic to the new OS-specific raw topic.
  - Remove the internal `filter` transform (as routing is now handled by Kafka topics).
- Cleanup legacy `bankrange-raw` topic in infrastructure.

### Out of Scope
- Modifying the clean data topics (already handled by `trident-vectors-v1`).
- Changes to the API endpoint logic (only the outbound publisher changes).
- Changes to the UI dashboard logic.

## Capabilities

### New Capabilities
- `os-specific-raw-topics`: Provisioning and routing of raw log data into dedicated Kafka topics per operating system.

### Modified Capabilities
- `orchestration`: Update infrastructure setup to support specialized raw topics and service subscriptions.

## Approach

1. **Adapter Update**: Modify `KafkaPublisher.publish` to use a mapping or conditional logic to select the target topic based on `event.os`.
2. **Infrastructure Update**: 
   - Update `kafka-init` service in `docker-compose.yml`.
   - Update environment variables for Vector services in `docker-compose.yml` if topics are configured via env.
3. **Vector Config Cleanup**: 
   - Direct source to the OS topic.
   - Remove the `routing` or `filter` transforms that were previously used to discard logs from other OSs.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `adapters/outbound/kafka_publisher.py` | Modified | Routing logic for OS-specific topics. |
| `docker-compose.yml` | Modified | Topic creation and service configuration. |
| `config/vector/windows.yaml` | Modified | Source topic and filter removal. |
| `config/vector/linux.yaml` | Modified | Source topic and filter removal. |
| `config/vector/macos.yaml` | Modified | Source topic and filter removal. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Missing 'os' field in event | Low | Add default topic or error handling in `KafkaPublisher`. |
| Topic names mismatch | Medium | Use constants for topic names. |
| Incomplete cleanup of legacy topic | Low | Verify `kafka-init` removes or stops creating `bankrange-raw`. |

## Rollback Plan

Revert changes in `kafka_publisher.py`, `docker-compose.yml`, and `config/vector/*.yaml` to return to the single `bankrange-raw` topic and internal filtering.

## Dependencies

- None.

## Success Criteria

- [ ] Events from different OSs are published to their respective `bankrange-raw-*` topics.
- [ ] Each Vector instance receives ONLY logs from its target OS.
- [ ] `sdd-verify` passes verification checks for topic isolation.
