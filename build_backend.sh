#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend/parquetformatter_api"
REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"
VENV_PATH="$BACKEND_DIR/.venv_build"

PYTHON_BIN=${PYTHON_BIN:-/opt/homebrew/bin/python3.11}
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN=${PYTHON_BIN_FALLBACK:-python3.11}
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "❌ $PYTHON_BIN not found. Install Python 3.11 (e.g. 'brew install python@3.11') and ensure it is on your PATH, or set PYTHON_BIN to the interpreter you want to use." >&2
  exit 1
fi

printf '\n▶︎ Setting up backend virtual environment\n'
"$PYTHON_BIN" -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"
pip install --upgrade pip >/dev/null
pip install -r "$REQUIREMENTS_FILE" >/dev/null

printf '\n▶︎ Running backend tests\n'
pytest "$BACKEND_DIR/tests"

deactivate
rm -rf "$VENV_PATH"

printf '\n✅ Backend build/test complete\n'
