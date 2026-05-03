# Vector Specialists Specification

## Purpose
Define the requirements for specialized Vector instances processing logs per platform (Windows, Linux, macOS).

## Requirements

### Requirement: Platform-Specific Configuration
Each Vector instance MUST have a dedicated YAML configuration file in `config/vector/`.
- `windows.yaml`
- `linux.yaml`
- `macos.yaml`

#### Scenario: Configuration Isolation
- GIVEN the `config/vector/` directory.
- WHEN a new specialist is added.
- THEN it MUST have its own configuration file, independent of others.

### Requirement: VRL Specialization
Each specialist MUST implement VRL (Vector Remap Language) transforms tailored to its platform's log format.

#### Scenario: Windows Parsing
- GIVEN a Windows Event Log entry.
- WHEN processed by `bankrange-vector-windows`.
- THEN it MUST extract Windows-specific fields (e.g., EventID, ProviderName).

### Requirement: Pipeline Lag Calculation
Each specialist MUST expose its pipeline lag metric via `internal_metrics`.

#### Scenario: Lag Monitoring
- GIVEN a specialist is processing logs.
- WHEN metrics are queried.
- THEN the `pipeline_lag_seconds` MUST be available and reflect the delay between log ingestion and sink delivery.

### Requirement: Dual Sinks
Each specialist MUST send processed logs to both Kafka and Loki.

#### Scenario: Data Consistency
- GIVEN a clean log event.
- WHEN processed by a specialist.
- THEN it MUST arrive in the specific OS Kafka topic AND in Loki with an `os` label.
