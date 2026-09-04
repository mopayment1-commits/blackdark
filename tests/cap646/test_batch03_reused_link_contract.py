"""Type-4 semantic contract tests for Batch03 REUSED-LINK pairs (#106/#107/#110/#125)."""

from __future__ import annotations

import pytest

REUSED_LINK_PAIRS = {
    106: 63,
    107: 64,
    110: 69,
    125: 85,
}
SYMBOLS = ["BTC", "ETH", "SOL", "AVAX", "DOGE"]


@pytest.mark.parametrize("symbol", SYMBOLS)
@pytest.mark.parametrize("duplicate_id,canonical_id", list(REUSED_LINK_PAIRS.items()))
@pytest.mark.asyncio
async def test_reused_link_catalog_contract(duplicate_id: int, canonical_id: int, symbol: str):
    from cap646.runtime import execute_capability

    dup = await execute_capability(
        duplicate_id,
        skip_entitlement=True,
        params={"symbol": symbol, "tier": "pro"},
    )
    canon = await execute_capability(
        canonical_id,
        skip_entitlement=True,
        params={"symbol": symbol, "tier": "pro"},
    )

    assert dup["success"] is True, dup
    assert canon["success"] is True, canon
    assert dup["surface"] == canon["surface"]
    link = dup.get("catalog_link") or {}
    assert link.get("duplicate_of") == canonical_id
    assert link.get("classification") == "REUSED-LINK"
    assert dup.get("classification") == "REUSED-LINK"
    assert dup.get("production_spine") == "batch03"
