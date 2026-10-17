# AGENTS.md — SpellBreaker (IBM Z Datathon 2026) — Autonomous Build Spec

> You are the sole engineer on this repo for the rest of the hackathon. The humans are recording the demo video and are **not available**. Read this whole file before acting. It is the single source of truth.

---

## 0. Operating rules (read first, obey always)

1. **Never ask the user a question. Never wait for confirmation.** When something is ambiguous, pick the most reasonable option, write it in `DECISIONS.md` (one line: time, decision, why), and continue.
2. **Resume protocol.** On every start, including when the user just types `continue`:
   1. Read `PROGRESS.md`, `DECISIONS.md` and `BLOCKERS.md` if they exist.
   2. Run `git log --oneline -20`.
   3. Continue from the first unchecked task. Never redo finished work unless its verification now fails.
3. **Progress tracking.** Keep `PROGRESS.md` as a checklist mirroring §6. Tick a task **only after its Verify command passes**. Add a timestamp (SGT) to each tick.
4. **Commit after every task** (`git add -A && git commit -m "<phase>: <task>"`). If a remote named `origin` exists and `gh auth status` succeeds, `git push` after each phase. Otherwise skip pushing silently.
5. **Blockers never stop you.** If something external fails (SSH, Kaggle, package install on s390x, LLM runtime):
   - try the fallbacks listed in §10;
   - record what failed and what you did instead in `BLOCKERS.md`, under "Needs human" if a human must act;
   - keep going on everything else.
6. **Timeboxes are hard.** Each task has one. When it expires, ship the fallback, log it, move on.
7. **Truth policy.** README, docs and UI may only claim what an evidence file proves (§9).
   - Never claim IBM Secure Execution / Hyper Protect is used. The LinuxONE Community Cloud VM does not provide it; describe it only as the production deployment target.
   - Never claim the Telum AI accelerator (NNPA) is used unless `evidence/cpu_features.txt` contains `nnpa` **and** the model actually ran via zDLC.
   - Never present synthetic data as real.
8. **Safety and brand rules.**
   - The bank in the app is the fictional **"Merlion Bank"**. Never use any real bank's name, logo, colours or page layout.
   - No real personal data anywhere. All customers are synthetic.
   - No secrets in the repo. `.gitignore` must cover `data/`, `*.csv`, `*.joblib`, `.env`, `models/`, `*.gguf`.
9. **Originality.** All code is written during the event. Every third-party library and dataset used must be listed in `docs/OPEN_SOURCE.md` with a link (a submission requirement).
10. **Keep it simple.**
    - No front-end build step: plain HTML + vanilla JS + CSS. CDN Chart.js is allowed.
    - Python 3.9+, FastAPI, scikit-learn, numpy, pandas, joblib.
    - Avoid packages that commonly fail on s390x: pyarrow, streamlit, lightgbm, xgboost, matplotlib, torch. Use them only if already installed.

---

## 1. Context

### 1.1 Event facts (from the official guidebook)

- **Hard deadline: Sunday 18 Oct 2026, 10:00 SGT** (APAC virtual continuation ends 10:00; closing ceremony 10:30).
- **Code freeze for the video: 07:45 SGT.** After that, only bug fixes and docs.
- **Required submission:**
  - a video of at most 3 minutes covering problem, data, solution, and **how it leverages IBM Z (tech stack, show the LinuxONE instance and model)**;
  - a GitHub repo.
- **Optional submission:** flowchart, prototype.
- Project title format: `[Team Name_IBM Z Datathon 2026 Project]`. Event code **SSF2026** must appear in the project description.
- **Judging, 4 × 10 points:**
  1. Value to community and theme alignment
  2. Novelty and originality
  3. **Technical design and use of LinuxONE Community Cloud + AI/ML open-source packages running ON LinuxONE**: architecture strength, multi-model "Predictive AI hybrid", "Predictive AI + Generative AI", and platform capabilities (containerisation, security, scalability, compute) **evidenced by screenshots**
  4. Execution and pitch
- There is also an "AI Innovation Excellence" award, judged on AI originality plus technical excellence.

### 1.2 Product in one line

SpellBreaker scores every bank transfer in real time on IBM LinuxONE. It detects when a **genuine customer is being manipulated by a scammer** into sending money, and breaks the "spell" with a targeted, scam-type-specific interruption. No customer data leaves the bank's platform.

### 1.3 Why it matters (use these exact figures; cite the source in docs)

All figures are from the Singapore Police Force, 2025 annual scam figures:

- S$913.1M lost to scams; 41,974 cases.
- **81.8% were self-effected transfers.** The real customer sends the money, so every identity-based fraud check passes.
- Seniors were about 15% of victims but had the **highest average loss, S$37,053**.

Source: https://www.police.gov.sg/media-hub/police-life/2026/02/scams-and-cybercrime-fell-by-almost-a-quarter-in-2025

Singapore's **Protection from Scams Act** lets police order banks to restrict a person's transfers (up to 30 days, extendable). It is manual and last-resort. SpellBreaker is the automated layer that comes before it.

