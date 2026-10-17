# Privacy

The web demo sends a synthetic customer ID, payee and transfer details, plus `on_call`, `pasted_account`, `rushed_score`, and `clicked_flagged_link_recent` signals. It never sends caller numbers, call audio, contacts, messages, clipboard contents, raw keystroke timings or location. Only a 0–1 timing summary is kept by the client.

The prototype processes requests in its local API process. Deployment to a LinuxONE VM is pending; the claim that no data leaves the bank platform is a design goal, not a production security certification. No external AI API is configured. Case notes receive a decision summary and use a deterministic template.
