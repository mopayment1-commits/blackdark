"""Blocker contracts for batch04 canonical pairs (#159, #183) — owner final decisions."""

from __future__ import annotations

import pytest

BLOCKER_IDS = frozenset({159, 183})


@pytest.mark.parametrize("capability_id", sorted(BLOCKER_IDS))
@pytest.mark.asyncio
async def test_blocker_contract_not_complete_no_reused_link(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(
        capability_id,
        skip_entitlement=True,
        params={"symbol": "BTC", "tier": "pro"},
    )
    assert result["success"] is True
    assert result.get("classification") == "NOT_COMPLETE"
    assert result.get("production_spine") == "batch04"
    link = result.get("catalog_link")
    assert link is None or link.get("classification") != "REUSED-LINK"
    if capability_id == 159:
        assert result.get("blocker") == "BLOCKER-159-103"
        assert result["api_data_platform"]["canonical_overlap"] == 103
        assert result["api_data_platform"]["canonical_status"] == "OVERLAP-PARTIAL"
        assert result["api_data_platform"]["institutional_api"] == "/api/institutional"
    if capability_id == 183:
        assert result.get("blocker") == "BLOCKER-183-130"
        assert result["whale_transaction"]["risk_score"] >= 0
        assert "catalog_link" not in result.get("whale_transaction", {})


@pytest.mark.parametrize("capability_id", sorted(BLOCKER_IDS))
def test_acceptance_marks_not_complete(capability_id: int):
    import json
    from pathlib import Path

    doc = json.loads(Path("docs/BATCH04_ACCEPTANCE_151_200.json").read_text(encoding="utf-8"))
    row = next(r for r in doc["rows"] if r["capability_id"] == capability_id)
    assert row["status"] == "NOT_COMPLETE"
    assert row.get("pending_canonical_audit") in {"BLOCKER-159-103", "BLOCKER-183-130"}
