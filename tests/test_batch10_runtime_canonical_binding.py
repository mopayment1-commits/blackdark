"""Batch10 final canonical runtime binding proof — IDs 451–500 only."""

from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bd_platform.batch10_membership import HERO_DELEGATE_ID, shared_core_49_ids
from bd_platform.batch10_semantic_engine import CAPABILITY_SEMANTIC_SPECS, compute_semantic_extra
from bd_platform.heroes_capability_layer import metric_methodology_registry_458
from bd_platform.whales_institutional_layer import build_methodology_docs_86
from cap646.backend_registry import binding_for, resolve_binding
from cap646.handlers.platform import handle_platform_capability
from cap646.runtime import _route_handler, execute_capability
from pdf_capability_registry import discover_bindings
from tests.batch10_independent_semantic_oracles import PRIMARY_FIELD, independent_primary

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/partial_batches/batch_10_451_500.json"


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def client() -> TestClient:
    from dashboard import app

    return TestClient(app)


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_pdf_registry_matches_backend_registry(capability_id: int):
    mod, entry = discover_bindings()[capability_id]
    binding = resolve_binding(capability_id)
    assert binding.module == mod, binding
    assert binding.entrypoint == entry, binding
    assert binding.source == "pdf_capability_registry"


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_runtime_routes_to_platform_registry_handler(capability_id: int):
    from cap646.catalog import catalog_by_id

    row = catalog_by_id()[capability_id]
    handler = _route_handler(row["track"], row["capability"], capability_id)
    assert handler is handle_platform_capability


@pytest.mark.parametrize("capability_id", _batch_ids())
@pytest.mark.asyncio
async def test_cap646_runtime_binding_and_output(capability_id: int, seed: dict):
    mod, entry = discover_bindings()[capability_id]
    result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "ETH"})
    assert result.get("success") is True, result
    assert result.get("backend_module") == mod
    assert result.get("backend_entrypoint") == entry
    assert result.get("binding_source") == "pdf_capability_registry"

    payload = result.get("result") or result
    assert isinstance(payload, dict)

    if capability_id == HERO_DELEGATE_ID:
        canonical = build_methodology_docs_86(locale="en")
        assert payload.get("methodology") == canonical.get("methodology")
        return

    assert payload.get("semantic_rule"), payload
    spec = CAPABILITY_SEMANTIC_SPECS[capability_id]
    rule = spec["rule"]
    block = seed.get(f"cap_{capability_id}") or {}
    raw = block.get("semantic_inputs") or block
    inputs = {key: float(raw.get(key, default)) for key, default in spec["defaults"].items()}
    expected = independent_primary(rule, inputs, symbol="ETH")
    field = PRIMARY_FIELD[rule]
    assert payload[field] == expected


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_http_get_production_path(client: TestClient, capability_id: int):
    response = client.get(f"/api/cap646/{capability_id}", params={"symbol": "ETH"})
    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is True, body
    mod, entry = discover_bindings()[capability_id]
    assert body.get("backend_module") == mod
    assert body.get("backend_entrypoint") == entry
    payload = body.get("result") or body
    if capability_id == HERO_DELEGATE_ID:
        assert "methodology" in payload
    else:
        assert payload.get("semantic_rule")


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_http_post_gateway_execute_path(client: TestClient, capability_id: int):
    response = client.post(
        f"/api/cap646/{capability_id}/execute",
        json={"params": {"symbol": "ETH"}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is True, body
    mod, entry = discover_bindings()[capability_id]
    assert body.get("backend_module") == mod
    assert body.get("backend_entrypoint") == entry
    assert body.get("gateway", {}).get("audited") is True


@pytest.mark.asyncio
async def test_cap458_runtime_canonical_reuse_proven():
    facade = metric_methodology_registry_458(locale="en")
    runtime = await execute_capability(458, skip_entitlement=True, params={"symbol": "BTC"})
    assert runtime.get("success") is True
    assert runtime.get("backend_module") == "bd_platform.heroes_capability_layer"
    payload = runtime.get("result") or {}
    assert payload.get("methodology") == facade.get("methodology")


def test_no_orphan_semantic_implementations():
    bindings = discover_bindings()
    for cap_id in shared_core_49_ids():
        mod, entry = bindings[cap_id]
        assert mod == "bd_platform.defi_yield_intelligence_layer"
        fn = getattr(importlib.import_module(mod), entry)
        out = fn(symbol="ETH", seed=json.loads(Path("data/legal_retail_commercial_seed.json").read_text()))
        assert out.get("semantic_rule")


def test_runtime_binding_summary_flags():
    wrong = []
    for cap_id in _batch_ids():
        mod, entry = discover_bindings()[cap_id]
        binding = binding_for(cap_id)
        if binding["backend_module"] != mod or binding["backend_entrypoint"] != entry:
            wrong.append(cap_id)
    assert wrong == []
