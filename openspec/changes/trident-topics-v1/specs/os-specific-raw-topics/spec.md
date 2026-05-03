# Spec: os-specific-raw-topics

## Purpose
Define the structure and routing of raw log data into dedicated Kafka topics per operating system.

## Requirements

### Requirement: OS-Specific Raw Topics
The system MUST provide dedicated Kafka topics for raw data:
- `bankrange-raw-windows`
- `bankrange-raw-linux`
- `bankrange-raw-macos`

#### Scenario: Raw Topic Creation
- GIVEN the `kafka-init` service.
- WHEN the stack starts.
- THEN all three specialized raw topics MUST be created with 3 partitions and 1 replication factor.

### Requirement: Raw Data Routing
The outbound event publisher MUST route events to the correct Kafka topic based on the `os` field of the log event.

#### Scenario: Routing Linux Raw Event
- GIVEN a log event with `os="linux"`.
- WHEN published to Kafka.
- THEN it MUST be sent to the `bankrange-raw-linux` topic.

#### Scenario: Routing Windows Raw Event
- GIVEN a log event with `os="windows"`.
- WHEN published to Kafka.
- THEN it MUST be sent to the `bankrange-raw-windows` topic.

#### Scenario: Routing MacOS Raw Event
- GIVEN a log event with `os="macos"`.
- WHEN published to Kafka.
- THEN it MUST be sent to the `bankrange-raw-macos` topic.

### Requirement: Vector Subscription
Each specialized Vector instance MUST subscribe ONLY to its corresponding OS-specific raw topic.

#### Scenario: Windows Vector Subscription
- GIVEN the `bankrange-vector-windows` service.
- WHEN configured at startup.
- THEN it MUST subscribe to `bankrange-raw-windows` and NOT to other raw topics.