Source: https://www.mha.gov.sg/media-room/newsroom/introduction-of-the-protection-from-scams-bill/

**Core insight (the pitch hinges on it):** fraud AI asks "is this the account owner?" For 82% of scams the answer is YES. SpellBreaker asks "**is the owner under someone else's control right now?**"

### 1.4 Tracks

- **Primary:** Real-Time AI for Critical Decisions (detect, decide, respond).
- **Secondary:** AI Secured — Innovation Without Exposure.

---

## 2. Environment assumptions and preflight

- You run on the user's laptop, in this repo.
- The LinuxONE Community Cloud VM is reachable as SSH host alias **`l1cc`** (configured by the user in `~/.ssh/config`). Test it with `ssh -o BatchMode=yes -o ConnectTimeout=10 l1cc 'uname -m'`. The expected output is `s390x`.
  - If unreachable: build and verify everything locally, write deploy scripts anyway, and log "Needs human: SSH to l1cc" in `BLOCKERS.md`.
- **Data:**
  - `data/HI-Small_Trans.csv` (IBM AMLworld, from Kaggle `ealtman2019/ibm-transactions-for-anti-money-laundering-aml`) may or may not be present.
  - If absent, try `kaggle datasets download -d ealtman2019/ibm-transactions-for-anti-money-laundering-aml -f HI-Small_Trans.csv -p data/` (only if the `kaggle` CLI and credentials exist).
  - Otherwise use the placeholder mule-score distributions and log it.
- **Existing files the user placed in the repo:** `ml/mulenet_baseline.py`, `ml/spellbreaker_train.py`, `docs/SpellBreaker_PRD.md`. They are working starting points (§4). Extend them; do not rewrite from scratch.

**Preflight task (P0):** record the results of all checks in `evidence/preflight_local.txt` and, if reachable, `evidence/preflight_l1cc.txt`:

- python version, pip, git, podman/docker presence;
- on l1cc: `uname -a`, `lscpu`, `free -g`, `nproc`, `cat /etc/os-release`, `grep -m1 features /proc/cpuinfo`, `grep -c nnpa /proc/cpuinfo`, `podman --version || docker --version`, `python3 --version`.

---

## 3. Repository layout (target)

```
.
├── AGENTS.md                 # this file
├── PROGRESS.md  DECISIONS.md  BLOCKERS.md
├── README.md                 # judge-facing (see §8)
├── .gitignore
├── ml/
│   ├── mulenet_baseline.py   # given; add --export-scores
│   ├── spellbreaker_train.py # given; extend per §4
│   └── requirements.txt
├── service/
│   ├── app.py                # FastAPI: API + serves static UIs
│   ├── features.py           # live feature builder (same definitions as training)
│   ├── policy.py             # risk -> level/action/messages
│   ├── explain.py            # model-derived reasons (occlusion)
│   ├── state.py              # in-memory customer profiles, payees, recent transfers
│   ├── genai.py              # local LLM analyst case note + fallback
│   ├── seed_demo.py          # demo customers, payees, mule account map
│   ├── requirements.txt
│   └── Containerfile
├── web/
│   ├── bank/                 # Merlion Bank mock mobile app (index.html, app.js, style.css)
│   └── dashboard/            # live decision dashboard (index.html, dash.js, style.css)
├── bench/loadtest.py
├── tests/test_api.py         # acceptance scenarios (§5.6)
├── scripts/
│   ├── deploy_l1cc.sh        # rsync + build/run on l1cc
│   ├── train_l1cc.sh         # run training ON LinuxONE, pull report back
│   ├── collect_evidence.sh   # writes evidence/*.txt on l1cc and pulls them
│   └── run_local.sh
├── results/                  # model_report.json, bench.json, ...
├── evidence/                 # text outputs for screenshots (§9)
└── docs/
    ├── SpellBreaker_PRD.md  ARCHITECTURE.md (mermaid)  RESULTS.md
    ├── VIDEO_SCRIPT.md  SUBMISSION.md  OPEN_SOURCE.md  PRIVACY.md  RESPONSIBLE_AI.md
    └── architecture.png (optional, if mermaid-cli available)
```

---

## 4. ML specification

### 4.1 Current state (already working)

`ml/spellbreaker_train.py` simulates customers, normal sessions, hard negatives and four scam types:

- `gov_impersonation`
- `investment` (pig-butchering)
- `job`
- `phishing_led`

It then builds causal features, uses a time split (train days 30–64, validate 65–76, test 77–89), and trains M1 (risk, HistGradientBoosting) and M2 (scam type). Thresholds are set from legit validation percentiles (99.0 / 99.7 / 99.9). It reports ablations, a rules baseline, a leave-one-type-out test and latency, and saves `spellbreaker_model.joblib`.

A trial run (`--customers 5000 --loto`) gave **PR-AUC 0.97, which is too easy**. Rules caught 30% of scam S$ vs ML 99% at equal friction. Leave-one-type-out recall was 45–72%. Your job is to make it **realistic**, add the missing signals, and add fairness and export features.

