# Results

Synthetic victim-side simulator, temporal holdout; not a real-world effectiveness estimate.

AI stack: scikit-learn (risk + scam-type models), XGBoost (mule model), llama-cpp-python + IBM Granite (case notes; Granite was attempted, and the active runtime is the deterministic template fallback).

## Model report

```json
{
  "full": {
    "pr_auc": 0.8730447866940966,
    "roc_auc": 0.9792830494948241,
    "recall_at_t1": 0.7764423076923077,
    "precision_at_t1": 0.8282051282051283,
    "legit_interruption_rate": 0.013497179693795327
  },
  "rules_baseline": {
    "recall": 0.20192307692307693,
    "legit_interruption_rate": 0.014302981466559226
  },
  "thresholds": {
    "T1": 0.4503555339006614,
    "T2": 0.7283795912499044,
    "T3": 0.8473781248357712
  },
  "per_type_recall": {
    "gov_impersonation": 0.9056603773584906,
    "investment": 0.6704545454545454,
    "job": 0.7572815533980582,
    "phishing_led": 0.7563025210084033
  },
  "fairness_by_age_band": {
    "18-34": {
      "legit_interruption_rate": 0.010966415352981495,
      "scam_recall": 0.696078431372549,
      "n_legit": 1459,
      "n_scam": 102
    },
    "35-49": {
      "legit_interruption_rate": 0.011984021304926764,
      "scam_recall": 0.8080808080808081,
      "n_legit": 1502,
      "n_scam": 99
    },
    "50-64": {
      "legit_interruption_rate": 0.01794453507340946,
      "scam_recall": 0.803921568627451,
      "n_legit": 1226,
      "n_scam": 153
    },
    "65+": {
      "legit_interruption_rate": 0.014157014157014158,
      "scam_recall": 0.7903225806451613,
      "n_legit": 777,
      "n_scam": 62
    }
  },
  "ablations": {
    "no_behaviour": 0.8437723183497567,
    "no_mule_score": 0.8734701318382191,
    "full": 0.8730447866940966
  },
  "leave_one_type_out_recall": {
    "gov_impersonation": 0.7735849056603774,
    "investment": 0.5795454545454546,
    "job": 0.6504854368932039,
    "phishing_led": 0.680672268907563
  },
  "trained_on": "arm64",
  "generation_parameters": {
    "difficulty": "realistic",
    "customers": 5000,
    "rows": 25000,
    "scam_fraction": 0.0752,
    "hard_negative_rate": 0.04,
    "behavioral_label_noise": 0.03,
    "overlap_adjustment": "on_call scam .24 (gov .72), pasted gov .60, new payee scam .36 (gov .75), 10% legit high-balance transfers; 450 gov, 300 job-sequence and 300 rising-investment training-only typology cases",
    "seed": 42
  },
  "latency_ms_per_score": 0.43864265799095686,
  "effectiveness_assumption": "Risk flags trigger a friction/interruption; prevented-loss curves assume interrupted scams are prevented."
}
```

## Notebook-only PyTorch MLP challenger

Inside the official s390x Jupyter image, a compact PyTorch MLP (16 inputs, hidden layers 24/8, 25 epochs) was compared with scikit-learn HistGradientBoosting on the same 3,492-row synthetic training split and 1,302-row temporal test split. HistGradientBoosting PR-AUC / ROC-AUC was 0.8679 / 0.9800; the MLP was 0.8444 / 0.9752. This small challenger is evidence-only and is not part of the scoring service. The exact code and output are in `evidence/SpellBreaker_on_LinuxONE.executed.ipynb`.

## Benchmark

Local 10,000-request run, concurrency 16, Uvicorn workers equal to the laptop's 10 logical CPUs. The before run used the pre-fix scoring path; the after run used the optimized scoring path. Latencies below are measured inside `/score` on the server. The full raw reports are in `results/bench_before.json` and `results/bench.json`.

| Run | Duration | Throughput | Server p50 | Server p95 | Server p99 |
|---|---:|---:|---:|---:|---:|
| Before | 488.98 s | 20.45 req/s | 760.05 ms | 902.48 ms | 996.16 ms |
| After | 8.38 s | 1,193.98 req/s | 7.53 ms | 17.63 ms | 27.37 ms |

The after run meets the real-time target (server p50 < 10 ms and p99 < 50 ms). Changes were: set native math-library thread counts to one before model imports; pass NumPy arrays rather than DataFrames; infer M2 once; batch all occlusion rows into one `predict_proba`; keep model artifacts, thresholds, medians and mule scores in startup globals; append to a bounded deque; generate case notes through FastAPI background tasks; and run the short CPU-bound scoring handler on the worker event loop. The local launcher and container use one worker so process-local demo state stays coherent; the benchmark explicitly uses 10 workers.

Debug-stage median over 25 local `TestClient` calls with `SPELLBREAKER_DEBUG_TIMINGS=1` (single process, diagnostic only):

| Parse | Features | M1 | M2 | Explain | Policy | Logging | Total |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.298 ms | 0.021 ms | 0.520 ms | 2.644 ms | 0.518 ms | 0.002 ms | 0.010 ms | 4.079 ms |

These stage values are a local diagnostic sample, not the multi-worker benchmark. Enable the breakdown with `SPELLBREAKER_DEBUG_TIMINGS=1`; the service returns `debug_timings_ms` and logs the same timing object.

