"""Tests — DeFi, Yield & Token Economics Intelligence (#401–#500)."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts" / "partial_batches" / "batch_05_401_500.json"


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


def _call_capability(fn, seed: dict):
    sig = inspect.signature(fn)
    kwargs: dict = {}
    if "symbol" in sig.parameters:
        kwargs["symbol"] = "BTC"
    if "seed" in sig.parameters:
        kwargs["seed"] = seed
    if "limit" in sig.parameters and "limit" not in kwargs:
        kwargs["limit"] = 5
    if "locale" in sig.parameters:
        kwargs["locale"] = "en"
    if inspect.iscoroutinefunction(fn):
        return asyncio.run(fn(**kwargs) if kwargs else fn())
    return fn(**kwargs) if kwargs else fn()


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_defi_yield_capability(capability_id: int, seed: dict):
    from pdf_capability_registry import discover_bindings

    mod_path, fn_name = discover_bindings()[capability_id]
    mod = importlib.import_module(mod_path)
    fn = getattr(mod, fn_name)
    out = _call_capability(fn, seed)
    assert out.get("ok") is True, out
    assert out.get("capability_id") == capability_id
    if "analysis_only" in out:
        assert out["analysis_only"] is True


def test_e2e_batch_smoke(seed: dict):
    from bd_platform import defi_yield_intelligence_layer as dyi

    out = dyi.run_defi_yield_intelligence_e2e_batch(seed=seed)
    assert out["ok"] is True
    assert out["sample_ok"] is True
