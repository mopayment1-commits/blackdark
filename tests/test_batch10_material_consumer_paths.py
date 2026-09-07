"""Batch10 material consumer paths — registry, module, and cap646 runtime (not gateway-only)."""

from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path

import pytest

from bd_platform.batch10_membership import HERO_DELEGATE_ID, shared_core_49_ids
from pdf_capability_registry import discover_bindings, execute_capability

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/partial_batches/batch_10_451_500.json"


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("capability_id", shared_core_49_ids())
def test_direct_module_builder_material_output(capability_id: int, seed: dict):
    mod_name, fn_name = discover_bindings()[capability_id]
    mod = importlib.import_module(mod_name)
    builder = getattr(mod, fn_name)
    out = builder(symbol="ETH", seed=seed)
    assert out.get("ok") is True, out
    assert out.get("capability_id") == capability_id
    assert out.get("semantic_rule"), out
    payload_keys = set(out.keys()) - {"ok", "capability_id", "symbol", "disclaimer", "analysis_only"}
    assert len(payload_keys) >= 3, out


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_registry_execute_material_output(capability_id: int):
    out = asyncio.run(execute_capability(capability_id))
    assert out.get("ok") is True, out
    assert out.get("capability_id") == capability_id


@pytest.mark.asyncio
async def test_cap646_runtime_material_path_representative():
    from cap646.runtime import execute_capability as cap646_execute

    for capability_id in (451, 458, 500):
        result = await cap646_execute(capability_id, params={"symbol": "BTC"}, skip_entitlement=False)
        assert result.get("success") is True, result


def test_458_hero_facade_delegates_to_canonical_86():
    from bd_platform.heroes_capability_layer import metric_methodology_registry_458
    from bd_platform.whales_institutional_layer import build_methodology_docs_86

    facade = metric_methodology_registry_458(locale="en")
    canonical = build_methodology_docs_86(locale="en")
    assert facade.get("ok") is True
    assert canonical.get("ok") is True
    assert facade.get("methodology") == canonical.get("methodology")


@pytest.mark.asyncio
async def test_500_pdf_registry_defi_yield_production_binding():
    from cap646.backend_registry import resolve_binding
    from cap646.runtime import execute_capability

    binding = resolve_binding(500)
    assert binding.module == "bd_platform.defi_yield_intelligence_layer"
    assert binding.entrypoint == "data_quality_normalization_500"
    assert binding.source == "pdf_capability_registry"
    result = await execute_capability(500, skip_entitlement=True, params={"symbol": "BTC"})
    assert result.get("success") is True, result
    payload = result.get("result") or result
    assert payload.get("semantic_rule") == "data_quality_normalization"
