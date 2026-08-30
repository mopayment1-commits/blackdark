"""Final 24 capability closure tests (826/826 minus human-only external)."""

from __future__ import annotations

import pytest

from pdf_capability_registry import discover_bindings, execute_capability

FINAL_IDS = [
    2, 18, 29, 31, 49, 270, 288, 316, 331, 378, 379, 390, 393, 396, 409, 517, 528, 630, 702, 745, 752, 753, 816, 819,
]

HUMAN_ONLY = {693}


@pytest.mark.parametrize("capability_id", FINAL_IDS)
@pytest.mark.asyncio
async def test_final_capability_executes(capability_id: int):
    binding = discover_bindings().get(capability_id)
    assert binding is not None, f"missing binding for {capability_id}"
    result = await execute_capability(capability_id)
    assert result.get("ok") is True, result


@pytest.mark.asyncio
async def test_human_only_polygon_not_auto_bound():
    assert 693 in HUMAN_ONLY
    assert discover_bindings().get(693) is None
