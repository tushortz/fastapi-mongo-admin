.PHONY: install test lint

install:
	uv sync --group dev

test:
	uv run pytest -v

lint:
	uv run ruff check .
