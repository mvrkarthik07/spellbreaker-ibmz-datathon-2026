#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

arch=$(ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'uname -m')
if [ "$arch" != s390x ]; then
  echo "P5 requires l1cc to report s390x; got: $arch" >&2
  exit 1
fi

rsync -az --exclude=.git/ --exclude=.venv/ --exclude=__pycache__/ --exclude=.pytest_cache/ \
  --exclude=data/ --exclude=models/ --exclude=results/ --exclude=evidence/ ./ l1cc:~/spellbreaker/
ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'cd ~/spellbreaker && ./scripts/deploy_l1cc_remote.sh'

health=$(ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do curl -fsS localhost:8000/health && exit 0; sleep 1; done; exit 1')
printf '%s\n' "$health"
case "$health" in
  *'"arch":"s390x"'*'"trained_on":"s390x"'*) ;;
  *) echo "P5 requires arch and trained_on to be s390x; got: $health" >&2; exit 1 ;;
esac

ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'cd ~/spellbreaker && python3 bench/loadtest.py --url http://127.0.0.1:8000 --requests 10000 --concurrency 16'
./scripts/collect_evidence.sh
