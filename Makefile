.PHONY: help install test up down logs run run-heavy clean

help: ## Show this help message
	@echo "======================================================================"
	@echo "🛡️  BankRange: Cyber Log Simulator - Developer Commands"
	@echo "======================================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using uv
	uv pip install -e .
	uv sync

test: ## Run strict TDD unit and integration tests
	uv run pytest tests/ -v

up: ## Start the local Kafka infrastructure (KRaft) and Web UI
	docker-compose up -d
	@echo "Waiting for Kafka to be healthy..."
	@sleep 5
	@echo "✅ Infrastructure is UP! Kafka UI available at: http://localhost:8080"

down: ## Stop the local Kafka infrastructure & wipe volumes
	docker-compose down -v
	@echo "🧹 Infrastructure wiped cleanly."

logs: ## Follow the logs of the Docker infrastructure
	docker-compose logs -f

run-cli: ## (Legacy) Run the static terminal simulation CLI 
	uv run python -m adapters.inbound.cli.runner

run-api: ## Start the C&C FastAPI Engine Background Loop
	uv run uvicorn adapters.inbound.api.app:app --host 0.0.0.0 --port 8000

run-ui: ## Start the Streamlit Control Panel Interface
	uv run streamlit run adapters/inbound/ui/dashboard.py

topic-create: ## Manually provision the Double-Hop topics
	docker-compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic bankrange-raw --partitions 3 --replication-factor 1
	docker-compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic bankrange-clean --partitions 3 --replication-factor 1

clean: ## Remove python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
