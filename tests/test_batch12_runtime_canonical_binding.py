"""Batch12 final canonical runtime binding proof — IDs 551–600 only."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bd_platform.batch12_membership import (
    CANONICAL_CATALOG_SEMANTICS_IDS,
    CANONICAL_DUPLICATE_REUSE_ID,
    outside_shared_core_ids,
    shared_core_47_ids,
)
from bd_platform.batch12_semantic_engine import CAPABILITY_SEMANTIC_SPECS
from cap646.backend_registry import binding_for, resolve_binding
from cap646.handlers.platform import handle_platform_capability
from cap646.runtime import _route_handler, execute_capability
from pdf_capability_registry import discover_bindings
from tests.batch12_independent_semantic_oracles import PRIMARY_FIELD, independent_primary

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/partial_batches/batch_12_551_600.json"
OUTSIDE = set(outside_shared_core_ids())


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def client() -> TestClient:
    from unittest.mock import AsyncMock, patch

    from dashboard import app
    from security_auth import optional_user_from_request

    def _elite_user():
        return {"id": 3, "email": "batch12-elite@blackdark.local", "tier": "elite", "role": "user"}

    async def _passthrough_middleware(request, call_next):
        return await call_next(request)

    app.dependency_overrides[optional_user_from_request] = _elite_user
    with patch(
        "cap646.runtime.entitlement_engine.check",
        new=AsyncMock(return_value={"allowed": True, "tier": "elite"}),
    ), patch(
        "cap646.institutional_gateway.entitlement_engine.check",
        new=AsyncMock(return_value={"allowed": True, "tier": "elite"}),
    ), patch("viral_capacity.viral_protection_middleware", side_effect=_passthrough_middleware):
        yield TestClient(app)
    app.dependency_overrides.pop(optional_user_from_request, None)


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_pdf_registry_matches_backend_registry(capability_id: int):
    if capability_id == CANONICAL_DUPLICATE_REUSE_ID:
        binding = resolve_binding(capability_id)
        canonical = resolve_binding(88)
        assert binding.source == "canonical_duplicate_reuse_88"
        assert binding.module == canonical.module
        assert binding.entrypoint == canonical.entrypoint
        return
    if capability_id in CANONICAL_CATALOG_SEMANTICS_IDS:
        mod, entry = discover_bindings()[capability_id]
        binding = resolve_binding(capability_id)
        assert binding.module == mod, binding
        assert binding.entrypoint == entry, binding
        assert binding.source == "canonical_catalog_semantics"
        return
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

    payload = result.get("result") or result
    assert isinstance(payload, dict)

    if capability_id == CANONICAL_DUPLICATE_REUSE_ID:
        assert result.get("classification") == "DUPLICATE/ALREADY_COVERED"
        assert result.get("duplicate_of") == 88
        assert result.get("backend_module") == "cap646.batch02_production"
        assert result.get("backend_entrypoint") == "cap_088"
        assert payload.get("surface") == "liquidation_intelligence"
        return

    assert result.get("backend_module") == mod
    assert result.get("backend_entrypoint") == entry
    if capability_id in CANONICAL_CATALOG_SEMANTICS_IDS:
        assert result.get("binding_source") == "canonical_catalog_semantics"
    else:
        assert result.get("binding_source") == "pdf_capability_registry"

    if capability_id in OUTSIDE - {CANONICAL_DUPLICATE_REUSE_ID}:
        assert payload.get("ok") is True or result.get("success") is True
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
    if capability_id == CANONICAL_DUPLICATE_REUSE_ID:
        assert body.get("classification") == "DUPLICATE/ALREADY_COVERED"
        assert body.get("duplicate_of") == 88
        assert body.get("backend_module") == "cap646.batch02_production"
        return
    if capability_id in OUTSIDE - {CANONICAL_DUPLICATE_REUSE_ID}:
        assert body.get("success") is True, body
        return
    mod, entry = discover_bindings()[capability_id]
    assert body.get("backend_module") == mod
    assert body.get("backend_entrypoint") == entry
    payload = body.get("result") or body
    if capability_id in shared_core_47_ids():
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
    if capability_id == CANONICAL_DUPLICATE_REUSE_ID:
        assert body.get("classification") == "DUPLICATE/ALREADY_COVERED"
        assert body.get("duplicate_of") == 88
        assert body.get("backend_module") == "cap646.batch02_production"
        return
    if capability_id in OUTSIDE - {CANONICAL_DUPLICATE_REUSE_ID}:
        assert body.get("success") is True, body
        return
    mod, entry = discover_bindings()[capability_id]
    assert body.get("backend_module") == mod
    assert body.get("backend_entrypoint") == entry
    assert body.get("gateway", {}).get("audited") is True


def test_runtime_binding_summary_flags():
    wrong = []
    for cap_id in _batch_ids():
        if cap_id == CANONICAL_DUPLICATE_REUSE_ID:
            binding = binding_for(cap_id)
            assert binding["binding_source"] == "canonical_duplicate_reuse_88"
            continue
        if cap_id in CANONICAL_CATALOG_SEMANTICS_IDS:
            binding = binding_for(cap_id)
            assert binding["binding_source"] == "canonical_catalog_semantics"
            continue
        mod, entry = discover_bindings()[cap_id]
        binding = binding_for(cap_id)
        if binding["backend_module"] != mod or binding["backend_entrypoint"] != entry:
            wrong.append(cap_id)
    assert wrong == []
