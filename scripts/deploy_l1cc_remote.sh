#!/bin/sh
set -eu
cd "$HOME/spellbreaker"
mkdir -p evidence results models

if command -v podman >/dev/null 2>&1 && podman build -t spellbreaker:latest -f service/Containerfile .; then
  podman rm -f spellbreaker >/dev/null 2>&1 || true
  if podman run -d --name spellbreaker -p 8000:8000 spellbreaker:latest; then
    exit 0
  fi
fi

if command -v docker >/dev/null 2>&1 && docker build -t spellbreaker:latest -f service/Containerfile .; then
  docker rm -f spellbreaker >/dev/null 2>&1 || true
  if docker run -d --name spellbreaker -p 8000:8000 spellbreaker:latest; then
    exit 0
  fi
fi

python3 -m venv .venv
.venv/bin/pip install -r ml/requirements.txt -r service/requirements.txt
nohup .venv/bin/python -m uvicorn service.app:app --host 0.0.0.0 --port 8000 > evidence/uvicorn.log 2>&1 &
