# Evidence guide

These files distinguish local development from claims that require LinuxONE access.

- `preflight_local.txt`: laptop Python, pip, git, Docker, and SSH preflight result.
- `platform.txt`, `cpu_features.txt`, `container.txt`, `python_env.txt`, `train_l1cc.log`, `health.json`, `bench.txt`, and `crypto.txt`: produced only by `scripts/collect_evidence.sh` after a successful `l1cc` deployment. They are not present because the configured host alias could not be resolved.
- `results/model_report.json` and `results/curves.json`: local model outputs from synthetic simulator data; not LinuxONE evidence.
- `results/bench.json`: local API benchmark only; do not present it as s390x performance.

`evidence/cpu_features.txt` is the required proof before any NNPA claim. No NNPA or CPACF acceleration claim is made here.
