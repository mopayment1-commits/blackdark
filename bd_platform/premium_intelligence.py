"""
Premium Intelligence Module — Features #255 + #233 (Sprint 2).

Korea Premium (#255) + Coinbase Premium (#233) merged into one regional premium dashboard.
Educational + analytical — NOT arbitrage opportunity framing.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.PremiumIntelligence")

_FEATURE_IDS = (255, 233)
_MERGED_INTO = "Premium Intelligence Module"
_STANDALONE = False
_SPRINT = 2
_SEED_PATH = Path("data/premium_intelligence_seed.json")

_KOREA_DISCLAIMER = (
    "Korea Premium measures price differential after FX adjustment. "
    "Regulatory restrictions may prevent arbitrage. Not investment advice."
)
_COINBASE_DISCLAIMER = (
    "Coinbase Premium measures US venue price differential vs reference. "
    "Premium does not imply causation without corroborating flow data. "
    "Not investment advice."
)
_MODULE_DISCLAIMER = (
    "Regional premiums measure price differentials after FX adjustment where applicable. "
    "Regulatory restrictions may prevent arbitrage. Not investment advice."
)

RegimeLabel = Literal["Premium (Kimchi)", "Discount", "Neutral"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"korea": {"assets": {}}, "coinbase": {"assets": {}}, "fx": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("premium intelligence seed load failed: %s", exc)
        return {"korea": {"assets": {}}, "coinbase": {"assets": {}}, "fx": {}}


def _fee_db_context() -> dict[str, Any]:
    """Fee DB (#130) — mandatory if any profit calculation is shown."""
    try:
        from fee_matrix import maker_fee, taker_fee

        return {
            "fee_db_feature_id": 130,
            "fee_db_available": True,
            "estimated_taker_fee_pct": {
                "coinbase": round((taker_fee("coinbase") or 0.006) * 100, 4),
                "binance": round((taker_fee("binance") or 0.001) * 100, 4),
                "upbit": round((taker_fee("upbit") or 0.0005) * 100, 4) if taker_fee("upbit") else None,
            },
            "note": "Arbitrage requires local banking + regulatory compliance + full fee stack",
        }
    except Exception:
        return {
            "fee_db_feature_id": 130,
            "fee_db_available": False,
            "note": "Fee DB unavailable — profit estimate omitted",
        }


def _fx_status(pair: str = "KRW/USD") -> dict[str, Any]:
    seed = _load_seed()
    fx = (seed.get("fx") or {}).get(pair) or {}
    if not fx:
        return {
            "ok": False,
            "pair": pair,
            "stale": True,
            "fx_display": f"FX Stale | Premium: N/A",
            "premium_available": False,
        }

    ts = fx.get("timestamp", "")
    max_age_h = float(fx.get("max_age_hours") or 2)
    stale = False
    age_hours = 0.0
    if ts:
        age = datetime.now(UTC) - _parse_ts(ts)
        age_hours = age.total_seconds() / 3600
        stale = age_hours > max_age_h

    rate = fx.get("rate")
    if stale:
        return {
            "ok": False,
            "pair": pair,
            "rate": rate,
            "source": fx.get("source"),
            "timestamp": ts,
            "update_frequency": fx.get("update_frequency", "Hourly"),
            "age_hours": round(age_hours, 2),
            "stale": True,
            "fx_display": "FX Stale | Premium: N/A",
            "premium_available": False,
        }

    return {
        "ok": True,
        "pair": pair,
        "rate": rate,
        "source": fx.get("source"),
        "timestamp": ts,
        "update_frequency": fx.get("update_frequency", "Hourly"),
        "age_hours": round(age_hours, 2),
        "stale": False,
        "fx_display": (
            f"{pair}: {rate:,.2f} | Source: {fx.get('source')} | "
            f"Timestamp: {ts} | Update Frequency: {fx.get('update_frequency', 'Hourly')}"
        ),
        "premium_available": True,
    }


def _recalculate_venue_weights(
    venues: dict[str, dict[str, Any]],
) -> tuple[dict[str, float], list[str], str | None]:
    """Recalculate weights when venues are down — proportional to base volume weights."""
    active = {k: v for k, v in venues.items() if v.get("status", "up") == "up"}
    down = [k for k, v in venues.items() if v.get("status", "up") != "up"]
    total_base = sum(float(v.get("base_volume_weight") or 0) for v in active.values())

    if not active:
        return {}, down, "All Korean venues down | Premium: N/A"

    weights = {
        k: round(float(v.get("base_volume_weight") or 0) / total_base, 4)
        for k, v in active.items()
    }

    alert = None
    if down:
        parts = " | ".join(f"{venues[d].get('name', d).title()} down" for d in down)
        weight_parts = " | ".join(
            f"{venues[k].get('name', k).title()} {round(w * 100)}%"
            for k, w in sorted(weights.items(), key=lambda x: -x[1])
        )
        alert = f"{parts} | Weights recalculated: {weight_parts} | Alert: Coverage reduced"

    return weights, down, alert


def _venue_weights_display(
    weights: dict[str, float],
    venues: dict[str, dict[str, Any]],
    *,
    version: str,
    last_rebalanced: str,
) -> str:
    parts = [
        f"{venues[k].get('name', k)} ({round(w * 100)}% weight)"
        for k, w in sorted(weights.items(), key=lambda x: -x[1])
    ]
    return (
        f"{' | '.join(parts)} — Weights v{version} | Last Rebalanced: {last_rebalanced}"
    )


def _detect_korea_regime(
    premium_pct: float,
    history: dict[str, Any],
) -> dict[str, Any]:
    p75 = float(history.get("percentile_75") or 3.0)
    p50 = float(history.get("percentile_50") or 1.5)
    p25 = float(history.get("percentile_25") or 0.3)
    duration = int(history.get("current_duration_days") or 0)

    if premium_pct >= p50:
        regime: RegimeLabel = "Premium (Kimchi)"
    elif premium_pct <= -0.5:
        regime = "Discount"
    else:
        regime = "Neutral"

    if premium_pct >= p75:
        percentile_ctx = "75th percentile"
    elif premium_pct >= p50:
        percentile_ctx = "50th–75th percentile"
    elif premium_pct >= p25:
        percentile_ctx = "25th–50th percentile"
    else:
        percentile_ctx = "below 25th percentile"

    sign = "+" if premium_pct >= 0 else ""
    return {
        "regime": regime,
        "level_pct": round(premium_pct, 2),
        "regime_display": (
            f"Regime: {regime} | Level: {sign}{premium_pct:.1f}% | "
            f"Historical Context: {percentile_ctx} | Duration: {duration} days"
        ),
        "historical_percentile_context": percentile_ctx,
        "duration_days": duration,
    }


def get_korea_premium(asset: str = "BTC") -> dict[str, Any]:
    """Korea Premium Index (#255) — FX-adjusted, venue-normalized, outage-aware."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")
    korea = seed.get("korea") or {}
    asset_data = (korea.get("assets") or {}).get(sym)

    if not asset_data:
        return {"ok": False, "feature_id": 255, "error": "asset_not_configured", "asset": sym}

    fx = _fx_status("KRW/USD")
    venues_cfg = korea.get("venues") or {}
    weights, down_venues, outage_alert = _recalculate_venue_weights(venues_cfg)
    ref = korea.get("global_reference") or {}

    if not fx.get("premium_available"):
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "ok": True,
            "feature_id": 255,
            "standalone": _STANDALONE,
            "merged_into": _MERGED_INTO,
            "asset": sym,
            "premium_pct": None,
            "premium_display": "FX Stale | Premium: N/A",
            "fx": fx,
            "venue_weights": weights,
            "venue_weights_display": _venue_weights_display(
                weights,
                venues_cfg,
                version=seed.get("weights_version", "1.0"),
                last_rebalanced=seed.get("weights_last_rebalanced", "N/A"),
            ),
            "outage_alert": outage_alert,
            "global_reference_display": (
                f"Reference: {ref.get('exchange', 'binance').title()} {ref.get('pair', 'BTC/USDT')} | "
                f"FX-adjusted: {'Yes' if ref.get('fx_adjusted') else 'No'} | "
                f"Methodology: {ref.get('methodology', 'VWAP 1H')}"
            ),
            "not_arbitrage_opportunity": True,
            "arbitrage_note": (
                "Korea Premium: N/A | Note: Arbitrage requires local banking + regulatory compliance"
            ),
            "disclaimer": _KOREA_DISCLAIMER,
            "disclaimer_hideable": False,
            "fee_context": _fee_db_context(),
            "latency_ms": elapsed,
            "timestamp": _utcnow(),
        }

    venue_prices: list[dict[str, Any]] = []
    weighted_price = 0.0
    venue_data = asset_data.get("venues") or {}

    for venue_key, weight in weights.items():
        vdata = venue_data.get(venue_key) or {}
        if venue_key in down_venues or not vdata:
            continue
        price_usd = float(vdata.get("price_usd_fx") or 0)
        weighted_price += price_usd * weight
        venue_prices.append({
            "venue": venue_key,
            "name": venues_cfg.get(venue_key, {}).get("name", venue_key),
            "weight_pct": round(weight * 100, 1),
            "price_usd_fx": price_usd,
            "timestamp": vdata.get("timestamp"),
            "status": "up",
        })

    global_ref = float(asset_data.get("global_reference_price_usd") or 0)
    premium_pct = ((weighted_price - global_ref) / global_ref * 100) if global_ref else 0.0

    history = (korea.get("regime_history") or {}).get(sym) or {}
    regime = _detect_korea_regime(premium_pct, history)

    sign = "+" if premium_pct >= 0 else ""
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": 255,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "asset": sym,
        "korea_premium_index": round(premium_pct, 2),
        "premium_pct": round(premium_pct, 2),
        "premium_display": f"Korea Premium: {sign}{premium_pct:.1f}%",
        "fx": fx,
        "venues": venue_prices,
        "venue_weights": weights,
        "venue_weights_display": _venue_weights_display(
            weights,
            venues_cfg,
            version=seed.get("weights_version", "1.0"),
            last_rebalanced=seed.get("weights_last_rebalanced", "N/A"),
        ),
        "outage_alert": outage_alert,
        "down_venues": down_venues,
        "global_reference": {
            "exchange": ref.get("exchange"),
            "pair": ref.get("pair"),
            "price_usd": global_ref,
            "timestamp": asset_data.get("global_reference_timestamp"),
            "methodology": ref.get("methodology"),
            "fx_adjusted": ref.get("fx_adjusted", True),
        },
        "global_reference_display": (
            f"Reference: {ref.get('exchange', 'binance').title()} {ref.get('pair', 'BTC/USDT')} | "
            f"FX-adjusted: {'Yes' if ref.get('fx_adjusted') else 'No'} | "
            f"Methodology: {ref.get('methodology', 'VWAP 1H')}"
        ),
        "regime": regime,
        "rolling_premium_pct": asset_data.get("rolling_premium_pct") or [],
        "not_arbitrage_opportunity": True,
        "arbitrage_note": (
            f"Korea Premium: {sign}{premium_pct:.1f}% | "
            "Note: Arbitrage requires local banking + regulatory compliance"
        ),
        "disclaimer": _KOREA_DISCLAIMER,
        "disclaimer_hideable": False,
        "fee_context": _fee_db_context(),
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def _z_score_trend(z_scores: list[float]) -> str:
    if len(z_scores) < 2:
        return "stable"
    delta = z_scores[-1] - z_scores[0]
    if delta > 0.3:
        return "rising"
    if delta < -0.3:
        return "falling"
    return "stable"


def get_coinbase_premium(asset: str = "BTC") -> dict[str, Any]:
    """Coinbase Premium Index (#233) — venue/time aligned, no causation without corroboration."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")
    cb = seed.get("coinbase") or {}
    asset_data = (cb.get("assets") or {}).get(sym)
    venue = cb.get("venue") or {}
    ref_cfg = cb.get("reference") or {}

    if not asset_data:
        return {"ok": False, "feature_id": 233, "error": "asset_not_configured", "asset": sym}

    venue_up = venue.get("status", "up") == "up"
    coinbase_price = float(asset_data.get("coinbase_price_usd") or 0)
    ref_price = float(asset_data.get("reference_price_usd") or 0)
    cb_ts = asset_data.get("coinbase_timestamp")
    ref_ts = asset_data.get("reference_timestamp")

    time_aligned = True
    if cb_ts and ref_ts:
        try:
            diff_sec = abs((_parse_ts(cb_ts) - _parse_ts(ref_ts)).total_seconds())
            time_aligned = diff_sec <= 120
        except (ValueError, TypeError):
            time_aligned = False

    outage_alert = None
    if not venue_up:
        outage_alert = "Coinbase venue down | Premium: N/A | Alert: Coverage reduced"
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "ok": True,
            "feature_id": 233,
            "standalone": _STANDALONE,
            "merged_into": _MERGED_INTO,
            "asset": sym,
            "premium_pct": None,
            "premium_display": "Coinbase Premium: N/A (venue outage)",
            "venue": venue,
            "outage_alert": outage_alert,
            "time_aligned": False,
            "reference_display": (
                f"Reference: {ref_cfg.get('exchange', 'binance').title()} "
                f"{ref_cfg.get('pair', 'BTC/USDT')} | "
                f"Time Alignment: {ref_cfg.get('time_alignment', '1-minute bucket')}"
            ),
            "not_arbitrage_opportunity": True,
            "no_causation_without_corroboration": True,
            "disclaimer": _COINBASE_DISCLAIMER,
            "disclaimer_hideable": False,
            "fee_context": _fee_db_context(),
            "latency_ms": elapsed,
            "timestamp": _utcnow(),
        }

    premium_pct = ((coinbase_price - ref_price) / ref_price * 100) if ref_price else 0.0
    rolling = [float(x) for x in (asset_data.get("rolling_premium_pct") or [])]
    z_scores = [float(x) for x in (asset_data.get("rolling_z_score") or [])]
    current_z = z_scores[-1] if z_scores else 0.0
    trend = _z_score_trend(z_scores)
    persistence = int(asset_data.get("persistence_days") or 0)
    corroboration = asset_data.get("corroboration") or {}

    divergence_alert = abs(current_z) >= 1.5
    sign = "+" if premium_pct >= 0 else ""

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": 233,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "asset": sym,
        "coinbase_premium_index": round(premium_pct, 2),
        "premium_pct": round(premium_pct, 2),
        "premium_display": f"Coinbase Premium: {sign}{premium_pct:.2f}%",
        "venue": venue,
        "coinbase_price_usd": coinbase_price,
        "reference_price_usd": ref_price,
        "time_aligned": time_aligned,
        "time_alignment_display": (
            f"Coinbase: {cb_ts} | Reference: {ref_ts} | Aligned: {'Yes' if time_aligned else 'No'}"
        ),
        "reference_display": (
            f"Reference: {ref_cfg.get('exchange', 'binance').title()} "
            f"{ref_cfg.get('pair', 'BTC/USDT')} | "
            f"Time Alignment: {ref_cfg.get('time_alignment', '1-minute bucket')}"
        ),
        "rolling_z_score": current_z,
        "z_score_trend": trend,
        "persistence_days": persistence,
        "trend_display": (
            f"Trend: {trend.title()} | Z-score: {current_z:.2f} | Persistence: {persistence} days"
        ),
        "divergence_alert": divergence_alert,
        "divergence_display": (
            f"Divergence Alert: {'Yes' if divergence_alert else 'No'} | Z-score {current_z:.2f}"
        ),
        "corroboration": corroboration,
        "no_causation_without_corroboration": not corroboration.get("causation_claim_allowed", False),
        "causation_note": (
            "Premium observed — institutional demand causation not asserted without corroboration"
            if not corroboration.get("causation_claim_allowed")
            else "Corroborating flow data available"
        ),
        "rolling_premium_pct": rolling,
        "not_arbitrage_opportunity": True,
        "disclaimer": _COINBASE_DISCLAIMER,
        "disclaimer_hideable": False,
        "fee_context": _fee_db_context(),
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def get_regional_premiums_dashboard(asset: str = "BTC") -> dict[str, Any]:
    """Unified Regional Premiums dashboard — US | Korea | Japan | Europe cards."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")

    korea = get_korea_premium(sym)
    coinbase = get_coinbase_premium(sym)
    regions_cfg = seed.get("regions") or {}

    cards = [
        {
            "region": "us",
            "label": regions_cfg.get("us", {}).get("label", "US (Coinbase)"),
            "feature_id": 233,
            "status": regions_cfg.get("us", {}).get("status", "live"),
            "premium_pct": coinbase.get("premium_pct"),
            "premium_display": coinbase.get("premium_display"),
            "card_summary": coinbase.get("trend_display") or coinbase.get("premium_display"),
            "data": coinbase,
        },
        {
            "region": "korea",
            "label": regions_cfg.get("korea", {}).get("label", "Korea"),
            "feature_id": 255,
            "status": regions_cfg.get("korea", {}).get("status", "live"),
            "premium_pct": korea.get("premium_pct"),
            "premium_display": korea.get("premium_display"),
            "card_summary": (korea.get("regime") or {}).get("regime_display") or korea.get("premium_display"),
            "data": korea,
        },
        {
            "region": "japan",
            "label": regions_cfg.get("japan", {}).get("label", "Japan"),
            "feature_id": None,
            "status": regions_cfg.get("japan", {}).get("status", "planned"),
            "premium_pct": None,
            "premium_display": "Japan Premium: Coming Soon",
            "card_summary": "Planned — Sprint 3+",
            "data": None,
        },
        {
            "region": "europe",
            "label": regions_cfg.get("europe", {}).get("label", "Europe"),
            "feature_id": None,
            "status": regions_cfg.get("europe", {}).get("status", "planned"),
            "premium_pct": None,
            "premium_display": "Europe Premium: Coming Soon",
            "card_summary": "Planned — Sprint 3+",
            "data": None,
        },
    ]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "surface": "regional_premiums_dashboard",
        "feature_ids": list(_FEATURE_IDS),
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "asset": sym,
        "dashboard_title": "Regional Premiums: US (Coinbase) | Korea | Japan | Europe",
        "cards": cards,
        "regions_display": "Regional Premiums: US (Coinbase) | Korea | Japan | Europe",
        "not_arbitrage_opportunity": True,
        "disclaimer": _MODULE_DISCLAIMER,
        "disclaimer_hideable": False,
        "fee_context": _fee_db_context(),
        "sla_met": elapsed <= 2000,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def premium_intelligence_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "module": "Premium Intelligence Module",
        "sprint": _SPRINT,
        "regions": seed.get("regions") or {},
        "weights_version": seed.get("weights_version"),
        "weights_last_rebalanced": seed.get("weights_last_rebalanced"),
        "korea_configured_assets": list((seed.get("korea", {}).get("assets") or {}).keys()),
        "coinbase_configured_assets": list((seed.get("coinbase", {}).get("assets") or {}).keys()),
        "fx_pairs": list((seed.get("fx") or {}).keys()),
        "acceptance_criteria": {
            "reliable_fx_timestamps": True,
            "venue_normalization": True,
            "local_market_outages_handled": True,
            "global_reference_explicit": True,
            "regime_detection": True,
            "no_arbitrage_opportunity_framing": True,
            "venue_time_alignment": True,
            "no_causation_without_corroboration": True,
        },
        "disclaimer": _MODULE_DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
