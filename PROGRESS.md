# Progress

- [x] P0 — Bootstrap — verified 2026-10-18 00:57 SGT (dependency imports pass)
- [x] P1 — Service + UI — verified 2026-10-18 01:06 SGT (`/health` ok; `/bank/` and `/dashboard/` HTTP 200; stub fallback retained)
- [x] P2 — ML realistic model — verified 2026-10-18 01:06 SGT (`--customers 5000 --loto`; PR-AUC 0.873; fairness report present; artifact and curves generated)
- [x] P3 — Real model in the service — verified 2026-10-18 01:06 SGT (8 acceptance checks pass, including S1–S7, 100-row feature parity, and template case note)
- [x] P4 — LinuxONE deployment + training on s390x — verified 2026-10-18 02:01 SGT: apt-backed project venv trained 20,000 customers in 13s (`trained_on=s390x`, PR-AUC 0.889); Ubuntu 24.04 Docker image deployed on port 8000; `/health` reports `arch=s390x`, `trained_on=s390x`, and a live CRITICAL score returned in 6.72 ms. Environment versions are recorded remotely in `evidence/python_env.txt`.
- [x] LinuxONE Jupyter notebook — verified 2026-10-18 02:03 SGT: `notebooks/SpellBreaker_on_LinuxONE.ipynb` executed through `nbconvert --execute` inside the official s390x JupyterLab image via `~/shared`; executed copy saved under `evidence/`.
- [x] P5 — Benchmark + evidence — verified 2026-10-18 02:04 SGT — l1cc benchmark: 10,000 requests, concurrency 16; server p50/p95/p99 22.98/24.05/25.74 ms, client p50/p95/p99 74.48/77.27/103.11 ms, 212.06 RPS; final P6 deployment benchmark recorded 2026-10-18 02:29 SGT. The server p99 is below 50 ms. §9 evidence was collected into `evidence/` and the l1cc model report/curves/benchmark are in `results/`.
  - [x] Critical local latency fix — verified 2026-10-18 01:33 SGT — debug-stage timing enabled and observed; optimized benchmark p50 7.53 ms, p99 27.37 ms; `pytest -q tests/` passes (8 tests).
- [x] P6 — GenAI case notes — verified 2026-10-18 02:29 SGT: attempted local Granite 3.0 1B Q4 inference in the official prebuilt s390x JupyterLab runtime; factuality validation rejected unrelated scam labels and unsupported email claims, so the service uses the 4-sentence fact-based template. `/health` and the UI badge report `template`; `/score` remains non-blocking and the executed notebook confirms a ready CRITICAL case note with `runtime=template`. Details in `evidence/genai_runtime.txt` and `docs/RESULTS.md`.
- [x] P7 — Docs, video support, polish — verified 2026-10-18 02:29 SGT (`node --check web/dashboard/dash.js` passes; dashboard waits up to 30 seconds for asynchronous case notes; remote acceptance suite passes 8/8).
- [ ] P8 — Post-freeze and hand-off — hand-off section drafted; post-freeze final push/recheck remains scheduled after 07:45 SGT

## Hand-off

- Local demo: `./scripts/run_local.sh`; open `http://localhost:8000/bank/` and `http://localhost:8000/dashboard/`.
- LinuxONE demo URL after service deployment: `http://148.100.98.199:8000` (public port test returned HTTP 200 at 2026-10-18 01:52 SGT). Tunnel fallback: `ssh -N -L 8000:localhost:8000 l1cc`.
- Demo click path: bank app → demo controls → “Scam: fake ICA officer” → Review transfer → inspect CRITICAL reasons → dashboard live feed; reset → “Rent while on call” → allowed result.
- Current blockers: AMLworld CSV absent; team name placeholder remains. See `BLOCKERS.md` for exact recovery actions.
- Set the project title team name in submission fields; `[Team Name]` remains a literal placeholder.
