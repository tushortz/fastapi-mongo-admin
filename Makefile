.DEFAULT_GOAL := help

.PHONY: help install test lint secure

help: ## Show available commands
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Install dev dependencies with uv
	uv sync --group dev

test: ## Run pytest suite
	uv run pytest -v

lint: ## Run ruff linter
	uv run ruff check .

secure: ## Run bandit and pysentry-rs security scans
	uv run bandit -r fastapi_mongo_admin example/ecommerce -ll
	uv run pysentry-rs .