## LinuxONE training and benchmark

The initial model was trained directly on l1cc (s390x) with 20,000 customers in 13 seconds. Test PR-AUC was 0.889, ROC-AUC 0.974, recall at T1 0.783, and legit interruption 1.10%. After MuleNet integration, SpellBreaker was retrained on l1cc with 20,000 customers in 17 seconds. The current report shows PR-AUC 0.8805, ROC-AUC 0.9708, recall at T1 0.7760, and legit interruption 1.14%. The report records age-band fairness, per-type recall, the XGBoost MuleNet score source and generation parameters. `evidence/train_l1cc.log`, `results/model_report.json`, and `results/curves.json` contain the current run artifacts.

The service runs in a non-root Ubuntu 24.04 container using the same Ubuntu-prebuilt scikit-learn 1.4.1.post1 stack as the host training venv. Docker inspection verified UID/GID 10001:10001, `ReadonlyRootfs=true`, `/tmp` tmpfs, and `CapDrop=[ALL]`. After retraining with XGBoost MuleNet receiver scores, the LinuxONE benchmark ran 10,000 `/score` requests at concurrency 16 on localhost with one Uvicorn worker:

| Duration | Throughput | Server p50 | Server p95 | Server p99 | Client p50 | Client p99 |
|---:|---:|---:|---:|---:|---:|---:|
| 47.64 s | 209.91 req/s | 23.28 ms | 24.35 ms | 25.23 ms | 75.43 ms | 104.54 ms |

The server-side p99 meets the <50 ms target. Client round-trip latency includes queueing and transport. This final run uses the deterministic case-note fallback; the local Granite runtime was tested but rejected because it repeatedly generated unrelated scam labels and unsupported email claims, so `/health` and the dashboard correctly report `template`. Full results are in `results/bench.json` and `evidence/bench.txt`; §9 platform, CPU, container, package, health, GenAI attempt and crypto evidence is in `evidence/`. The executed LinuxONE notebook verifies a live CRITICAL score and asynchronous case note in `evidence/SpellBreaker_on_LinuxONE.executed.ipynb`.

```json
{
  "requests": 10000,
  "concurrency": 16,
  "duration_s": 8.375355374999344,
  "rps": 1193.979186823554,
  "client_round_trip_ms": {
    "p50": 11.771499994210899,
    "p95": 25.27149999514222,
    "p99": 43.79658302059397
  },
  "server_latency_ms": {
    "p50": 7.5291250250302255,
    "p95": 17.625665990635753,
    "p99": 27.37029199488461
  }
}
```

## LinuxONE GenAI runtime decision

The official JupyterLab image supplied a prebuilt s390x `llama-cpp-python` runtime and was used to attempt local Granite 3.0 1B Q4 inference. Generated responses repeatedly substituted unrelated scam labels or invented email details. An exact scam-type output validator rejected those responses, and the service returned its fact-based 4-sentence template asynchronously. The deployed `/health.genai` value and dashboard badge are `template`; the attempt and model details are recorded in `evidence/genai_runtime.txt`. The refreshed executed notebook records a 5.61 ms CRITICAL score, an asynchronous case note ready with `runtime=template`, and the PyTorch challenger metrics.


## XGBoost MuleNet comparison and retraining

MuleNet ran on l1cc inside the official prebuilt s390x JupyterLab image against the AMLworld HI-Small CSV, capped at 2,000,000 rows because l1cc has 7 GB RAM. XGBoost 3.4.1 and scikit-learn 1.9.0 trained on the same chronological split: 1.6 million train rows and 400,000 holdout rows. XGBoost reached PR-AUC 0.00567 / ROC-AUC 0.77193; scikit-learn HistGradientBoosting reached PR-AUC 0.00317 / ROC-AUC 0.69887. This is a highly imbalanced receiver-mule task; collaboration and oracle PR-AUC are not computed. The selected XGBoost model exported 149,128 receiver-account scores. The exact command and output are in `evidence/mulenet_l1cc.log`; the metrics and versions are in `results/mulenet_report.json`.

SpellBreaker was then retrained on l1cc with 20,000 customers in 17 seconds. The report confirms that all 149,128 real XGBoost receiver scores were sampled with replacement across the synthetic transfer sessions and used as the `receiver_mule_score` training feature. The retrained model reports PR-AUC 0.8805, ROC-AUC 0.9708, and `trained_on=s390x`. Its model report and curves are in `results/`; the service was rebuilt from that model and the post-deploy server p99 is 25.23 ms. Both deployment and training sync scripts exclude `data/`, preserving the 454 MB dataset on l1cc.

## Platform security evidence

`evidence/container.txt` records the inspected container user and hardening flags. `evidence/cpu_features.txt` reports the CPACF MSA feature and the literal NNPA line count (`1`); this means NNPA is exposed, not that Telum inference ran. No model was compiled with or executed through zDLC, so Telum on-chip inference via zDLC remains a production path. `evidence/crypto.txt` records OpenSSL SHA-256 speed on LinuxONE and a synthetic HMAC-SHA256 token generated by Python `hmac`/`hashlib` using CPython's `_hashlib` provider; the random demo key was ephemeral and not saved. The separate token export utility omits raw account identifiers and requires an out-of-band HMAC key. `evidence/genai_prompt_sample.txt` shows that the local model prompt includes only a scam-type string and contains no names, account numbers or raw transaction data.
