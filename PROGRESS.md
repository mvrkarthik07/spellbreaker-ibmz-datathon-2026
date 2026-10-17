# Progress

- [x] P0 — Bootstrap — verified 2026-10-18 00:57 SGT (dependency imports pass)
- [x] P1 — Service + UI — verified 2026-10-18 01:06 SGT (`/health` ok; `/bank/` and `/dashboard/` HTTP 200; stub fallback retained)
- [x] P2 — ML realistic model — verified 2026-10-18 01:06 SGT (`--customers 5000 --loto`; PR-AUC 0.873; fairness report present; artifact and curves generated)
- [x] P3 — Real model in the service — verified 2026-10-18 01:06 SGT (8 acceptance checks pass, including S1–S7, 100-row feature parity, and template case note)
- [ ] P4 — LinuxONE deployment + training on s390x — scripts ready; verification blocked because `l1cc` does not resolve
- [ ] P5 — Benchmark + evidence — verified 2026-10-18 01:07 SGT — local 100-request run recorded 22.16 RPS and p50/p95 server latency 347.7/356.3 ms; required 10,000-request s390x benchmark/evidence blocked with `l1cc`
- [x] P6 — GenAI case notes — verified 2026-10-18 01:07 SGT using documented deterministic `template` fallback; `/health` reports `template`, HIGH/CRITICAL case note tested
- [x] P7 — Docs, video support, polish — verified 2026-10-18 01:12 SGT (fresh clone installed dependencies, trained, and passed all 8 acceptance tests)
- [ ] P8 — Post-freeze and hand-off — hand-off section drafted; post-freeze final push/recheck remains scheduled after 07:45 SGT

## Hand-off

- Local demo: `./scripts/run_local.sh`; open `http://localhost:8000/bank/` and `http://localhost:8000/dashboard/`.
- LinuxONE tunnel once deployed: `ssh -N -L 8000:localhost:8000 l1cc`; then use the same local URLs. No remote URL is verified.
- Demo click path: bank app → demo controls → “Scam: fake ICA officer” → Review transfer → inspect CRITICAL reasons → dashboard live feed; reset → “Rent while on call” → allowed result.
- Current blockers: `l1cc` SSH alias unresolved; AMLworld CSV absent; team name placeholder remains. See `BLOCKERS.md` for exact recovery actions.
- Set the project title team name in submission fields; `[Team Name]` remains a literal placeholder.
