"""Batch09 shared-core semantic distinctness — per-ID oracle tests (401-450)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from bd_platform.batch09_semantic_engine import CAPABILITY_SEMANTIC_SPECS, compute_semantic_extra, shared_core_ids
from pdf_capability_registry import discover_bindings, execute_capability

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/partial_batches/batch_09_401_450.json"


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.mark.parametrize("capability_id", shared_core_ids())
def test_shared_core_semantic_rule_present(capability_id: int, seed: dict):
    spec = CAPABILITY_SEMANTIC_SPECS[capability_id]
    extra = compute_semantic_extra(capability_id, symbol="ETH", seed=seed)
    assert extra["semantic_rule"] == spec["rule"]
    assert extra["feature"] == spec["feature"]
    assert extra.get("formula_visible") is True
    # Must expose more than a renamed metric scalar
    scalar_keys = {k for k in extra if k not in {"feature", "semantic_rule", "attribution", "formula_visible", "analysis_only"}}
    assert len(scalar_keys) >= 2, extra


@pytest.mark.parametrize("capability_id", shared_core_ids())
def test_neighbor_semantic_outputs_differ(capability_id: int, seed: dict):
    peers = [p for p in shared_core_ids() if p != capability_id]
    mine = compute_semantic_extra(capability_id, symbol="BTC", seed=seed)
    peer_id = peers[capability_id % len(peers)]
    other = compute_semantic_extra(peer_id, symbol="BTC", seed=seed)
    mine_rule = mine["semantic_rule"]
    other_rule = other["semantic_rule"]
    assert mine_rule != other_rule
    primary_key = next(k for k in mine if k not in {"feature", "semantic_rule", "attribution", "formula_visible", "analysis_only", "consumer_mode"})
    other_primary = next(k for k in other if k not in {"feature", "semantic_rule", "attribution", "formula_visible", "analysis_only", "consumer_mode"})
    assert mine[primary_key] != other.get(other_primary, object())


@pytest.mark.parametrize("capability_id", [437, 441])
def test_remediated_special_semantics(capability_id: int, seed: dict):
    mod, fn = discover_bindings()[capability_id]
    assert mod == "bd_platform.defi_yield_intelligence_layer"
    out = asyncio.run(execute_capability(capability_id))
    assert out.get("ok") is True
    if capability_id == 437:
        assert "defi_risk_radar" in out
        assert "risk_signals" in out
    else:
        assert "oracle_risk" in out
        assert "oracle_freshness_status" in out


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_execute_capability_semantic_surface(capability_id: int, seed: dict):
    out = asyncio.run(execute_capability(capability_id))
    assert out.get("ok") is True, out
    assert out.get("capability_id") == capability_id
    if capability_id in shared_core_ids():
        assert "semantic_rule" in out


def test_shared_core_count_batch09():
    assert len(shared_core_ids()) == 47
