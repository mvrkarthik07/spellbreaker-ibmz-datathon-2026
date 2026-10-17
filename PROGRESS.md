# Progress

- [x] P0 — Bootstrap — verified 2026-10-18 00:57 SGT (dependency imports pass)
- [x] P1 — Service + UI — verified 2026-10-18 01:06 SGT (`/health` ok; `/bank/` and `/dashboard/` HTTP 200; stub fallback retained)
- [x] P2 — ML realistic model — verified 2026-10-18 01:06 SGT (`--customers 5000 --loto`; PR-AUC 0.873; fairness report present; artifact and curves generated)
- [ ] P3 — Real model in the service
- [ ] P4 — LinuxONE deployment + training on s390x
- [ ] P5 — Benchmark + evidence
- [ ] P6 — GenAI case notes
- [ ] P7 — Docs, video support, polish
- [ ] P8 — Post-freeze and hand-off

## Hand-off

- LinuxONE SSH alias `l1cc` was unavailable during this run. Needs human: configure SSH, run `./scripts/deploy_l1cc.sh`, then verify `/health` reports `s390x`.
- Set the project title team name in the submission fields; `[Team Name]` remains a placeholder.
