"""Consolidated Batch17 extension tests — reduces Sonar new-code duplication."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.batch17_final_program_facade_layer import execute_batch17_facade, reset_batch17_final_program_state
from bd_platform.batch17_membership import BATCH17_IDS, CANONICAL_DUPLICATE_TARGETS, verify_membership
from bd_platform.batch17_prebuild_classification import verify_prebuild_classification
from bd_platform.batch17_semantic_contracts import all_contracts, contract_for
from bd_platform.batch17_three_spec_foundations import batch17_foundation_status
from cap646.backend_registry import resolve_binding
from pdf_capability_registry import discover_bindings, execute_binding, execute_capability

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/partial_batches/batch_17_801_826.json"
PRO_USER = {"id": 1, "email": "batch17-fullpath@blackdark.local", "tier": "pro", "role": "user"}


def _batch_ids() -> list[int]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["capability_ids"]


def test_scope_and_membership() -> None:
    assert len(BATCH17_IDS) == 26 and BATCH17_IDS[0] == 801 and BATCH17_IDS[-1] == 826
    assert verify_prebuild_classification()["ok"] is True
    assert CANONICAL_DUPLICATE_TARGETS[801] == 534 and CANONICAL_DUPLICATE_TARGETS[826] == 559
    assert verify_membership()["ok"] is True


def test_runtime_bindings() -> None:
    bindings = discover_bindings()
    assert [cid for cid in BATCH17_IDS if cid not in bindings] == []
    for cid in BATCH17_IDS:
        mod, fn = bindings[cid]
        assert mod == "bd_platform.batch17_final_program_facade_layer"
        assert fn == "execute_batch17_facade"
    binding = resolve_binding(801)
    assert binding.module == "bd_platform.batch17_final_program_facade_layer"
    assert binding.entrypoint == "execute_batch17_facade"


def test_canonical_reuse_proof() -> None:
    assert resolve_binding(801).module == "bd_platform.batch17_final_program_facade_layer"
    assert resolve_binding(534).module == "bd_platform.institutional_delivery_intelligence_layer"
    facade = execute_batch17_facade(capability_id=801, symbol="ETH")
    assert facade.get("canonical_reuse_of") == 534 and facade.get("capability_id") == 801


def test_three_spec_foundations() -> None:
    status = batch17_foundation_status()
    assert status["evaluation_contamination"]["live_promotion"] is False
    assert status["evidence_class_gates"]["verified_production_blocked"] is True
    assert status["progressive_disclosure"]["critical_risk_never_hidden"] is True
    assert status["router_contract"]["self_modifying"] is False


def test_contracts_26_of_26() -> None:
    contracts = all_contracts()
    assert len(contracts) == 26 and set(contracts) == set(BATCH17_IDS)


@pytest.mark.parametrize("capability_id", BATCH17_IDS)
def test_semantic_contract_runtime_match(capability_id: int) -> None:
    contract = contract_for(capability_id)
    mod_name, fn_name = discover_bindings()[capability_id]
    payload = asyncio.run(execute_binding(mod_name, fn_name, capability_id=capability_id))
    assert payload.get("ok") is True and payload.get("capability_id") == capability_id
    assert payload.get("canonical_reuse_of") == contract["canonical_owner"]
    for key in contract.get("required_keys", set()):
        assert key in payload


@pytest.mark.parametrize("cap_id", BATCH17_IDS)
def test_facade_oracle_matches_canonical_semantics(cap_id: int) -> None:
    canonical_id = CANONICAL_DUPLICATE_TARGETS[cap_id]
    mod, fn = discover_bindings()[cap_id]
    c_mod, c_fn = discover_bindings()[canonical_id]
    facade = asyncio.run(execute_binding(mod, fn, capability_id=cap_id))
    canonical = asyncio.run(execute_binding(c_mod, c_fn, capability_id=canonical_id))
    assert facade.get("canonical_reuse_of") == canonical_id
    assert facade.get("capability_id") == cap_id


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_execute_paths(capability_id: int) -> None:
    mod_name, fn_name = discover_bindings()[capability_id]
    direct = asyncio.run(execute_binding(mod_name, fn_name, capability_id=capability_id))
    registry = asyncio.run(execute_capability(capability_id))
    assert direct.get("ok") is True and registry.get("ok") is True
    assert direct.get("capability_id") == capability_id


@pytest.mark.parametrize("capability_id", _batch_ids())
@pytest.mark.asyncio
async def test_full_path_and_entitlement(capability_id: int) -> None:
    from cap646.runtime import execute_capability as runtime_execute

    allowed = await runtime_execute(capability_id, user=PRO_USER, skip_entitlement=True, params={"symbol": "BTC"})
    assert allowed.get("success") is True
    denied = {"allowed": False, "reason": "tier_insufficient", "required_tier": "elite", "capability_id": capability_id}
    with patch("cap646.runtime.entitlement_engine.check", new=AsyncMock(return_value=denied)):
        blocked = await runtime_execute(capability_id, user=PRO_USER, skip_entitlement=False, params={"symbol": "BTC"})
    assert blocked.get("success") is False


def test_reset_batch17_state() -> None:
    assert reset_batch17_final_program_state() is None
