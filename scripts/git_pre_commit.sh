#!/usr/bin/env bash
# Built-in Git pre-commit security & quality gate (installed via `make install-hooks`)
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Resolve Python / Ruff / Pytest from local .venv, /tmp/acg-venv, or PATH
PYTHON_BIN=""
for candidate in "$REPO_ROOT/.venv/bin/python" "/tmp/acg-venv/bin/python" "$(command -v python3 || true)"; do
  if [ -n "$candidate" ] && [ -x "$candidate" ]; then
    PYTHON_BIN="$candidate"
    break
  fi
done

RUFF_BIN=""
for candidate in "$REPO_ROOT/.venv/bin/ruff" "/tmp/acg-venv/bin/ruff" "$(command -v ruff || true)"; do
  if [ -n "$candidate" ] && [ -x "$candidate" ]; then
    RUFF_BIN="$candidate"
    break
  fi
done

echo "[pre-commit] 1/3 Running static security & secret scan..."
"$PYTHON_BIN" scripts/security_check.py

if [ -n "$RUFF_BIN" ]; then
  echo "[pre-commit] 2/3 Running Ruff lint (including flake8-bandit S security rules)..."
  "$RUFF_BIN" check src/ scripts/ main.py ui_app.py app.py tests/
else
  echo "[pre-commit] WARNING: ruff not found on PATH; skipping Ruff check."
fi

PYTEST_BIN="${PYTHON_BIN%python*}pytest"
if [ -x "$PYTEST_BIN" ]; then
  echo "[pre-commit] 3/3 Running security regression tests..."
  PYTHONPATH=. "$PYTEST_BIN" tests/test_security.py -q
else
  echo "[pre-commit] WARNING: pytest not found; skipping security unit tests."
fi

echo "[pre-commit] All security & quality checks passed."
