#!/bin/sh
set -eu
cd "$HOME/spellbreaker"
mkdir -p evidence results models
python3 -m pip install -r ml/requirements.txt -r service/requirements.txt
if [ -f data/HI-Small_Trans.csv ]; then
  rows="${MULENET_NROWS:-}"
  mem_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
  if [ -z "$rows" ] && [ "${mem_kb:-0}" -lt 6291456 ]; then rows=2000000; echo "RAM below 6 GB; MuleNet capped at 2000000 rows." | tee -a evidence/train_l1cc.log; fi
  if [ -n "$rows" ]; then python3 ml/mulenet_baseline.py --nrows "$rows" --export-scores results/mule_scores.csv; else python3 ml/mulenet_baseline.py --export-scores results/mule_scores.csv; fi
else
  echo 'Needs human: download AMLworld HI-Small to data/' >> BLOCKERS.md
fi
python3 ml/spellbreaker_train.py --customers "${CUSTOMERS:-20000}" --loto 2>&1 | tee evidence/train_l1cc.log
