"""War room — phantom extension IDs registered on production path."""

from __future__ import annotations

import pytest

from cap646.backend_registry import binding_for, resolve_binding
from cap646.catalog import catalog_by_id
from cap646.extension_capabilities import is_extension_id

PHANTOM_IDS = [704, 708, 725, 812, 813, 814, 815]


@pytest.mark.parametrize("cap_id", PHANTOM_IDS)
def test_phantom_ids_in_merged_catalog(cap_id: int):
    assert cap_id in catalog_by_id()
    assert is_extension_id(cap_id)


@pytest.mark.parametrize("cap_id", PHANTOM_IDS)
def test_phantom_ids_have_production_binding(cap_id: int):
    binding = binding_for(cap_id)
    assert binding["backend_module"] == "cap646.extension_capabilities"
    assert binding["binding_source"] == "extension_registry_remediation"


@pytest.mark.asyncio
@pytest.mark.parametrize("cap_id", PHANTOM_IDS)
async def test_phantom_ids_execute_on_production_path(cap_id: int):
    from cap646.backend_executor import execute_binding

    result = await execute_binding(cap_id, params={"symbol": "BTC"})
    assert result["success"] is True
    assert result["capability_id"] == cap_id
