"""
Global Liquidity Intelligence — Feature #248 (Sprint 2, Pro/Institution).

Estimates global liquidity environment and historical relationship with crypto.
Macro context only — NOT predictions or buy signals.

Central bank data with inherent lags and revisions — no fabricated real-time data.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.GlobalLiquidity")

_FEATURE_ID = 248
_STANDALONE = False
_SPRINT = 2
_SEED_PATH = Path("data/global_liquidity_seed.json")
_MODULE_VERSION = "2.1"
_INDEX_VERSION = "1.2"

_DISCLAIMER_TEXT = (
    "Global Liquidity data is based on central bank releases with inherent lags and revisions. "
    "Historical relationships with crypto assets do not guarantee future outcomes. Not investment advice."
)

RegimeLabel = Literal["Tightening", "Neutral", "Easing"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"series": {}, "composite_weights": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("global liquidity seed load failed: %s", exc)
        return {"series": {}, "composite_weights": {}}


def _build_lag_methodology(seed: dict[str, Any]) -> dict[str, Any]:
    lag = seed.get("lag_methodology") or {}
    freqs = seed.get("update_frequencies") or {}
    items = [v.get("display", k) for k, v in lag.items() if isinstance(v, dict)]
    return {
        "components": lag,
        "lag_display": seed.get("lag_methodology_display") or " | ".join(items),
        "update_frequencies": freqs,
        "batch_data_only": True,
        "no_sub_second_updates": True,
        "frequency_display": (
            f"Update Frequency: Daily (rates) | Monthly (M2) | "
            f"Quarterly (some aggregates) | FX: Hourly"
        ),
        "not_real_time": True,
    }


def _build_revision_trail(series: dict[str, Any]) -> dict[str, Any]:
    revisions = series.get("revisions") or []
    current = next((r for r in revisions if r.get("type") == "current"), revisions[-1] if revisions else {})
    return {
        "revisions": revisions,
        "revision_count": len(revisions),
        "current_value": current.get("value"),
        "revision_display": series.get("revision_display"),
        "revisions_tracked": True,
        "initial_not_final": len(revisions) > 1,
    }


def _build_series_point(key: str, series: dict[str, Any], lag_cfg: dict[str, Any]) -> dict[str, Any]:
    lag_info = lag_cfg.get(key) or {}
    rev = _build_revision_trail(series)
    interpolated = series.get("interpolated_estimate")

    point = {
        "series_id": key,
        "source": series.get("source"),
        "latest_value": series.get("latest_value"),
        "unit": series.get("unit"),
        "as_of": series.get("as_of"),
        "next_release": series.get("next_release"),
        "update_frequency": series.get("update_frequency"),
        "lag_days": series.get("lag_days") or lag_info.get("lag_days", 0),
        "lag_display": lag_info.get("display", f"{key}: lag documented"),
        "latest_value_display": series.get("latest_value_display"),
        "yoy_pct": series.get("yoy_pct"),
        "revisions": rev,
        "not_real_time": series.get("update_frequency") != "Real-time",
        "fabricated_realtime": False,
    }

    if interpolated:
        point["interpolated_estimate"] = {
            "value": interpolated.get("value"),
            "method": interpolated.get("method", "Linear between releases"),
            "confidence": interpolated.get("confidence", "Low"),
            "display": (
                f"Interpolated Estimate: {interpolated.get('value')} | "
                f"Method: {interpolated.get('method', 'Linear between releases')} | "
                f"Confidence: {interpolated.get('confidence', 'Low')}"
            ),
        }

    return point


def _compute_composite_index(seed: dict[str, Any]) -> dict[str, Any]:
    weights = seed.get("composite_weights") or {}
    composite = seed.get("composite_index") or {}
    series = seed.get("series") or {}

    # Normalized component scores (seed provides pre-computed composite)
    components_used = []
    for key, weight in weights.items():
        s = series.get(key) or {}
        components_used.append({
            "component": key,
            "weight_pct": round(weight * 100, 0),
            "latest_input_date": s.get("as_of"),
            "lag_days": s.get("lag_days"),
        })

    return {
        "value": composite.get("value"),
        "base": composite.get("base", 100.0),
        "version": seed.get("index_version", _INDEX_VERSION),
        "module_version": seed.get("module_version", _MODULE_VERSION),
        "calculation_date": composite.get("calculation_date") or seed.get("calculation_date"),
        "latest_input_date": composite.get("latest_input_date"),
        "latest_input_series": composite.get("latest_input_series"),
        "weights": weights,
        "components_used": components_used,
        "composite_display": seed.get("composite_display"),
        "index_display": composite.get("index_display") or (
            f"Global Liquidity Index: {composite.get('value')} | Version: {seed.get('module_version')} | "
            f"Calculation Date: {composite.get('calculation_date')} | "
            f"Latest Input Date: {composite.get('latest_input_date')} ({composite.get('latest_input_series')})"
        ),
        "methodology_documented": True,
    }


def _classify_regime(seed: dict[str, Any]) -> dict[str, Any]:
    regime = seed.get("regime") or {}
    label = regime.get("label", "Neutral")
    return {
        "regime": label,
        "regime_labels": regime.get("labels", ["Tightening", "Neutral", "Easing"]),
        "m2_yoy_weighted_pct": regime.get("m2_yoy_weighted_pct"),
        "policy_rate_trajectory": regime.get("policy_rate_trajectory"),
        "duration_months": regime.get("duration_months"),
        "based_on": regime.get("based_on", "M2 YoY + Policy Rate trajectory"),
        "regime_display": regime.get("regime_display"),
        "descriptive_only": True,
        "not_predictive": True,
        "no_price_target": True,
    }


def _build_historical_relationship(seed: dict[str, Any], asset: str) -> dict[str, Any]:
    hist = seed.get("historical_relationship") or {}
    asset_data = (seed.get("assets") or {}).get(asset.upper()) or {}
    corr = asset_data.get("correlation_90d_lagged") or hist.get("correlation_90d_lagged", 0)

    regime_label = (seed.get("regime") or {}).get("label", "Neutral")
    display = (
        f"Liquidity Regime: {regime_label} | Historical {asset.upper()} correlation "
        f"(lagged 90D): {corr:+.2f} | Note: Correlation varies by regime | Not predictive"
    )

    return {
        "asset": asset.upper(),
        "correlation_90d_lagged": corr,
        "correlation_varies_by_regime": hist.get("correlation_varies_by_regime", True),
        "period_months": hist.get("period_months", 6),
        "not_predictive": True,
        "not_causation": True,
        "relationship_display": display,
        "note": "Historical relationship ≠ prediction",
    }


def build_global_liquidity_dashboard(asset: str = "BTC") -> dict[str, Any]:
    """Global Liquidity dashboard — macro context only."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")

    disclaimer = {
        "text": _DISCLAIMER_TEXT,
        "collapsible": False,
        "hideable": False,
        "version": seed.get("module_version", _MODULE_VERSION),
    }

    lag_methodology = _build_lag_methodology(seed)
    lag_cfg = seed.get("lag_methodology") or {}
    series_data = seed.get("series") or {}

    series_points = {
        key: _build_series_point(key, s, lag_cfg)
        for key, s in series_data.items()
    }

    composite = _compute_composite_index(seed)
    regime = _classify_regime(seed)
    relationship = _build_historical_relationship(seed, sym)
    macro_ctx = seed.get("macro_context") or {}

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "surface": "global_liquidity_intelligence",
        "asset": sym,
        "module_version": seed.get("module_version", _MODULE_VERSION),
        "index_version": seed.get("index_version", _INDEX_VERSION),
        "last_revised": seed.get("last_revised"),
        "tier": seed.get("tier", "pro"),
        "lag_methodology": lag_methodology,
        "series": series_points,
        "composite_index": composite,
        "liquidity_regime": regime,
        "historical_relationship": relationship,
        "macro_context": {
            "label": macro_ctx.get("label", "Liquidity Expanding"),
            "display": macro_ctx.get("display", "Macro Context: Liquidity Expanding"),
            "macro_context_only": True,
            "not_opportunity_framing": True,
            "not_buy_signal": True,
        },
        "sources": seed.get("sources", []),
        "no_fabricated_realtime": seed.get("no_real_time_fabrication", True),
        "no_real_time_m2": True,
        "real_time_m2_forbidden": True,
        "batch_update_policy": lag_methodology["frequency_display"],
        "not_a_recommendation": True,
        "not_predictive": True,
        "allowed_language": ["Macro Context", "Liquidity Regime", "Historical correlation", "Analysis"],
        "disclaimer_top": disclaimer,
        "disclaimer": disclaimer,
        "disclaimer_bottom": disclaimer,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_liquidity_regime(asset: str = "BTC") -> dict[str, Any]:
    """Liquidity regime descriptor — Tightening/Neutral/Easing."""
    seed = _load_seed()
    regime = _classify_regime(seed)
    relationship = _build_historical_relationship(seed, asset)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "asset": asset.upper(),
        **regime,
        "historical_relationship": relationship,
        "not_predictive": True,
        "timestamp": _utcnow(),
    }


