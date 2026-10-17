#!/bin/sh
set -eu
rsync -az --exclude data --exclude .git ./ l1cc:~/spellbreaker/
ssh l1cc 'cd ~/spellbreaker && ./scripts/train_l1cc.sh'
ssh l1cc 'cd ~/spellbreaker && if command -v podman >/dev/null 2>&1; then podman build -t spellbreaker:latest -f service/Containerfile . && (podman rm -f spellbreaker || true) && podman run -d --name spellbreaker -p 8000:8000 spellbreaker:latest; elif command -v docker >/dev/null 2>&1; then docker build -t spellbreaker:latest -f service/Containerfile . && (docker rm -f spellbreaker || true) && docker run -d --name spellbreaker -p 8000:8000 spellbreaker:latest; else python3 -m venv .venv && .venv/bin/pip install -r ml/requirements.txt -r service/requirements.txt && (nohup .venv/bin/python -m uvicorn service.app:app --host 0.0.0.0 --port 8000 > evidence/uvicorn.log 2>&1 &); fi'
ssh l1cc 'curl -fsS localhost:8000/health'
ssh l1cc 'cd ~/spellbreaker && python3 bench/loadtest.py --requests 10000 --concurrency 16'
./scripts/collect_evidence.sh
