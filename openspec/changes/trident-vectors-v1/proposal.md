# Proposal: Trident of Vectors Architecture (v1)

## Intent

The current architecture uses a single Vector instance for all log types. This is a single point of failure and makes specialized processing (VRL) for different operating systems complex to maintain. The "Trident of Vectors" architecture splits log processing into three specialized Vector instances (Windows, Linux, macOS) to improve scalability, maintainability, and allow for platform-specific parsing and metadata enrichment.

## Scope

### In Scope
- Create specialized Vector configurations: `config/vector/windows.yaml`, `config/vector/linux.yaml`, `config/vector/macos.yaml`.
- Update `docker-compose.yml` to define three independent Vector services.
- Configure `kafka-init` to create separate "clean" topics for each OS: `bankrange-clean-windows`, `bankrange-clean-linux`, `bankrange-clean-macos`.
- Implement dual sinks for each Vector: Kafka (topic per OS) and Loki (unified with `os` label).
- Implement pipeline lag calculation metrics in each specialist.
- Remove legacy `config/vector.yaml`.

### Out of Scope
- Migrating existing dashboards to the new topic structure (future work).
- Implementing log rotation or retention policies in Vector.

## Capabilities

### New Capabilities
- `vector-specialists`: The ability to process logs using platform-specific Vector instances with specialized VRL.
- `os-specific-topics`: Individual Kafka topics for cleaned logs per OS, enabling easier downstream consumption.

### Modified Capabilities
- `log-orchestration`: Updating how Vector services are deployed and interconnected via Docker Compose.

## Approach

1. **Decoupling**: Replace the monolithic `vector.yaml` with three files in `config/vector/`. Each will share common base logic (Loki sink) but have unique VRL for parsing.
2. **Infrastructure-as-Code**: Update `docker-compose.yml` to reflect the trident structure, ensuring each Vector instance has proper environment variables and volume mounts.
3. **Observability**: Add `internal_metrics` source to each Vector and a `transform` to calculate lag, exposed for Loki/Grafana.
4. **Cleanup**: Only after verification of the new pipeline, the old configuration is purged.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `config/vector/` | New | Location for specialized YAML configs. |
| `docker-compose.yml` | Modified | Update services and Kafka topics. |
| `config/vector.yaml` | Removed | Legacy monolithic configuration. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Increased resource usage (3 containers vs 1) | Medium | Monitor container memory/CPU; Vector is lightweight. |
| Topic name mismatch in downstream consumers | Low | Standardize naming (bankrange-clean-{os}). |

## Rollback Plan

Revert `docker-compose.yml` changes and restore `config/vector.yaml` from Git history.

## Dependencies

- Vector (existing in project)
- Kafka (existing in project)
- Loki (existing in project)

## Success Criteria

- [ ] Three Vector services running in Docker Compose.
- [ ] Logs from Windows, Linux, and macOS arriving in their respective Kafka topics.
- [ ] All logs available in Loki with correct `os` labels.
- [ ] Pipeline lag metrics visible for each instance.
- [ ] Legacy `config/vector.yaml` is deleted.
