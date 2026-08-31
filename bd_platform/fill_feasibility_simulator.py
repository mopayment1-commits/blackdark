"""
Fill Feasibility Simulator — Feature #415 (Liquidity Depth Analyzer).

Liquidity analysis layer in Intelligence Ledger + Arbitrage Scanner (#403).
Non-custodial depth replay: full-fill / partial-fill / not-fillable verdicts.
Stale depth rejected; missing depth never treated as executable.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bd_platform.oracle_vwap_layer import build_fair_value_index, build_market_radar_vwap_context

logger = logging.getLogger("BLACKDARK.FillFeasibilitySimulator")

_FEATURE_ID = 415
_TITLE = "Fill Feasibility Simulator"
_LEGAL_NAME = "Liquidity Depth Analyzer"
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger + Arbitrage Scanner"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/fill_feasibility_seed.json")
_METHODOLOGY_VERSION = "1.0"
_STALE_MS_DEFAULT = 5000
_MIN_FILL_RATIO = 0.95

_DISCLAIMER = (
    "Liquidity depth analysis — simulation only, no execution. "
    "Fill feasibility estimates based on order-book replay. "
    "Stale or missing depth never treated as executable."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"pairs": {}, "arbitrage_opportunities": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("fill feasibility seed load failed: %s", exc)
        return {"pairs": {}, "arbitrage_opportunities": []}


def _normalize_symbol(symbol: str) -> str:
    sym = symbol.upper().replace("-", "/")
    if "/" not in sym and sym.endswith("USDT"):
        sym = f"{sym[:-4]}/USDT"
    if "/" not in sym:
        sym = f"{sym}/USDT"
    return sym


def _walk_book(
    levels: list[list[float]],
    size: float,
) -> tuple[float, float, float]:
    """Deterministic order-book replay. Returns (filled, weighted_price, residual)."""
    if size <= 0 or not levels:
        return 0.0, 0.0, size

    remaining = size
    notional = 0.0
    filled = 0.0
    for level in levels:
        if remaining <= 0:
            break
        if len(level) < 2:
            continue
        price, qty = float(level[0]), float(level[1])
        if price <= 0 or qty <= 0:
            continue
        take = min(remaining, qty)
        notional += take * price
        filled += take
        remaining -= take

    wavg = notional / filled if filled > 0 else 0.0
    return filled, wavg, remaining


def _book_for_side(book: dict[str, Any], side: str) -> list[list[float]]:
    if side == "buy":
        return list(book.get("asks") or [])
    return list(book.get("bids") or [])


def _snapshot_age_ms(book: dict[str, Any]) -> int | None:
    freshness = book.get("freshness") or {}
    age = freshness.get("snapshot_age_ms")
    return int(age) if age is not None else None


def _is_stale(book: dict[str, Any], *, stale_ms: int) -> bool:
    age = _snapshot_age_ms(book)
    if age is None:
        return True
    return age > stale_ms


def _spread_bps(book: dict[str, Any]) -> float | None:
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    if not bids or not asks:
        return None
    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    if best_bid <= 0 or best_ask <= 0:
        return None
    mid = (best_bid + best_ask) / 2
    return round((best_ask - best_bid) / mid * 10000, 2) if mid > 0 else None


def _liquidity_score(
    *,
    fill_ratio: float,
    depth_levels: int,
    spread_bps: float | None,
    stale: bool,
) -> int:
    if stale or depth_levels <= 0:
        return 0
    base = min(100, int(fill_ratio * 70) + min(depth_levels * 4, 20))
    if spread_bps is not None and spread_bps > 0:
        base = max(0, base - min(25, int(spread_bps / 2)))
    return max(0, min(100, base))


def _verdict(fill_ratio: float, has_depth: bool, stale: bool, *, min_ratio: float) -> str:
    if stale or not has_depth:
        return "not_fillable"
    if fill_ratio >= min_ratio:
        return "full_fill"
    if fill_ratio > 0:
        return "partial_fill"
    return "not_fillable"


def simulate_fill(
    *,
    symbol: str,
    venue: str,
    side: str,
    size: float,
    seed: dict[str, Any] | None = None,
    book: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    sym = _normalize_symbol(symbol)
    stale_ms = int(seed.get("stale_threshold_ms") or _STALE_MS_DEFAULT)
    min_ratio = float(seed.get("min_fillable_ratio") or _MIN_FILL_RATIO)

    if book is None:
        pair_books = (seed.get("pairs") or {}).get(sym) or {}
        book = pair_books.get(venue.lower())

    if not book:
        return {
            "ok": False,
            "symbol": sym,
            "venue": venue,
            "side": side,
            "requested_size": size,
            "verdict": "not_fillable",
            "fillable_size": 0.0,
            "residual_size": size,
            "weighted_fill_price": None,
            "expected_slippage_pct": None,
            "liquidity_score": 0,
            "confidence": "low",
            "stale": True,
            "reason": "missing_depth_never_executable",
            "evidence_class": "BACKTESTED",
        }

    stale = _is_stale(book, stale_ms=stale_ms)
    if stale:
        return {
            "ok": False,
            "symbol": sym,
            "venue": venue,
            "side": side,
            "requested_size": size,
            "verdict": "not_fillable",
            "fillable_size": 0.0,
            "residual_size": size,
            "weighted_fill_price": None,
            "expected_slippage_pct": None,
            "liquidity_score": 0,
            "confidence": "low",
            "stale": True,
            "reason": "stale_depth_rejected",
            "snapshot_age_ms": _snapshot_age_ms(book),
            "evidence_class": "BACKTESTED",
        }

    levels = _book_for_side(book, side)
    filled, wavg, residual = _walk_book(levels, size)
    fill_ratio = filled / size if size > 0 else 0.0
    best = float(levels[0][0]) if levels else 0.0
    slip: float | None = None
    if best > 0 and filled > 0:
        slip = abs(wavg - best) / best * 100

    spread = _spread_bps(book)
    verdict = _verdict(fill_ratio, bool(levels), stale, min_ratio=min_ratio)
    score = _liquidity_score(
        fill_ratio=fill_ratio,
        depth_levels=len(levels),
        spread_bps=spread,
        stale=stale,
    )

    return {
        "ok": True,
        "symbol": sym,
        "venue": venue,
        "side": side,
        "requested_size": size,
        "verdict": verdict,
        "fillable_size": round(filled, 8),
        "residual_size": round(residual, 8),
        "weighted_fill_price": round(wavg, 2) if wavg else None,
        "expected_slippage_pct": round(slip, 4) if slip is not None else None,
        "liquidity_score": score,
        "confidence": "high" if score >= 70 else ("medium" if score >= 40 else "low"),
        "stale": False,
        "depth_levels_used": len(levels),
        "spread_bps": spread,
        "simulation_only": True,
        "evidence_class": "BACKTESTED",
    }


def max_executable_size(
    *,
    symbol: str,
    venue: str,
    side: str,
    max_slippage_pct: float = 0.5,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    sym = _normalize_symbol(symbol)
    stale_ms = int(seed.get("stale_threshold_ms") or _STALE_MS_DEFAULT)
    pair_books = (seed.get("pairs") or {}).get(sym) or {}
    book = pair_books.get(venue.lower())

    if not book or _is_stale(book, stale_ms=stale_ms):
        return {
            "ok": False,
            "symbol": sym,
            "venue": venue,
            "max_executable_size": 0.0,
            "reason": "missing_or_stale_depth",
            "evidence_class": "BACKTESTED",
        }

    levels = _book_for_side(book, side)
    if not levels:
        return {
            "ok": False,
            "symbol": sym,
            "venue": venue,
            "max_executable_size": 0.0,
            "reason": "no_levels",
            "evidence_class": "BACKTESTED",
        }

    best = float(levels[0][0])
    total_depth = sum(float(level[1]) for level in levels if len(level) >= 2)
    lo, hi = 0.0, total_depth
    result_size = 0.0
    result_price = 0.0

    for _ in range(24):
        mid = (lo + hi) / 2
        filled, wavg, _ = _walk_book(levels, mid)
        if filled <= 0:
            hi = mid
            continue
        slip = abs(wavg - best) / best * 100 if best > 0 else 999.0
        if slip <= max_slippage_pct:
            result_size = filled
            result_price = wavg
            lo = mid
        else:
            hi = mid

    return {
        "ok": True,
        "symbol": sym,
        "venue": venue,
        "side": side,
        "max_executable_size": round(result_size, 8),
        "weighted_fill_price": round(result_price, 2) if result_price else None,
        "max_slippage_pct": max_slippage_pct,
        "simulation_only": True,
        "evidence_class": "BACKTESTED",
    }


def liquidity_score_for_venue(
    symbol: str,
    venue: str,
    *,
    side: str = "buy",
    size: float = 1.0,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sim = simulate_fill(symbol=symbol, venue=venue, side=side, size=size, seed=seed)
    return {
        "symbol": sim["symbol"],
        "venue": venue,
        "liquidity_score": sim["liquidity_score"],
        "verdict": sim["verdict"],
        "fillable_size": sim["fillable_size"],
        "evidence_class": "BACKTESTED",
    }


def enrich_arbitrage_opportunity(
    opp: dict[str, Any],
    *,
    size: float = 1.0,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach volume feasibility to arbitrage scanner opportunities (#403)."""
    seed = seed or _load_seed()
    buy_v = str(opp.get("buy_venue") or "")
    sell_v = str(opp.get("sell_venue") or "")
    asset = str(opp.get("asset") or "BTC")
    symbol = str(opp.get("symbol") or f"{asset}/USDT")
    min_ratio = float(seed.get("min_fillable_ratio") or _MIN_FILL_RATIO)

    buy_sim = simulate_fill(symbol=symbol, venue=buy_v, side="buy", size=size, seed=seed) if buy_v else None
    sell_sim = simulate_fill(symbol=symbol, venue=sell_v, side="sell", size=size, seed=seed) if sell_v else None

    from bd_platform.exchange_health_monitor import evaluate_exchange

    buy_health = evaluate_exchange(buy_v) if buy_v else None
    sell_health = evaluate_exchange(sell_v) if sell_v else None
    health_suppressed = (
        (buy_health or {}).get("low_health")
        or (sell_health or {}).get("low_health")
    )

    buy_fill = (buy_sim or {}).get("fillable_size") or 0.0
    sell_fill = (sell_sim or {}).get("fillable_size") or 0.0
    max_feasible = min(buy_fill, sell_fill) if buy_fill and sell_fill else 0.0

    scores = [
        s for s in [
            (buy_sim or {}).get("liquidity_score"),
            (sell_sim or {}).get("liquidity_score"),
        ]
        if s is not None
    ]
    avg_score = int(sum(scores) / len(scores)) if scores else 0

    enriched = dict(opp)
    enriched["volume_feasibility"] = {
        "requested_size": size,
        "max_executable_size": round(max_feasible, 8),
        "buy_leg": buy_sim,
        "sell_leg": sell_sim,
        "liquidity_score": avg_score,
        "signal_suppressed": max_feasible < size * min_ratio or health_suppressed,
        "exchange_health_suppressed": health_suppressed,
        "buy_venue_grade": (buy_health or {}).get("exchange_grade"),
        "sell_venue_grade": (sell_health or {}).get("exchange_grade"),
        "simulation_only": True,
        "evidence_class": "BACKTESTED",
    }
    return enriched


