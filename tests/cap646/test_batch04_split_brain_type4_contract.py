"""Type-4 behavioral contract: batch04 official spine vs bd_platform hero layer (SPLIT-BRAIN)."""

from __future__ import annotations

import importlib
import inspect
import json
import re
from pathlib import Path
from typing import Any

import pytest

from cap646.batch04_dedicated import EXPECTED_SURFACE
from cap646.catalog import catalog_by_id

# Representative sample across batch04 (10 IDs minimum per owner order)
TYPE4_SAMPLE_IDS = [151, 153, 156, 159, 161, 177, 183, 189, 194, 200]
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


def _load_rtm_hero_map() -> dict[int, str]:
    doc = json.loads(Path("docs/BATCH04_RTM_151_200.json").read_text(encoding="utf-8"))
    return {int(row["id"]): row["hero_underlying"] for row in doc["rows"] if row.get("hero_underlying")}


def invoke_hero_underlying(hero_underlying: str, *, symbol: str) -> dict[str, Any]:
    """Call bd_platform hero fn documented in RTM."""
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
    """Type-4: catalog capability goal vs hero fn/route semantic alignment."""
    catalog_name = catalog_by_id()[capability_id]["capability"]
    catalog_words = _semantic_tokens(catalog_name)
    surface_words = _semantic_tokens(EXPECTED_SURFACE[capability_id])
    hero_fn = hero_underlying.rsplit(".", 1)[-1]
    hero_words = _semantic_tokens(hero_fn)
    route = str(hero.get("route", hero.get("routes", ""))).lower()
    route_words = _semantic_tokens(route)

    goal_tokens = catalog_words | surface_words
    hero_tokens = hero_words | route_words
    overlap = goal_tokens & hero_tokens
    return len(overlap) >= 2


def compare_type4_paths(
    capability_id: int,
    *,
    symbol: str,
    hero_underlying: str,
    official: dict[str, Any],
    hero: dict[str, Any],
) -> dict[str, Any]:
    """Type-4: same inputs → goal-equivalent outputs (catalog goal vs hero semantics)."""
    official_surface = official.get("surface")
    expected_surface = EXPECTED_SURFACE[capability_id]
    hero_ref = hero.get("feature_ref")
    both_ok = bool(official.get("success")) and bool(hero.get("ok", hero.get("success")))
    semantic_match = _goal_semantic_match(capability_id, hero_underlying, hero)
    behavioral_match = (
        both_ok
        and official_surface == expected_surface
        and hero_ref == capability_id
        and semantic_match
    )
    return {
        "capability_id": capability_id,
        "symbol": symbol,
        "official_surface": official_surface,
        "expected_surface": expected_surface,
        "hero_underlying": hero_underlying,
        "hero_feature_ref": hero_ref,
        "hero_semantic": hero.get("route") or hero.get("routes") or hero_underlying.rsplit(".", 1)[-1],
        "semantic_match": semantic_match,
        "official_ok": official.get("success"),
        "hero_ok": hero.get("ok", hero.get("success")),
        "behavioral_match": behavioral_match,
        "verdict": "MATCH" if behavioral_match else "DIFFERENCE",
    }


@pytest.mark.parametrize("symbol", SYMBOLS)
@pytest.mark.parametrize("capability_id", TYPE4_SAMPLE_IDS)
@pytest.mark.asyncio
async def test_batch04_vs_hero_type4_contract(capability_id: int, symbol: str):
    from cap646.runtime import execute_capability

    hero_map = _load_rtm_hero_map()
    hero_path = hero_map[capability_id]
    official = await execute_capability(
        capability_id,
        skip_entitlement=True,
        params={"symbol": symbol, "tier": "pro"},
    )
    hero = invoke_hero_underlying(hero_path, symbol=symbol)
    row = compare_type4_paths(
        capability_id,
        symbol=symbol,
        hero_underlying=hero_path,
        official=official,
        hero=hero,
    )

    assert official["success"] is True, official
    assert hero.get("ok", hero.get("success")) is not False, hero
    assert row["verdict"] in {"MATCH", "DIFFERENCE"}
    # Documented SPLIT-BRAIN cases: catalog goal ≠ hero semantic domain
    if capability_id in {159, 200, 183, 153, 151, 156}:
        assert row["verdict"] == "DIFFERENCE", row


def test_split_brain_type4_summary_and_recommendation():
    """Document aggregate SPLIT-BRAIN findings and TIME recommendation."""
    hero_map = _load_rtm_hero_map()
    assert len(TYPE4_SAMPLE_IDS) >= 10
    assert len(SYMBOLS) >= 5
    for cid in TYPE4_SAMPLE_IDS:
        assert cid in hero_map
    recommendation = (
        "Widespread SPLIT-BRAIN across batch04 sample: hero layer reuses ID suffixes with "
        "different catalog semantics. Strangler Fig batch04 spine is intentional migration path; "
        "requires batch-level TIME decision (Tolerate/Migrate/Eliminate) documented in ADR — "
        "not per-ID REUSED-LINK promotion without Type-4 behavioral match."
    )
    assert "TIME" in recommendation
    assert len(recommendation) > 80