### 4.2 Required changes to `ml/spellbreaker_train.py`

1. **`--difficulty {realistic,easy}`**, default `realistic`. In realistic mode, increase overlap so the test PR-AUC lands around 0.70–0.90:
   - normal `on_call` 0.05 → 0.12;
   - gov `pasted` 0.80 → 0.60;
   - gov amount ratio U(5,50) → U(2,40);
   - hard negatives 2% → 4% of normal volume;
   - add label noise: 3% of scam sessions get behavioural flags drawn from the normal distribution.

   If PR-AUC is still above 0.93, increase overlap further and log the parameters in `DECISIONS.md`.
2. **New signals** (named in the team's original concept, missing from the current script):
   - `balance_fraction` = amount ÷ available balance (simulate per-customer balance, about lognormal(log(median × 40), 0.8)).
     - normal mostly < 0.15;
     - gov impersonation 0.4–1.0 ("draining savings");
     - investment rising over the episode;
     - contractor hard negative 0.2–0.7.
   - `from_long_term_savings` (bool): the transfer is funded from a savings or fixed-deposit pot.
     - normal p = 0.03;
     - gov p = 0.55;
     - investment p = 0.35;
     - family-urgent hard negative p = 0.25.
   - Add both to `FEATS`. Add `balance_fraction` and `from_long_term_savings` to the live feature builder too.
3. **Age band for fairness reporting only. Never a model feature.**
   - Assign each customer an `age_band` ∈ {18-34, 35-49, 50-64, 65+} with population weights 0.30/0.30/0.25/0.15.
   - Make scam victim selection over-weight 65+ so they are about 15% of victims, with larger amounts (consistent with the SPF figures).
   - Report legit interruption rate and scam recall **per age band** in the model report. If 65+ legit interruption is more than 2× the overall rate, note it in `docs/RESPONSIBLE_AI.md` with a mitigation (e.g. threshold review).
4. **Model-derived reasons** (moved into `service/explain.py` but defined here):
   - Occlusion attribution: for each feature, replace its value with the median legit training value, re-score, and take the risk drop.
   - Return the top 4 features with drop > 0.02, mapped to plain-English templates (§5.4).
   - Save `legit_medians` in the joblib bundle.
5. **Export** `results/model_report.json` (everything currently printed plus age-band fairness, plus the generation parameters used) and the bundle `models/spellbreaker_model.joblib` containing:
   - `risk_model`, `type_model`, `features`, `thresholds`, `legit_medians`, `effectiveness_assumption`, `difficulty`, `version`, `trained_on` (`platform.machine()`), `trained_at`.
6. **Curves for the dashboard:** also write `results/curves.json`:
   - loss-prevented vs legit-interruption curve, at 20 points between 0.1% and 5% friction, for ML and for the rules baseline;
   - the ablation table;
   - per-type recall;
   - leave-one-type-out recall.
7. **`--mule-scores` path:** if `results/mule_scores.csv` exists, use it automatically.
8. Keep the runtime of `--customers 20000` under 10 minutes on l1cc. If it exceeds that, use `--customers 10000` and log it.

### 4.3 MuleNet (`ml/mulenet_baseline.py`)

- Add `--export-scores results/mule_scores.csv`. Write one row per receiving account in the test window with columns `score,is_mule`, where:
  - `score` = the model's mean predicted probability over that account's incoming transactions;
  - `is_mule` = 1 if any incoming laundering transaction.

  Also write `results/mulenet_report.json` (siloed / collab / oracle metrics, exposure %).
- Add `--nrows` (default: all). On l1cc, if RAM is under 6 GB, use `--nrows 2000000` and log it.
- If `data/HI-Small_Trans.csv` is missing: skip, and log "Needs human: download AMLworld HI-Small to data/".

### 4.4 Acceptance (ML)

```bash
python3 ml/spellbreaker_train.py --customers 5000 --loto            # < 60 s locally
python3 -c "import json;r=json.load(open('results/model_report.json'));assert 0.6<r['full']['pr_auc']<0.95;assert 'fairness_by_age_band' in r"
test -f models/spellbreaker_model.joblib && test -f results/curves.json
```

---

## 5. Service specification (FastAPI, `service/`)

### 5.1 Startup

- Load `models/spellbreaker_model.joblib`.
- Load `results/mule_scores.csv` if present (else the placeholder Beta scores).
- Seed demo state from `seed_demo.py`.
- Log the architecture (`platform.machine()`).
- Serve:
  - `/` → redirect to `/bank/`
  - `/bank/` → `web/bank`
  - `/dashboard/` → `web/dashboard`

  Same origin, so no CORS issues. Also enable CORS for `*` anyway, for safety.

### 5.2 Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/score` | Score a transfer (contract below) |
| POST | `/transfer/confirm` | `{decision_id, user_choice}` records the outcome (proceeded / cancelled) and updates state (payee saved, recent transfers) |
| GET | `/decisions?limit=50` | Latest decisions for the dashboard (newest first) |
| GET | `/case/{decision_id}` | Analyst case note (GenAI or fallback), generated async |
| GET | `/report` | Contents of `results/model_report.json` + `curves.json` + `bench.json` if present |
| GET | `/privacy` | Static JSON: what the phone sends vs what never leaves the device (§5.5) |
| GET | `/health` | `{"status":"ok","model_version":..,"arch":platform.machine(),"trained_on":..,"genai":"local-llm"|"template"}` |
| POST | `/demo/reset` | Reset in-memory state to the seed (for repeated video takes) |

### 5.3 `POST /score` contract (frozen; the UI depends on it)

Request:
```json
{
  "customer_id": "C-TAN",
  "payee_account": "MB-778-201-9931",
  "payee_name": "Secure Govt Account",
  "amount": 20000,
  "source_pot": "savings|current",
  "flags": {"on_call": true, "pasted_account": true, "rushed_score": 0.82, "clicked_flagged_link_recent": false},
  "timestamp": "optional ISO8601; default now"
}
```

Response:
```json
{
  "decision_id": "d_000123",
  "risk": 0.94, "level": "LOW|MEDIUM|HIGH|CRITICAL",
  "scam_type": "gov_impersonation|investment|job|phishing_led|none",
  "scam_type_confidence": 0.88,
  "action": "ALLOW|ASK_QUESTION|HOLD_30M_ALERT_CONTACT|HOLD_AND_ESCALATE",
  "question": "string or null",
  "message": "string",
  "reasons": ["On an active call", "New payee", "14x your usual amount", "Receiver shows money-mule behaviour (0.91)"],
  "features_used": {"...": "the exact numeric vector, for the dashboard"},
  "latency_ms": 3.1,
  "scored_on": "IBM LinuxONE (s390x)"
}
```

- `latency_ms` is measured server-side, from request parse to response build. It excludes the GenAI work, which runs async.
- `scored_on` reads `"IBM LinuxONE (s390x)"` only if `platform.machine()=="s390x"`; otherwise `"local dev (<arch>)"`.
- **Features must be computed by `service/features.py` with exactly the training definitions:**
  - `new_payee`: payee not in the customer's saved payees;
  - `payee_repeat_escalation`: payee paid before and amount > last amount to them;
  - `n_1h`, `n_24h`, `n_new_payees_7d`: from recent transfers in state;
  - `log_amount_ratio`: vs the customer baseline median;
  - `balance_fraction`, `from_long_term_savings` (`source_pot=="savings"`);
  - `receiver_mule_score`: lookup by payee account → mule score (default = median non-mule score);
  - hour features from the timestamp.

  Write a unit test asserting feature parity between `features.py` and the training featurizer on 100 sampled sessions.

### 5.4 Policy and messages (`service/policy.py`)

**Levels** from the bundle thresholds: `risk ≥ T3` → CRITICAL, `≥ T2` → HIGH, `≥ T1` → MEDIUM, else LOW.

**Actions:**
- LOW → `ALLOW`
- MEDIUM → `ASK_QUESTION`
- HIGH → `HOLD_30M_ALERT_CONTACT`
- CRITICAL → `HOLD_AND_ESCALATE`

**Questions by scam type** (the MEDIUM `question`; also shown on HIGH/CRITICAL screens):
- `gov_impersonation`: "Is someone on the phone right now telling you to move money to keep it safe? Real police, government and bank officers will never ask you to do this."
- `investment`: "Have you been promised guaranteed or unusually high returns? Have you been able to withdraw any profit yet?"
- `job`: "Are you being asked to pay money to complete tasks or unlock earnings for a job?"
- `phishing_led`: "Did you get here from a link in an SMS, email or chat? Banks will never send you a link to make a payment."
- `none`: "This transfer looks unusual for you. Do you know and trust this payee?"

**Messages:**
- HIGH: "We've paused this transfer for 30 minutes to keep you safe. Your trusted contact has been notified. If someone is pressuring you, hang up and call the ScamShield Helpline at 1799."
- CRITICAL: "For your protection, Merlion Bank will call you before this transfer is released. Do not share any codes with anyone."

**Reason templates** (from `explain.py` feature keys):

| Feature key | Reason text |
|---|---|
| `on_call` | "You're on an active phone call" |
| `new_payee` | "New payee you haven't paid before" |
| `log_amount_ratio` | "{x}× your usual transfer amount" |
| `balance_fraction` | "Moves {p}% of your available balance" |
| `from_long_term_savings` | "Drawn from your long-term savings" |
| `pasted_account` | "Account number was pasted, not typed" |
| `rushed_score` | "Unusually rushed or hesitant input" |
| `receiver_mule_score` | "Receiving account shows money-mule behaviour ({s})" |
| `n_1h` | "{n} transfers in the last hour" |
| `payee_repeat_escalation` | "Payments to this payee keep increasing" |
| `clicked_flagged_link_recent` | "You recently opened a link flagged as a scam" |
| `is_late_night` | "Late-night transfer" |

### 5.5 Privacy (`/privacy` and the dashboard panel)

The phone sends only these values:
- `on_call` (yes/no)
- `pasted_account` (yes/no)
- `rushed_score` (one number)
- `clicked_flagged_link_recent` (yes/no)
- the transfer itself

**Never sent:** the caller's number, call audio, contacts, messages, clipboard contents, raw keystroke timings, location.

Scoring runs inside the bank's platform (LinuxONE). No external AI API ever receives customer data. The GenAI note runs **locally on the same LinuxONE VM** and receives only the decision summary (risk, type, reasons, amount band), never names or account numbers.

### 5.6 Acceptance scenarios (`tests/test_api.py`, pytest with FastAPI TestClient)

Seed customers in `seed_demo.py` (all synthetic):

| Customer | Profile | Saved payees | Balance |
|---|---|---|---|
| `C-TAN` ("Mdm Tan", 65+) | Usual transfers ~S$300 | Landlord S$1,800, Daughter, SP Group | Current S$9,000; savings S$85,000 |
| `C-LIM` ("Mr Lim", 35-49) | Usual ~S$900 | Landlord, Contractor-known | Current S$25,000; savings S$40,000 |
| `C-RAJ` ("Raj", 18-34) | Usual ~S$150 | Friends | Current S$3,000; savings S$6,000 |

Demo payee accounts:
- `MB-778-201-9931` "Secure Govt Account": receiver mule score from the top-decile real mule score (or 0.91).
- `MB-554-310-1207` "Apex Wealth Desk": mule score about 0.8. Used for the investment sequence.
- `MB-201-889-4410` "TaskHub Rewards": mule score about 0.75.
- Saved payees: clean, about 0.05.

| # | Scenario | Expected |
|---|---|---|
| S1 | C-TAN, new payee 9931, S$20,000 from savings, on_call, pasted, rushed 0.8 | `CRITICAL`, `gov_impersonation`; "active phone call" in reasons |
| S2 | C-TAN, landlord, S$1,800 from current, on_call, typed, rushed 0.2 | `LOW` |
| S3 | C-LIM, new contractor payee, S$8,000, typed, not on call | `LOW` or `MEDIUM`, never `HIGH`/`CRITICAL` |
| S4 | C-RAJ, 3rd escalating payment to 1207 (S$500 → S$1,200 → S$2,800) | ≥ `MEDIUM`, `investment` |
| S5 | C-RAJ, TaskHub small task payments ×4 in an evening, rising | 4th payment ≥ `MEDIUM`, `job` |
| S6 | `/health` | `ok`; arch present |
| S7 | `POST /demo/reset` then S1 again | Same result (deterministic) |

**If S1–S5 fail with the trained model, do NOT hack the tests.** Adjust the seed profiles to be realistic for their story (e.g. the baseline amounts) and log it. If they still fail, the model or features have a bug: fix it. As a last resort for demo reliability only, add a documented, clearly labelled `DEMO_MODE` calibration that is OFF by default. Never ship hidden overrides.

**Verify:**
```bash
pytest -q tests/
```

### 5.7 GenAI analyst case note (`service/genai.py`) — Predictive AI + Generative AI

**Purpose:** for HIGH and CRITICAL decisions, generate a 4–6 sentence case note for the bank's fraud analyst:
- what happened;
- why it's suspicious (from the reasons);
- the likely scam type;
- a recommended next step (call-back script points);
- and whether this case could warrant a Protection from Scams Act escalation if the customer insists.

It runs **async** (a background task) and never blocks `/score`.

**Runtime preference order** (timebox 90 minutes total; first that works wins):
1. Whatever LLM runtime the official LinuxONE "Predictive AI + Generative AI" lab uses. Inspect https://github.com/linuxone-community-cloud/jupyter-lab-ml and the l1cc VM (e.g. `ollama`, a running container, an existing model) and mirror it.
2. `llama.cpp` built from source on l1cc (it supports s390x) with a small instruct model (≤ 1.5B params, e.g. a Qwen2.5-0.5B/1.5B-Instruct GGUF). s390x is **big-endian**: you must use a big-endian GGUF (convert with llama.cpp's `convert_hf_to_gguf.py --bigendian`, or find a published big-endian GGUF). Serve it with `llama-server` on localhost:8081.
3. Any locally runnable small text-generation model that installs on s390x.
4. **Fallback:** a deterministic template note built from the same fields, labelled `"genai":"template"` in `/health` and in the UI badge. Log in `BLOCKERS.md`.

**Prompt rules:**
- Pass only: level, risk, scam type, reasons, amount band (e.g. "S$10k–50k"), age band.
- Never pass names or account numbers.
- Cap generation at about 180 tokens, with a 25 s timeout, then fall back to the template.

### 5.8 Containerisation and deployment (`service/Containerfile`, `scripts/deploy_l1cc.sh`)

- **Base image:** a multi-arch Python image that has s390x (e.g. `registry.access.redhat.com/ubi9/python-311` or `python:3.11-slim`). Verify it pulls on l1cc.
- **Build on l1cc:**
  ```bash
  podman build -t spellbreaker:latest -f service/Containerfile .
  ```
  Use docker if podman is absent.
- **Run:**
  ```bash
  podman run -d --name spellbreaker -p 8000:8000 spellbreaker:latest
  ```
  Run as a non-root user inside the container. Uvicorn with `--workers 2`, or `nproc`.
- **`deploy_l1cc.sh`:**
  1. `rsync -az --exclude data --exclude .git ./ l1cc:~/spellbreaker/`
  2. `ssh l1cc 'cd ~/spellbreaker && ./scripts/train_l1cc.sh && podman build ... && podman rm -f spellbreaker; podman run ...'`
  3. Then curl `/health` via ssh.
- **Container fallback:** if container build fails within 45 minutes, run with a venv + `nohup uvicorn ...` on l1cc. Log it, and still document the Containerfile.
- **Access for the video:** the user runs `ssh -N -L 8000:localhost:8000 l1cc` and opens `http://localhost:8000/bank/` and `/dashboard/`. Put this in the README. If the VM has a public IP with port 8000 open, also note the direct URL.
- **Training ON LinuxONE (scored by judges):** `scripts/train_l1cc.sh` runs MuleNet (if data present) and `spellbreaker_train.py --customers 20000 --loto` on l1cc, saving the logs to `evidence/train_l1cc.log` and `results/`. The served model must be the one trained on l1cc: `trained_on` must equal `s390x` in `/health`.

---

## 6. Phased plan (times in SGT; start immediately)

Tick in `PROGRESS.md`. Each task: timebox, then Verify.

### P0 — Bootstrap (≤ 15 min)
- [ ] Create the layout (§3), `.gitignore`, `PROGRESS.md`/`DECISIONS.md`/`BLOCKERS.md`; `git init` if needed.
- [ ] Run the preflight checks (§2) and write `evidence/preflight_*.txt`.
- [ ] Create a local venv and install `ml/requirements.txt` + `service/requirements.txt`.
- **Verify:** `python3 -c "import fastapi, sklearn, pandas, joblib"`

### P1 — Service skeleton + UI wired to a stub (target done by 02:15)
- [ ] `service/app.py` with all §5.2 endpoints. `/score` returns a deterministic stub until the model exists.
- [ ] `web/bank` (§7.1) and `web/dashboard` (§7.2), wired to the stub.
- **Verify:** `./scripts/run_local.sh` starts; curl `/health` returns ok; opening `/bank/` and `/dashboard/` returns 200 (curl).

### P2 — ML realistic model (target done by 03:15)
- [ ] All §4.2 changes; MuleNet export (§4.3) if data is present.
- [ ] Run locally with `--customers 5000 --loto`; check the §4.4 acceptance.
- **Verify:** §4.4 commands pass.

### P3 — Real model in the service (target done by 04:00)
- [ ] `features.py` parity, `explain.py`, `policy.py`, `state.py`, `seed_demo.py`, `/transfer/confirm`, `/demo/reset`.
- [ ] `tests/test_api.py` S1–S7 plus the feature-parity test.
- **Verify:** `pytest -q` all green.

### P4 — LinuxONE deployment + training on s390x (target done by 05:15)
- [ ] `train_l1cc.sh`, `deploy_l1cc.sh`, Containerfile; the model trained on l1cc is served from the container.
- **Verify:** `ssh l1cc 'curl -s localhost:8000/health'` shows `"arch":"s390x"` and `"trained_on":"s390x"`. Run pytest against the l1cc URL via the tunnel (`BASE_URL` env var support in the tests).

### P5 — Benchmark + evidence (target done by 05:45)
- [ ] `bench/loadtest.py`: 10,000 `/score` requests at concurrency 16, varied realistic payloads; record p50/p95/p99 latency (server-side `latency_ms` and client round-trip separately) and RPS. Write `results/bench.json`. Run it **on l1cc against localhost** (no tunnel noise).
- [ ] `scripts/collect_evidence.sh` (§9) runs on l1cc and pulls the files into `evidence/`.
- **Verify:** `results/bench.json` and all §9 evidence files exist and are non-empty.

### P6 — GenAI case notes (timebox 90 min; target done by 07:15)
- [ ] §5.7 runtime ladder; wire it to `/case/{id}` and the dashboard.
- **Verify:** a HIGH/CRITICAL decision gets a case note within 30 s. `/health.genai` states which runtime.

### P7 — Docs, video support, polish (target done by 07:45 CODE FREEZE)
- [ ] `README.md` (§8), `docs/*` (§8).
- [ ] Final run of the whole flow on l1cc; `/demo/reset` works; UI final polish.
- **Verify:** README commands work from a fresh clone (run them in a temp dir).

### P8 — Post-freeze (07:45–09:30)
- [ ] Only bug fixes, docs and evidence refresh.
- [ ] Final push. Write `docs/SUBMISSION.md` with ready-to-paste fields.
- [ ] Update `PROGRESS.md` with a "Hand-off" section: URLs, the tunnel command, the demo click-path, the open blockers.

**If behind schedule, cut in this order:** GenAI (use the template) → MuleNet real scores (use the placeholder) → container (use the venv) → bench concurrency (use sequential). **Never cut:** a working demo on LinuxONE, tests S1–S2, evidence of s390x, README.

---

## 7. UI specification

Plain HTML/CSS/JS. Clean, modern, high-contrast, large fonts (seniors). Fictional brand "Merlion Bank": teal/navy palette, a simple geometric logo of your own making. Must look good in a 1920×1080 screen recording.

### 7.1 `web/bank/` — Merlion Bank mobile app (rendered inside a phone frame, centred)

**Screens:**
1. **Home.** Greeting "Good evening, Mdm Tan"; Current and Savings balances; a "Transfer" button; recent transfers.
2. **Transfer.**
   - "From" pot selector (Current / Savings).
   - Payee: choose a saved payee, or "+ New payee" (name + account number).
   - Amount.
   - "Send" button.
   - **Paste detection** on the account-number field (`paste` event sets `pasted_account=true`).
   - **`rushed_score`:** from the inter-keystroke timing on the amount and account fields, computed client-side as a 0–1 score. Only the number is kept.
3. **Result screens by level:**
   - LOW → green "Transfer sent".
   - MEDIUM → a modal with the scam-type question and two buttons: "Yes, someone asked me" (→ cancel, show safety tips + ScamShield 1799) and "No, continue" (→ proceed).
   - HIGH → an amber hold screen with a 30:00 countdown, "Your trusted contact (Daughter) has been notified", and the 1799 helpline.
   - CRITICAL → a red "Merlion Bank will call you before this transfer is released" screen.
   - Every non-LOW screen lists the human-readable reasons in a "Why am I seeing this?" expander.

**Demo control drawer** (a small gear icon; collapsible; labelled "Demo controls — simulates phone signals"):
- **On active call** toggle. Browsers can't detect calls, so state this honestly in the drawer.
- "Recently opened flagged link" toggle.
- Customer switcher (C-TAN / C-LIM / C-RAJ).
- **Preset buttons** that pre-fill the form for reliable video takes:
  - "Scam: fake ICA officer" (S1)
  - "Rent while on call" (S2)
  - "Contractor payment" (S3)
  - "Investment payment #3" (S4)
  - "Job task payment" (S5)
- "Reset demo" (calls `/demo/reset`).

**Footer badge:** "Protected by SpellBreaker · scored on IBM LinuxONE".

### 7.2 `web/dashboard/` — Live decision console (for the bank's fraud team and for judges)

- Polls `/decisions` every 1 s.
- **Top KPI row:**
  - transfers scored;
  - interrupted;
  - S$ protected (sum of the amounts of HIGH+CRITICAL decisions the user didn't override);
  - median latency (ms);
  - platform badge from `/health` ("IBM LinuxONE · s390x"; or "local dev");
  - GenAI badge (local LLM / template).
- **Live feed:** cards with time, customer (synthetic ID only), amount, a level badge (colour), scam type, risk gauge, reasons, latency.
- **Selected decision panel:**
  - the feature vector as bars;
  - **"What the phone sent vs what never left the device"** (from `/privacy`);
  - the GenAI analyst case note (loading state while it generates).
- **"Model evidence" tab** (from `/report`), using Chart.js:
  - loss-prevented vs friction curve (ML vs rules);
  - ablation bars (full / no behavioural / no mule score);
  - per-type recall;
  - leave-one-type-out recall;
  - fairness by age band;
  - benchmark latency histogram/percentiles;
  - "Trained on: s390x" stamp.
- **Architecture tab:** an inline SVG or mermaid render of the §8 diagram.

---

## 8. Documentation deliverables

**`README.md`** (judge-facing; first screen must sell it):
1. Title line: `SpellBreaker — [Team Name]_IBM Z Datathon 2026 Project`. Leave `[Team Name]` as a literal placeholder and list it in `BLOCKERS.md` "Needs human".
2. One-line pitch, plus the core insight with the SPF figures (cited).
3. Demo GIF/screenshot placeholders (paths in `docs/img/`).
4. **How it uses IBM Z / LinuxONE** (a short, factual table, linking evidence files):
   - trained on s390x;
   - served from a container on LinuxONE;
   - real-time latency/throughput numbers from `results/bench.json`;
   - data never leaves the platform;
   - local GenAI on LinuxONE (if achieved);
   - production path: IBM Hyper Protect / Secure Execution, Telum on-chip inference via zDLC. Explicitly labelled **"production target, not used in this prototype"** unless proven.
5. **Architecture:** a mermaid diagram showing:
   - bank app → `/score` on LinuxONE;
   - inside: features → M1 risk + M2 type + M3 mule score → policy → response;
   - async: GenAI case note;
   - dashboard.

   Also list "multi-model hybrid: 3 predictive models + 1 generative model".
6. **Results:** key numbers from `model_report.json` and `bench.json` (auto-filled by a small script `scripts/fill_results.py` that writes `docs/RESULTS.md` and the README results block between markers).
7. **Privacy by design** (5 bullets) and **Responsible AI** (age-band fairness, human-in-the-loop, no auto-freeze, synthetic data disclosure).
8. **Data:**
   - IBM AMLworld (real, IBM) for the receiver side;
   - the typology simulator for the victim side, with an explicit justification: banks cannot share manipulated-customer data; IBM built AMLworld for the same reason; every pattern traces to an SPF typology.
9. Run locally / deploy to LinuxONE / tunnel command / run tests / run benchmark.
10. **Open-source and data credits** (link `docs/OPEN_SOURCE.md`).
11. Event code **SSF2026**.

**Other docs:**
- `docs/ARCHITECTURE.md` — the diagram plus a component table.
- `docs/RESULTS.md` — the full metrics.
- `docs/PRIVACY.md`, `docs/RESPONSIBLE_AI.md`.
- `docs/OPEN_SOURCE.md` — every library, model, dataset and CDN, with links and licences where known.
- `docs/SUBMISSION.md` — ready-to-paste: project title, a 150-word description including **SSF2026**, track(s), repo link placeholder, video link placeholder, open-source links list.
- `docs/VIDEO_SCRIPT.md` — a **≤ 3:00** shot list, with exact screens and the numbers to quote. It must cover what judges require:

| Time | Content |
|---|---|
| 0:00–0:20 | Problem + data (SPF figures) + core insight |
| 0:20–1:15 | Skit: scam call → Merlion Bank transfer → SpellBreaker CRITICAL interruption; dashboard shows reasons + "scored on LinuxONE in X ms" |
| 1:15–1:30 | Counter-case: rent while on call → allowed silently |
| 1:30–2:15 | How it works: 3 predictive models + local GenAI note; privacy panel; model evidence tab (ML vs rules curve, leave-one-type-out, fairness) |
| 2:15–2:50 | **IBM Z section (mandatory):** terminal on l1cc showing `uname -m` → s390x, `podman ps`, the training log tail, `/health`, bench numbers; tech-stack slide |
| 2:50–3:00 | Impact + close |

---

## 9. Evidence files (for screenshots; judges score platform usage on screenshots)

`scripts/collect_evidence.sh` runs on l1cc and writes the following, then pulls them into `evidence/`:

| File | Contents |
|---|---|
| `evidence/platform.txt` | `uname -a`, `cat /etc/os-release`, `lscpu`, `nproc`, `free -g` |
| `evidence/cpu_features.txt` | `grep -m1 features /proc/cpuinfo`, `grep -c nnpa /proc/cpuinfo` (0 means no Telum NNPA visible) |
| `evidence/container.txt` | `podman --version`, `podman images`, `podman ps`, `podman inspect spellbreaker --format '{{.Config.User}}'` |
| `evidence/python_env.txt` | `python3 --version`, `pip freeze` (inside the container) |
| `evidence/train_l1cc.log` | Full training log, including `platform.machine()` |
| `evidence/health.json` | `curl localhost:8000/health` |
| `evidence/bench.txt` | Human-readable benchmark summary |
| `evidence/crypto.txt` | `openssl version`; `openssl speed -seconds 2 -evp sha256` (CPACF-accelerated hashing used for the masked mule-account tokens; describe it as "hardware-accelerated crypto via CPACF" only if the cpu features include the message-security-assist facility; otherwise just "OpenSSL") |

Also generate `evidence/README.md` explaining what each file proves.

---

## 10. Fallback table (use without asking)

| Problem | Fallback |
|---|---|
| `l1cc` SSH unreachable | Finish everything locally; write all scripts; log "Needs human" with exact commands to run. |
| AMLworld CSV missing / no Kaggle creds | Placeholder Beta mule scores; log "Needs human". |
| l1cc RAM too small for MuleNet | `--nrows 2000000`; if it still fails, run MuleNet locally and copy `mule_scores.csv` up; log it (training of SpellBreaker itself must still happen on l1cc). |
| A pip package fails on s390x | Use the standard-library or pure-Python alternative; drop optional extras. Never block on it. |
| Podman/docker unavailable or the build fails | venv + `nohup uvicorn`; keep the Containerfile; log it. |
| No LLM runtime within 90 min | Template case notes; badge "template"; log it. |
| A test scenario fails | Fix features/seeds (realistic), never hack the tests; a documented `DEMO_MODE` is the last resort, OFF by default. |
| Running out of time | Cut order in §6. |

---

## 11. Definition of done (all must be true at 07:45 SGT)

- [ ] The bank app and dashboard work end-to-end, served from **LinuxONE** (via tunnel); `/health` shows `arch=s390x`, `trained_on=s390x`.
- [ ] S1–S7 pass against the l1cc deployment.
- [ ] `results/model_report.json`, `curves.json`, `bench.json` come from the l1cc runs; the dashboard's Model Evidence tab renders them.
- [ ] Evidence files (§9) are present.
- [ ] README, VIDEO_SCRIPT (≤ 3:00), SUBMISSION (with SSF2026), OPEN_SOURCE are complete; no unverified claims.
- [ ] `PROGRESS.md` has a Hand-off section; `BLOCKERS.md` lists every "Needs human" item with the exact action to take.
- [ ] All work is committed (and pushed if a remote exists).