# SpellBreaker — [Team Name]_IBM Z Datathon 2026 Project

**SpellBreaker spots the moment a genuine customer is being manipulated into sending money, then interrupts with a scam-specific warning.** It asks: **“Is the owner under someone else’s control right now?”**

In 2025, Singapore recorded S$913.1 million in scam losses across 41,974 cases. 81.8% of cases involved self-effected transfers, where the real account owner sent the money. Seniors were about 15% of victims and had the highest average loss at S$37,053. [Singapore Police Force, 2025 annual scam figures](https://www.police.gov.sg/media-hub/police-life/2026/02/scams-and-cybercrime-fell-by-almost-a-quarter-in-2025)

The Protection from Scams Act allows police to direct banks to restrict an individual’s transfers for up to 30 days, with an extension possible. SpellBreaker is designed as an earlier intervention layer. [Ministry of Home Affairs](https://www.mha.gov.sg/media-room/newsroom/introduction-of-the-protection-from-scams-bill/)

<!-- RESULTS:START -->
Local synthetic PR-AUC: 0.873; legit interruption rate at T1: 1.35%.

Optimized local benchmark (10,000 requests, concurrency 16): server p50 7.53 ms and p99 27.37 ms. LinuxONE post-XGBoost MuleNet benchmark: server p50 23.28 ms and p99 25.23 ms. The synthetic model metrics and measured service latency are separate from real-world effectiveness.

See [full model results](docs/RESULTS.md).
<!-- RESULTS:END -->

## Demo

Screenshot/GIF placeholders: `docs/img/bank-demo.png`, `docs/img/dashboard.png`.

## IBM Z / LinuxONE evidence

| Claim | Evidence | Current status |
|---|---|---|
| Model trained on s390x | `evidence/train_l1cc.log`, bundle `trained_on` | Verified; report says `trained_on=s390x` |
| Served in a container on LinuxONE | `evidence/container.txt` | Verified; Ubuntu 24.04 container on l1cc |
| Real-time latency and throughput | `results/bench.json`, `evidence/bench.txt` | Verified; LinuxONE server p99 25.23 ms |
| Customer data stays within bank platform | `docs/PRIVACY.md` | Prototype design statement; no production deployment verified |
| Local GenAI | `/health` and `evidence/health.json` | Granite was attempted; factuality checks rejected outputs, so case notes use the deterministic template |
| Hyper Protect / Secure Execution; Telum NNPA via zDLC | — | **Production target, not used in this prototype** |

**AI stack:** scikit-learn (transfer-risk + scam-type models), XGBoost (receiver-mule model), and llama-cpp-python + IBM Granite (case notes; attempted on LinuxONE, with the deterministic template active after factuality checks rejected the generated output). MuleNet compares XGBoost with scikit-learn HistGradientBoosting on the same AMLworld holdout; XGBoost receiver scores were consumed by SpellBreaker training. A small PyTorch MLP is also evaluated as a notebook-only M1 challenger and is not served. See `results/mulenet_report.json`, `evidence/mulenet_l1cc.log`, and the executed notebook under `evidence/`.

## Platform security on LinuxONE

- The scoring container runs as UID/GID `10001:10001`; Docker inspection recorded the configured user. It also runs with a read-only root filesystem, a size-bounded `/tmp` tmpfs, and all Linux capabilities dropped. See `evidence/container.txt`.
- LinuxONE exposes the CPACF message-security-assist (MSA) CPU facility. `evidence/cpu_features.txt` records the CPU flags and the literal `grep -c nnpa /proc/cpuinfo` result; `evidence/crypto.txt` records OpenSSL speed output and its OpenSSL runtime. Receiver-account sharing supports keyed HMAC-SHA256 tokens through Python `hmac`/`hashlib`; the evidence includes only a synthetic identifier and an ephemeral key is discarded.
- The local case-note adapter receives only allow-listed case fields and constructs its prompt from the scam type. Names, account numbers, and raw transaction identifiers are excluded; see `evidence/genai_prompt_sample.txt`.
- NNPA is visible in CPU flags, but no model ran through zDLC in this prototype. Telum on-chip inference via zDLC is a production path, not a capability claimed as used here. Secure Execution / Hyper Protect is also a production target only.

## Team

- [Name — role — contribution]
- [Name — role — contribution]
- [Name — role — contribution]
- [Name — role — contribution]
- [Name — role — contribution]
- [Name — role — contribution]

## Judging rubric mapping

| Playbook tip / judging evidence | Evidence in this submission |
|---|---|
| Named AI frameworks and predictive + generative AI | This README's AI stack; `results/mulenet_report.json` compares XGBoost and HistGradientBoosting; the executed notebook reports the PyTorch MLP challenger; `evidence/genai_runtime.txt` documents the Granite attempt and active template. Dashboard model/runtime indicators. |
| Run and train on LinuxONE | `evidence/platform.txt`, `evidence/train_l1cc.log`, `evidence/health.json`, and `notebooks/SpellBreaker_on_LinuxONE.ipynb` (executed copy in `evidence/`). |
| Containerisation and real-time performance | `evidence/container.txt`, `evidence/bench.txt`, `results/bench.json`; LinuxONE service p99 is recorded in Results. |
| Demonstrated platform security | `evidence/container.txt` (UID, read-only root, dropped capabilities), `evidence/crypto.txt` and `evidence/cpu_features.txt` (OpenSSL, MSA and NNPA visibility), and `evidence/genai_prompt_sample.txt` (privacy allow-list). |
| Community value and responsible data use | `docs/RESULTS.md`, `docs/PRIVACY.md`, `docs/RESPONSIBLE_AI.md`, and `docs/OPEN_SOURCE.md` (AMLworld Kaggle source and CDLA-Sharing-1.0). |
| Team contribution and execution | This README's Team placeholders and the 10-second Team & roles segment in `docs/VIDEO_SCRIPT.md`; replace placeholders with the actual team before submission. |

## Architecture

```mermaid
flowchart LR
  B[Merlion Bank demo app] -->|transfer signals| API[FastAPI /score on LinuxONE target]
  API --> F[Feature builder]
  F --> M1[M1 transfer risk]
  F --> M2[M2 scam type]
  F --> M3[M3 receiver mule score]
  M1 --> P[Policy and intervention]
  M2 --> P
  M3 --> P
  P -->|decision| B
  P -. async case summary .-> G[Local analyst note template]
  API --> D[Fraud dashboard]
```

## Results

See [docs/RESULTS.md](docs/RESULTS.md) and the generated [model report](results/model_report.json). The reported data are synthetic. Do not interpret simulated losses prevented as real-world outcomes.

## Privacy and responsible AI

- Only a small set of transfer and yes/no interaction signals is sent to the scoring service.
- Caller number, audio, contacts, messages, clipboard contents, raw keystroke timings and location are not sent.
- All named customers and accounts are synthetic.
- A high score pauses or escalates a transfer for human review; the model does not automatically freeze an account.
- The age band is used only for reporting, never as a model feature. Review [docs/RESPONSIBLE_AI.md](docs/RESPONSIBLE_AI.md).

## Data

The victim-side data are generated by a typology simulator because banks cannot share real manipulated-customer cases. It reflects the four scam patterns in the specification and is explicitly synthetic. IBM AMLworld HI-Small was supplied in `data/` on the laptop and LinuxONE; XGBoost MuleNet and the HistGradientBoosting comparison ran on a 2,000,000-row subset on l1cc inside the official Jupyter image. The XGBoost receiver-score export and comparison report are in `results/`, and the Kaggle link and CDLA-Sharing-1.0 licence are in [docs/OPEN_SOURCE.md](docs/OPEN_SOURCE.md).

## Run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
python ml/spellbreaker_train.py --customers 5000 --loto
./scripts/run_local.sh
```

Then open `http://localhost:8000/bank/` or `http://localhost:8000/dashboard/`. For LinuxONE, run `./scripts/deploy_l1cc.sh`, then tunnel with `ssh -N -L 8000:localhost:8000 l1cc` and open the same URLs. Run acceptance checks with `pytest -q tests/`; benchmark with `python bench/loadtest.py --requests 10000 --concurrency 16`.

## Open source and data credits

See [docs/OPEN_SOURCE.md](docs/OPEN_SOURCE.md). Event code: **SSF2026**.
