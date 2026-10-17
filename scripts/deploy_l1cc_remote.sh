#!/bin/sh
set -eu
cd "$HOME/spellbreaker"
mkdir -p evidence results models
sudo apt-get install -y python3-numpy python3-pandas python3-sklearn python3-scipy python3-joblib python3-fastapi python3-uvicorn python3-httpx python3-pytest python3-venv

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
  if docker run -d --name spellbreaker -p 8000:8000 spellbreaker:latest; then
    record_container_env
    exit 0
  fi
fi

echo 'Ubuntu 24.04 package image build/run failed; trying the official prebuilt s390x Jupyter image.' | tee -a evidence/deploy_l1cc.log
if docker build -t spellbreaker:latest -f service/Containerfile.jupyter .; then
  docker rm -f spellbreaker >/dev/null 2>&1 || true
  if docker run -d --name spellbreaker -p 8000:8000 spellbreaker:latest; then
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
