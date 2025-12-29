#!/bin/zsh
set -euo pipefail

# Run from this script's directory so .env loads correctly.
SCRIPT_DIR="${0:A:h}"
cd "$SCRIPT_DIR"

# Use the repo's virtual environment Python.
VENV_PY="${SCRIPT_DIR:h}/.venv/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
  echo "ERROR: Python venv not found at: $VENV_PY" >&2
  echo "Create it and install deps first:" >&2
  echo "  python3 -m venv .venv" >&2
  echo "  .venv/bin/python -m pip install -r twitterbot/requirements.txt" >&2
  exit 1
fi

exec "$VENV_PY" twitter_bot.py
