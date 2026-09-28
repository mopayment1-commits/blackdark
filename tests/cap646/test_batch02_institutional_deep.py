"""Deep institutional tests — batch02 IDs 26–50 (v6 §2.1 semantic assertions)."""

from __future__ import annotations

import pytest

from cap646.batch02_closure_spec import BATCH02_DOMAIN_PAYLOAD_KEYS, BATCH02_OFFICIAL_RANGE, expected_surface
from cap646.batch02_official_production import execute

STANDARD_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "tier": "pro",
}


@pytest.mark.parametrize("capability_id", list(BATCH02_OFFICIAL_RANGE))
@pytest.mark.asyncio
async def test_batch02_domain_payload(capability_id: int):
    result = await execute(capability_id, params=STANDARD_PARAMS)
    assert result["success"] is True, result
    assert result["surface"] == expected_surface(capability_id)
    keys = BATCH02_DOMAIN_PAYLOAD_KEYS[capability_id]
    assert any(k in result for k in keys), (capability_id, keys, list(result.keys()))


@pytest.mark.parametrize("capability_id", list(BATCH02_OFFICIAL_RANGE))
@pytest.mark.asyncio
async def test_batch02_production_spine(capability_id: int):
    result = await execute(capability_id, params=STANDARD_PARAMS)
    assert result["backend_module"] == "cap646.batch02_official_production"
    assert result["binding_source"] == "explicit_option_a"
    assert result["official_batch"] == "batch02"
    assert "invoke_substantive" not in str(result.get("build_method", ""))


@pytest.mark.parametrize("capability_id", list(BATCH02_OFFICIAL_RANGE))
@pytest.mark.asyncio
async def test_batch02_provenance_and_evidence(capability_id: int):
    result = await execute(capability_id, params=STANDARD_PARAMS)
    prov = result.get("data_provenance") or result.get("provenance")
    assert isinstance(prov, dict), result
    assert prov.get("score") is not None or prov.get("band") is not None or len(prov) >= 2
    assert result.get("compliance_footer") or result.get("evidence_metadata")
