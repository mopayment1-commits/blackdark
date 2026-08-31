"""Option A production-path tests — #338, #500, #507, #534."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "capability_id,expected_surface,expected_module,expected_entrypoint",
    [
        (338, "data_quality_pipeline", "cap646.data_spine", "data_quality_pipeline_report"),
        (500, "data_quality_normalization", "cap646.data_spine", "normalization_report"),
        (507, "ohlcv", "cap646.fallbacks", "resolve_ohlcv_closes"),
        (534, "bucketed_cvd", "cap646.data_spine", "bucketed_cvd_report"),
    ],
)
async def test_option_a_runtime_execute(capability_id, expected_surface, expected_module, expected_entrypoint):
    from cap646.runtime import execute_capability

    result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "BTC"})
    assert result["success"] is True
    assert result["surface"] == expected_surface
    assert result.get("backend_module") == expected_module or result.get("binding_source") == "explicit_option_a"
    assert result.get("compliance_footer")


@pytest.mark.asyncio
@pytest.mark.parametrize("capability_id", [338, 500, 507, 534])
async def test_option_a_backend_registry_binding(capability_id):
    from cap646.backend_registry import binding_for

    binding = binding_for(capability_id)
    assert binding["binding_source"] == "explicit_option_a"
    assert binding["backend_module"] in {
        "cap646.data_spine",
        "cap646.fallbacks",
    }


@pytest.mark.asyncio
async def test_option_a_534_bucketed_cvd_shape():
    from cap646.runtime import execute_capability

    result = await execute_capability(534, skip_entitlement=True, params={"symbol": "BTC", "buckets": 4})
    assert result["success"] is True
    assert result["surface"] == "bucketed_cvd"
    assert isinstance(result.get("buckets"), list)
    assert len(result["buckets"]) >= 1
    assert result.get("formula_visible") is True
