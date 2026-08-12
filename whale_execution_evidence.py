"""Whale readiness evidence — measured large-capital depth/impact/exitability."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from canonical_adoption import adopt_order_books, adopt_symbol, adopt_venue
from path_safety import ensure_under, safe_data_file

_EVIDENCE = safe_data_file("whale_execution_evidence.jsonl")
_DATA_BASE = Path(__file__).resolve().parent / "data"

# Default whale notionals under test (USD)
WHALE_NOTIONALS_USD = (50_000.0, 250_000.0, 1_000_000.0)


@dataclass
class WhaleDepthProbe:
    symbol: str
    venue: str
    notional_usd: float
    side: str
    filled: bool
    slippage_bps: float | None
    levels_consumed: int
    capacity_usd: float
    market_impact_bps: float | None
    exitable: bool
    executable: bool
    reason: str = ""


def _walk_capacity(book: dict[str, Any], *, side: str, notional: float) -> WhaleDepthProbe | None:
    """Measure capacity and slippage for a large notional on one book."""
    from arbitrage_engine import walk_asks, walk_bids

    venue = adopt_venue(str(book.get("venue") or "unknown"))
    symbol = adopt_symbol(str(book.get("symbol") or "BTC/USDT"))
    if side == "buy":
        ex = walk_asks(book, notional)
        if ex is None:
            # compute raw capacity
            asks = book.get("asks") or []
            cap = sum(float(p) * float(q) for p, q in asks)
            return WhaleDepthProbe(
                symbol=symbol,
                venue=venue,
                notional_usd=notional,
                side=side,
                filled=False,
                slippage_bps=None,
                levels_consumed=0,
                capacity_usd=cap,
                market_impact_bps=None,
                exitable=False,
                executable=False,
                reason="insufficient_ask_depth",
            )
        return WhaleDepthProbe(
            symbol=symbol,
            venue=venue,
            notional_usd=notional,
            side=side,
            filled=True,
            slippage_bps=float(ex.slippage_bps),
            levels_consumed=int(ex.levels_consumed),
            capacity_usd=float(ex.quote_cost),
            market_impact_bps=float(ex.slippage_bps),
            exitable=True,
            executable=float(ex.slippage_bps) < 150.0,
            reason="" if float(ex.slippage_bps) < 150.0 else "impact_too_high",
        )
    # sell: convert notional to base via mid
    bids = book.get("bids") or []
    if not bids:
        return WhaleDepthProbe(
            symbol=symbol,
            venue=venue,
            notional_usd=notional,
            side=side,
            filled=False,
            slippage_bps=None,
            levels_consumed=0,
            capacity_usd=0.0,
            market_impact_bps=None,
            exitable=False,
            executable=False,
            reason="no_bids",
        )
    mid = float(bids[0][0])
    base_amt = notional / mid if mid > 0 else 0.0
    ex = walk_bids(book, base_amt)
    if ex is None:
        cap = sum(float(p) * float(q) for p, q in bids)
        return WhaleDepthProbe(
            symbol=symbol,
            venue=venue,
            notional_usd=notional,
            side=side,
            filled=False,
            slippage_bps=None,
            levels_consumed=0,
            capacity_usd=cap,
            market_impact_bps=None,
            exitable=False,
            executable=False,
            reason="insufficient_bid_depth",
        )
    return WhaleDepthProbe(
        symbol=symbol,
        venue=venue,
        notional_usd=notional,
        side=side,
        filled=True,
        slippage_bps=float(ex.slippage_bps),
        levels_consumed=int(ex.levels_consumed),
        capacity_usd=float(ex.quote_value),
        market_impact_bps=float(ex.slippage_bps),
        exitable=True,
        executable=float(ex.slippage_bps) < 150.0,
        reason="" if float(ex.slippage_bps) < 150.0 else "impact_too_high",
    )


def score_capital_aware(
    *,
    base_score: float,
    notional_usd: float,
    probes: list[WhaleDepthProbe],
) -> dict[str, Any]:
    """Down-weight opportunity score when large capital cannot exit cleanly."""
    if not probes:
        return {
            "capital_aware_score": None,
            "executable": False,
            "reason": "no_probes",
            "confidence_type": "insufficient_evidence",
        }
    exec_ok = all(p.executable for p in probes)
    max_impact = max((p.market_impact_bps or 0.0) for p in probes)
    # Linear penalty above 25 bps
    penalty = max(0.0, (max_impact - 25.0) / 100.0)
    score = max(0.0, float(base_score) * (1.0 - min(0.9, penalty)))
    if notional_usd >= 250_000 and not exec_ok:
        score = 0.0
    return {
        "capital_aware_score": round(score, 4),
        "executable": exec_ok,
        "max_impact_bps": max_impact,
        "notional_usd": notional_usd,
        "confidence_type": "heuristic_score",
    }


def measure_whale_readiness(
    order_books: dict[str, dict[str, dict[str, Any]]],
    *,
    symbol: str,
    notionals: tuple[float, ...] = WHALE_NOTIONALS_USD,
) -> dict[str, Any]:
    books = adopt_order_books(order_books, source="whale_evidence")
    sym = adopt_symbol(symbol)
    probes: list[dict[str, Any]] = []
    for venue, symbols in books.items():
        book = symbols.get(sym) or symbols.get(f"{sym}@perpetual")
        if not book:
            continue
        book = {**book, "venue": venue, "symbol": sym}
        for n in notionals:
            for side in ("buy", "sell"):
                probe = _walk_capacity(book, side=side, notional=n)
                if probe:
                    probes.append(asdict(probe))
    if not probes:
        result = {
            "whale_ready": False,
            "reason": "no_books_for_symbol",
            "symbol": sym,
            "probes": [],
            "product_complete": False,
            "measured_at": datetime.now(UTC).isoformat(),
        }
    else:
        # Ready only if 50k buy+sell executable on >=2 venues
        venues_ok = set()
        for p in probes:
            if p["notional_usd"] == 50_000 and p["executable"]:
                venues_ok.add((p["venue"], p["side"]))
        buy_venues = {v for v, s in venues_ok if s == "buy"}
        sell_venues = {v for v, s in venues_ok if s == "sell"}
        ready = len(buy_venues) >= 2 and len(sell_venues) >= 2
        scoring = score_capital_aware(
            base_score=80.0,
            notional_usd=250_000,
            probes=[WhaleDepthProbe(**p) for p in probes if p["notional_usd"] == 250_000],
        )
        result = {
            "whale_ready": ready,
            "symbol": sym,
            "venues_buy_ok": sorted(buy_venues),
            "venues_sell_ok": sorted(sell_venues),
            "probes": probes,
            "capital_aware": scoring,
            "product_complete": ready,
            "measured_at": datetime.now(UTC).isoformat(),
            "evidence_standard": "depth_walk_slippage_capacity_exitability",
        }
    path = ensure_under(_EVIDENCE, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(result, ensure_ascii=False) + "\n")
    return result


def whale_status() -> dict[str, Any]:
    return {
        "surface": "whale_execution_evidence",
        "notionals_usd": list(WHALE_NOTIONALS_USD),
        "product_complete": True,
        "note": "Whale readiness requires measured multi-venue depth/impact evidence — not endpoint existence.",
    }
