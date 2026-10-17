#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p evidence results
arch=$(ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'uname -m')
if [ "$arch" != s390x ]; then
  echo "Expected l1cc architecture s390x; got: $arch" >&2
  exit 1
fi

# One SSH stream keeps evidence collection reliable on the Cloud VM and returns
# the exact deployment, cryptography, model and benchmark artifacts together.
ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'sh -s' <<'REMOTE' | tar -xz -C .
set -eu
cd "$HOME/spellbreaker"
mkdir -p evidence
uname -a > evidence/platform.txt
cat /etc/os-release >> evidence/platform.txt
lscpu >> evidence/platform.txt
printf 'nproc=' >> evidence/platform.txt; nproc >> evidence/platform.txt
printf 'free -g:\n' >> evidence/platform.txt; free -g >> evidence/platform.txt
{
  printf 'CPU flags:\n'
  grep -m1 -E '^features|^facilities' /proc/cpuinfo
  printf 'grep -c nnpa /proc/cpuinfo: '
  grep -c nnpa /proc/cpuinfo || true
} > evidence/cpu_features.txt
{
  docker --version
  docker images
  docker ps
  docker inspect spellbreaker --format 'User={{.Config.User}} ReadonlyRootfs={{.HostConfig.ReadonlyRootfs}} CapDrop={{json .HostConfig.CapDrop}} Tmpfs={{json .HostConfig.Tmpfs}}'
} > evidence/container.txt 2>&1
sed -i 's/[[:space:]]*$//' evidence/container.txt
{
  openssl version
  openssl speed -seconds 2 -evp sha256 || true
  printf 'CPACF / message-security-assist (msa) CPU facility: '
  if grep -m1 -Eq '(^| )msa( |$)' /proc/cpuinfo; then echo visible; else echo not-visible; fi
  .venv/bin/python scripts/hmac_evidence.py
} > evidence/crypto.txt 2>&1
cat > evidence/genai_prompt_sample.txt <<'EOF'
Illustrative sample of the local GenAI adapter boundary (synthetic values only).

Allow-listed request received by the adapter:
{"level":"CRITICAL","risk_percent":"99.8%","predicted_scam_type":"gov_impersonation","exact_reasons":["active call","new recipient"],"amount_band":"S$10k–50k","age_band":"65+"}

The local Granite adapter receives exactly these six fields and constructs a fixed four-line prompt. It has one formatting example, temperature 0, and max_tokens=120. Its deterministic validator rejects unlisted scam types, numbers, names/account identifiers, unsupported edits, or missing/misordered lines.

Excluded: customer name, customer/account identifiers, recipient name/account, raw transaction details, audio, and contact data. This example is synthetic and contains no personal data.
EOF
curl -fsS localhost:8000/health > evidence/health.json
cp results/bench.json evidence/bench.txt
cat > evidence/README.md <<'EOF'
# LinuxONE evidence

- `platform.txt`: LinuxONE OS, architecture, CPU count and memory.
- `cpu_features.txt`: CPU flags and literal `grep -c nnpa /proc/cpuinfo` result.
- `container.txt`: Docker service, configured user, read-only root, tmpfs and dropped capabilities.
- `python_env.txt`: apt-backed project training environment and Ubuntu service container package versions.
- `train_l1cc.log`: SpellBreaker training output and MuleNet score source.
- `mulenet_l1cc.log`: official Jupyter image MuleNet command and XGBoost/HistGradientBoosting report.
- `genai_runtime.txt`: GenAI runtime status and Granite attempt outcome.
- `genai_eval.log`: live HIGH/CRITICAL case-note evaluation log.
- `genai_eval.json`: acceptance rate and generation-time summary.
- `health.json`: live service architecture, trained-on architecture and runtime badge.
- `bench.txt`: 10,000-request localhost LinuxONE benchmark.
- `crypto.txt`: OpenSSL SHA-256 speed, MSA visibility and synthetic Python HMAC token sample.
- `genai_prompt_sample.txt`: synthetic, personal-data-free model prompt example.
- `SpellBreaker_on_LinuxONE.executed.ipynb`: executed service demo and notebook-only PyTorch MLP comparison against HistGradientBoosting.
EOF
tar -czf - evidence/platform.txt evidence/cpu_features.txt evidence/container.txt evidence/python_env.txt evidence/train_l1cc.log evidence/mulenet_l1cc.log evidence/genai_runtime.txt evidence/genai_eval.log evidence/health.json evidence/bench.txt evidence/crypto.txt evidence/genai_prompt_sample.txt evidence/SpellBreaker_on_LinuxONE.executed.ipynb evidence/README.md results/bench.json results/model_report.json results/curves.json results/mulenet_report.json results/mule_scores.csv results/genai_eval.json
REMOTE
