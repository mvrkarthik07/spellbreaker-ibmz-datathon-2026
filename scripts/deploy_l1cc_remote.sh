#!/bin/sh
set -eu
cd "$HOME/spellbreaker"
mkdir -p evidence results models
sudo apt-get install -y python3-numpy python3-pandas python3-sklearn python3-scipy python3-joblib python3-fastapi python3-uvicorn python3-httpx python3-pytest python3-venv

LLM_ENV=""
LLM_MODEL="$HOME/shared/models/granite-3.0-1b-a400m-instruct-be.Q4_K_M.gguf"
LLM_IMAGE=registry.linuxone.cloud.marist.edu/l1cc/jupyterlab-image-s390x:latest
if [ "${SPELLBREAKER_ENABLE_LLM:-0}" = "1" ] && [ -s "$LLM_MODEL" ] && docker image inspect "$LLM_IMAGE" >/dev/null 2>&1; then
  docker rm -f spellbreaker-llm >/dev/null 2>&1 || true
  docker run -d --restart unless-stopped --name spellbreaker-llm --network host \
    -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 \
    -e LLM_BIND_HOST=127.0.0.1 -e MODEL_PATH=/models/$(basename "$LLM_MODEL") -e LLAMA_THREADS=3 \
    -v "$HOME/shared/models:/models:ro" \
    -v "$HOME/spellbreaker/service/genai_llm_server.py:/app/genai_llm_server.py:ro" \
    --entrypoint python3 "$LLM_IMAGE" /app/genai_llm_server.py >/dev/null
  for i in $(seq 1 120); do
    if curl -fsS http://127.0.0.1:8081/health > evidence/genai_runtime.txt; then
      printf 'model_file=%s\n' "$(basename "$LLM_MODEL")" >> evidence/genai_runtime.txt
      LLM_ENV='-e SPELLBREAKER_LLM_URL=http://127.0.0.1:8081'
      break
    fi
    sleep 1
  done
  if [ -z "$LLM_ENV" ]; then
    echo 'Local Granite model failed its health check; retaining the template fallback.' | tee -a evidence/deploy_l1cc.log
    docker logs --tail 60 spellbreaker-llm >> evidence/genai_runtime.txt 2>&1 || true
  fi
else
  docker rm -f spellbreaker-llm >/dev/null 2>&1 || true
  cat > evidence/genai_runtime.txt <<'EOF'
runtime=template
attempted_runtime=llama-cpp-python in official LinuxONE JupyterLab s390x image
model=Granite 3.0 1B A400M Instruct Q4_K_M big-endian GGUF
result=attempted; generation repeatedly returned unrelated scam labels or unsupported email claims, rejected by exact type validation; service uses the deterministic fact-based template
EOF
  echo 'Granite output failed factuality validation; using the deterministic template runtime.' | tee -a evidence/deploy_l1cc.log
fi

record_container_env() {
  .venv/bin/python - <<'PY' > evidence/python_env_host.txt
import platform, sys
from importlib.metadata import version
print(f"python={sys.version.split()[0]}\nmachine={platform.machine()}")
for package in ("numpy", "pandas", "scikit-learn", "scipy", "joblib", "fastapi", "uvicorn", "httpx", "pytest"):
    print(f"{package}={version(package)}")
PY
  docker exec spellbreaker python3 -c 'import platform,sys; from importlib.metadata import version; print(f"python={sys.version.split()[0]}\nmachine={platform.machine()}"); [print(f"{p}={version(p)}") for p in ("numpy","pandas","scikit-learn","scipy","joblib","fastapi","uvicorn","httpx","pytest")]' > evidence/python_env_container.txt
  { printf '[training_venv / host]\n'; cat evidence/python_env_host.txt; printf '\n[service_container / ubuntu:24.04]\n'; cat evidence/python_env_container.txt; } > evidence/python_env.tmp
  mv evidence/python_env.tmp evidence/python_env.txt
}

if command -v docker >/dev/null 2>&1 && docker build -t spellbreaker:latest -f service/Containerfile .; then
  docker rm -f spellbreaker >/dev/null 2>&1 || true
  if docker run -d --restart unless-stopped --name spellbreaker --network host \
      --user 10001:10001 --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m --cap-drop ALL \
      $LLM_ENV spellbreaker:latest; then
    record_container_env
    exit 0
  fi
fi

echo 'Ubuntu 24.04 package image build/run failed; trying the official prebuilt s390x Jupyter image.' | tee -a evidence/deploy_l1cc.log
if docker build -t spellbreaker:latest -f service/Containerfile.jupyter .; then
  docker rm -f spellbreaker >/dev/null 2>&1 || true
  if docker run -d --restart unless-stopped --name spellbreaker --network host \
      --user 10001:10001 --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m --cap-drop ALL \
      $LLM_ENV spellbreaker:latest; then
    record_container_env
    exit 0
  fi
fi

# Last fallback is the already provisioned apt-backed virtual environment; no
# package is compiled or installed from source in this path.
if [ -x .venv/bin/python ]; then
  nohup .venv/bin/python -m uvicorn service.app:app --host 0.0.0.0 --port 8000 > evidence/uvicorn.log 2>&1 &
  echo 'Docker and official image failed; serving from the apt-backed venv.' | tee -a evidence/deploy_l1cc.log
  exit 0
fi
echo 'Ubuntu package image, official Jupyter fallback, and apt-backed venv are unavailable.' >&2
exit 1
