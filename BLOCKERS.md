# Blockers

## Needs human

- Confirm the final team role descriptions with **Karthik Manda**, **Pranay Kanth Molugu**, **Sai Prakash Reddy**, and **Amrutha Vanaparthi** before submission; the proposed roles are in README.
- Record and upload the final ≤3-minute demo, then replace the video URL placeholder in `docs/SUBMISSION.md`.

## Resolved / fallbacks

- No starter files were present. Implementing the requested app and ML prototype from the spec.
- Container runtime: Docker is installed locally; Podman is absent.
- LinuxONE access and setup are resolved: `l1cc` is `s390x`, Docker passed `hello-world`, and the project has a 4 GiB persistent swap. A pip source-metadata attempt failed on SciPy's missing Fortran compiler; this was replaced by Ubuntu's prebuilt s390x apt stack and a `--system-site-packages` venv. Training and Ubuntu-image service deployment now pass. Public port 8000 returned HTTP 200. The AMLworld HI-Small dataset is now present locally and on l1cc; MuleNet scores were generated and consumed by the l1cc retraining.
- Granite evaluation is complete: 0/50 accepted notes and the serial model probe timed out at 90 seconds. Template is the default; Granite remains optional. See `results/genai_eval.json`.
- MuleNet full-file reporting and the SpellBreaker retrain are complete on l1cc; latest report covers 5,078,345 rows, and post-retrain `/health` reports `trained_on=s390x`.
