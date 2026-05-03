# Design: Trident of Vectors Architecture (v1)

## Technical Approach

The "Trident of Vectors" decentralizes the monolithic log processing into three specialized Vector instances. Each instance is responsible for a single platform's log format, reducing VRL complexity and improving resource isolation. The architecture leverages Docker Compose for orchestration and Kafka as the message broker for both raw and cleaned logs.

## Architecture Decisions

### Decision: Per-Platform Specialists

**Choice**: Three separate Vector containers (`bankrange-vector-windows`, `bankrange-vector-linux`, `bankrange-vector-macos`).
**Alternatives considered**: A single Vector instance with a large `router` transform.
**Rationale**: Isolation allows for platform-specific VRL tuning without risking the entire pipeline. If the Windows parser crashes or hangs, Linux and macOS processing continues.

### Decision: OS-Specific Kafka Topics

**Choice**: `bankrange-clean-windows`, `bankrange-clean-linux`, `bankrange-clean-macos`.
**Alternatives considered**: A single `bankrange-clean` topic with an `os` field in the JSON.
**Rationale**: Separate topics allow downstream consumers (like specific ML models or alerting rules) to subscribe only to the data they need, reducing cross-talk and improving throughput.

### Decision: Shared Loki Sink with Labels

**Choice**: All three specialists send to the same Loki endpoint but with a mandatory `os` label.
**Alternatives considered**: Separate Loki instances.
**Rationale**: Loki is designed for multi-tenancy and label-based filtering. A single instance is more cost-effective and easier to query in Grafana.

## Data Flow

```
   [Simulator API] ───→ [Kafka: bankrange-raw]
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
[Vector: Windows]     [Vector: Linux]       [Vector: macOS]
  (VRL XML)             (VRL Syslog)         (VRL Tabular)
         │                     │                     │
         ├─────────────────────┼─────────────────────┤
         ▼                     ▼                     ▼
[Kafka: clean-win]    [Kafka: clean-lin]    [Kafka: clean-mac]
         │                     │                     │
         └─────────────────────┴──────┬──────────────┘
                                      ▼
                               [Grafana / Loki]
                                (Labels: os, level)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `config/vector/windows.yaml` | Create | Specialist config for Windows Event Logs. |
| `config/vector/linux.yaml` | Create | Specialist config for Linux Syslog-style logs. |
| `config/vector/macos.yaml` | Create | Specialist config for macOS tabular logs. |
| `docker-compose.yml` | Modify | Replace `vector` service with the trident services and update `kafka-init`. |
| `config/vector.yaml` | Delete | Remove the legacy monolithic configuration. |

## Interfaces / Contracts

### Loki Label Schema
Every log entry MUST have the following labels in Loki:
- `os`: One of `windows`, `linux`, `macos`.
- `level`: Log level (normalized to lowercase).
- `environment`: Defaults to `simulation`.
- `branch`: The source branch of the simulation.

### Kafka Topic Contract
Topics MUST be created by `kafka-init` before Vector starts:
- `bankrange-clean-windows`
- `bankrange-clean-linux`
- `bankrange-clean-macos`

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Integration | Topic Creation | Verify `kafka-init` success in CI. |
| Integration | End-to-End Flow | Send a Windows log to `raw`, verify it appears in `clean-windows`. |
| Validation | VRL Logic | Use `vector vrl` command to validate snippets (manual/scripted). |

## Migration / Rollout

1. Deploy the new `config/vector/` directory.
2. Update `docker-compose.yml`.
3. Run `make up`.
4. Verify data flow in Kafka UI and Grafana.
5. Remove `config/vector.yaml`.

## Open Questions

- [ ] Should we use a base YAML and includes? *Decision: No, keep them self-contained for simplicity.*
