"""Sonar PR #362 — behavioral coverage for Batch03 new-code lines (<80% gate)."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.asyncio
async def test_gateway_execute_denied_stamps_canonical_ids() -> None:
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(
        125,
        user={"tier": "free", "email": "sonar-free-125@blackdark.local"},
        params={"symbol": "BTC", "tier": "free"},
    )
    assert result["success"] is False
    assert result["error"] == "entitlement_denied"
    assert result["requested_capability_id"] == 125
    assert result["canonical_capability_id"] == 85
    assert result["entitlement"]["required_tier"] == "pro"


@pytest.mark.asyncio
async def test_gateway_execute_allowed_stamps_gateway_metadata() -> None:
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(
        106,
        user={"tier": "free", "email": "sonar-free-106@blackdark.local"},
        params={"symbol": "BTC", "tier": "free"},
    )
    assert result["success"] is True
    gateway = result["gateway"]
    assert gateway["requested_capability_id"] == 106
    assert gateway["canonical_capability_id"] == 63
    assert gateway["audited"] is True


@pytest.mark.asyncio
async def test_batch03_execute_rejects_out_of_spine() -> None:
    from cap646.batch03_production import execute

    with pytest.raises(ValueError, match="not in batch03 production spine"):
        await execute(99, params={"symbol": "BTC"})


@pytest.mark.asyncio
async def test_batch03_execute_rejects_unmapped_in_range() -> None:
    from cap646.batch03_production import execute

    with pytest.raises(ValueError, match="batch03: unmapped capability"):
        await execute(103, params={"symbol": "BTC"})


def test_wrap_stamps_reused_link_catalog_link() -> None:
    from cap646.dedicated_common import wrap

    payload: dict[str, Any] = {
        "success": True,
        "catalog_link": {
            "duplicate_of": 63,
            "classification": "REUSED-LINK",
        },
    }
    out = wrap(
        106,
        expected_surface={106: "data_provenance_hot_storage"},
        symbol="BTC",
        payload_key="data",
        payload=payload,
    )
    assert out["classification"] == "REUSED-LINK"
    assert out["catalog_link"]["duplicate_of"] == 63
