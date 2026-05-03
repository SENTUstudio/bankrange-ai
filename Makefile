.PHONY: help install test test-cov lint lint-fix format typecheck quality up down logs run run-api run-ui clean

help: ## Show this help message
	@echo "======================================================================"
	@echo "🛡️  BankRange: Cyber Log Simulator - Developer Commands"
	@echo "======================================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using uv
	uv sync

test: ## Run unit and integration tests
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage report
	uv run pytest tests/ -v --cov=adapters --cov=config --cov=core --cov-report=term-missing --cov-report=html

lint: ## Run linter (ruff check)
	uv run ruff check .

lint-fix: ## Run linter and auto-fix issues
	uv run ruff check --fix .

format: ## Format code with ruff
	uv run ruff format .

typecheck: ## Run static type checker (mypy)
	uv run mypy .

quality: ## Run all quality checks (format, lint, typecheck, test-cov)
	@echo "🧹 Running formatter..."
	uv run ruff format .
	@echo "🔍 Running linter..."
	uv run ruff check .
	@echo "📝 Running type checker..."
	uv run mypy .
	@echo "🧪 Running tests with coverage..."
	uv run pytest tests/ -v --cov=adapters --cov=config --cov=core --cov-report=term-missing

up: ## Start the full dockerized stack
	docker-compose up -d --build
	@echo "🚀 Stack is UP! API: http://localhost:8000, UI: http://localhost:8501, Kafka UI: http://localhost:8080"

down: ## Stop the stack & wipe volumes
	docker-compose down -v
	@echo "🧹 Infrastructure wiped cleanly."

logs: ## Follow the logs of the Docker infrastructure
	docker-compose logs -f

run-api: ## Start the C&C FastAPI Engine Background Loop (local)
	uv run uvicorn adapters.inbound.api.app:app --host 0.0.0.0 --port 8000

run-ui: ## Start the Streamlit Control Panel Interface (local)
	uv run streamlit run adapters/inbound/ui/dashboard.py

clean: ## Remove cache files and docker build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	docker system prune -f
