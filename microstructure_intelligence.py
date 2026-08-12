"""Microstructure + liquidity intelligence — depth, imbalance, impact, capacity."""

from __future__ import annotations

from typing import Any

from confidence_truth import claim_heuristic, claim_insufficient


def order_book_microstructure(book: dict[str, Any], *, notional: float = 10_000.0) -> dict[str, Any]:
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    if not bids or not asks:
        return {
            "kind": "microstructure",
            "executable": False,
            "reason": "empty_book",
            "score": claim_insufficient(label="microstructure").to_dict(),
        }
    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    if best_bid <= 0 or best_ask <= 0 or best_ask < best_bid:
        return {
            "kind": "microstructure",
            "executable": False,
            "reason": "crossed_or_invalid",
            "score": claim_insufficient(label="microstructure").to_dict(),
        }
    mid = (best_bid + best_ask) / 2.0
    spread_bps = ((best_ask - best_bid) / mid) * 10_000
    bid_depth = sum(float(p) * float(q) for p, q in bids[:10])
    ask_depth = sum(float(p) * float(q) for p, q in asks[:10])
    imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) else 0.0
    capacity = min(bid_depth, ask_depth)
    participation = float(notional) / capacity if capacity > 0 else 999.0
    anomaly = spread_bps > 50 or abs(imbalance) > 0.85 or participation > 0.25
    return {
        "kind": "microstructure",
        "best_bid": best_bid,
        "best_ask": best_ask,
        "mid": mid,
        "spread_bps": round(spread_bps, 4),
        "bid_depth_usd": round(bid_depth, 2),
        "ask_depth_usd": round(ask_depth, 2),
        "imbalance": round(imbalance, 6),
        "capacity_usd": round(capacity, 2),
        "participation": round(participation, 6),
        "anomaly": anomaly,
        "executable": not anomaly and capacity >= notional,
        "score": claim_heuristic(min(1.0, participation), label="participation").to_dict(),
    }


def liquidity_intelligence(
    books_by_venue: dict[str, dict[str, Any]],
    *,
    notional: float,
) -> dict[str, Any]:
    if not books_by_venue:
        return {
            "kind": "liquidity_intelligence",
            "executable": False,
            "reason": "no_venues",
            "score": claim_insufficient(label="liquidity").to_dict(),
        }
    rows = []
    for venue, book in books_by_venue.items():
        m = order_book_microstructure(book, notional=notional)
        rows.append({"venue": venue, **m})
    ok = [r for r in rows if r.get("executable")]
    frag = len(rows) >= 2 and len(ok) < len(rows)
    return {
        "kind": "liquidity_intelligence",
        "venues": rows,
        "fragmentation": frag,
        "exitability": bool(ok),
        "best_venues": [r["venue"] for r in ok],
        "executable": bool(ok),
        "large_capital": notional >= 50_000,
        "score": claim_heuristic(len(ok) / max(1, len(rows)), label="venue_exit_ratio").to_dict(),
    }


def microstructure_status() -> dict[str, Any]:
    return {
        "surface": "microstructure_liquidity",
        "product_complete": True,
        "modules": ["order_book_microstructure", "liquidity_intelligence"],
    }
