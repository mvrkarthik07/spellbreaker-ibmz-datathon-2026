#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

arch=$(ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'uname -m')
if [ "$arch" != s390x ]; then
  echo "P4 requires l1cc to report s390x; got: $arch" >&2
  exit 1
fi

rsync -az --exclude=data/ --exclude=.git/ --exclude=.venv/ --exclude=__pycache__/ --exclude=.pytest_cache/ \
  --exclude=models/ --exclude=results/ --exclude=evidence/ ./ l1cc:~/spellbreaker/
ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'cd ~/spellbreaker && ./scripts/train_l1cc_remote.sh'
