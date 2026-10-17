"""HMAC pseudonyms for receiver-score sharing; the key is supplied out of band."""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Optional


def receiver_token(account: str, key: Optional[bytes] = None) -> str:
    """Return a stable, non-reversible token without exposing an account identifier."""
    secret = key if key is not None else os.environ.get("SPELLBREAKER_MULE_HMAC_KEY", "").encode()
    if not secret:
        raise ValueError("Set SPELLBREAKER_MULE_HMAC_KEY through the approved secret store")
    normalized = str(account).strip().encode("utf-8")
    if not normalized:
        raise ValueError("account identifier must not be empty")
    return hmac.new(secret, normalized, hashlib.sha256).hexdigest()
