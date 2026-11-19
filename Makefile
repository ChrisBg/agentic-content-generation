.PHONY: help install dev format lint check security gate install-hooks test models run ui clean

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with uv
	uv pip install -e ".[ui]"

dev:  ## Install development and UI dependencies
	uv pip install -e ".[dev,ui]"

format:  ## Format code with ruff
	ruff format src/ scripts/ main.py ui_app.py app.py tests/

lint:  ## Lint code with ruff (includes flake8-bandit S security rules)
	ruff check src/ scripts/ main.py ui_app.py app.py tests/

check:  ## Run format and lint checks
	ruff format --check src/ scripts/ main.py ui_app.py app.py tests/
	ruff check src/ scripts/ main.py ui_app.py app.py tests/

security:  ## Run static security/secret scanner + security regression tests
	python scripts/security_check.py
	pytest tests/test_security.py -v

gate: check security test  ## Full pre-commit / pre-merge quality & security gate

install-hooks:  ## Install local Git pre-commit security hook
	cp scripts/git_pre_commit.sh .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "Installed .git/hooks/pre-commit security gate."

fix:  ## Auto-fix linting issues
	ruff check --fix src/ scripts/ main.py ui_app.py app.py tests/

test:  ## Run unit tests
	pytest tests/ -v

models:  ## Display active Multi-LLM routing table
	python main.py --models

run:  ## Run the v2 pipeline on the sample MFA experiment
	python main.py --topic "Frugal Hybrid MFA Detection" --input-dir examples/sample_mfa_experiment --channels linkedin,x,youtube --lang fr

ui:  ## Launch the Gradio v2 Studio UI (localhost 127.0.0.1 by default)
	@echo "Launching Research-to-Brand Multi-LLM Studio v2 at http://127.0.0.1:7860"
	python ui_app.py

clean:  ## Clean up generated caches
	rm -rf .ruff_cache __pycache__ .pytest_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
