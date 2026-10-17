# Blockers

## Needs human

- Supply the team name to replace `[Team Name]` in the project title.
- Optional: place IBM AMLworld `HI-Small_Trans.csv` at `data/HI-Small_Trans.csv` or configure Kaggle credentials to enable MuleNet receiver scores.

## Resolved / fallbacks

- No starter files were present. Implementing the requested app and ML prototype from the spec.
- Container runtime: Docker is installed locally; Podman is absent.
- LinuxONE phases are active: `l1cc` returned `s390x`; Docker and the requested VM setup passed on 2026-10-18 01:52 SGT. The first P4 install hit PEP 668; its project `.venv` retry is still building dependencies. Public port 8000 returned HTTP 200; the official JupyterLab image is downloading in the background.
- No LLM runtime was evaluated on LinuxONE because the VM is unreachable; app uses the deterministic `template` fallback.
