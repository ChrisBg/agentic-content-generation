.PHONY: help install dev format lint check test run clean

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with uv
	uv pip install -e .

dev:  ## Install development dependencies
	uv pip install -e ".[dev]"

format:  ## Format code with ruff
	ruff format src/ main.py tests/

lint:  ## Lint code with ruff
	ruff check src/ main.py tests/

check:  ## Run format and lint checks
	ruff format --check src/ main.py tests/
	ruff check src/ main.py tests/

fix:  ## Auto-fix linting issues
	ruff check --fix src/ main.py tests/

test:  ## Run tests
	pytest tests/ -v

run:  ## Run the main agent
	python main.py

clean:  ## Clean up generated files
	rm -rf .ruff_cache __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
