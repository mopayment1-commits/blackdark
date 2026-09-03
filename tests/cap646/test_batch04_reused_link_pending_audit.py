"""Pending canonical audit contracts for batch04 REUSED-LINK candidates (#159, #183)."""

from __future__ import annotations

import pytest

PENDING_CANONICAL_AUDIT = frozenset({159, 183})


@pytest.mark.parametrize("capability_id", sorted(PENDING_CANONICAL_AUDIT))
@pytest.mark.asyncio
async def test_pending_canonical_audit_contract(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(
        capability_id,
        skip_entitlement=True,
        params={"symbol": "BTC", "tier": "pro"},
    )
    assert result["success"] is True
    link = result.get("catalog_link") or {}
    assert link.get("classification") == "REUSED-LINK"
    if capability_id == 159:
        assert link.get("duplicate_of") == 103
        assert result["api_data_platform"]["institutional_api"] == "/api/institutional"
    if capability_id == 183:
        assert link.get("duplicate_of") == 130
        assert result["whale_transaction"]["risk_score"] >= 0
    assert result["production_spine"] == "batch04"
    # Build phase: never PRODUCTION-ALIGNED on batch04 independent spine
    assert result.get("classification") != "PRODUCTION-ALIGNED" or capability_id not in PENDING_CANONICAL_AUDIT


@pytest.mark.parametrize("capability_id", sorted(PENDING_CANONICAL_AUDIT))
def test_acceptance_marks_not_complete(capability_id: int):
    import json
    from pathlib import Path

    doc = json.loads(Path("docs/BATCH04_ACCEPTANCE_151_200.json").read_text(encoding="utf-8"))
    row = next(r for r in doc["rows"] if r["capability_id"] == capability_id)
    assert row["status"] == "NOT_COMPLETE"
    assert row.get("pending_canonical_audit") in {"BLOCKER-159-103", "BLOCKER-183-130"}
