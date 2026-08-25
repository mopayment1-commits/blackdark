"""
Premium Intelligence Module — Features #255 + #233 (Sprint 2).

Korea Premium (#255) + Coinbase Premium (#233) merged into one regional premium dashboard.
Educational + analytical — NOT arbitrage opportunity framing.
"""

from __future__ import annotations

import json
import logging
import statistics
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
    "Coinbase Premium measures price differential between Coinbase and reference markets. "
    "It reflects US demand conditions but does not predict future prices. Not investment advice."
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


def _format_ts_identical(ts: str) -> str:
    """Normalize timestamp for identical venue/time alignment display."""
    try:
        dt = _parse_ts(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " UTC"
    except (ValueError, TypeError):
        return ts


def _build_venue_time_alignment(
    cb_ts: str | None,
    ref_ts: str | None,
    *,
    ref_exchange: str,
    ref_pair: str,
    fx_note: str = "N/A (both USD)",
) -> dict[str, Any]:
    cb_fmt = _format_ts_identical(cb_ts or "")
    ref_fmt = _format_ts_identical(ref_ts or "")
    identical = False
    if cb_ts and ref_ts:
        try:
            identical = abs((_parse_ts(cb_ts) - _parse_ts(ref_ts)).total_seconds()) <= 1.0
        except (ValueError, TypeError):
            identical = False

    return {
        "coinbase_timestamp": cb_fmt,
        "reference_timestamp": ref_fmt,
        "fx_note": fx_note,
        "identical": identical,
        "alignment_display": (
            f"Coinbase: {cb_fmt} | Reference: {ref_exchange.title()} {ref_pair} {ref_fmt} | FX: {fx_note}"
        ),
        "time_aligned": identical,
    }


def _build_z_score_context(
    z_score: float,
    rolling_premium_pct: list[float],
    *,
    window_days: int = 30,
) -> dict[str, Any]:
    mean = round(statistics.mean(rolling_premium_pct), 2) if rolling_premium_pct else 0.0
    stddev = round(statistics.stdev(rolling_premium_pct), 2) if len(rolling_premium_pct) > 1 else 0.0

    if abs(z_score) >= 2.0:
        interpretation = "Extreme"
    elif abs(z_score) >= 1.5:
        interpretation = "Elevated but not extreme"
    elif abs(z_score) >= 1.0:
        interpretation = "Moderately elevated"
    else:
        interpretation = "Within normal range"

    sign = "+" if mean >= 0 else ""
    return {
        "z_score": round(z_score, 2),
        "window_days": window_days,
        "mean_pct": mean,
        "stddev_pct": stddev,
        "interpretation": interpretation,
        "z_score_display": (
            f"Z-Score: {z_score:.1f} | Window: {window_days}D | Mean: {sign}{mean}% | "
            f"StdDev: {stddev}% | Interpretation: {interpretation}"
        ),
    }


def _build_persistence_analysis(
    duration_days: int,
    *,
    historical_median_days: int,
) -> dict[str, Any]:
    regime = "Persistent" if duration_days > historical_median_days else "Transient"
    return {
        "duration_days": duration_days,
        "historical_median_days": historical_median_days,
        "regime": regime,
        "persistence_display": (
            f"Premium Duration: {duration_days} days | Historical median duration: "
            f"{historical_median_days} days | Regime: {regime}"
        ),
    }


def _detect_premium_price_divergence(
    premium_change_pct: float,
    price_change_pct: float,
) -> dict[str, Any]:
    """Premium vs price divergence — analysis only, not a sell signal."""
    divergence = "None"
    explanation = "Premium and price moving in alignment"
    confidence = 0.0

    if premium_change_pct > 0 and price_change_pct < 0:
        divergence = "Bearish"
        explanation = "Selling pressure on offshore venues"
        confidence = min(95.0, 60 + abs(premium_change_pct) * 10 + abs(price_change_pct) * 5)
    elif premium_change_pct < 0 and price_change_pct > 0:
        divergence = "Bullish"
        explanation = "US demand weakening while global price rises"
        confidence = min(95.0, 60 + abs(premium_change_pct) * 10 + abs(price_change_pct) * 5)

    if divergence == "None":
        display = "Divergence Detected: None | Premium and price aligned"
    else:
        prem_arrow = "↑" if premium_change_pct > 0 else "↓"
        price_arrow = "↑" if price_change_pct > 0 else "↓"
        display = (
            f"Premium {prem_arrow} + BTC Price {price_arrow} = {divergence} Divergence | "
            f"Confidence: {confidence:.0f}% | Possible explanation: {explanation}"
        )

    return {
        "divergence": divergence,
        "confidence_pct": round(confidence, 1),
        "explanation": explanation,
        "premium_change_pct": round(premium_change_pct, 3),
        "price_change_pct": round(price_change_pct, 3),
        "display": display,
        "not_a_signal": True,
        "label": "Divergence Detected: Price/Premium" if divergence != "None" else "No Divergence",
    }


def _us_demand_gauge(z_score: float, premium_pct: float) -> dict[str, Any]:
    if z_score >= 1.5 or premium_pct >= 1.0:
        level = "Elevated"
    elif z_score >= 0.5 or premium_pct >= 0.3:
        level = "Moderate"
    elif z_score <= -1.0 or premium_pct <= -0.5:
        level = "Weak"
    else:
        level = "Neutral"
    return {
        "level": level,
        "display": f"US Demand Gauge: {level}",
        "macro_context_only": True,
        "not_buy_signal": True,
    }


def _build_corroboration_context(
    premium_pct: float,
    corroboration: dict[str, Any],
    *,
    historical_correlation_90d: float | None,
) -> dict[str, Any]:
    corr = historical_correlation_90d if historical_correlation_90d is not None else 0.0
    sign = "+" if premium_pct >= 0 else ""
    correlation_display = (
        f"Premium: {sign}{premium_pct:.1f}% | Historical correlation (90D): {corr:+.2f} | "
        "Note: Correlation ≠ Causation"
    )

    corroborated_items: list[str] = []
    etf_flow = corroboration.get("etf_inflow_usd")
    if etf_flow:
        corroborated_items.append(f"ETF inflows {_format_flow_usd(etf_flow)}")
    if corroboration.get("institutional_flow_proxy") == "strong":
        corroborated_items.append("institutional flow proxy strong")

    context_display = correlation_display
    if corroborated_items and premium_pct > 0.5:
        context_display = (
            f"Premium elevated | Corroborated by: {' + '.join(corroborated_items)} | "
            "Context: Strong US demand"
        )

    return {
        "historical_correlation_90d": corr,
        "correlation_display": correlation_display,
        "context_display": context_display,
        "corroborated_by": corroborated_items,
        "causation_claim_allowed": bool(corroboration.get("causation_claim_allowed")),
        "no_causation_without_corroboration": not corroboration.get("causation_claim_allowed", False),
    }


def _format_flow_usd(value: float) -> str:
    sign = "+" if value >= 0 else ""
    if abs(value) >= 1_000_000_000:
        return f"{sign}${abs(value) / 1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"{sign}${abs(value) / 1_000_000:.0f}M"
    return f"{sign}${value:,.0f}"


def _arbitrage_net_context(premium_pct: float, fee_context: dict[str, Any]) -> dict[str, Any] | None:
    """Fee DB (#130) — net after transfer fees when arbitrage gap referenced."""
    if not fee_context.get("fee_db_available"):
        return None
    taker_cb = float((fee_context.get("estimated_taker_fee_pct") or {}).get("coinbase") or 0.6)
    taker_bn = float((fee_context.get("estimated_taker_fee_pct") or {}).get("binance") or 0.1)
    fx_spread = 0.1
    net = premium_pct - taker_cb - taker_bn - fx_spread
    return {
        "arbitrage_gap_pct": round(premium_pct, 2),
        "net_after_fees_pct": round(net, 2),
        "fee_db_feature_id": 130,
        "display": (
            f"Arbitrage gap: {premium_pct:+.1f}% | Net after transfer fees + FX spread: {net:+.1f}%"
        ),
        "macro_context_only": True,
        "not_arbitrage_opportunity": True,
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


def _coinbase_outage_response(
    *,
    sym: str,
    venue: dict[str, Any],
    ref_cfg: dict[str, Any],
    asset_data: dict[str, Any],
    cb: dict[str, Any],
    elapsed: float,
) -> dict[str, Any]:
    """Handle Coinbase outage/degraded — no stale data presented as live."""
    last_valid = asset_data.get("last_valid_timestamp") or venue.get("last_valid_timestamp")
    fallback = cb.get("fallback") or asset_data.get("fallback") or {}
    fallback_up = fallback.get("status") == "up"

    outage_display = (
        f"Coinbase API degraded | Premium: N/A | Last valid: {last_valid or 'N/A'}"
    )
    if fallback_up:
        outage_display += f" | Fallback: {fallback.get('venue', 'kraken').title()} {fallback.get('pair', 'BTC/USD')}"

    disclaimer = {
        "text": _COINBASE_DISCLAIMER,
        "collapsible": False,
        "hideable": False,
    }

    result: dict[str, Any] = {
        "ok": True,
        "feature_id": 233,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "asset": sym,
        "premium_pct": None,
        "premium_display": "Coinbase Premium: N/A",
        "venue": venue,
        "outage_alert": outage_display,
        "last_valid_timestamp": last_valid,
        "stale_data_hidden": True,
        "time_aligned": False,
        "reference_display": (
            f"Reference: {ref_cfg.get('exchange', 'binance').title()} "
            f"{ref_cfg.get('pair', 'BTC/USDT')} | "
            f"Time Alignment: {ref_cfg.get('time_alignment', '1-minute bucket')}"
        ),
        "macro_context_only": True,
        "not_arbitrage_opportunity": True,
        "not_buy_sell_signal": True,
        "no_causation_without_corroboration": True,
        "disclaimer": _COINBASE_DISCLAIMER,
        "disclaimer_top": disclaimer,
        "disclaimer_bottom": disclaimer,
        "disclaimer_hideable": False,
        "fee_context": _fee_db_context(),
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }

    if fallback_up:
        fb_price = float(fallback.get("price_usd") or 0)
        ref_price = float(asset_data.get("reference_price_usd") or 0)
        fb_premium = ((fb_price - ref_price) / ref_price * 100) if ref_price else None
        result["fallback"] = {
            "venue": fallback.get("venue", "kraken"),
            "pair": fallback.get("pair", "BTC/USD"),
            "price_usd": fb_price,
            "premium_pct": round(fb_premium, 2) if fb_premium is not None else None,
            "display": (
                f"Fallback: {fallback.get('venue', 'kraken').title()} {fallback.get('pair', 'BTC/USD')} | "
                f"Premium (fallback): {fb_premium:+.2f}%" if fb_premium is not None else "Fallback active"
            ),
            "not_live_coinbase": True,
        }

    return result


def get_coinbase_premium(asset: str = "BTC") -> dict[str, Any]:
    """Coinbase Premium Index (#233) — venue/time aligned, no causation without corroboration."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")
    cb = seed.get("coinbase") or {}
    asset_data = (cb.get("assets") or {}).get(sym)
    venue = cb.get("venue") or {}
    ref_cfg = cb.get("reference") or {}

    disclaimer_block = {
        "text": _COINBASE_DISCLAIMER,
        "collapsible": False,
        "hideable": False,
    }

    if not asset_data:
        return {"ok": False, "feature_id": 233, "error": "asset_not_configured", "asset": sym}

    venue_status = venue.get("status", "up")
    if venue_status in ("down", "degraded"):
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        return _coinbase_outage_response(
            sym=sym,
            venue=venue,
            ref_cfg=ref_cfg,
            asset_data=asset_data,
            cb=cb,
            elapsed=elapsed,
        )

    coinbase_price = float(asset_data.get("coinbase_price_usd") or 0)
    ref_price = float(asset_data.get("reference_price_usd") or 0)
    cb_ts = asset_data.get("coinbase_timestamp")
    ref_ts = asset_data.get("reference_timestamp")
    ref_exchange = ref_cfg.get("exchange", "binance")
    ref_pair = ref_cfg.get("pair", "BTC/USDT")

    alignment = _build_venue_time_alignment(
        cb_ts,
        ref_ts,
        ref_exchange=ref_exchange,
        ref_pair=ref_pair,
    )

    premium_pct = ((coinbase_price - ref_price) / ref_price * 100) if ref_price else 0.0
    rolling = [float(x) for x in (asset_data.get("rolling_premium_pct") or [])]
    z_scores = [float(x) for x in (asset_data.get("rolling_z_score") or [])]
    current_z = z_scores[-1] if z_scores else 0.0
    trend = _z_score_trend(z_scores)
    persistence_days = int(asset_data.get("persistence_days") or 0)
    median_days = int(asset_data.get("persistence_median_days") or 2)
    corroboration = asset_data.get("corroboration") or {}
    hist_corr = asset_data.get("historical_correlation_90d")
    z_window = int(asset_data.get("z_score_window_days") or 30)

    z_context = _build_z_score_context(current_z, rolling, window_days=z_window)
    persistence = _build_persistence_analysis(persistence_days, historical_median_days=median_days)
    corroboration_ctx = _build_corroboration_context(
        premium_pct,
        corroboration,
        historical_correlation_90d=float(hist_corr) if hist_corr is not None else None,
    )
    demand_gauge = _us_demand_gauge(current_z, premium_pct)

    prem_change = float(asset_data.get("premium_change_pct_1d") or 0)
    price_change = float(asset_data.get("btc_price_change_pct_1d") or 0)
    divergence = _detect_premium_price_divergence(prem_change, price_change)

    fee_context = _fee_db_context()
    arbitrage_ctx = _arbitrage_net_context(premium_pct, fee_context)
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
        "premium_index": {
            "value_pct": round(premium_pct, 2),
            "trend": trend,
            "z_score": z_context,
            "persistence": persistence,
            "divergence": divergence,
        },
        "venue": venue,
        "coinbase_price_usd": coinbase_price,
        "reference_price_usd": ref_price,
        "venue_time_alignment": alignment,
        "time_aligned": alignment["time_aligned"],
        "time_alignment_display": alignment["alignment_display"],
        "reference_display": (
            f"Reference: {ref_exchange.title()} {ref_pair} | "
            f"Time Alignment: {ref_cfg.get('time_alignment', '1-minute bucket')}"
        ),
        "rolling_z_score": current_z,
        "z_score_context": z_context,
        "z_score_trend": trend,
        "persistence": persistence,
        "persistence_days": persistence_days,
        "trend_display": (
            f"Trend: {trend.title()} | {z_context['z_score_display']} | {persistence['persistence_display']}"
        ),
        "divergence": divergence,
        "divergence_alert": divergence["divergence"] != "None",
        "divergence_display": divergence["display"],
        "us_demand_gauge": demand_gauge,
        "corroboration": corroboration,
        "corroboration_context": corroboration_ctx,
        "no_causation_without_corroboration": corroboration_ctx["no_causation_without_corroboration"],
        "causation_note": corroboration_ctx["context_display"],
        "rolling_premium_pct": rolling,
        "arbitrage_context": arbitrage_ctx,
        "macro_context_only": True,
        "not_arbitrage_opportunity": True,
        "not_buy_sell_signal": True,
        "disclaimer": _COINBASE_DISCLAIMER,
        "disclaimer_top": disclaimer_block,
        "disclaimer_bottom": disclaimer_block,
        "disclaimer_hideable": False,
        "fee_context": fee_context,
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
            "card_summary": coinbase.get("us_demand_gauge", {}).get("display")
            or coinbase.get("trend_display")
            or coinbase.get("premium_display"),
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
            "rolling_z_score_documented": True,
            "persistence_analysis": True,
            "divergence_alerts_context_only": True,
            "us_demand_gauge_not_buy_signal": True,
        },
        "disclaimer": _MODULE_DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
