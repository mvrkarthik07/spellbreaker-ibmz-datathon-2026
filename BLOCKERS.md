# Blockers

## Needs human

- Supply the team name to replace `[Team Name]` in the project title.
- Optional: place IBM AMLworld `HI-Small_Trans.csv` at `data/HI-Small_Trans.csv` or configure Kaggle credentials to enable MuleNet receiver scores.

## Resolved / fallbacks

- No starter files were present. Implementing the requested app and ML prototype from the spec.
- Container runtime: Docker is installed locally; Podman is absent.
- LinuxONE phases are now active: `l1cc` returned `s390x` at 2026-10-18 01:43 SGT. The first P4 install hit Debian PEP 668; training now creates a project `.venv` and is being retried.
- No LLM runtime was evaluated on LinuxONE because the VM is unreachable; app uses the deterministic `template` fallback.
