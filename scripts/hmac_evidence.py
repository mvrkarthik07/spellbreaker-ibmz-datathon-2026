#!/usr/bin/env python3
"""Emit a safe synthetic demonstration of HMAC tokenization and OpenSSL runtime."""
import secrets
import ssl
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.mule_share import receiver_token

print("implementation=hmac.new(key, account_utf8, hashlib.sha256)")
print(f"python_openssl={ssl.OPENSSL_VERSION}")
print(f"hashlib_sha256_provider={hashlib.sha256().__class__.__module__}")
print("input=synthetic receiver identifier DEMO-RECEIVER-001")
print(f"token={receiver_token('DEMO-RECEIVER-001', secrets.token_bytes(32))}")
print("key=ephemeral 256-bit random value; not printed or saved")
