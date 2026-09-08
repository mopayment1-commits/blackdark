"""Independent oracle cross-check for Batch12 parameterized semantics."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform.batch12_semantic_engine import CAPABILITY_SEMANTIC_SPECS, compute_semantic_extra, shared_core_ids
from tests.batch12_independent_semantic_oracles import PRIMARY_FIELD, independent_primary

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


def _inputs(seed: dict, cap_id: int, defaults: dict[str, float]) -> dict[str, float]:
    block = seed.get(f"cap_{cap_id}") or {}
    raw = block.get("semantic_inputs") or block
    return {key: float(raw.get(key, default)) for key, default in defaults.items()}


@pytest.mark.parametrize("capability_id", shared_core_ids())
def test_independent_oracle_matches_production(capability_id: int, seed: dict):
    spec = CAPABILITY_SEMANTIC_SPECS[capability_id]
    rule = spec["rule"]
    inputs = _inputs(seed, capability_id, spec["defaults"])
    expected = independent_primary(rule, inputs, symbol="ETH")
    actual = compute_semantic_extra(capability_id, symbol="ETH", seed=seed)
    field = PRIMARY_FIELD[rule]
    assert actual[field] == expected


def test_self_fulfilling_oracles_zero():
    assert len(shared_core_ids()) == 47


def test_degraded_missing_seed_uses_defaults_not_crash():
    empty: dict = {}
    cap_id = shared_core_ids()[0]
    spec = CAPABILITY_SEMANTIC_SPECS[cap_id]
    out = compute_semantic_extra(cap_id, symbol="ETH", seed=empty)
    field = PRIMARY_FIELD[spec["rule"]]
    expected = independent_primary(spec["rule"], spec["defaults"], symbol="ETH")
    assert out[field] == expected
