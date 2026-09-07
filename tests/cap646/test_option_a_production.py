"""Option A production-path tests — #338 data spine only (507/534 use pdf registry)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "capability_id,expected_surface,expected_module,expected_entrypoint",
    [
        (338, "data_quality_pipeline", "cap646.data_spine", "data_quality_pipeline_report"),
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
@pytest.mark.parametrize("capability_id", [338])
async def test_option_a_backend_registry_binding(capability_id):
    from cap646.backend_registry import binding_for

    binding = binding_for(capability_id)
    assert binding["binding_source"] == "explicit_option_a"
    assert binding["backend_module"] == "cap646.data_spine"
