# Progress

- [x] P0 — Bootstrap — verified 2026-10-18 00:57 SGT (dependency imports pass)
- [x] P1 — Service + UI — verified 2026-10-18 01:06 SGT (`/health` ok; `/bank/` and `/dashboard/` HTTP 200; stub fallback retained)
- [x] P2 — ML realistic model — verified 2026-10-18 01:06 SGT (`--customers 5000 --loto`; PR-AUC 0.873; fairness report present; artifact and curves generated). Real receiver-score augmentation later verified on l1cc 2026-10-18 02:39 SGT (MuleNet scores used by the retrained 20,000-customer model).
- [x] P3 — Real model in the service — verified 2026-10-18 01:06 SGT (8 acceptance checks pass, including S1–S7, 100-row feature parity, and template case note)
- [x] P4 — LinuxONE deployment + training on s390x — refreshed 2026-10-18 03:20 SGT: apt-backed venv retrained 20,000 customers in 17s with 237,983 full-file XGBoost MuleNet scores (`trained_on=s390x`, PR-AUC 0.8802, ROC-AUC 0.9708); hardened Ubuntu 24.04 Docker image deployed on port 8000. Environment versions are in `evidence/python_env.txt`.
- [x] LinuxONE Jupyter notebook — verified 2026-10-18 02:03 SGT: `notebooks/SpellBreaker_on_LinuxONE.ipynb` executed through `nbconvert --execute` inside the official s390x JupyterLab image via `~/shared`; executed copy saved under `evidence/`.
- [x] P5 — Benchmark + evidence — refreshed after the 2026-10-18 03:49 SGT UI deployment — latest l1cc run: 10,000 requests, concurrency 16; server p50/p95/p99 23.62/24.97/26.85 ms, client p50/p95/p99 76.59/80.14/106.86 ms, 206.56 RPS. The server p99 is below 50 ms. Security, CPU, crypto, prompt privacy, MuleNet comparison/scores, and notebook evidence are collected in `evidence/` and `results/`.
  - [x] Critical local latency fix — verified 2026-10-18 01:33 SGT — debug-stage timing enabled and observed; optimized benchmark p50 7.53 ms, p99 27.37 ms; `pytest -q tests/` passes (8 tests).
- [x] P6 — GenAI case notes — refreshed 2026-10-18 03:15 SGT: fixed fact-sheet-only Granite prompt, strict four-line deterministic validator, asynchronous fallback logging, and 50-case l1cc evaluation. Acceptance was 0/50 under the 90-second primary-inference timeout/burst gate, so template is default and Granite remains optional. Post-change l1cc p99 stayed 25.19 ms; remote acceptance passed 9/9.
- [x] P7 — Docs and polish — refreshed 2026-10-18 03:15 SGT: tokenmaxxers roster, rubric mapping, security, Granite evaluation and privacy evidence documented. Five demo presets returned expected levels over HTTP. `docs/VIDEO_SCRIPT.md` removed at the user's request on 2026-10-18.
- [x] MuleNet account-level reporting — full HI-Small run completed on l1cc inside the official s390x JupyterLab image (5,078,345 rows); account ROC-AUC, precision/recall/lift at top 1% and 5%, and HMAC red-flag-gated silo collaboration are in `results/mulenet_report.json` and `docs/RESULTS.md`.
- [x] Public GitHub — public submission repository is `https://github.com/mvrkarthik07/spellbreaker-ibmz-datathon-2026`; key/data scans and ignore checks passed, and `main` is pushed.
- [x] UI smoke review + flowchart — verified live LinuxONE banking UI presets and interaction buttons in the browser; all 9 remote acceptance checks pass. Added `evidence/ui_smoke_test.txt`, replaced the SVG with a root Markdown/Mermaid flowchart, and embedded the rendered Mermaid source in README for visibility. `git diff --check` passes. Verified 2026-10-18 03:45 SGT.
- [x] Banking interface polish — rebuilt the customer UI with Singapore-localized account details, clearer hierarchy, privacy balance toggle, editable scenario controls and no customer-facing “demo” wording; verified the new live model hold and safe-transfer screens on LinuxONE. Hid the internal `hour_sin` feature from the dashboard selected-case list without changing model inputs. Verified 2026-10-18 03:49 SGT.
- [ ] P8 — Post-freeze and hand-off — hand-off section drafted; post-freeze final push/recheck remains scheduled after 07:45 SGT

## Hand-off

- Local demo: `./scripts/run_local.sh`; open `http://localhost:8000/bank/` and `http://localhost:8000/dashboard/`.
- LinuxONE demo URL after service deployment: `http://148.100.98.199:8000` (public port test returned HTTP 200 at 2026-10-18 01:52 SGT). Tunnel fallback: `ssh -N -L 8000:localhost:8000 l1cc`.
- Demo click path: bank app → demo controls → “Scam: fake ICA officer” → Review transfer → inspect CRITICAL reasons → dashboard live feed; reset → “Rent while on call” → allowed result.
- Current human tasks: confirm the proposed role descriptions and record/upload the final ≤3-minute video. AMLworld HI-Small remains on laptop and l1cc; deploy/training scripts exclude it and preserve all protected runtime directories.
