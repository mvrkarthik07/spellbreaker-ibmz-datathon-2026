# Blockers

## Needs human

- Configure SSH alias `l1cc` and run `./scripts/deploy_l1cc.sh`; current laptop cannot resolve `l1cc`.
- Supply the team name to replace `[Team Name]` in the project title.
- Optional: place IBM AMLworld `HI-Small_Trans.csv` at `data/HI-Small_Trans.csv` or configure Kaggle credentials to enable MuleNet receiver scores.

## Resolved / fallbacks

- No starter files were present. Implementing the requested app and ML prototype from the spec.
- Container runtime: Docker is installed locally; Podman is absent.
- No LinuxONE evidence, s390x training, remote container, or remote benchmark was captured. The laptop SSH client cannot resolve `l1cc`; exact recovery action: configure the SSH host alias, then run `./scripts/deploy_l1cc.sh` and `./scripts/collect_evidence.sh`.
- No LLM runtime was evaluated on LinuxONE because the VM is unreachable; app uses the deterministic `template` fallback.
