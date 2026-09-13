"""Deep institutional tests — batch01 IDs 1–25 (v6 §2.1 semantic assertions)."""

from __future__ import annotations

import pytest

from cap646.batch01_closure_spec import BATCH01_DOMAIN_PAYLOAD_KEYS, BATCH01_OFFICIAL_RANGE, expected_surface
from cap646.batch01_production import execute

STANDARD_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "tier": "pro",
}


@pytest.mark.parametrize("capability_id", list(BATCH01_OFFICIAL_RANGE))
@pytest.mark.asyncio
async def test_batch01_domain_payload(capability_id: int):
    """G03 — goal-specific domain keys present (not generic invoke shell)."""
    result = await execute(capability_id, params=STANDARD_PARAMS)
    assert result["success"] is True, result
    assert result["surface"] == expected_surface(capability_id)
    keys = BATCH01_DOMAIN_PAYLOAD_KEYS[capability_id]
    assert any(k in result for k in keys), (capability_id, keys, list(result.keys()))


@pytest.mark.parametrize("capability_id", list(BATCH01_OFFICIAL_RANGE))
@pytest.mark.asyncio
async def test_batch01_production_spine(capability_id: int):
    """G02/G05 — batch01 dedicated spine, not generated official_batch invoke."""
    result = await execute(capability_id, params=STANDARD_PARAMS)
    assert result["backend_module"] == "cap646.batch01_production"
    assert result["binding_source"] == "explicit_option_a"
    assert result["official_batch"] == "batch01"
    assert result.get("production_spine") == "batch01"


@pytest.mark.parametrize("capability_id", list(BATCH01_OFFICIAL_RANGE))
@pytest.mark.asyncio
async def test_batch01_provenance_and_evidence(capability_id: int):
    """G08/G11/G13 — provenance + compliance evidence."""
    result = await execute(capability_id, params=STANDARD_PARAMS)
    prov = result.get("data_provenance") or result.get("provenance")
    assert isinstance(prov, dict), result
    assert prov.get("score") is not None or prov.get("band") is not None or len(prov) >= 2
    assert result.get("compliance_footer") or result.get("evidence_metadata")
    assert result.get("latency_ms") is not None or result.get("performance_gate") is True
