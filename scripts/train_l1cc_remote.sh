#!/bin/sh
set -eu
cd "$HOME/spellbreaker"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p evidence results models

# Ubuntu supplies native s390x wheels/libraries for the complete ML stack.
sudo apt-get install -y python3-numpy python3-pandas python3-sklearn python3-scipy python3-joblib python3-fastapi python3-uvicorn python3-httpx python3-pytest python3-venv
rm -rf .venv
python3 -m venv --system-site-packages .venv
.venv/bin/python - <<'PY' > evidence/python_env.txt
import platform
import sys
from importlib.metadata import version
print(f"python={sys.version.split()[0]}")
print(f"machine={platform.machine()}")
for package in ("numpy", "pandas", "scikit-learn", "scipy", "joblib", "fastapi", "uvicorn", "httpx", "pytest"):
    print(f"{package}={version(package)}")
PY
.venv/bin/python - <<'PY'
import numpy, pandas, sklearn, scipy, joblib, fastapi, uvicorn, httpx, pytest
print("Ubuntu prebuilt s390x ML/service stack imports passed in the project venv.")
PY

if [ -f data/HI-Small_Trans.csv ] && [ ! -s results/mule_scores.csv ]; then
  rows="${MULENET_NROWS:-}"
  mem_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
  if [ -z "$rows" ] && [ "${mem_kb:-0}" -gt 5242880 ]; then rows=2000000; echo "Available memory exceeds about 5 GiB; MuleNet capped at 2000000 rows." | tee -a evidence/train_l1cc.log; fi
  if [ -n "$rows" ]; then .venv/bin/python ml/mulenet_baseline.py --nrows "$rows" --export-scores results/mule_scores.csv; else .venv/bin/python ml/mulenet_baseline.py --export-scores results/mule_scores.csv; fi
elif [ -s results/mule_scores.csv ]; then
  echo 'Using existing results/mule_scores.csv; MuleNet was already run.' | tee -a evidence/train_l1cc.log
else
  echo 'Needs human: download AMLworld HI-Small to data/' >> BLOCKERS.md
fi

customers="${CUSTOMERS:-20000}"
start=$(date +%s)
set +e
timeout 600 .venv/bin/python ml/spellbreaker_train.py --customers "$customers" --loto > evidence/train_l1cc.log 2>&1
status=$?
set -e
elapsed=$(($(date +%s) - start))
if [ "$status" -eq 124 ] && [ "$customers" -gt 10000 ]; then
  echo "Training exceeded 600 seconds at $customers customers; retrying with 10000." | tee -a evidence/train_l1cc.log
  customers=10000
  start=$(date +%s)
  timeout 600 .venv/bin/python ml/spellbreaker_train.py --customers "$customers" --loto >> evidence/train_l1cc.log 2>&1
  elapsed=$(($(date +%s) - start))
fi
echo "Training completed in ${elapsed}s with customers=${customers}." | tee -a evidence/train_l1cc.log
.venv/bin/python - <<'PY'
import json, platform
report=json.load(open('results/model_report.json'))
assert platform.machine()=='s390x', platform.machine()
assert report.get('trained_on')=='s390x', report.get('trained_on')
assert report.get('mule_score_source',{}).get('used') is True, report.get('mule_score_source')
with open('evidence/train_l1cc.log','a') as log:
    log.write('\nMuleNet scores used by SpellBreaker training:\n')
    log.write(json.dumps(report['mule_score_source'],indent=2)+'\n')
PY
cat evidence/train_l1cc.log
