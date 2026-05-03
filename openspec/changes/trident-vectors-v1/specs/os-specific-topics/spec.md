# OS-Specific Topics Specification

## Purpose
Define the Kafka topic structure for cleaned logs per operating system.

## Requirements

### Requirement: Dedicated Clean Topics
The system MUST provide individual Kafka topics for cleaned logs:
- `bankrange-clean-windows`
- `bankrange-clean-linux`
- `bankrange-clean-macos`

#### Scenario: Topic Creation
- GIVEN the `kafka-init` service.
- WHEN the stack starts.
- THEN all three specialized topics MUST be created with 3 partitions and 1 replication factor.

#### Scenario: Routing Accuracy
- GIVEN a Linux log entry.
- WHEN cleaned by the Linux specialist.
- THEN it MUST be published only to `bankrange-clean-linux`.
