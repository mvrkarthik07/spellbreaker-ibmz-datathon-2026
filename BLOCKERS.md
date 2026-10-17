# Blockers

## Needs human

- Fix the `l1cc` SSH alias target. Latest check at 2026-10-18 01:33 SGT: `ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'uname -m'` resolves to the literal `<vm_public_ip>` placeholder and fails DNS. Replace that placeholder in `~/.ssh/config` with the VM's public IP, rerun the same check (expected `s390x`), then run `./scripts/train_l1cc.sh`, `./scripts/deploy_l1cc.sh`, and `./scripts/collect_evidence.sh`. Retry the check every 10 minutes until reachable.
- Supply the team name to replace `[Team Name]` in the project title.
- Optional: place IBM AMLworld `HI-Small_Trans.csv` at `data/HI-Small_Trans.csv` or configure Kaggle credentials to enable MuleNet receiver scores.

## Resolved / fallbacks

- No starter files were present. Implementing the requested app and ML prototype from the spec.
- Container runtime: Docker is installed locally; Podman is absent.
- No LinuxONE evidence, s390x training, remote container, or remote benchmark was captured. `l1cc` currently points at the literal `<vm_public_ip>` placeholder; exact recovery action is recorded under Needs human above.
- No LLM runtime was evaluated on LinuxONE because the VM is unreachable; app uses the deterministic `template` fallback.