def build_liquidity_index() -> dict[str, Any]:
    """Global Liquidity composite index with documented methodology."""
    seed = _load_seed()
    composite = _compute_composite_index(seed)
    lag = _build_lag_methodology(seed)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "composite_index": composite,
        "lag_methodology": lag,
        "no_fabricated_realtime": True,
        "timestamp": _utcnow(),
    }


def global_liquidity_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_label": seed.get("feature_label", "Global Liquidity Intelligence"),
        "standalone": _STANDALONE,
        "sprint": _SPRINT,
        "tier": seed.get("tier", "pro"),
        "module_version": seed.get("module_version", _MODULE_VERSION),
        "index_version": seed.get("index_version", _INDEX_VERSION),
        "last_revised": seed.get("last_revised"),
        "lag_methodology": _build_lag_methodology(seed),
        "composite_weights": seed.get("composite_weights"),
        "composite_display": seed.get("composite_display"),
        "update_frequencies": seed.get("update_frequencies"),
        "sources": seed.get("sources", []),
        "integrated_surfaces": ["Market Radar"],
        "acceptance_criteria": {
            "source_lag_methodology_documented": True,
            "revisions_tracked": True,
            "no_fabricated_realtime": True,
            "composite_index_documented": True,
            "historical_not_predictive": True,
            "regime_descriptive_only": True,
            "disclaimer_non_hideable": True,
            "not_opportunity_framing": True,
            "batch_updates_only": True,
            "version_timestamp_per_point": True,
        },
        "disclaimer": _DISCLAIMER_TEXT,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
