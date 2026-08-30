"""PDF capability registry — binding discovery and execution smoke tests."""

from __future__ import annotations

import pytest

from pdf_capability_registry import batch_test_module_for, discover_bindings, execute_capability


def test_discover_bindings_minimum():
    bindings = discover_bindings()
    assert len(bindings) >= 200
    assert 57 in bindings
    assert 113 in bindings


@pytest.mark.asyncio
async def test_execute_known_binding():
    result = await execute_capability(57)
    assert result.get("ok") is True
    assert "binding" in result


def test_batch_test_mapping():
    assert batch_test_module_for(57) == "tests/test_legal_retail_batch57_66.py"
    assert batch_test_module_for(113) == "tests/test_missing_capabilities_closure.py"
    assert batch_test_module_for(270) == "tests/test_hero_batch_03_capabilities.py"
    assert batch_test_module_for(262) == "tests/test_hero_batch_03_capabilities.py"
    assert batch_test_module_for(350) == "tests/test_hero_batch_04_capabilities.py"
    assert batch_test_module_for(301) == "tests/test_charting_market_intelligence_batch301_400.py"
