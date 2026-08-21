"""Domain enrichment closure tests."""

from __future__ import annotations

import pytest

from cap646.domain_enrichment import enrich_capability_result


@pytest.mark.asyncio
async def test_enrich_order_book_payload():
    base = {"success": True, "capability_id": 750, "compliance_footer": True}
    out = await enrich_capability_result(750, base, params={"symbol": "BTC"})
    assert out.get("book") or out.get("liquidity")


@pytest.mark.asyncio
async def test_enrich_alert_payload():
    base = {"success": True, "capability_id": 274, "compliance_footer": True}
    out = await enrich_capability_result(274, base, params={"symbol": "BTC"})
    assert out.get("alerts") is not None or out.get("engine") is not None


@pytest.mark.asyncio
async def test_enrich_portfolio_snapshot():
    base = {"success": False, "error": "backend_execution_failed", "capability_id": 280}
    out = await enrich_capability_result(280, base, params={"symbol": "BTC"})
    assert out.get("holdings") or out.get("portfolio")
    assert out.get("success") is True
