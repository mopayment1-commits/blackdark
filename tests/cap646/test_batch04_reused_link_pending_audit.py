"""Blocker contracts for batch04 canonical pairs (#159, #183) — owner final decisions."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_blocker_159_not_complete_no_reused_link():
    from cap646.runtime import execute_capability

    result = await execute_capability(
        159,
        skip_entitlement=True,
        params={"symbol": "BTC", "tier": "pro"},
    )
    assert result["success"] is True
    assert result.get("classification") == "NOT_COMPLETE"
    assert result.get("production_spine") == "batch04"
    link = result.get("catalog_link")
    assert link is None or link.get("classification") != "REUSED-LINK"
    assert result.get("blocker") == "BLOCKER-159-103"
    assert result["api_data_platform"]["canonical_overlap"] == 103
    assert result["api_data_platform"]["canonical_status"] == "OVERLAP-PARTIAL"
    assert result["api_data_platform"]["institutional_api"] == "/api/institutional"


@pytest.mark.asyncio
async def test_blocker_183_distinct_no_reused_link_to_130():
    from cap646.runtime import execute_capability

    result = await execute_capability(
        183,
        skip_entitlement=True,
        params={"symbol": "BTC", "amount_usd": 2_000_000, "flow_direction": "exchange_inflow", "tier": "pro"},
    )
    assert result["success"] is True
    assert result.get("production_spine") == "batch04"
    assert result.get("catalog_link") is None
    wt = result["whale_transaction"]
    assert wt["distinct_from_130"]["reused_link"] is False
    assert wt["whale_tier"] == "mega_whale"
    assert "catalog_link" not in wt


def test_acceptance_marks_159_not_complete():
    import json
    from pathlib import Path

    doc = json.loads(Path("docs/BATCH04_ACCEPTANCE_151_200.json").read_text(encoding="utf-8"))
    row = next(r for r in doc["rows"] if r["capability_id"] == 159)
    assert row["status"] == "NOT_COMPLETE"
    assert row.get("pending_canonical_audit") == "BLOCKER-159-103"
