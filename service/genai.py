"""Fact-sheet-only local Granite notes with deterministic validation and fallback."""
from __future__ import annotations

import json
import os
import re
import threading
import time
from urllib.request import Request, urlopen

LLM_URL = os.environ.get("SPELLBREAKER_LLM_URL", "").rstrip("/")
GENAI_MODE = os.environ.get("SPELLBREAKER_GENAI_MODE", "template").strip().lower()
CASE_FIELDS = ("level", "risk", "scam_type", "reasons", "amount_band", "age_band")
_LLM_GATE = threading.Lock()
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?%?")
_IDENTIFIER_RE = re.compile(
    r"(?i)(?:[\w.+-]+@[\w.-]+\.[a-z]{2,}|\b\d{8,}\b|"
    r"\b(?:account|acct|customer|client|payee|recipient)\s*(?:number|no\.?|id)\s*[:#-]?\s*[a-z0-9-]+|"
    r"\b[A-Z]{1,5}[- ]\d{4,}\b)"
)
_SCAM_ALIASES = {
    "gov_impersonation": ("gov impersonation", "government impersonation", "government scam"),
    "investment": ("investment scam", "investment"),
    "job": ("job scam", "job"),
    "phishing_led": ("phishing led", "phishing-led", "phishing scam"),
}


def runtime_status() -> str:
    return "granite (validated)" if GENAI_MODE == "granite" and LLM_URL else "template (fallback)"


RUNTIME = runtime_status()


def _risk_percent(case: dict) -> str:
    return f"{float(case.get('risk', 0.0)) * 100:.1f}%"


def _reasons(case: dict) -> list[str]:
    reasons = case.get("reasons") or []
    if not isinstance(reasons, list):
        return []
    return [str(reason).strip() for reason in reasons[:8] if str(reason).strip()]


def _expected_lines(case: dict) -> list[str]:
    level = str(case.get("level", "HIGH")).upper()
    amount = str(case.get("amount_band", "undisclosed amount"))
    age = str(case.get("age_band", "unknown"))
    scam_type = str(case.get("scam_type", "unknown"))
    reason_text = "; ".join(_reasons(case)) or "an unusual transfer pattern"
    return [
        f"What happened: A {level} transfer in {amount} was flagged at {_risk_percent(case)} risk.",
        f"Why suspicious: {reason_text}; age band: {age}.",
        f"Likely scam: {scam_type}",
        "Next step: Independently verify the transfer using the bank's registered channel.",
    ]


def validate_note(note: str, case: dict) -> tuple[bool, str | None]:
    """Accept only the exact four-line, decision-grounded output template."""
    lines = [line.strip() for line in str(note or "").strip().splitlines() if line.strip()]
    labels = ("What happened:", "Why suspicious:", "Likely scam:", "Next step:")
    if len(lines) != 4 or any(not line.startswith(label) for line, label in zip(lines, labels)):
        return False, "missing_or_misordered_line"

    predicted = str(case.get("scam_type", "unknown")).strip().lower()
    predicted_line = lines[2].split(":", 1)[1].strip().lower()
    if predicted_line != predicted:
        return False, "predicted_scam_type_mismatch"
    text = "\n".join(lines).lower()
    for scam_type, aliases in _SCAM_ALIASES.items():
        if scam_type != predicted and any(alias in text for alias in aliases):
            return False, "additional_scam_type"

    fact_sheet = {
        "level": str(case.get("level", "HIGH")),
        "risk_percent": _risk_percent(case),
        "predicted_scam_type": predicted,
        "exact_reasons": _reasons(case),
        "amount_band": str(case.get("amount_band", "undisclosed amount")),
        "age_band": str(case.get("age_band", "unknown")),
    }
    facts_text = json.dumps(fact_sheet, ensure_ascii=False)
    permitted_numbers = set(_NUMBER_RE.findall(facts_text))
    output_numbers = set(_NUMBER_RE.findall("\n".join(lines)))
    if _IDENTIFIER_RE.search("\n".join(lines)):
        return False, "name_or_account_identifier"
    if not output_numbers.issubset(permitted_numbers):
        return False, "number_not_in_fact_sheet"

    expected_lines = _expected_lines(case)
    allowed_titlecase = set(re.findall(r"\b[A-Z][a-z]{2,}\b", facts_text + "\n".join(expected_lines)))
    unexpected_titlecase = {
        word for word in re.findall(r"\b[A-Z][a-z]{2,}\b", "\n".join(lines))
        if word not in allowed_titlecase
    }
    if unexpected_titlecase:
        return False, "name_or_account_identifier"
    if lines != expected_lines:
        return False, "unsupported_or_changed_fact"
    return True, None


def template_note(case: dict) -> str:
    reasons = ", ".join(_reasons(case)) or "an unusual transfer pattern"
    return (
        f"A {str(case.get('level', 'HIGH')).lower()} risk transfer of "
        f"{case.get('amount_band', 'an undisclosed amount')} was detected. "
        f"Indicators include {reasons}. The likely typology is "
        f"{str(case.get('scam_type', 'unknown')).replace('_', ' ')}. "
        "Call the customer using the bank's registered number; ask them to end any active call and independently verify the recipient. "
        "If the customer insists and coercion remains apparent, consider whether a Protection from Scams Act escalation is warranted."
    )


def _fallback(case: dict, reason: str, started: float) -> dict:
    return {
        "note": template_note(case),
        "runtime": "template (fallback)",
        "validated": False,
        "fallback_reason": reason,
        "generation_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def generate_note(case: dict) -> dict:
    started = time.perf_counter()
    if GENAI_MODE != "granite":
        return _fallback(case, "template_default_mode", started)
    if not LLM_URL:
        return _fallback(case, "granite_sidecar_not_configured", started)
    if not _LLM_GATE.acquire(blocking=False):
        return _fallback(case, "granite_busy", started)

    try:
        # This allow-list is the complete fact sheet sent to the local model.
        payload = {
            "level": str(case.get("level", "HIGH")),
            "risk_percent": _risk_percent(case),
            "predicted_scam_type": str(case.get("scam_type", "unknown")),
            "exact_reasons": _reasons(case),
            "amount_band": str(case.get("amount_band", "undisclosed amount")),
            "age_band": str(case.get("age_band", "unknown")),
        }
        request = Request(
            LLM_URL + "/generate",
            data=json.dumps(payload, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=90) as response:
                note = json.loads(response.read()).get("note", "")
        except Exception as exc:
            return _fallback(case, f"granite_request_{type(exc).__name__}", started)

        accepted, reason = validate_note(note, case)
        if not accepted:
            return _fallback(case, f"validator_{reason}", started)
        return {
            "note": note,
            "runtime": "granite (validated)",
            "validated": True,
            "fallback_reason": None,
            "generation_ms": round((time.perf_counter() - started) * 1000, 3),
        }
    finally:
        _LLM_GATE.release()
