#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PYTHON=.venv/bin/python
[ -x "$PYTHON" ] || PYTHON=python3
WORKERS=${UVICORN_WORKERS:-1}
exec "$PYTHON" -m uvicorn service.app:app --host 0.0.0.0 --port 8000 --workers "$WORKERS"