def build_arbitrage_feasibility_panel(
    symbol: str = "BTC/USDT",
    *,
    size: float = 1.0,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    sym = _normalize_symbol(symbol)
    asset = sym.split("/")[0]
    opps = [
        o for o in (seed.get("arbitrage_opportunities") or [])
        if str(o.get("asset", "")).upper() == asset
    ]
    enriched = [enrich_arbitrage_opportunity(o, size=size, seed=seed) for o in opps]
    vwap_benchmark = build_fair_value_index(asset, seed=None)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "symbol": sym,
        "size": size,
        "opportunities": enriched,
        "count": len(enriched),
        "vwap_benchmark": vwap_benchmark if vwap_benchmark.get("ok") else None,
        "simulation_only": True,
        "evidence_class": "BACKTESTED",
        "timestamp": _utcnow(),
    }


def build_liquidity_heatmap(
    symbol: str = "BTC/USDT",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    sym = _normalize_symbol(symbol)
    stale_ms = int(seed.get("stale_threshold_ms") or _STALE_MS_DEFAULT)
    pair_books = (seed.get("pairs") or {}).get(sym) or {}
    venues: list[dict[str, Any]] = []

    for venue, book in pair_books.items():
        if _is_stale(book, stale_ms=stale_ms):
            venues.append({
                "venue": venue,
                "liquidity_score": 0,
                "bid_depth_usd": None,
                "ask_depth_usd": None,
                "status": "stale",
            })
            continue

        bids = book.get("bids") or []
        asks = book.get("asks") or []
        bid_usd = sum(float(b[0]) * float(b[1]) for b in bids if len(b) >= 2)
        ask_usd = sum(float(a[0]) * float(a[1]) for a in asks if len(a) >= 2)
        buy_sim = simulate_fill(symbol=sym, venue=venue, side="buy", size=1.0, seed=seed, book=book)
        venues.append({
            "venue": venue,
            "liquidity_score": buy_sim["liquidity_score"],
            "bid_depth_usd": round(bid_usd, 2),
            "ask_depth_usd": round(ask_usd, 2),
            "spread_bps": _spread_bps(book),
            "status": "active",
        })

    return {
        "ok": True,
        "symbol": sym,
        "venues": sorted(venues, key=lambda v: v.get("liquidity_score") or 0, reverse=True),
        "evidence_class": "BACKTESTED",
        "timestamp": _utcnow(),
    }


def build_market_radar_panel(
    symbol: str = "BTC/USDT",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    sym = _normalize_symbol(symbol)
    asset = sym.split("/")[0]
    heatmap = build_liquidity_heatmap(sym, seed=seed)
    vwap_ctx = build_market_radar_vwap_context(asset)

    return {
        "ok": True,
        "integration": "market_radar",
        "symbol": sym,
        "liquidity_heatmap": heatmap,
        "fair_value_vwap": vwap_ctx.get("fair_value_index"),
        "venue_deviations": vwap_ctx.get("venue_deviations"),
        "evidence_class": "BACKTESTED",
        "timestamp": _utcnow(),
    }


def rank_signals_by_liquidity(
    signals: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    ranked = []
    for sig in signals:
        sym = str(sig.get("symbol") or "BTC/USDT")
        venue = str(sig.get("venue") or "binance")
        score_doc = liquidity_score_for_venue(sym, venue, seed=seed)
        merged = dict(sig)
        merged["liquidity_score"] = score_doc["liquidity_score"]
        merged["fill_verdict"] = score_doc["verdict"]
        ranked.append(merged)
    return sorted(ranked, key=lambda s: s.get("liquidity_score") or 0, reverse=True)


def build_fill_feasibility_panel(
    symbol: str = "BTC/USDT",
    *,
    venue: str = "binance",
    size: float = 5.0,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    sym = _normalize_symbol(symbol)
    buy_sim = simulate_fill(symbol=sym, venue=venue, side="buy", size=size, seed=seed)
    sell_sim = simulate_fill(symbol=sym, venue=venue, side="sell", size=size, seed=seed)
    max_buy = max_executable_size(symbol=sym, venue=venue, side="buy", seed=seed)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "symbol": sym,
        "venue": venue,
        "size": size,
        "buy_simulation": buy_sim,
        "sell_simulation": sell_sim,
        "max_executable_buy": max_buy,
        "liquidity_heatmap": build_liquidity_heatmap(sym, seed=seed),
        "arbitrage_feasibility": build_arbitrage_feasibility_panel(sym, size=size, seed=seed),
        "simulation_only": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def build_intelligence_ledger_integration(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    sample_signals = [
        {"signal_id": "sig_btc_momentum", "symbol": "BTC/USDT", "venue": "binance"},
        {"signal_id": "sig_btc_arb", "symbol": "BTC/USDT", "venue": "okx"},
    ]
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "integration": "intelligence_ledger",
        "liquidity_ranked_signals": rank_signals_by_liquidity(sample_signals, seed=seed),
        "liquidity_heatmap": build_liquidity_heatmap("BTC/USDT", seed=seed),
        "simulation_only": True,
        "evidence_class": "BACKTESTED",
        "timestamp": _utcnow(),
    }


def fill_feasibility_simulator_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "simulation_only": True,
        "venue_count": seed.get("venue_count", 0),
        "venues": seed.get("venues") or [],
        "stale_depth_rejected": True,
        "missing_depth_never_executable": True,
        "partial_fills_supported": True,
        "integrations": {
            "arbitrage_scanner_403": True,
            "market_radar": True,
            "intelligence_ledger": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "ledger layer"})
    checks.append({"id": "legal_name", "passed": seed.get("legal_name") == "Liquidity Depth Analyzer", "detail": "renamed"})

    fresh = simulate_fill(symbol="BTC/USDT", venue="binance", side="buy", size=5.0, seed=seed)
    checks.append({"id": "deterministic_replay", "passed": fresh.get("ok") and fresh.get("weighted_fill_price", 0) > 0, "detail": "book walk"})

    stale = simulate_fill(symbol="BTC/USDT", venue="okx", side="buy", size=1.0, seed=seed)
    checks.append({"id": "stale_depth_rejected", "passed": stale.get("reason") == "stale_depth_rejected", "detail": "okx stale"})

    missing = simulate_fill(symbol="BTC/USDT", venue="nonexistent", side="buy", size=1.0, seed=seed)
    checks.append({"id": "missing_depth_never_executable", "passed": missing.get("reason") == "missing_depth_never_executable", "detail": "no book"})

    partial = simulate_fill(symbol="BTC/USDT", venue="binance", side="buy", size=1000.0, seed=seed)
    checks.append({"id": "partial_fills_supported", "passed": partial.get("verdict") in {"partial_fill", "not_fillable"}, "detail": partial.get("verdict")})

    arb = build_arbitrage_feasibility_panel("BTC/USDT", size=1.0, seed=seed)
    checks.append({"id": "arbitrage_volume_feasibility", "passed": arb.get("count", 0) >= 1 and "volume_feasibility" in (arb["opportunities"][0] if arb.get("opportunities") else {}), "detail": "403 integration"})

    heatmap = build_liquidity_heatmap("BTC/USDT", seed=seed)
    checks.append({"id": "liquidity_heatmap", "passed": len(heatmap.get("venues") or []) >= 2, "detail": "market radar"})

    score = liquidity_score_for_venue("BTC/USDT", "binance", seed=seed)
    checks.append({"id": "liquidity_score_0_100", "passed": 0 <= score["liquidity_score"] <= 100, "detail": str(score["liquidity_score"])})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
