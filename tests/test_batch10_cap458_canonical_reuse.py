"""Batch10 #458 canonical reuse proof against #86."""

from __future__ import annotations

import asyncio

import pytest

from bd_platform.heroes_capability_layer import metric_methodology_registry_458
from bd_platform.whales_institutional_layer import build_methodology_docs_86
from pdf_capability_registry import discover_bindings, execute_capability


def test_binding_is_hero_facade_not_shared_core():
    mod, fn = discover_bindings()[458]
    assert mod == "bd_platform.heroes_capability_layer"
    assert fn == "metric_methodology_registry_458"


def test_semantic_equivalence_facade_vs_canonical():
    facade = metric_methodology_registry_458(locale="en")
    canonical = build_methodology_docs_86(locale="en")
    for key in ("methodology", "locale", "capability_id"):
        if key in canonical:
            assert facade.get(key) == canonical.get(key), key


@pytest.mark.asyncio
async def test_registry_path_no_parallel_semantic_engine():
    out = await execute_capability(458)
    assert out.get("ok") is True, out
    assert out.get("capability_id") == 458
    result = out.get("result") or out
    if isinstance(result, dict):
        assert "methodology" in result or result.get("ok") is True


@pytest.mark.asyncio
async def test_cap646_runtime_path_resolves_hero_facade():
    from cap646.runtime import execute_capability as cap646_execute

    result = await cap646_execute(458, skip_entitlement=True, params={"symbol": "BTC"})
    assert result.get("success") is True, result
    assert result.get("backend_module") == "bd_platform.heroes_capability_layer"
    assert result.get("backend_entrypoint") == "metric_methodology_registry_458"
    payload = result.get("result") or {}
    canonical = build_methodology_docs_86(locale="en")
    assert payload.get("methodology") == canonical.get("methodology")


def test_no_batch10_semantic_rule_for_458():
    from bd_platform.batch10_semantic_engine import CAPABILITY_SEMANTIC_SPECS

    assert 458 not in CAPABILITY_SEMANTIC_SPECS
