#!/usr/bin/env python3
"""Evaluate validated case notes on 50 synthetic HIGH/CRITICAL service decisions."""
import argparse
import concurrent.futures
import json
import statistics
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def get_json(url):
    with urlopen(url, timeout=15) as response:
        return json.loads(response.read())


def post_json(url, payload):
    request = Request(url, data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--max-attempts", type=int, default=150)
    parser.add_argument("--concurrency", type=int, default=16)
    args = parser.parse_args()
    base = args.url.rstrip("/")
    decisions = []
    attempts = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = []
        while len(decisions) < args.count and attempts < args.max_attempts:
            attempts += 1
            attempt = attempts
            payload = {
                "customer_id": f"C-GENAI-EVAL-{attempt:03d}",
                "payee_account": f"MB-GENAI-EVAL-{attempt % 17:02d}",
                "payee_name": "Synthetic review recipient",
                "amount": float((attempt % 5 + 1) * 5000),
                "source_pot": "savings",
                "flags": {"on_call": True, "pasted_account": True, "rushed_score": 0.91},
            }
            futures.append(pool.submit(post_json, base + "/score", payload))
            # Flush bounded batches so the service's async notes overlap without
            # creating an unbounded local queue.
            if len(futures) >= args.concurrency or attempt == args.max_attempts:
                for future in concurrent.futures.as_completed(futures):
                    decision = future.result()
                    if decision.get("level") in {"HIGH", "CRITICAL"}:
                        decisions.append(decision)
                    if len(decisions) >= args.count:
                        break
                futures.clear()

    if len(decisions) < args.count:
        raise RuntimeError(f"Collected {len(decisions)} HIGH/CRITICAL decisions; expected {args.count} in {attempts} attempts")

    observed_by_id = {}
    deadline = time.monotonic() + 125
    pending = {d["decision_id"] for d in decisions[:args.count]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        while pending and time.monotonic() < deadline:
            ids = list(pending)
            cases = list(pool.map(lambda did: get_json(base + "/case/" + did), ids))
            for did, case in zip(ids, cases):
                if case.get("status") == "pending":
                    continue
                observed_by_id[did] = {
                    "decision_id": did, "runtime": case.get("runtime"),
                    "validated": bool(case.get("validated")),
                    "fallback_reason": case.get("fallback_reason"),
                    "generation_ms": case.get("generation_ms"),
                }
                pending.remove(did)
            print(f"completed={args.count - len(pending)}/{args.count} pending={len(pending)}", flush=True)
            if pending:
                time.sleep(0.5)

    observed = []
    for decision in decisions[:args.count]:
        did = decision["decision_id"]
        observed.append(observed_by_id.get(did, {
            "decision_id": did, "runtime": "template (fallback)",
            "validated": False, "fallback_reason": "case_note_timeout", "generation_ms": None,
        }))
    times = [x["generation_ms"] for x in observed if isinstance(x.get("generation_ms"), (int, float))]
    validated = sum(x["validated"] for x in observed)
    by_reason = {}
    for item in observed:
        reason = item["fallback_reason"] or "accepted"
        by_reason[reason] = by_reason.get(reason, 0) + 1
    result = {
        "evaluation": "synthetic HIGH/CRITICAL decisions scored through the live LinuxONE service",
        "requested_decisions": args.count,
        "evaluated_decisions": len(observed),
        "attempts": attempts,
        "acceptance_rate": validated / len(observed),
        "accepted": validated,
        "fallbacks": len(observed) - validated,
        "mean_generation_time_ms": statistics.fmean(times) if times else None,
        "mean_generation_time_scope": "all completed case-note jobs including validator/template fallbacks; excludes case-note timeouts",
        "fallback_reasons": by_reason,
        "cases": observed,
        "granite_default_threshold": 0.60,
    }
    path = ROOT / "results/genai_eval.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
