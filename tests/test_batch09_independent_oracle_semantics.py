"""Independent-oracle semantic verification for Batch09 parameterized IDs."""

from __future__ import annotations

import asyncio

import pytest

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
    assert boundary == boundary  # not NaN
    production = compute_semantic_extra(capability_id, symbol="ETH", seed={})
    field = PRIMARY_FIELD[rule]
    assert production[field] == production[field]


@pytest.mark.parametrize("capability_id", shared_core_ids())
def test_semantic_rule_distinct_from_neighbors(capability_id: int):
    rules = [CAPABILITY_SEMANTIC_SPECS[i]["rule"] for i in shared_core_ids()]
    assert len(rules) == len(set(rules)) == 47
    assert CAPABILITY_SEMANTIC_SPECS[capability_id]["rule"] in rules


def test_shared_core_membership_reconciliation():
    batch = set(range(401, 451))
    parameterized = set(shared_core_ids())
    custom = {437, 441}
    shared_48 = parameterized | {437}
    outside_48 = batch - shared_48
    assert len(batch) == 50
    assert len(parameterized) == 47
    assert len(shared_48) == 48
    assert len(outside_48) == 2
    assert outside_48 == {409, 441}
    assert custom == {437, 441}
    assert parameterized & custom == set()
    assert parameterized & outside_48 == set()
    assert shared_48 & custom == {437}
    assert shared_48 & outside_48 == set()


def test_oracle_437_independent():
    out = asyncio.run(execute_capability(437))
    expected = oracle_437_risk_score(72.5, 18.4)
    assert out["defi_risk_radar"] == pytest.approx(expected, rel=0, abs=0.01)


def test_oracle_441_independent():
    out = asyncio.run(execute_capability(441))
    status = out.get("oracle_freshness_status")
    expected = oracle_441_risk_score(str(status))
    assert out["oracle_risk"] == pytest.approx(expected, rel=0, abs=0.01)
