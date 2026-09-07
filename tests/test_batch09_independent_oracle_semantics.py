"""Independent-oracle semantic verification for Batch09 parameterized IDs."""

from __future__ import annotations

import asyncio
import math

import pytest

from bd_platform.batch09_membership import verify_membership
from bd_platform.batch09_semantic_engine import CAPABILITY_SEMANTIC_SPECS, compute_semantic_extra, shared_core_ids
from pdf_capability_registry import execute_capability
from tests.batch09_independent_semantic_oracles import (
    PRIMARY_FIELD,
    independent_boundary_primary,
    independent_primary,
    oracle_437_risk_score,
    oracle_441_risk_score,
)


@pytest.mark.parametrize("capability_id", shared_core_ids())
def test_independent_oracle_matches_production_defaults(capability_id: int):
    spec = CAPABILITY_SEMANTIC_SPECS[capability_id]
    rule = spec["rule"]
    inputs = {k: float(v) for k, v in spec["defaults"].items()}
    field = PRIMARY_FIELD[rule]
    expected = independent_primary(rule, inputs)
    actual_payload = compute_semantic_extra(capability_id, symbol="ETH", seed={})
    assert field in actual_payload
    assert actual_payload[field] == pytest.approx(expected, rel=0, abs=1e-4)


@pytest.mark.parametrize("capability_id", shared_core_ids())
def test_independent_boundary_oracle_finite(capability_id: int):
    spec = CAPABILITY_SEMANTIC_SPECS[capability_id]
    rule = spec["rule"]
    inputs = {k: float(v) for k, v in spec["defaults"].items()}
    boundary = independent_boundary_primary(rule, inputs)
    production = compute_semantic_extra(capability_id, symbol="ETH", seed={})
    field = PRIMARY_FIELD[rule]
    finite_values = (boundary, production[field])
    assert all(math.isfinite(value) for value in finite_values)


@pytest.mark.parametrize("capability_id", shared_core_ids())
def test_semantic_rule_distinct_from_neighbors(capability_id: int):
    rules = [CAPABILITY_SEMANTIC_SPECS[i]["rule"] for i in shared_core_ids()]
    assert len(rules) == len(set(rules)) == 47
    assert CAPABILITY_SEMANTIC_SPECS[capability_id]["rule"] in rules


def test_shared_core_membership_reconciliation():
    m = verify_membership()
    assert m["batch09_total_ids_exact"] == 50
    assert m["shared_core_count_exact"] == 48
    assert m["parameterized_count_exact"] == 47
    assert m["outside_shared_core_count_exact"] == 2
    assert m["custom_count_exact"] == 2
    assert m["B_outside_shared_core_ids"] == [409, 441]
    assert m["D_custom_implementation_ids"] == [437, 441]
    assert m["ranges"]["shared_core_48"] == "401–408, 410–440, 442–450"
    assert m["ranges"]["parameterized_47"] == "401–408, 410–436, 438–440, 442–450"
    assert m["437_custom_inside_shared_core"] is True
    assert m["441_custom_outside_shared_core"] is True
    assert m["shared_core_membership_unambiguous"] is True
    assert m["membership_overlap_errors"] == []
    assert m["membership_missing_ids"] == []


def test_oracle_437_independent():
    out = asyncio.run(execute_capability(437))
    expected = oracle_437_risk_score(72.5, 18.4)
    assert out["defi_risk_radar"] == pytest.approx(expected, rel=0, abs=0.01)


def test_oracle_441_independent():
    out = asyncio.run(execute_capability(441))
    status = out.get("oracle_freshness_status")
    expected = oracle_441_risk_score(str(status))
    assert out["oracle_risk"] == pytest.approx(expected, rel=0, abs=0.01)
