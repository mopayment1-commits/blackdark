"""
BLACKDARK — Stealth Execution Advisor (whale persona).

Advisory sizing / slice guidance to reduce market impact using live book
depth / ADV heuristics when available. Not a live stealth-routing guarantee.
"""

from __future__ import annotations

from typing import Any


def _estimate_adv_usd(asset: str, provided: float | None) -> tuple[float, str]:
    if provided is not None and float(provided) > 0:
        return float(provided), "caller"
    asset_u = (asset or "BTC").upper()
    # Conservative public ADV priors when book/ADV unavailable
    priors = {
        "BTC": 25_000_000_000.0,
        "ETH": 12_000_000_000.0,
        "SOL": 2_500_000_000.0,
        "BNB": 1_200_000_000.0,
        "XRP": 1_500_000_000.0,
    }
    return float(priors.get(asset_u, 50_000_000.0)), "prior_table"


def _book_depth_usd(asset: str) -> tuple[float | None, str]:
    try:
        from live_book_hub import get_top_of_book  # type: ignore

        book = get_top_of_book(f"{asset.upper()}USDT") or get_top_of_book(asset.upper())
        if not book:
            return None, "book_unavailable"
        bid = float(book.get("bid_qty") or book.get("bid_size") or 0)
        ask = float(book.get("ask_qty") or book.get("ask_size") or 0)
        mid = float(book.get("mid") or book.get("bid") or book.get("ask") or 0)
        if mid <= 0:
            return None, "book_no_mid"
        depth = (bid + ask) * mid
        return (depth if depth > 0 else None), "live_book_hub"
    except Exception:
        pass
    try:
        from live_book_hub import book_snapshot  # type: ignore

        snap = book_snapshot(asset.upper())
        if isinstance(snap, dict):
            depth = float(snap.get("top_depth_usd") or snap.get("depth_usd") or 0)
            if depth > 0:
                return depth, "live_book_snapshot"
    except Exception:
        pass
    return None, "book_unavailable"


def advise_stealth_execution(
    *,
    asset: str,
    notional_usd: float,
    side: str = "buy",
    half_life_seconds: float | None = None,
    average_daily_volume_usd: float | None = None,
) -> dict[str, Any]:
    notional = max(0.0, float(notional_usd or 0))
    adv, adv_source = _estimate_adv_usd(asset, average_daily_volume_usd)
    depth_usd, depth_source = _book_depth_usd(asset)
    participation = (notional / adv) if adv > 0 else 0.0
    depth_participation = (notional / depth_usd) if depth_usd and depth_usd > 0 else None

    if participation > 0.02 or (depth_participation is not None and depth_participation > 5):
        slices = max(5, min(20, int(max(participation, (depth_participation or 0) / 50) * 400)))
        style = "aggressive_slice"
        note = "Size is large vs ADV/depth — slice across time; avoid single print."
    elif participation > 0.005 or (depth_participation is not None and depth_participation > 1.5):
        slices = max(3, min(10, int(participation * 500) or 3))
        style = "standard_slice"
        note = "Moderate footprint — use staggered limits."
    else:
        slices = 1
        style = "single_clip_ok"
        note = "Small vs ADV — single clip usually fine."

    urgency = "normal"
    hl = half_life_seconds
    if hl is None:
        try:
            from opportunity_tracker import estimate_half_life_seconds  # type: ignore

            hl = float(estimate_half_life_seconds(asset.upper()) or 0) or None
        except Exception:
            hl = None
    if hl is not None and hl < 30:
        urgency = "edge_dying"
        note += " Half-life short — prioritize speed over stealth or stand down."

    slice_usd = round(notional / slices, 2) if slices else notional
    return {
        "asset": asset.upper(),
        "side": side.lower(),
        "notional_usd": round(notional, 2),
        "average_daily_volume_usd": round(adv, 2),
        "adv_source": adv_source,
        "top_depth_usd": round(depth_usd, 2) if depth_usd else None,
        "depth_source": depth_source,
        "participation_of_adv": round(participation, 5),
        "participation_of_top_depth": round(depth_participation, 4)
        if depth_participation is not None
        else None,
        "recommended_slices": slices,
        "slice_usd": slice_usd,
        "style": style,
        "urgency": urgency,
        "half_life_seconds": hl,
        "advice": note,
        "disclaimer": (
            "Advisory only — not a guarantee against front-running. "
            "Not financial advice. Live stealth routing may require Whale execution keys."
        ),
        "hero_deepening": "portfolio_ai",
        "status": "advisory_v2",
    }
