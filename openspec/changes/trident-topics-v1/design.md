# Design: OS-Specific Raw Topics (trident-topics-v1)

## Architecture Decision

Refactor the raw data pipeline to use OS-specific Kafka topics for raw data instead of a single shared `bankrange-raw` topic.

## Components

### 1. Kafka Topics
Provision 3 new topics:
- `bankrange-raw-windows`
- `bankrange-raw-linux`
- `bankrange-raw-macos`
These will replace the legacy `bankrange-raw` topic.

### 2. Outbound Publisher (KafkaPublisher)
Update `KafkaPublisher` in `adapters/outbound/kafka_publisher.py` to route events to the correct topic based on the `os` field of the event.
Topics will follow the pattern: `bankrange-raw-{os}`.

### 3. Infrastructure (Docker Compose)
- Update `kafka-init` service to create all 6 topics (3 raw, 3 clean).
- Update Vector services' environment variables/subscriptions to point to their respective raw topics.

### 4. Vector Specialists
Update each specialist's config (`config/vector/*.yaml`) to use the new OS-specific raw topic as source and remove unnecessary internal filtering.

## Tradeoffs

### Pros
- Simplifies Vector routing logic.
- Improves performance by reducing unnecessary data processing in each Vector instance.
- Better separation of concerns.

### Cons
- Increased number of Kafka topics (manageable for this scale).
- Requires updates to multiple components simultaneously.

## Verification Strategy

- Automated tests for `KafkaPublisher` routing.
- Integration test for `docker-compose.yml` connectivity.
- Functional verification of end-to-end data flow per OS.
