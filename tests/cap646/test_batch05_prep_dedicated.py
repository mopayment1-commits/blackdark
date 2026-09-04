"""Dedicated-backend tests for batch05 capabilities (IDs 201–250)."""

from __future__ import annotations

import pytest

from cap646.batch05_dedicated import (
    BATCH05_DEDICATED_IDS,
    BATCH05_REUSED_LINK_BATCH01_IDS,
    BATCH05_REUSED_LINK_BATCH02_IDS,
    BATCH05_REUSED_LINK_IDS,
    EXPECTED_SURFACE,
    GENERIC_SURFACES,
)
from cap646.batch05_production import BATCH05_IDS

CATALOG_ALIGNED_SAMPLE = frozenset({201, 204, 211, 217, 229, 233, 237, 243, 246, 250})


@pytest.mark.parametrize("capability_id", sorted(BATCH05_DEDICATED_IDS - BATCH05_REUSED_LINK_IDS))
@pytest.mark.asyncio
async def test_batch05_dedicated_surface_and_success(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(
        capability_id,
        skip_entitlement=True,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "tier": "pro",
        },
    )
    assert result["success"] is True, result
    assert result["surface"] == EXPECTED_SURFACE[capability_id], result
    if EXPECTED_SURFACE[capability_id] not in GENERIC_SURFACES:
        assert result["surface"] not in GENERIC_SURFACES
    assert result["production_spine"] == "batch05"
    assert result["backend_module"] == "cap646.batch05_production"


@pytest.mark.parametrize("capability_id", sorted(BATCH05_DEDICATED_IDS))
@pytest.mark.asyncio
async def test_batch05_dedicated_direct_execute(capability_id: int):
    from cap646.batch05_dedicated import execute

    result = await execute(
        capability_id,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        },
    )
    assert result["success"] is True
    assert result["surface"] == EXPECTED_SURFACE[capability_id]


@pytest.mark.parametrize("capability_id", sorted(CATALOG_ALIGNED_SAMPLE))
@pytest.mark.asyncio
async def test_batch05_catalog_aligned_have_domain_payload(capability_id: int):
    from cap646.batch05_dedicated import execute

    result = await execute(capability_id, params={"symbol": "BTC"})
    root = EXPECTED_SURFACE[capability_id]
    assert root in result
    assert result[root]["feature_ref"] == capability_id
    assert result[root]["ok"] is True


def test_batch05_manifest_count():
    assert len(BATCH05_IDS) == 50
    assert len(BATCH05_DEDICATED_IDS) == 50


@pytest.mark.asyncio
async def test_cap214_reused_link_facade():
    from cap646.batch05_dedicated import execute

    result = await execute(214, params={"symbol": "BTC"})
    assert result["classification"] == "REUSED-LINK"
    assert result["catalog_link"]["canonical_spine"] == "batch01"
    assert result["catalog_link"]["binding"] == "cap646/batch01_dedicated.py::_cap214_watchlists"
    assert result.get("count", 0) > 0
    assert len(result["watchlists"].get("items", [])) >= 1


@pytest.mark.asyncio
async def test_cap245_reused_link_facade():
    from cap646.batch05_dedicated import execute

    result = await execute(245, params={"symbol": "BTC"})
    assert result["classification"] == "REUSED-LINK"
    assert result["catalog_link"]["canonical_spine"] == "batch01"
    assert result["catalog_link"]["binding"] == "cap646/batch01_production.py::cap_245"
    assert "freshness_chip" in result or "executable_fresh" in result


@pytest.mark.asyncio
async def test_cap214_245_runtime_via_batch01_legacy_spine():
    """Runtime routes legacy batch01 extension IDs before batch05 (same as #175)."""
    from cap646.runtime import execute_capability

    for capability_id in sorted(BATCH05_REUSED_LINK_BATCH01_IDS):
        result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "BTC"})
        assert result["success"] is True
        assert result["production_spine"] == "batch01"
        assert result["surface"] == EXPECTED_SURFACE[capability_id]


@pytest.mark.asyncio
async def test_cap214_245_batch05_facade_stamps_reused_link():
    from cap646.batch05_production import execute

    for capability_id in sorted(BATCH05_REUSED_LINK_BATCH01_IDS):
        result = await execute(capability_id, params={"symbol": "BTC"})
        assert result["production_spine"] == "batch05"
        assert result["classification"] == "REUSED-LINK"
        assert result["catalog_link"]["canonical_spine"] == "batch01"


@pytest.mark.asyncio
async def test_cap206_228_reused_link_facade():
    from cap646.batch05_dedicated import execute

    for capability_id in sorted(BATCH05_REUSED_LINK_BATCH02_IDS):
        result = await execute(capability_id, params={"symbol": "BTC"})
        assert result["classification"] == "REUSED-LINK"
        assert result["catalog_link"]["canonical_spine"] == "batch02"
        assert result["catalog_link"]["canonical_capability_id"] == 86
        assert result["catalog_link"]["binding"] == "cap646/batch02_production.py::cap_086"
        assert result.get("funding_rate") is not None
        assert result["surface"] == "funding_rate_intelligence"


@pytest.mark.asyncio
async def test_cap232_reused_link_facade():
    from cap646.batch05_dedicated import execute

    result = await execute(232, params={"symbol": "BTC"})
    assert result["classification"] == "REUSED-LINK"
    assert result["catalog_link"]["canonical_spine"] == "batch05"
    assert result["catalog_link"]["canonical_capability_id"] == 205
    assert result["catalog_link"]["binding"] == "cap646/batch05_dedicated.py::_cap205"
    assert result["open_interest_intelligence"]["feature_ref"] == 205
    assert result["open_interest_intelligence"]["ok"] is True


@pytest.mark.asyncio
async def test_cap206_228_runtime_via_batch05_facade_spine():
    from cap646.runtime import execute_capability

    for capability_id in sorted(BATCH05_REUSED_LINK_BATCH02_IDS):
        result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "BTC"})
        assert result["success"] is True
        assert result["production_spine"] == "batch05"
        assert result["classification"] == "REUSED-LINK"
        assert result["surface"] == EXPECTED_SURFACE[capability_id]


@pytest.mark.parametrize("capability_id", sorted(BATCH05_REUSED_LINK_IDS))
def test_reused_link_ids_documented_in_acceptance(capability_id: int):
    import json
    from pathlib import Path

    doc = json.loads(Path("docs/BATCH05_ACCEPTANCE_201_250.json").read_text(encoding="utf-8"))
    row = next(r for r in doc["rows"] if r["capability_id"] == capability_id)
    assert row["status"] == "REUSED-LINK"
    if capability_id in BATCH05_REUSED_LINK_BATCH01_IDS:
        assert row["production_spine"] == "batch01"
    elif capability_id in BATCH05_REUSED_LINK_BATCH02_IDS:
        assert row["production_spine"] == "batch02"
    else:
        assert row["production_spine"] == "batch05"
