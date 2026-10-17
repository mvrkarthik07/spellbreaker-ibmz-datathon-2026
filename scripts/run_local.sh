#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
PYTHON=.venv/bin/python
[ -x "$PYTHON" ] || PYTHON=python3
exec "$PYTHON" -m uvicorn service.app:app --host 0.0.0.0 --port 8000
