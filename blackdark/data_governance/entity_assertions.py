"""Entity assertion contracts — DSR-011, D-09, D-20."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from blackdark.data_governance._paths import ENTITY_ASSERTIONS_PATH, ensure_governance_dirs

CONFLICT_STATES = ("CONFIRMED", "CONFLICTED", "LOW_CONFIDENCE", "EXPIRED", "PENDING")


def record_entity_assertion(
    *,
    entity_type: str,
    entity_id: str,
    assertion: str,
    source: str,
    confidence: float,
    evidence_ref: str | None = None,
    expires_at: str | None = None,
    conflict_state: str = "PENDING",
) -> dict[str, Any]:
    ensure_governance_dirs()
    if conflict_state not in CONFLICT_STATES:
        conflict_state = "PENDING"
    row = {
        "assertion_id": f"asrt_{uuid4().hex[:12]}",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "assertion": assertion,
        "source": source,
        "confidence": confidence,
        "evidence_ref": evidence_ref,
        "validity": "active",
        "expires_at": expires_at,
        "conflict_state": conflict_state,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    with ENTITY_ASSERTIONS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row


def is_displayable_assertion(assertion: dict[str, Any]) -> bool:
    state = assertion.get("conflict_state", "PENDING")
    return state == "CONFIRMED" and float(assertion.get("confidence", 0)) >= 0.7
