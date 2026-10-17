#!/bin/sh
set -eu
mkdir -p evidence
if ! ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'test -d ~/spellbreaker'; then
  echo 'Needs human: SSH alias l1cc unavailable; evidence was not captured.' > evidence/README.md
  exit 1
fi
arch=$(ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'uname -m')
if [ "$arch" != s390x ]; then
  echo "Expected l1cc architecture s390x; got: $arch" >&2
  exit 1
fi
ssh l1cc 'uname -a; cat /etc/os-release; lscpu; nproc; free -g' > evidence/platform.txt
ssh l1cc 'grep -m1 features /proc/cpuinfo; grep -c nnpa /proc/cpuinfo || true' > evidence/cpu_features.txt
ssh l1cc 'cd ~/spellbreaker && if command -v podman >/dev/null 2>&1; then podman --version; podman images; podman ps; podman inspect spellbreaker --format "{{.Config.User}}" || true; elif command -v docker >/dev/null 2>&1; then docker --version; docker images; docker ps; docker inspect spellbreaker --format "{{.Config.User}}" || true; else echo "Container runtime unavailable; service uses the documented venv + uvicorn fallback."; fi' > evidence/container.txt 2>&1
ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'cd ~/spellbreaker && cat evidence/python_env.txt' > evidence/python_env.txt
if ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'test -f ~/spellbreaker/evidence/genai_runtime.txt'; then
  ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'cd ~/spellbreaker && cat evidence/genai_runtime.txt' > evidence/genai_runtime.txt
fi
ssh l1cc 'cd ~/spellbreaker && cat evidence/train_l1cc.log' > evidence/train_l1cc.log
ssh l1cc 'curl -fsS localhost:8000/health' > evidence/health.json
ssh l1cc 'cd ~/spellbreaker && cat results/bench.json' > results/bench.json
cp results/bench.json evidence/bench.txt
ssh l1cc 'cd ~/spellbreaker && cat results/model_report.json' > results/model_report.json
ssh l1cc 'cd ~/spellbreaker && cat results/curves.json' > results/curves.json
if ssh l1cc 'test -f ~/spellbreaker/results/mule_scores.csv'; then
  ssh l1cc 'cd ~/spellbreaker && cat results/mule_scores.csv' > results/mule_scores.csv
fi
if ssh l1cc 'test -f ~/spellbreaker/results/mulenet_report.json'; then
  ssh l1cc 'cd ~/spellbreaker && cat results/mulenet_report.json' > results/mulenet_report.json
fi
if ssh l1cc 'test -f ~/spellbreaker/evidence/mulenet_l1cc.log'; then
  ssh l1cc 'cd ~/spellbreaker && cat evidence/mulenet_l1cc.log' > evidence/mulenet_l1cc.log
fi
ssh l1cc 'openssl version; openssl speed -seconds 2 -evp sha256 || true' > evidence/crypto.txt 2>&1
cat > evidence/README.md <<'EOF'
# LinuxONE evidence

- `platform.txt`: LinuxONE VM operating system, architecture, CPU count and memory.
- `cpu_features.txt`: exposed CPU feature flags and NNPA visibility.
- `container.txt`: container runtime, image, running service and configured user, or the documented venv fallback.
- `python_env.txt`: Python version and installed packages used by the service.
- `train_l1cc.log`: model training output, including the training architecture.
- `mulenet_l1cc.log`: l1cc MuleNet command, memory selection and output.
- `results/mulenet_report.json` and `results/mule_scores.csv`: MuleNet holdout report and receiver-account scores.
- `genai_runtime.txt`: GenAI runtime status and local-model attempt outcome.
- `health.json`: live service architecture, trained-on architecture and runtime badge.
- `bench.txt`: 10,000-request localhost benchmark summary from LinuxONE.
- `crypto.txt`: OpenSSL version and SHA-256 speed output.
EOF
