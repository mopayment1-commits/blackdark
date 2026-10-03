"""FIPS 140-3 path state — no false validation claims (FDS-08)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_FIPS_STATUS_NOT_PROVEN = "FIPS_VALIDATION_NOT_PROVEN"
_FIPS_STATUS_EVIDENCE_ATTACHED = "FIPS_VALIDATION_EVIDENCE_ATTACHED"


def _evidence_path() -> Path | None:
    raw = (os.getenv("FIPS_VALIDATION_EVIDENCE_PATH") or "").strip()
    return Path(raw) if raw else None


def fips_state() -> dict[str, Any]:
    provider = (os.getenv("CRYPTO_PROVIDER") or "cryptography-default").strip()
    module_id = (os.getenv("FIPS_MODULE_ID") or "").strip() or None
    evidence = _evidence_path()
    has_evidence = bool(evidence and evidence.is_file())
    status = _FIPS_STATUS_EVIDENCE_ATTACHED if has_evidence else _FIPS_STATUS_NOT_PROVEN
    payload: dict[str, Any] = {
        "status": status,
        "validated": False,
        "provider": provider,
        "module_id": module_id,
        "evidence_path": str(evidence) if evidence else None,
        "external_validation_pending": not has_evidence,
        "false_claim_prevented": status != "FIPS_VALIDATED",
    }
    if has_evidence and evidence:
        try:
            payload["evidence_summary"] = json.loads(evidence.read_text(encoding="utf-8"))
            if payload["evidence_summary"].get("certificate_id"):
                payload["validated"] = True
                payload["status"] = "FIPS_VALIDATED"
                payload["external_validation_pending"] = False
                payload["false_claim_prevented"] = True
        except Exception:
            payload["evidence_summary_error"] = "invalid_evidence_file"
    return payload


def assert_no_false_fips_claim() -> None:
    state = fips_state()
    if (os.getenv("FIPS_VALIDATED", "").strip().lower() in {"1", "true", "yes"}) and not state.get("validated"):
        raise RuntimeError("false_fips_validation_claim_blocked")
