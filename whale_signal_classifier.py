"""
BLACKDARK — Signal vs Noise Whale Classifier (Section Z #3).

Classifies large transfers before calling them buy/sell:
internal custody move · collateral · hedged vs real accumulation/distribution.
Cross-checks Funding / OI context when available.
"""

from __future__ import annotations

from typing import Any


def classify_whale_alert(
    alert: dict[str, Any],
    *,
    derivatives_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return signal-vs-noise classification for one whale alert."""
    ctx = derivatives_context or {}
    direction = str(alert.get("direction") or alert.get("flow_type") or alert.get("side") or "").lower()
    detail = str(alert.get("detail") or alert.get("narrative") or alert.get("note") or "").lower()
    exchange = str(alert.get("exchange") or alert.get("venue") or "").lower()
    usd = float(alert.get("amount_usd") or alert.get("value_usd") or alert.get("notional_usd") or 0)

    tags: list[str] = []
    class_id = "unknown_transfer"
    actionable = False
    confidence = 0.45

    # Noise heuristics (documented market failure: transfers ≠ trades)
    if any(k in detail for k in ("custody", "cold wallet", "internal", "omnibus", "rebalance")):
        class_id = "internal_custody_move"
        tags.append("noise")
        confidence = 0.72
    elif any(k in detail for k in ("collateral", "margin", "deposit to futures", "futures deposit")):
        class_id = "collateral_or_margin"
        tags.append("noise")
        confidence = 0.68
    elif "bridge" in detail or "wrapped" in detail:
        class_id = "bridge_or_wrap"
        tags.append("noise")
        confidence = 0.6
    elif "in" in direction or "buy" in direction or "accum" in direction:
        class_id = "possible_accumulation"
        tags.append("candidate_signal")
        actionable = True
        confidence = 0.55
    elif "out" in direction or "sell" in direction or "distrib" in direction:
        class_id = "possible_distribution"
        tags.append("candidate_signal")
        actionable = True
        confidence = 0.55
    else:
        class_id = "unclassified_transfer"
        tags.append("noise_until_proven")
        confidence = 0.4

    # Hedge cross-check via funding / OI
    funding = ctx.get("funding_rate")
    oi_change = ctx.get("open_interest_change_pct")
    hedge_note = None
    if actionable and funding is not None:
        try:
            fr = float(funding)
            if class_id == "possible_accumulation" and fr < -0.0001:
                # Spot buy while funding very negative often = basis trade / hedge
                tags.append("possible_hedge")
                actionable = False
                class_id = "hedged_or_basis_trade"
                hedge_note = "Funding negative while spot inflow — do not treat as naive buy."
                confidence = 0.7
            elif class_id == "possible_distribution" and fr > 0.0003:
                tags.append("possible_hedge")
                actionable = False
                class_id = "hedged_or_basis_trade"
                hedge_note = "Funding elevated while spot outflow — may be hedge unwind, not pure dump."
                confidence = 0.65
        except (TypeError, ValueError):
            pass

    if oi_change is not None and actionable:
        try:
            oi = float(oi_change)
            if abs(oi) < 0.5:
                tags.append("flat_oi")
                hedge_note = (hedge_note or "") + " OI flat — transfer may be wallet reshuffle."
                confidence = min(confidence, 0.5)
        except (TypeError, ValueError):
            pass

    label = "SIGNAL" if actionable else "NOISE"
    sentence = (
        f"{label}: {class_id.replace('_', ' ')} on {alert.get('asset') or '?'} "
        f"(${usd:,.0f}"
        + (f", {exchange}" if exchange else "")
        + "). "
        + (hedge_note or "Transfers are not trades — classified before direction bias.")
    )

    return {
        "label": label,
        "class_id": class_id,
        "actionable": actionable,
        "confidence": round(confidence, 2),
        "tags": tags,
        "sentence": sentence,
        "hedge_note": hedge_note,
        "derivatives_used": {
            "funding_rate": funding,
            "open_interest_change_pct": oi_change,
        },
        "hero_deepening": "whale_intelligence",
    }


async def _derivatives_for_asset(asset: str) -> dict[str, Any]:
    """Pull live Funding/OI so hedge cross-check actually fires (report Z3)."""
    symbol = (asset or "BTC").upper().replace("USDT", "")
    out: dict[str, Any] = {"funding_rate": None, "open_interest_change_pct": None}
    try:
        import aiohttp

        from oracle_data_hub import fetch_onchain_derivatives_mesh

        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            row = await fetch_onchain_derivatives_mesh(session, asset=symbol)
        out["funding_rate"] = row.get("funding_rate")
        # Approximate OI pressure from long/short when % change absent
        lsr = row.get("long_short_ratio")
        if lsr is not None:
            try:
                # Map crowded longs → positive "oi pressure" proxy for classifier
                out["open_interest_change_pct"] = round((float(lsr) - 1.0) * 10.0, 3)
            except (TypeError, ValueError):
                pass
        if out["funding_rate"] is None and row.get("open_interest_usd") is not None:
            out["open_interest_usd"] = row.get("open_interest_usd")
    except Exception:
        pass
    return out


async def enrich_whale_narratives(limit: int = 5) -> dict[str, Any]:
    """Whale stories with Signal vs Noise classification attached."""
    from datetime import datetime, timezone

    from whale_tracker import (
        get_latest_institutional_context,
        get_latest_sector_flows,
        get_latest_whale_alerts,
    )

    alerts = await get_latest_whale_alerts(limit=limit)
    flows = await get_latest_sector_flows(limit=min(3, limit))
    ctx = await get_latest_institutional_context()
    base_deriv = {
        "funding_rate": (ctx or {}).get("avg_funding_rate") or (ctx or {}).get("funding_rate"),
        "open_interest_change_pct": (ctx or {}).get("oi_change_pct")
        or (ctx or {}).get("open_interest_change_pct"),
    }

    classified = []
    stories = []
    deriv_cache: dict[str, dict[str, Any]] = {}
    for alert in alerts[:limit]:
        asset = str(alert.get("asset") or "BTC").upper()
        if asset not in deriv_cache:
            live = await _derivatives_for_asset(asset)
            # Prefer live hub values; fall back to institutional context
            deriv_cache[asset] = {
                "funding_rate": live.get("funding_rate")
                if live.get("funding_rate") is not None
                else base_deriv.get("funding_rate"),
                "open_interest_change_pct": live.get("open_interest_change_pct")
                if live.get("open_interest_change_pct") is not None
                else base_deriv.get("open_interest_change_pct"),
            }
        c = classify_whale_alert(alert, derivatives_context=deriv_cache[asset])
        price = alert.get("price") or alert.get("spot_price") or alert.get("last_price")
        if price is None:
            try:
                from live_book_hub import get_top_of_book  # type: ignore

                book = get_top_of_book(f"{asset}USDT") or get_top_of_book(asset)
                if isinstance(book, dict):
                    price = book.get("mid") or book.get("bid") or book.get("ask")
            except Exception:
                price = None
        classified.append(
            {
                **{k: alert.get(k) for k in ("asset", "direction", "amount_usd", "value_usd")},
                "price": price,
                "funding_rate": deriv_cache[asset].get("funding_rate"),
                "open_interest_change_pct": deriv_cache[asset].get("open_interest_change_pct"),
                **c,
            }
        )
        stories.append(c["sentence"])

    for flow in flows[:3]:
        sector = flow.get("sector") or "market"
        net = float(flow.get("net_flow_usd") or 0)
        stories.append(f"Sector {sector} net flow ${net:,.0f} in the last window.")

    if not stories:
        stories = ["No major whale narratives in the current window — market in equilibrium."]

    headline = stories[0] if stories else ""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "headline": headline,
        "stories": stories,
        "alert_count": len(alerts),
        "flow_count": len(flows),
        "classified": classified,
        "classifier": "signal_vs_noise_v1",
        "derivatives_wired": any(
            (d.get("funding_rate") is not None) for d in deriv_cache.values()
        )
        or base_deriv.get("funding_rate") is not None,
        "note": "Transfers ≠ trades. Funding/OI hedge check applied when available.",
    }
