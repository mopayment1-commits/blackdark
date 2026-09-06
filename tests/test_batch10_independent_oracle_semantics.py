"""Independent oracle cross-check for Batch10 parameterized semantics."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform.batch10_semantic_engine import CAPABILITY_SEMANTIC_SPECS, compute_semantic_extra, shared_core_ids
from tests.batch10_independent_semantic_oracles import PRIMARY_FIELD, independent_primary

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
    assert len(shared_core_ids()) == 49
