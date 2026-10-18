# SpellBreaker — three-minute demo script

**Runtime:** 3:00. **Setup:** Open the live Merlion Bank page and analyst dashboard in separate tabs. Keep the terminal ready. Use `ssh l1cc 'uname -m; curl -fsS localhost:8000/health'` for the LinuxONE proof, then `cat evidence/bench.txt` for the captured benchmark. All customer and account details below are synthetic. The demo shows a scored review; do not click a transfer action that proceeds.

| Time | On screen / action | Narration |
|---|---|---|
| 0:00–0:20 | Start on the Merlion Bank home screen. | “In Singapore, most scam losses now come from transfers made by the real account holder. The customer is genuine; the scammer is influencing the decision. SpellBreaker looks for those pressure patterns while the customer is making a transfer.” |
| 0:20–0:40 | Click **New transfer**. Point out that there is no scenario menu. Choose **Savings**, leave **Add a new recipient**, and enter the synthetic recipient **Secure Govt Account**. | “This is the regular transfer form. There are no preset journeys behind the screen. The score comes from the submitted transfer details and the available behavioural and receiver-risk signals.” |
| 0:40–1:05 | Paste `MB-778-201-9931` into the account field; enter **20,000**. Point out the S$85,000 available balance. Click **Review transfer**. | “For this recorded example, I’m entering a synthetic test transfer: twenty thousand dollars from savings. Pasting the account is recorded as one risk signal. This account is a known synthetic fixture in our demo data; the recipient name itself is not used by the model.” |
| 1:05–1:30 | Show the **CRITICAL** result, hold message, reason list, and decision reference. Do not proceed. | “The service returns a critical hold. Here the model points to receiver-mule behaviour, an amount far above the customer’s usual transfer, savings being used, and the pasted account number. Merlion Bank asks the customer to stop and verify. A critical hold has no continue action.” |
| 1:30–1:45 | Click **Cancel transfer**. | “The review is cancelled. It does not appear as a completed payment in recent activity.” |
| 1:45–2:05 | Switch to the analyst dashboard and select the latest decision. Show the risk, reasons, and reference. | “The fraud analyst can trace the same decision and inspect its model evidence. The trace omits names, account numbers, and raw feature vectors.” |
| 2:05–2:30 | Show the architecture flowchart or model evidence panel. | “The predictive stack combines scikit-learn risk and scam-type models with the XGBoost receiver-mule score. That receiver model was trained on AMLworld data; the victim-side training data are synthetic. These are prototype evaluation results, not a claim of proven bank-wide performance.” |
| 2:30–2:48 | Show the l1cc terminal: `uname -m`, `/health`, and the benchmark line. | “Training and serving run on IBM LinuxONE. The live service reports s390x for both the host and training provenance. The latest ten-thousand-request run measured server p99 below twenty-six milliseconds.” |
| 2:48–3:00 | Return to the bank result or end card. | “Case notes are generated separately from scoring. Granite did not pass our format validator in evaluation, so the deployed service uses a deterministic template. We keep that limitation visible while we validate a faster, reliable language-model path.” |

## Demo transaction reference

The synthetic fixture above was scored live on LinuxONE as **CRITICAL**, with `risk=0.9861`, `scam_type=gov_impersonation`, and server-reported latency `5.69 ms` when the rushed signal was 0.15. The same input with the normal UI’s pasted-account signal returned CRITICAL in a second live score. Neither review was confirmed or proceeded. The API response IDs are visible in `/trace`; see `evidence/recipient_model_gap.txt` for the separate recipient-name limitation investigation.

**LLM status:** Granite case notes are asynchronous and optional. The deployed status is `template (fallback)`; evaluation accepted 0/50 notes, and the focused local Granite probe took 83.8 seconds and returned malformed text. Do not narrate Granite as a working sub-10-second feature.
