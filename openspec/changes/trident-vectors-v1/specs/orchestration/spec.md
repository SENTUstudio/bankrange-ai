# Delta for Orchestration

## MODIFIED Requirements

### Requirement: Automated Provisioning
(Previously: Kafka topics `bankrange-raw` and `bankrange-clean` must be created automatically. Topics must have 3 partitions and 1 replication factor.)

Kafka topics `bankrange-raw`, `bankrange-clean-windows`, `bankrange-clean-linux`, and `bankrange-clean-macos` MUST be created automatically. All topics SHALL have 3 partitions and 1 replication factor.

#### Scenario: Fresh Start
- GIVEN the environment is clean.
- WHEN `make up` is executed.
- THEN Kafka starts, then `kafka-init` creates all 4 topics, then specialized Vector services start, then API starts, then UI starts.
- AND all services are accessible.

### Requirement: Developer Workflow
(Previously: `make up` must start all components. `make down` must clean up all resources.)

`make up` MUST start all components, including the three specialized Vector services. `make down` SHALL clean up all resources, including the specialized Vector containers.

#### Scenario: Cleanup
- GIVEN the trident-vectors stack is running.
- WHEN `make down` is executed.
- THEN all three Vector services (`bankrange-vector-windows`, `bankrange-vector-linux`, `bankrange-vector-macos`) MUST be stopped and removed.
