"""Batch11 shared-core semantic distinctness — per-ID oracle tests (501-550)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from bd_platform.batch11_semantic_engine import CAPABILITY_SEMANTIC_SPECS, compute_semantic_extra, shared_core_ids
from pdf_capability_registry import discover_bindings, execute_capability

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/partial_batches/batch_11_501_550.json"


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
    scalar_keys = {k for k in extra if k not in {"feature", "semantic_rule", "attribution", "formula_visible", "analysis_only"}}
    assert len(scalar_keys) >= 2, extra


@pytest.mark.parametrize("capability_id", shared_core_ids())
def test_neighbor_semantic_outputs_differ(capability_id: int, seed: dict):
    peers = [p for p in shared_core_ids() if p != capability_id]
    mine = compute_semantic_extra(capability_id, symbol="BTC", seed=seed)
    peer_id = peers[capability_id % len(peers)]
    other = compute_semantic_extra(peer_id, symbol="BTC", seed=seed)
    assert mine["semantic_rule"] != other["semantic_rule"]


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_execute_capability_semantic_surface(capability_id: int, seed: dict):
    out = asyncio.run(execute_capability(capability_id))
    assert out.get("ok") is True, out
    assert out.get("capability_id") == capability_id
    if capability_id in shared_core_ids():
        assert "semantic_rule" in out


def test_shared_core_count_batch11():
    assert len(shared_core_ids()) == 47


def test_525_hero_delegate_binding():
    mod, fn = discover_bindings()[525]
    assert mod == "bd_platform.heroes_capability_layer"
    assert fn == "strategy_backtesting_525"
