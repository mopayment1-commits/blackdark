"""Independent oracles for all 50 Batch13 capabilities."""

from __future__ import annotations

import asyncio
import importlib
import math

import pytest

from bd_platform.batch13_membership import BATCH13_IDS, external_dependency_ids, parameterized_ids
from bd_platform.batch13_semantic_contracts import contract_for
from bd_platform.batch13_semantic_engine import CAPABILITY_SEMANTIC_SPECS, compute_semantic_extra
from pdf_capability_registry import discover_bindings, execute_binding
from tests.batch13_all_50_oracles import oracle_canonical_613, oracle_external_blocked, oracle_shared_core


@pytest.mark.parametrize("cap_id", parameterized_ids())
def test_shared_core_oracle_matches(cap_id: int) -> None:
    spec = CAPABILITY_SEMANTIC_SPECS[cap_id]
    inputs = dict(spec["defaults"])
    expected = oracle_shared_core(cap_id, spec["rule"], inputs, symbol="ETH")
    payload = compute_semantic_extra(cap_id, symbol="ETH", seed={})
    actual = payload[spec["rule"]]
    assert math.isfinite(float(actual))
    assert actual == expected


@pytest.mark.asyncio
async def test_canonical_613_oracle() -> None:
    from cap646.handlers.batch02 import handle_batch02_capability
    from bd_platform.batch13_operational_intelligence_layer import liquidation_screener_613

    canonical = await handle_batch02_capability(88, params={"symbol": "ETH"})
    expected = oracle_canonical_613(canonical)
    facade = await liquidation_screener_613(symbol="ETH")
    assert facade.get("canonical_reuse_of") == expected["canonical_reuse_of"]
    assert facade.get("surface") == expected["surface"]


@pytest.mark.parametrize("cap_id", external_dependency_ids())
def test_external_oracle_fail_closed(cap_id: int) -> None:
    expected = oracle_external_blocked(cap_id)
    mod, fn = discover_bindings()[cap_id]
    payload = getattr(importlib.import_module(mod), fn)(symbol="ETH")
    assert payload.get("ok") == expected["ok"]
    assert payload.get("classification") == expected["classification"]


@pytest.mark.parametrize("cap_id", [c for c in BATCH13_IDS if c not in parameterized_ids() and c not in external_dependency_ids() and c != 613])
def test_outside_binding_oracle_has_semantics(cap_id: int) -> None:
    contract = contract_for(cap_id)
    mod, fn = discover_bindings()[cap_id]
    payload = asyncio.run(execute_binding(mod, fn, capability_id=cap_id))
    assert payload.get("ok") is True, payload
    assert contract["classification"].startswith(("A.", "B."))
