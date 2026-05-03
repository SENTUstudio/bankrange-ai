# Delta for orchestration

## MODIFIED Requirements

### Requirement: Automated Provisioning

Kafka topics `bankrange-raw-windows`, `bankrange-raw-linux`, `bankrange-raw-macos` and `bankrange-clean` MUST be created automatically. Topics MUST have 3 partitions and 1 replication factor.
(Previously: Kafka topics `bankrange-raw` and `bankrange-clean` were created automatically).

#### Scenario: Fresh Start
- GIVEN the environment is clean.
- WHEN `make up` is executed.
- THEN Kafka starts, then `kafka-init` creates all specified topics, then API starts, then UI starts.
- AND all services are accessible.

#### Scenario: Service Recovery
- GIVEN the stack is running.
- WHEN the API container is restarted.
- THEN it MUST reconnect to Kafka and continue functioning.

#### Scenario: Volume Persistence
- GIVEN the stack is running and data has been produced.
- WHEN `make down` is executed WITHOUT `-v`.
- THEN Kafka data MUST persist on next `make up`.
