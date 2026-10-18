# Privacy

The bank UI sends a synthetic customer ID, recipient name and account number, amount, funding account, a pasted-account indicator, and a 0–1 typing-speed summary. The recipient name is not a model-vector field. The account string is used to look up its receiver-mule score; only that score enters the model vector. Recipient fields remain in the ordinary decision/dashboard context, while the `/trace` viewer is redacted. The UI does not collect call status or link-click history. It never sends caller numbers, call audio, contacts, messages, clipboard contents, raw keystroke timings, or location.

The prototype processes requests in the LinuxONE service. This is a prototype deployment, not a production security certification. No external AI API is configured. Case notes are prepared asynchronously from a fixed decision fact sheet; the deployed service uses a deterministic template because Granite did not pass its validation evaluation.
