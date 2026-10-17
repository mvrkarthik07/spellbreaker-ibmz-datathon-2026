# Progress

- [x] P0 — Bootstrap — verified 2026-10-18 00:57 SGT (dependency imports pass)
- [x] P1 — Service + UI — verified 2026-10-18 01:06 SGT (`/health` ok; `/bank/` and `/dashboard/` HTTP 200; stub fallback retained)
- [x] P2 — ML realistic model — verified 2026-10-18 01:06 SGT (`--customers 5000 --loto`; PR-AUC 0.873; fairness report present; artifact and curves generated)
- [x] P3 — Real model in the service — verified 2026-10-18 01:06 SGT (8 acceptance checks pass, including S1–S7, 100-row feature parity, and template case note)
- [ ] P4 — LinuxONE deployment + training on s390x — phase-guarded `./scripts/train_l1cc.sh` ready; latest `l1cc` check at 2026-10-18 01:33 SGT resolves to the literal `<vm_public_ip>` placeholder and cannot connect
- [ ] P5 — Benchmark + evidence — local portion verified 2026-10-18 01:33 SGT — 10,000 requests, concurrency 16, 10 Uvicorn workers: 1,193.98 RPS; server p50/p95/p99 7.53/17.63/27.37 ms. Local p50/p99 target passes. Phase-guarded `./scripts/deploy_l1cc.sh` preserves s390x outputs and collects §9 evidence; LinuxONE work remains blocked with `l1cc`.
  - [x] Critical local latency fix — verified 2026-10-18 01:33 SGT — debug-stage timing enabled and observed; optimized benchmark p50 7.53 ms, p99 27.37 ms; `pytest -q tests/` passes (8 tests).
- [x] P6 — GenAI case notes — verified 2026-10-18 01:07 SGT using documented deterministic `template` fallback; `/health` reports `template`, HIGH/CRITICAL case note tested
- [x] P7 — Docs, video support, polish — verified 2026-10-18 01:35 SGT (fresh-clone checks remain green; dashboard now retries pending background case notes; `node --check web/dashboard/dash.js` passes)
- [ ] P8 — Post-freeze and hand-off — hand-off section drafted; post-freeze final push/recheck remains scheduled after 07:45 SGT

## Hand-off

- Local demo: `./scripts/run_local.sh`; open `http://localhost:8000/bank/` and `http://localhost:8000/dashboard/`.
- LinuxONE tunnel once deployed: `ssh -N -L 8000:localhost:8000 l1cc`; then use the same local URLs. No remote URL is verified.
- Demo click path: bank app → demo controls → “Scam: fake ICA officer” → Review transfer → inspect CRITICAL reasons → dashboard live feed; reset → “Rent while on call” → allowed result.
- Current blockers: `l1cc` SSH alias unresolved; AMLworld CSV absent; team name placeholder remains. See `BLOCKERS.md` for exact recovery actions.
- Set the project title team name in submission fields; `[Team Name]` remains a literal placeholder.
