#!/usr/bin/env python3
"""Verify INSTITUTIONAL_OWNER_APPROVAL_SECRET matches committed owner approval evidence."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HMAC_MESSAGE = b"INSTITUTIONAL_CLOSED"
EVIDENCE_PATH = ROOT / "docs/INSTITUTIONAL_OWNER_APPROVAL_EVIDENCE.json"
OUTPUT_PATH = ROOT / "docs/INSTITUTIONAL_OWNER_SECRET_VERIFY.json"


def _prefix(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def main() -> int:
    secret = os.environ.get("INSTITUTIONAL_OWNER_APPROVAL_SECRET", "").strip()
    if not secret:
        payload = {
            "verified_at": datetime.now(UTC).isoformat(),
            "status": "FAILED",
            "reason": "INSTITUTIONAL_OWNER_APPROVAL_SECRET not set",
        }
        OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 1

    if not EVIDENCE_PATH.exists():
        payload = {
            "verified_at": datetime.now(UTC).isoformat(),
            "status": "FAILED",
            "reason": f"missing evidence file: {EVIDENCE_PATH.relative_to(ROOT)}",
        }
        OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 1

    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    expected_token_prefix = str(evidence.get("hmac", {}).get("token_sha256_prefix") or "")
    expected_secret_prefix = str(evidence.get("hmac", {}).get("secret_sha256_prefix") or "")

    token = hmac.new(secret.encode(), HMAC_MESSAGE, hashlib.sha256).hexdigest()
    token_prefix = _prefix(token)
    secret_prefix = _prefix(secret)

    os.environ["INSTITUTIONAL_OWNER_APPROVAL_TOKEN"] = token
    from cap646.closure_guard import ClosureGuardError, assert_owner_approval_for_closure

    guard_ok = False
    guard_error: str | None = None
    try:
        assert_owner_approval_for_closure(requested_status="INSTITUTIONAL_CLOSED")
        guard_ok = True
    except ClosureGuardError as exc:
        guard_error = str(exc)

    token_match = token_prefix == expected_token_prefix
    secret_match = secret_prefix == expected_secret_prefix
    status = "VERIFIED" if token_match and secret_match and guard_ok else "FAILED"

    payload = {
        "verified_at": datetime.now(UTC).isoformat(),
        "status": status,
        "hmac": {
            "algorithm": "HMAC-SHA256",
            "message": HMAC_MESSAGE.decode(),
            "token_sha256_prefix": token_prefix,
            "expected_token_sha256_prefix": expected_token_prefix,
            "token_prefix_match": token_match,
            "secret_sha256_prefix": secret_prefix,
            "expected_secret_sha256_prefix": expected_secret_prefix,
            "secret_prefix_match": secret_match,
            "ephemeral_secret_generated": evidence.get("hmac", {}).get("ephemeral_secret_generated"),
        },
        "closure_guard": {
            "assert_owner_approval_for_closure": guard_ok,
            "error": guard_error,
        },
        "evidence_source": str(EVIDENCE_PATH.relative_to(ROOT)),
    }
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if status == "VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
