# Architecture

```mermaid
flowchart LR
  B[Merlion Bank app] -->|transfer + minimal flags| API[FastAPI on LinuxONE]
  API --> F[Live feature builder]
  F --> M1[M1 HistGradientBoosting risk]
  F --> M2[M2 scam typology classifier]
  F --> M3[M3 receiver mule score lookup]
  M1 --> P[Policy: allow, ask, hold]
  M2 --> P
  M3 --> P
  P --> B
  P -. async .-> G[Local case note template]
  API --> D[Dashboard]
```

| Component | Responsibility |
|---|---|
| `ml/spellbreaker_train.py` | Synthetic manipulation typology training, time split, fairness and ablation reporting |
| `service/features.py` | Runtime transfer features and recent-history counts |
| M1 | Estimate manipulated transfer risk |
| M2 | Predict scam type for targeted interruption |
| M3 | Receiver account risk lookup (MuleNet scores from the supplied AMLworld subset) |
| `service/policy.py` | Map calibrated thresholds to intervention language and action |
| `service/genai.py` | Local deterministic analyst note fallback |
| Web apps | Synthetic bank transfer simulation and analyst dashboard |

The target hybrid comprises three predictive signals plus one generative component. This run includes MuleNet scores from AMLworld HI-Small. Case notes use the deterministic template because local Granite outputs failed factuality validation.
