# How a transfer gets checked

The bank sends a transfer for a quick check. SpellBreaker looks at the context, weighs three risk signals, and sends a clear next step back to the app. Case notes happen in the background, so they do not slow down the score.

```mermaid
flowchart LR
  bank[Bank app] --> score[SpellBreaker on LinuxONE]
  score --> context[Gather payee and recent transfer context]
  context --> risk[Transfer risk · scikit-learn]
  context --> type[Likely scam type · scikit-learn]
  context --> mule[Receiver risk · XGBoost score]
  risk --> action[Choose next step: allow, ask, pause or hold]
  type --> action
  mule --> action
  action --> reply[Send a clear response to the bank app]
  reply --> dashboard[Fraud analyst dashboard]
  action -. "High or critical · background" .-> note[Prepare a case note]
  note --> check{Granite note passes fact checks?}
  check -- Yes --> granite[Show the validated note]
  check -- No --> fallback[Use the ready-made note]
  granite --> dashboard
  fallback --> dashboard

  classDef bank fill:#eaf5f3,stroke:#438a88,color:#183b3a
  classDef service fill:#edf4f8,stroke:#4c819a,color:#1d3342
  classDef model fill:#f6f2fb,stroke:#8068a5,color:#33294a
  classDef decision fill:#fff8e8,stroke:#c49a42,color:#493915
  classDef async fill:#fffaf1,stroke:#c59a52,color:#493915
  class bank,reply bank
  class score,context,dashboard service
  class risk,type,mule model
  class action decision
  class note,check,granite,fallback async
```

Case notes are only for high or critical decisions and use approved facts. Names, account numbers and raw transaction IDs are left out. Granite is optional; a note that fails validation falls back to the ready-made version.
