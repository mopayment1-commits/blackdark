"""Type-4 behavioral contract: batch05 official spine vs bd_platform hero layer."""

from __future__ import annotations

import importlib
import inspect
import json
import re
from pathlib import Path
from typing import Any

import pytest

from cap646.batch05_dedicated import EXPECTED_SURFACE
from cap646.catalog import catalog_by_id

TYPE4_SAMPLE_IDS = [201, 205, 211, 217, 224, 228, 233, 237, 243, 250]
SYMBOLS = ["BTC", "ETH", "SOL", "AVAX", "DOGE"]

_NOISE_WORDS = frozenset(
    {
        "intelligence",
        "the",
        "and",
        "for",
        "per",
        "data",
        "access",
        "status",
        "layer",
        "run",
        "e2e",
    }
)


def _load_hero_map() -> dict[int, str]:
    doc = json.loads(Path("docs/BATCH05_CLASSIFICATION_INVEST_201_250.json").read_text(encoding="utf-8"))
    out: dict[int, str] = {}
    for row in doc["rows"]:
        cid = int(row["capability_id"])
        if cid in (214, 245):
            continue
        mod = row.get("hero_module")
        fn = row.get("hero_underlying")
        if mod and fn:
            out[cid] = f"{mod}.{fn}"
    return out


def invoke_hero_underlying(hero_underlying: str, *, symbol: str) -> dict[str, Any]:
    from cap646.dedicated_common import seed as _seed

    module_path, fn_name = hero_underlying.rsplit(".", 1)
    mod = importlib.import_module(module_path)
    fn = getattr(mod, fn_name)
    sig = inspect.signature(fn)
    kwargs: dict[str, Any] = {}
    if "seed" in sig.parameters:
        kwargs["seed"] = _seed()
    if "asset" in sig.parameters:
        kwargs["asset"] = symbol
    elif "symbol" in sig.parameters:
        kwargs["symbol"] = symbol
    if "address" in sig.parameters:
        kwargs["address"] = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    return fn(**kwargs)


def _semantic_tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in _NOISE_WORDS and len(w) > 2}


def _goal_semantic_match(capability_id: int, hero_underlying: str, hero: dict[str, Any]) -> bool:
    catalog_name = catalog_by_id()[capability_id]["capability"]
    catalog_words = _semantic_tokens(catalog_name)
    surface_words = _semantic_tokens(EXPECTED_SURFACE[capability_id])
    hero_fn = hero_underlying.rsplit(".", 1)[-1]
    hero_words = _semantic_tokens(hero_fn)
    route = str(hero.get("route", hero.get("routes", ""))).lower()
    route_words = _semantic_tokens(route)
    goal_tokens = catalog_words | surface_words
    hero_tokens = hero_words | route_words
    return len(goal_tokens & hero_tokens) >= 1


@pytest.mark.parametrize("capability_id", TYPE4_SAMPLE_IDS)
@pytest.mark.parametrize("symbol", SYMBOLS)
@pytest.mark.asyncio
async def test_type4_official_vs_hero(capability_id: int, symbol: str):
    from cap646.batch05_dedicated import execute

    hero_map = _load_hero_map()
    hero_underlying = hero_map[capability_id]
    official = await execute(capability_id, params={"symbol": symbol})
    hero = invoke_hero_underlying(hero_underlying, symbol=symbol)

    assert official["success"] is True
    assert official["surface"] == EXPECTED_SURFACE[capability_id]
    assert official[EXPECTED_SURFACE[capability_id]]["feature_ref"] == capability_id
    assert hero.get("ok", hero.get("success")) is not False
    assert _goal_semantic_match(capability_id, hero_underlying, hero) or hero.get("feature_ref") in {capability_id, 245}
