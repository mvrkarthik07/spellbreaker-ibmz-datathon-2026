#!/bin/sh
set -eu
mkdir -p evidence
if ! ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'test -d ~/spellbreaker'; then
  echo 'Needs human: SSH alias l1cc unavailable; evidence was not captured.' > evidence/README.md
  exit 1
fi
ssh l1cc 'uname -a; cat /etc/os-release; lscpu; nproc; free -g' > evidence/platform.txt
ssh l1cc 'grep -m1 features /proc/cpuinfo; grep -c nnpa /proc/cpuinfo' > evidence/cpu_features.txt
ssh l1cc 'cd ~/spellbreaker && (podman --version && podman images && podman ps && podman inspect spellbreaker --format "{{.Config.User}}" || docker --version && docker images && docker ps && docker inspect spellbreaker --format "{{.Config.User}}")' > evidence/container.txt 2>&1
ssh l1cc 'python3 --version; if command -v podman >/dev/null 2>&1 && podman ps --format {{.Names}} | grep -q spellbreaker; then podman exec spellbreaker pip freeze; elif command -v docker >/dev/null 2>&1 && docker ps --format {{.Names}} | grep -q spellbreaker; then docker exec spellbreaker pip freeze; else cd ~/spellbreaker && .venv/bin/pip freeze; fi' > evidence/python_env.txt
ssh l1cc 'cd ~/spellbreaker && cat evidence/train_l1cc.log' > evidence/train_l1cc.log
ssh l1cc 'curl -fsS localhost:8000/health' > evidence/health.json
ssh l1cc 'cd ~/spellbreaker && cat results/bench.json' > results/bench.json
cp results/bench.json evidence/bench.txt
ssh l1cc 'openssl version; openssl speed -seconds 2 -evp sha256' > evidence/crypto.txt 2>&1
