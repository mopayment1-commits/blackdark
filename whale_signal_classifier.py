"""
BLACKDARK — Signal vs Noise Whale Classifier (Section Z #3).

Classifies large transfers before calling them buy/sell:
internal custody move · collateral · hedged vs real accumulation/distribution.
Cross-checks Funding / OI context when available.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _base_class_from_text(direction: str, detail: str) -> tuple[str, list[str], bool, float]:
    if any(k in detail for k in ("custody", "cold wallet", "internal", "omnibus", "rebalance")):
        return "internal_custody_move", ["noise"], False, 0.72
    if any(k in detail for k in ("collateral", "margin", "deposit to futures", "futures deposit")):
        return "collateral_or_margin", ["noise"], False, 0.68
    if "bridge" in detail or "wrapped" in detail:
        return "bridge_or_wrap", ["noise"], False, 0.6
    if "in" in direction or "buy" in direction or "accum" in direction:
        return "possible_accumulation", ["candidate_signal"], True, 0.55
    if "out" in direction or "sell" in direction or "distrib" in direction:
        return "possible_distribution", ["candidate_signal"], True, 0.55
    return "unclassified_transfer", ["noise_until_proven"], False, 0.4


def _apply_funding_hedge(
    class_id: str,
    actionable: bool,
    tags: list[str],
    confidence: float,
    funding: Any,
) -> tuple[str, bool, list[str], float, str | None]:
    if not actionable or funding is None:
        return class_id, actionable, tags, confidence, None
    try:
        fr = float(funding)
    except (TypeError, ValueError):
        return class_id, actionable, tags, confidence, None
    if class_id == "possible_accumulation" and fr < -0.0001:
        tags.append("possible_hedge")
        return (
            "hedged_or_basis_trade",
            False,
            tags,
            0.7,
            "Funding negative while spot inflow — do not treat as naive buy.",
        )
    if class_id == "possible_distribution" and fr > 0.0003:
        tags.append("possible_hedge")
        return (
            "hedged_or_basis_trade",
            False,
            tags,
            0.65,
            "Funding elevated while spot outflow — may be hedge unwind, not pure dump.",
        )
    return class_id, actionable, tags, confidence, None


def _apply_oi_filter(
    actionable: bool,
    tags: list[str],
    confidence: float,
    hedge_note: str | None,
    oi_change: Any,
) -> tuple[list[str], float, str | None]:
    if oi_change is None or not actionable:
        return tags, confidence, hedge_note
    try:
        oi = float(oi_change)
    except (TypeError, ValueError):
        return tags, confidence, hedge_note
    if abs(oi) < 0.5:
        tags.append("flat_oi")
        hedge_note = (hedge_note or "") + " OI flat — transfer may be wallet reshuffle."
        confidence = min(confidence, 0.5)
    return tags, confidence, hedge_note


def _initial_whale_classification(direction: str, detail: str) -> dict[str, Any]:
    if any(k in detail for k in ("custody", "cold wallet", "internal", "omnibus", "rebalance")):
        return {"class_id": "internal_custody_move", "tags": ["noise"], "actionable": False, "confidence": 0.72}
    if any(k in detail for k in ("collateral", "margin", "deposit to futures", "futures deposit")):
        return {"class_id": "collateral_or_margin", "tags": ["noise"], "actionable": False, "confidence": 0.68}
    if "bridge" in detail or "wrapped" in detail:
        return {"class_id": "bridge_or_wrap", "tags": ["noise"], "actionable": False, "confidence": 0.6}
    if "in" in direction or "buy" in direction or "accum" in direction:
        return {"class_id": "possible_accumulation", "tags": ["candidate_signal"], "actionable": True, "confidence": 0.55}
    if "out" in direction or "sell" in direction or "distrib" in direction:
        return {"class_id": "possible_distribution", "tags": ["candidate_signal"], "actionable": True, "confidence": 0.55}
    return {"class_id": "unclassified_transfer", "tags": ["noise_until_proven"], "actionable": False, "confidence": 0.4}


def _apply_funding_hedge(classification: dict[str, Any], funding: Any) -> str | None:
    if not classification["actionable"] or funding is None:
        return None
    try:
        fr = float(funding)
    except (TypeError, ValueError):
        return None
    if classification["class_id"] == "possible_accumulation" and fr < -0.0001:
        classification.update({"actionable": False, "class_id": "hedged_or_basis_trade", "confidence": 0.7})
        classification["tags"].append("possible_hedge")
        return "Funding negative while spot inflow — do not treat as naive buy."
    if classification["class_id"] == "possible_distribution" and fr > 0.0003:
        classification.update({"actionable": False, "class_id": "hedged_or_basis_trade", "confidence": 0.65})
        classification["tags"].append("possible_hedge")
        return "Funding elevated while spot outflow — may be hedge unwind, not pure dump."
    return None


def _apply_oi_context(classification: dict[str, Any], oi_change: Any, hedge_note: str | None) -> str | None:
    if oi_change is None or not classification["actionable"]:
        return hedge_note
    try:
        oi = float(oi_change)
    except (TypeError, ValueError):
        return hedge_note
    if abs(oi) < 0.5:
        classification["tags"].append("flat_oi")
        classification["confidence"] = min(classification["confidence"], 0.5)
        return (hedge_note or "") + " OI flat — transfer may be wallet reshuffle."
    return hedge_note


def _whale_classification_sentence(
    *,
    label: str,
    class_id: str,
    alert: dict[str, Any],
    usd: float,
    exchange: str,
    hedge_note: str | None,
) -> str:
    return (
        f"{label}: {class_id.replace('_', ' ')} on {alert.get('asset') or '?'} "
        f"(${usd:,.0f}"
        + (f", {exchange}" if exchange else "")
        + "). "
        + (hedge_note or "Transfers are not trades — classified before direction bias.")
    )

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
    classification = _initial_whale_classification(direction, detail)
    funding = ctx.get("funding_rate")
    oi_change = ctx.get("open_interest_change_pct")
    hedge_note = _apply_funding_hedge(classification, funding)
    hedge_note = _apply_oi_context(classification, oi_change, hedge_note)
    label = "SIGNAL" if classification["actionable"] else "NOISE"
    return {
        "label": label,
        "class_id": classification["class_id"],
        "actionable": classification["actionable"],
        "confidence": round(classification["confidence"], 2),
        "tags": classification["tags"],
        "sentence": _whale_classification_sentence(
            label=label,
            class_id=classification["class_id"],
            alert=alert,
            usd=usd,
            exchange=exchange,
            hedge_note=hedge_note,
        ),
        "hedge_note": hedge_note,
        "derivatives_used": {"funding_rate": funding, "open_interest_change_pct": oi_change},
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
        lsr = row.get("long_short_ratio")
        if lsr is not None:
            try:
                out["open_interest_change_pct"] = round((float(lsr) - 1.0) * 10.0, 3)
            except (TypeError, ValueError):
                pass
        if out["funding_rate"] is None and row.get("open_interest_usd") is not None:
            out["open_interest_usd"] = row.get("open_interest_usd")
    except Exception:
        pass
    return out


def _merge_deriv(live: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    return {
        "funding_rate": live.get("funding_rate")
        if live.get("funding_rate") is not None
        else base.get("funding_rate"),
        "open_interest_change_pct": live.get("open_interest_change_pct")
        if live.get("open_interest_change_pct") is not None
        else base.get("open_interest_change_pct"),
    }


def _resolve_alert_price(alert: dict[str, Any], asset: str) -> Any:
    price = alert.get("price") or alert.get("spot_price") or alert.get("last_price")
    if price is not None:
        return price
    try:
        from live_book_hub import get_top_of_book  # type: ignore

        book = get_top_of_book(f"{asset}USDT") or get_top_of_book(asset)
        if isinstance(book, dict):
            return book.get("mid") or book.get("bid") or book.get("ask")
    except Exception:
        return None
    return None


async def _classify_alerts(
    alerts: list[dict[str, Any]],
    *,
    limit: int,
    base_deriv: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], dict[str, dict[str, Any]]]:
    classified: list[dict[str, Any]] = []
    stories: list[str] = []
    deriv_cache: dict[str, dict[str, Any]] = {}
    for alert in alerts[:limit]:
        asset = str(alert.get("asset") or "BTC").upper()
        if asset not in deriv_cache:
            live = await _derivatives_for_asset(asset)
            deriv_cache[asset] = _merge_deriv(live, base_deriv)
        c = classify_whale_alert(alert, derivatives_context=deriv_cache[asset])
        classified.append(
            {
                **{k: alert.get(k) for k in ("asset", "direction", "amount_usd", "value_usd")},
                "price": _resolve_alert_price(alert, asset),
                "funding_rate": deriv_cache[asset].get("funding_rate"),
                "open_interest_change_pct": deriv_cache[asset].get("open_interest_change_pct"),
                **c,
            }
        )
        stories.append(c["sentence"])
    return classified, stories, deriv_cache


def _append_flow_stories(stories: list[str], flows: list[dict[str, Any]]) -> list[str]:
    for flow in flows[:3]:
        sector = flow.get("sector") or "market"
        net = float(flow.get("net_flow_usd") or 0)
        stories.append(f"Sector {sector} net flow ${net:,.0f} in the last window.")
    if not stories:
        stories = ["No major whale narratives in the current window — market in equilibrium."]
    return stories


def _one_sentence(headline: str) -> str:
    one_sentence = " ".join(str(headline).split())
    if len(one_sentence) > 220:
        return one_sentence[:217].rstrip() + "…"
    return one_sentence


def _base_derivatives_context(ctx: dict[str, Any] | None) -> dict[str, Any]:
    source = ctx or {}
    return {
        "funding_rate": source.get("avg_funding_rate") or source.get("funding_rate"),
        "open_interest_change_pct": source.get("oi_change_pct") or source.get("open_interest_change_pct"),
    }


async def _derivatives_context_for_alert(
    asset: str,
    deriv_cache: dict[str, dict[str, Any]],
    base_deriv: dict[str, Any],
) -> dict[str, Any]:
    if asset not in deriv_cache:
        live = await _derivatives_for_asset(asset)
        deriv_cache[asset] = {
            "funding_rate": live.get("funding_rate")
            if live.get("funding_rate") is not None
            else base_deriv.get("funding_rate"),
            "open_interest_change_pct": live.get("open_interest_change_pct")
            if live.get("open_interest_change_pct") is not None
            else base_deriv.get("open_interest_change_pct"),
        }
    return deriv_cache[asset]


def _alert_price(alert: dict[str, Any], asset: str) -> Any:
    price = alert.get("price") or alert.get("spot_price") or alert.get("last_price")
    if price is not None:
        return price
    try:
        from live_book_hub import get_top_of_book  # type: ignore

        book = get_top_of_book(f"{asset}USDT") or get_top_of_book(asset)
        if isinstance(book, dict):
            return book.get("mid") or book.get("bid") or book.get("ask")
    except Exception:
        return None
    return None


def _classified_alert_row(
    alert: dict[str, Any],
    asset: str,
    deriv: dict[str, Any],
    classification: dict[str, Any],
) -> dict[str, Any]:
    return {
        **{k: alert.get(k) for k in ("asset", "direction", "amount_usd", "value_usd")},
        "price": _alert_price(alert, asset),
        "funding_rate": deriv.get("funding_rate"),
        "open_interest_change_pct": deriv.get("open_interest_change_pct"),
        **classification,
    }


async def _classify_whale_alerts(
    alerts: list[dict[str, Any]],
    limit: int,
    base_deriv: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], dict[str, dict[str, Any]]]:
    classified: list[dict[str, Any]] = []
    stories: list[str] = []
    deriv_cache: dict[str, dict[str, Any]] = {}
    for alert in alerts[:limit]:
        asset = str(alert.get("asset") or "BTC").upper()
        deriv = await _derivatives_context_for_alert(asset, deriv_cache, base_deriv)
        classification = classify_whale_alert(alert, derivatives_context=deriv)
        classified.append(_classified_alert_row(alert, asset, deriv, classification))
        stories.append(classification["sentence"])
    return classified, stories, deriv_cache


def _append_flow_stories(stories: list[str], flows: list[dict[str, Any]]) -> None:
    for flow in flows[:3]:
        sector = flow.get("sector") or "market"
        net = float(flow.get("net_flow_usd") or 0)
        stories.append(f"Sector {sector} net flow ${net:,.0f} in the last window.")


def _one_sentence_story(stories: list[str]) -> str:
    headline = stories[0] if stories else ""
    one_sentence = " ".join(str(headline).split())
    if len(one_sentence) > 220:
        return one_sentence[:217].rstrip() + "…"
    return one_sentence


def _derivatives_wired(deriv_cache: dict[str, dict[str, Any]], base_deriv: dict[str, Any]) -> bool:
    return any((d.get("funding_rate") is not None) for d in deriv_cache.values()) or base_deriv.get("funding_rate") is not None

async def enrich_whale_narratives(limit: int = 5) -> dict[str, Any]:
    """Whale stories with Signal vs Noise classification attached."""
    from whale_tracker import (
        get_latest_institutional_context,
        get_latest_sector_flows,
        get_latest_whale_alerts,
    )

    alerts = await get_latest_whale_alerts(limit=limit)
    flows = await get_latest_sector_flows(limit=min(3, limit))
    base_deriv = _base_derivatives_context(await get_latest_institutional_context())
    classified, stories, deriv_cache = await _classify_whale_alerts(alerts, limit, base_deriv)
    _append_flow_stories(stories, flows)
    if not stories:
        stories = ["No major whale narratives in the current window — market in equilibrium."]
    one_sentence = _one_sentence_story(stories)
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "headline": one_sentence,
        "one_sentence": one_sentence,
        "stories": stories,
        "alert_count": len(alerts),
        "flow_count": len(flows),
        "classified": classified,
        "classifier": "signal_vs_noise_v1",
        "derivatives_wired": _derivatives_wired(deriv_cache, base_deriv),
        "note": "Transfers ≠ trades. Funding/OI hedge check applied when available.",
        "hero": "whale_intelligence_radar",
        "acceptance": "one_plain_sentence_signal_vs_noise",
    }
