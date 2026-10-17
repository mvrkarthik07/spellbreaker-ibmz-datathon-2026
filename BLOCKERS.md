# Blockers

## Needs human

- Supply the team name to replace `[Team Name]` in the project title.
- Optional: place IBM AMLworld `HI-Small_Trans.csv` at `data/HI-Small_Trans.csv` or configure Kaggle credentials to enable MuleNet receiver scores.

## Resolved / fallbacks

- No starter files were present. Implementing the requested app and ML prototype from the spec.
- Container runtime: Docker is installed locally; Podman is absent.
- LinuxONE access and setup are resolved: `l1cc` is `s390x`, Docker passed `hello-world`, and the project has a 4 GiB persistent swap. A pip source-metadata attempt failed on SciPy's missing Fortran compiler; this was replaced by Ubuntu's prebuilt s390x apt stack and a `--system-site-packages` venv. Training and Ubuntu-image service deployment now pass. Public port 8000 returned HTTP 200. No AMLworld `HI-Small_Trans.csv` is present locally; the remote P4 helper checks for it before considering MuleNet.
- The app currently uses the deterministic `template` fallback. LinuxONE §5.7 runtime investigation is active in the 90-minute timebox started at 2026-10-18 02:05 SGT; record a runtime/package/model blocker here if no local model path works.
