"""Tests — Institutional Delivery & Entity Intelligence (#501–#600)."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts" / "partial_batches" / "batch_06_501_600.json"


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
@pytest.mark.asyncio
async def test_institutional_delivery_capability(capability_id: int, seed: dict):
    from pdf_capability_registry import discover_bindings, execute_capability

    mod_path, fn_name = discover_bindings()[capability_id]
    if mod_path.endswith("institutional_delivery_intelligence_layer"):
        mod = importlib.import_module(mod_path)
        fn = getattr(mod, fn_name)
        out = _call_capability(fn, seed)
        assert out.get("capability_id") == capability_id
        if "analysis_only" in out:
            assert out["analysis_only"] is True
    else:
        out = await execute_capability(capability_id)
    assert out.get("ok") is True, out


def test_e2e_batch_smoke(seed: dict):
    from bd_platform import institutional_delivery_intelligence_layer as idi

    out = idi.run_institutional_delivery_intelligence_e2e_batch(seed=seed)
    assert out["ok"] is True
    assert out["sample_ok"] is True
