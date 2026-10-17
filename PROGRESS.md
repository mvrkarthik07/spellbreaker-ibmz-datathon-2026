# Progress

- [x] P0 — Bootstrap — verified 2026-10-18 00:57 SGT (dependency imports pass)
- [x] P1 — Service + UI — verified 2026-10-18 01:06 SGT (`/health` ok; `/bank/` and `/dashboard/` HTTP 200; stub fallback retained)
- [x] P2 — ML realistic model — verified 2026-10-18 01:06 SGT (`--customers 5000 --loto`; PR-AUC 0.873; fairness report present; artifact and curves generated). Real receiver-score augmentation later verified on l1cc 2026-10-18 02:39 SGT (MuleNet scores used by the retrained 20,000-customer model).
- [x] P3 — Real model in the service — verified 2026-10-18 01:06 SGT (8 acceptance checks pass, including S1–S7, 100-row feature parity, and template case note)
- [x] P4 — LinuxONE deployment + training on s390x — initial verification 2026-10-18 02:01 SGT; updated verification 02:52 SGT: apt-backed project venv retrained 20,000 customers in 17s using XGBoost MuleNet scores (`trained_on=s390x`, PR-AUC 0.8805, ROC-AUC 0.9708); hardened Ubuntu 24.04 Docker image deployed on port 8000; `/health` reports `arch=s390x`, `trained_on=s390x`. Environment versions are in `evidence/python_env.txt`.
- [x] LinuxONE Jupyter notebook — verified 2026-10-18 02:03 SGT: `notebooks/SpellBreaker_on_LinuxONE.ipynb` executed through `nbconvert --execute` inside the official s390x JupyterLab image via `~/shared`; executed copy saved under `evidence/`.
- [x] P5 — Benchmark + evidence — refreshed 2026-10-18 02:52 SGT — l1cc benchmark: 10,000 requests, concurrency 16; server p50/p95/p99 23.28/24.35/25.23 ms, client p50/p95/p99 75.43/77.52/104.54 ms, 209.91 RPS after XGBoost MuleNet retraining and hardened redeployment. The server p99 is below 50 ms. Security, CPU, crypto, prompt privacy, MuleNet comparison/scores, and notebook evidence are collected in `evidence/` and `results/`.
  - [x] Critical local latency fix — verified 2026-10-18 01:33 SGT — debug-stage timing enabled and observed; optimized benchmark p50 7.53 ms, p99 27.37 ms; `pytest -q tests/` passes (8 tests).
- [x] P6 — GenAI case notes — verified 2026-10-18 02:29 SGT: attempted local Granite 3.0 1B Q4 inference in the official prebuilt s390x JupyterLab runtime; factuality validation rejected unrelated scam labels and unsupported email claims, so the service uses the 4-sentence fact-based template. `/health` and the UI badge report `template`; `/score` remains non-blocking and the executed notebook confirms a ready CRITICAL case note with `runtime=template`. Details in `evidence/genai_runtime.txt` and `docs/RESULTS.md`.
- [x] P7 — Docs, video support, polish — verified 2026-10-18 02:52 SGT (updated named AI stack, platform-security evidence, six Team placeholders and 10-second video segment, rubric mapping, AMLworld/XGBoost/PyTorch credits; notebook challenger executed on s390x. Hardened remote acceptance suite passes 8/8).
- [ ] P8 — Post-freeze and hand-off — hand-off section drafted; post-freeze final push/recheck remains scheduled after 07:45 SGT

## Hand-off

- Local demo: `./scripts/run_local.sh`; open `http://localhost:8000/bank/` and `http://localhost:8000/dashboard/`.
- LinuxONE demo URL after service deployment: `http://148.100.98.199:8000` (public port test returned HTTP 200 at 2026-10-18 01:52 SGT). Tunnel fallback: `ssh -N -L 8000:localhost:8000 l1cc`.
- Demo click path: bank app → demo controls → “Scam: fake ICA officer” → Review transfer → inspect CRITICAL reasons → dashboard live feed; reset → “Rent while on call” → allowed result.
- Current blocker: team name placeholder remains. AMLworld HI-Small is present on laptop and l1cc; MuleNet scores were generated and used for retraining. See `BLOCKERS.md` for exact recovery actions.
- Set the project title team name in submission fields; `[Team Name]` remains a literal placeholder.
