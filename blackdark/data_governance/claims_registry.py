"""Claims registry — DSR-022."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from blackdark.data_governance._paths import CLAIMS_REGISTRY_PATH, ensure_governance_dirs


def register_claim(
    *,
    claim: str,
    evidence_ref: str,
    version: str,
    valid_until: str | None = None,
    test_ref: str | None = None,
) -> dict[str, Any]:
    ensure_governance_dirs()
    row = {
        "claim_id": f"claim_{uuid4().hex[:12]}",
        "claim": claim,
        "evidence_ref": evidence_ref,
        "version": version,
        "valid_until": valid_until,
        "test_ref": test_ref,
        "status": "valid" if not valid_until or valid_until > datetime.now(UTC).isoformat() else "expired",
        "registered_at": datetime.now(UTC).isoformat(),
    }
    with CLAIMS_REGISTRY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row
