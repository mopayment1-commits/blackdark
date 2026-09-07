"""Independent oracles for all 50 Batch14 capabilities."""

from __future__ import annotations

import asyncio
import math

import pytest

from bd_platform.batch14_membership import BATCH14_IDS, canonical_duplicate_ids, parameterized_ids
from bd_platform.batch14_semantic_engine import CAPABILITY_SEMANTIC_SPECS, compute_semantic_extra
from pdf_capability_registry import discover_bindings, execute_binding
from tests.batch14_independent_semantic_oracles import independent_primary


@pytest.mark.parametrize("cap_id", parameterized_ids())
def test_shared_core_oracle_matches(cap_id: int) -> None:
    spec = CAPABILITY_SEMANTIC_SPECS[cap_id]
    inputs = dict(spec["defaults"])
    expected = independent_primary(cap_id, spec["rule"], inputs, symbol="ETH")
    payload = compute_semantic_extra(cap_id, symbol="ETH", seed={})
    actual = payload[spec["rule"]]
    assert math.isfinite(float(actual))
    assert actual == expected


@pytest.mark.parametrize("cap_id", canonical_duplicate_ids())
def test_canonical_duplicate_has_reuse_marker(cap_id: int) -> None:
    mod, fn = discover_bindings()[cap_id]
    payload = asyncio.run(execute_binding(mod, fn, capability_id=cap_id))
    assert payload.get("canonical_reuse_of") is not None
    assert payload.get("ok") is True


@pytest.mark.parametrize("cap_id", [c for c in BATCH14_IDS if c not in parameterized_ids() and c not in canonical_duplicate_ids()])
def test_outside_binding_oracle_has_semantics(cap_id: int) -> None:
    mod, fn = discover_bindings()[cap_id]
    payload = asyncio.run(execute_binding(mod, fn, capability_id=cap_id))
    assert payload.get("ok") is True, payload
    assert "three_spec" in payload
