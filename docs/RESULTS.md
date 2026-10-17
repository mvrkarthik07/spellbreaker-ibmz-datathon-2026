# Results

Synthetic victim-side simulator, temporal holdout; not a real-world effectiveness estimate.

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

The model was trained directly on l1cc (s390x) with 20,000 customers in 13 seconds. Test PR-AUC was 0.889, ROC-AUC 0.974, recall at T1 0.783, and legit interruption 1.10%. The report records age-band fairness, per-type recall and the generation parameters. `evidence/train_l1cc.log`, `results/model_report.json`, and `results/curves.json` contain the raw run artifacts.

The service runs in a non-root Ubuntu 24.04 container using the same Ubuntu-prebuilt scikit-learn 1.4.1.post1 stack as the host training venv. The LinuxONE benchmark ran 10,000 `/score` requests at concurrency 16 on localhost with one Uvicorn worker:

| Duration | Throughput | Server p50 | Server p95 | Server p99 | Client p50 | Client p99 |
|---:|---:|---:|---:|---:|---:|---:|
| 47.17 s | 212.00 req/s | 23.04 ms | 24.05 ms | 25.24 ms | 74.68 ms | 102.61 ms |

The server-side p99 meets the <50 ms target. Client round-trip latency includes queueing and transport. Full results are in `results/bench.json` and `evidence/bench.txt`; §9 platform, CPU, container, package, health and crypto evidence is in `evidence/`. The executed LinuxONE notebook verifies a live CRITICAL scoring response and asynchronous case note in `evidence/SpellBreaker_on_LinuxONE.executed.ipynb`.

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
