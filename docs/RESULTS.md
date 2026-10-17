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

```json
{
  "requests": 100,
  "concurrency": 8,
  "duration_s": 4.511672082997393,
  "rps": 22.16473142559678,
  "client_round_trip_ms": {
    "p50": 351.54283299925737,
    "p95": 370.18841700046323,
    "p99": 384.98162501491606
  },
  "server_latency_ms": {
    "p50": 347.7268749848008,
    "p95": 356.29812499973923,
    "p99": 368.7394170265179
  }
}
```
