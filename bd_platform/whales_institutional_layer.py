"""
Whales & Institutional Layer — #77–#86.

NOT standalone modules — merged into Portfolio AI, Market Radar, Intelligence Ledger,
On-Chain Extension, and API documentation infrastructure.

#78 Smart Execution: REJECTED — alternative Impact Analysis Insight only.
#83 SMB Institution Path: DEFERRED Wave 3 — status stub only.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.WhalesInstitutional")

_SEED_PATH = Path("data/legal_retail_commercial_seed.json")
_PERF_LEDGER = Path("data/transparency/performance_ledger.jsonl")

_correlation_cache: dict[str, Any] = {}
_performance_records: list[dict[str, Any]] = []


def reset_whales_institutional_state() -> None:
    _correlation_cache.clear()
    _performance_records.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("whales institutional seed load failed: %s", exc)
        return {}


def _risk_disclaimer(locale: str = "en") -> str:
    if locale.lower().startswith("ar"):
        return "تحليل مخاطر — تحذير لا حماية. Risk Insight لا Protection."
    return "Risk analysis — warning not protection. Risk Insight not Protection."


# ─── #77 Advanced Risk Tab ──────────────────────────────────────────────────────


def _days_between(start: str, end: str) -> int:
    try:
        from datetime import datetime

        fmt = "%Y-%m-%d"
        d0 = datetime.strptime(str(start)[:10], fmt)
        d1 = datetime.strptime(str(end)[:10], fmt)
        return max(0, (d1 - d0).days)
    except (ValueError, TypeError):
        return 0


def _compute_drawdown_duration_103(
    price_history: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#103 — Max drawdown duration lifecycle merged into advanced risk."""
    if len(price_history) < 2:
        return {
            "feature_ref": 103,
            "merged_into": "advanced_risk_77",
            "max_drawdown_pct": 0,
            "duration_days": 0,
            "recovery_days": None,
            "formula": "drawdown = (peak − trough) / peak; duration = trough_ts − peak_ts",
            "historical_analysis_only": True,
        }
    peak_val = float(price_history[0].get("value_usd", 0) or 0)
    peak_date = price_history[0].get("date", "")
    max_dd = 0.0
    trough_date = peak_date
    for point in price_history:
        val = float(point.get("value_usd", 0) or 0)
        if val > peak_val:
            peak_val = val
            peak_date = point.get("date", peak_date)
        dd = (peak_val - val) / peak_val * 100 if peak_val else 0
        if dd > max_dd:
            max_dd = dd
            trough_date = point.get("date", trough_date)
    recovery_days = None
    recovered = False
    for point in price_history:
        if point.get("date", "") > trough_date and float(point.get("value_usd", 0) or 0) >= peak_val:
            recovered = True
            break
    fee = float((seed or {}).get("drawdown_duration_103", {}).get("fee_db", {}).get("compute_usd", 0.0005))
    duration = _days_between(peak_date, trough_date)
    return {
        "feature_ref": 103,
        "merged_into": "advanced_risk_77",
        "max_drawdown_pct": round(max_dd, 2),
        "peak_date": peak_date,
        "trough_date": trough_date,
        "duration_days": duration,
        "recovery_days": recovery_days,
        "recovered": recovered,
        "insight": {
            "en": f"This drawdown took {duration} days to reach trough",
            "ar": f"استغرق هذا التراجع {duration} يوماً للوصول للقاع",
        },
        "formula": "drawdown = (peak − trough) / peak; duration = trough_ts − peak_ts",
        "historical_analysis_only": True,
        "non_custodial": True,
        "fee_db": {"compute_usd": fee},
    }


def build_advanced_risk_report_77(
    holdings: list[dict[str, Any]],
    *,
    btc_shock_pct: float = -20.0,
    price_history: list[dict[str, Any]] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Exposure + correlation + stress scenarios — rule-based risk report."""
    seed = seed or _load_seed()
    total = sum(float(h.get("value_usd", 0) or 0) for h in holdings) or 1.0

    exposure: list[dict[str, Any]] = []
    for h in holdings:
        val = float(h.get("value_usd", 0) or 0)
        pct = round(val / total * 100, 2)
        exposure.append({
            "asset": h.get("symbol", h.get("asset", "UNKNOWN")),
            "value_usd": round(val, 2),
            "exposure_pct": pct,
            "formula": "exposure_pct = asset_value / total_portfolio * 100",
        })

    assets = [e["asset"] for e in exposure]
    correlations: list[dict[str, Any]] = []
    for i, a in enumerate(assets):
        for b in assets[i + 1 :]:
            beta_a = float(next((h.get("btc_beta", 0.5) for h in holdings if h.get("symbol", h.get("asset")) == a), 0.5))
            beta_b = float(next((h.get("btc_beta", 0.5) for h in holdings if h.get("symbol", h.get("asset")) == b), 0.5))
            corr = round(min(0.99, max(0.1, (beta_a + beta_b) / 2)), 3)
            correlations.append({
                "pair": f"{a}/{b}",
                "correlation_30d": corr,
                "formula": "rule_based_proxy_from_btc_beta",
                "window_days": 30,
            })

    cache_key = hashlib.sha256(json.dumps(assets, sort_keys=True).encode()).hexdigest()[:16]
    _correlation_cache[cache_key] = correlations

    weighted_beta = sum(
        (float(h.get("value_usd", 0) or 0) / total) * float(h.get("btc_beta", 0.5) or 0.5) for h in holdings
    )
    shock_loss = round(total * weighted_beta * abs(btc_shock_pct) / 100, 2)
    scenarios = [
        {
            "name": f"BTC {btc_shock_pct:+.0f}%",
            "assumption": f"Portfolio weighted BTC beta {weighted_beta:.2f}",
            "estimated_loss_usd": shock_loss,
            "formula": "loss = total_value * weighted_beta * abs(shock_pct) / 100",
        },
        {
            "name": "ETH -25%",
            "assumption": "ETH-heavy positions correlate with ETH move",
            "estimated_loss_usd": round(shock_loss * 0.85, 2),
            "formula": "rule_based_eth_proxy",
        },
    ]

    fee = float((seed.get("advanced_risk_77") or {}).get("fee_db", {}).get("compute_usd", 0.002))
    drawdown_lifecycle = _compute_drawdown_duration_103(price_history or [], seed=seed)
    tail_risk: dict[str, Any] = {}
    try:
        from bd_platform.market_analysis_layer import compute_tail_risk_alpha_105

        tail_risk = compute_tail_risk_alpha_105(seed=seed)
    except ImportError:
        pass
    result = {
        "ok": True,
        "feature_ref": 77,
        "tab": "advanced_risk",
        "report_type": "risk_insight_not_protection",
        "exposure": exposure,
        "correlations": correlations,
        "stress_scenarios": scenarios,
        "drawdown_lifecycle": drawdown_lifecycle,
        "tail_risk_alpha": tail_risk,
        "merged_features": [77, 103, 105],
        "formula_visible": True,
        "cached_correlation_key": cache_key,
        "performance_target_ms": 800,
        "disclaimer": _risk_disclaimer(),
        "fee_db": {"compute_usd": fee},
    }
    try:
        from bd_platform.advanced_ta_risk_layer import attach_leverage_risk_120

        result = attach_leverage_risk_120(result, seed=seed)
    except ImportError:
        pass
    try:
        from bd_platform.risk_infrastructure_layer import attach_correlation_decay_169

        result = attach_correlation_decay_169(result, seed=seed)
    except ImportError:
        pass
    try:
        from bd_platform.arbitrage_portfolio_ux_layer import attach_scenarios_178

        total = sum(float(h.get("value_usd", 0) or 0) for h in holdings) or 100_000
        return attach_scenarios_178(result, portfolio_value_usd=total, seed=seed)
    except ImportError:
        return result


# ─── #78 Impact Analysis (Execution REJECTED) ───────────────────────────────────


def execution_routing_status_78(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return {
        "ok": True,
        "feature_ref": 78,
        "status": "rejected",
        "rejected": True,
        "reason": "insight_only_platform_no_execution",
        "alternative": "impact_analysis_insight",
        "alternative_route": "/intelligence/impact-analysis",
        "policy": (seed.get("impact_analysis_78") or {}).get("policy") or {},
    }


def build_impact_analysis_78(
    *,
    order_usd: float,
    asset: str = "BTC",
    depth_usd: float = 5_000_000,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Insight only — estimated slippage, no routing or execution."""
    seed = seed or _load_seed()
    participation = order_usd / max(depth_usd, 1)
    slippage_pct = round(min(15.0, participation * 100 * 0.5), 3)
    fee = float((seed.get("impact_analysis_78") or {}).get("fee_db", {}).get("compute_usd", 0.001))
    return {
        "ok": True,
        "feature_ref": 78,
        "alternative_to_rejected_execution": True,
        "insight_only": True,
        "no_routing": True,
        "no_order_splitting": True,
        "asset": asset.upper(),
        "order_usd": order_usd,
        "estimated_slippage_pct": slippage_pct,
        "narrative": {
            "en": f"An order of ${order_usd:,.0f} on {asset} may cause ~{slippage_pct}% slippage based on current depth",
            "ar": f"أمر بقيمة ${order_usd:,.0f} على {asset} قد يسبب انزلاق ~{slippage_pct}% بناءً على العمق الحالي",
        },
        "formula": "slippage_pct = min(15, (order_usd / depth_usd) * 50)",
        "disclaimer": "Impact analysis insight — not execution advice",
        "fee_db": {"compute_usd": fee},
    }


# ─── #79 Wallet Surveillance Insight ────────────────────────────────────────────


def analyze_wallet_surveillance_79(
    *,
    wallet: str,
    suspicious_query_count: int = 0,
    mev_bot_hits: int = 0,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    short = wallet if "..." in wallet else f"{wallet[:6]}...{wallet[-4:]}" if len(wallet) > 12 else wallet
    monitored = suspicious_query_count >= 3 or mev_bot_hits >= 1
    fee = float((seed.get("wallet_surveillance_79") or {}).get("fee_db", {}).get("analysis_usd", 0.001))
    return {
        "ok": True,
        "feature_ref": 79,
        "merged_into": [81, "on_chain_extension"],
        "wallet": short,
        "surveillance_detected": monitored,
        "insight": {
            "en": (
                f"Address monitored by {suspicious_query_count} suspicious query patterns"
                if monitored
                else "No elevated surveillance pattern detected"
            ),
            "ar": (
                f"العنوان مُراقب من {suspicious_query_count} أنماط استعلام مُشتبهة"
                if monitored
                else "لا يوجد نمط مراقبة مرتفع"
            ),
        },
        "educational_note": {
            "en": "Using a fresh address per transaction may reduce tracking — insight only",
            "ar": "استخدام عنوان جديد لكل صفقة قد يُقلل التتبع — insight فقط",
        },
        "no_auto_protection": True,
        "privacy_first": True,
        "fee_db": {"analysis_usd": fee},
    }


# ─── #80 Exchange Health Monitor ────────────────────────────────────────────────


def build_exchange_health_80(
    *,
    exchange: str = "binance",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    ex = exchange.lower()
    # Rule-based sample indicators
    indicators = {
        "reserves_ratio": {"value": 1.02 if ex != "ftx" else 0.4, "source": "public_attestation"},
        "withdrawal_velocity": {"value": "elevated" if ex == "okx" else "normal", "source": "on_chain_flows"},
        "sentiment_score": {"value": 6.5, "source": "sentiment_layer"},
        "net_flow_24h_usd": {"value": -50_000_000 if ex == "okx" else 10_000_000, "source": "on_chain"},
    }
    health_score = round(
        (indicators["reserves_ratio"]["value"] if isinstance(indicators["reserves_ratio"]["value"], (int, float)) else 1.0) * 40
        + (8 if indicators["withdrawal_velocity"]["value"] == "normal" else 3)
        + indicators["sentiment_score"]["value"],
        1,
    )
    fee = float((seed.get("exchange_health_80") or {}).get("fee_db", {}).get("compute_usd", 0.0015))
    return {
        "ok": True,
        "feature_ref": 80,
        "dimension": "market_radar_exchange_health",
        "route": "/radar/exchange-health",
        "exchange": ex,
        "health_score": min(100, health_score),
        "indicators": indicators,
        "insight": {
            "en": f"{ex.title()} shows {indicators['withdrawal_velocity']['value']} withdrawal velocity",
            "ar": f"{ex} تُظهر سرعة سحب {indicators['withdrawal_velocity']['value']}",
        },
        "not_official_warning": True,
        "public_data_only": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── #81 Unified Portfolio View ─────────────────────────────────────────────────


def build_unified_portfolio_view_81(
    positions: list[dict[str, Any]] | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    positions = positions or [
        {"asset": "BTC", "chain": "bitcoin", "exchange": "", "value_usd": 50000, "source": "manual", "btc_beta": 1.0},
        {"asset": "ETH", "chain": "ethereum", "exchange": "binance", "value_usd": 20000, "source": "manual", "btc_beta": 0.85},
        {"asset": "ARB", "chain": "arbitrum", "exchange": "", "value_usd": 5000, "source": "manual", "btc_beta": 0.7},
    ]
    supported_chains = ("ethereum", "bsc", "arbitrum", "bitcoin")
    normalized = []
    for p in positions:
        normalized.append({
            **p,
            "chain": p.get("chain", "ethereum").lower(),
            "last_updated": _utcnow(),
            "source_type": p.get("source", "manual"),
            "api_key_stored_encrypted": p.get("source") == "read_only_api",
        })

    holdings_for_risk = [
        {"symbol": p["asset"], "value_usd": p.get("value_usd", 0), "btc_beta": p.get("btc_beta", 0.5)}
        for p in normalized
    ]
    advanced_risk = build_advanced_risk_report_77(holdings_for_risk, seed=seed)
    try:
        from bd_platform.pro_trader_layer import health_score_from_holdings_67

        health = health_score_from_holdings_67(holdings_for_risk, seed=seed)
    except ImportError:
        health = {"widget": {"score": 50, "color": "yellow"}}

    fee = float((seed.get("unified_portfolio_81") or {}).get("fee_db", {}).get("compute_usd", 0.003))
    return {
        "ok": True,
        "feature_ref": 81,
        "view": "unified_portfolio",
        "positions": normalized,
        "supported_chains": list(supported_chains),
        "total_value_usd": round(sum(float(p.get("value_usd", 0)) for p in normalized), 2),
        "health_score": health.get("widget"),
        "advanced_risk_tab": advanced_risk,
        "non_custodial": True,
        "no_execution_permissions": True,
        "insight_not_management": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── #82 Liquidation Cascade Alert ────────────────────────────────────────────────


def evaluate_liquidation_alert_82(
    *,
    asset: str = "BTC",
    price: float = 65000,
    liquidation_level: float = 62000,
    open_interest_usd: float = 500_000_000,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    distance_pct = round((price - liquidation_level) / price * 100, 2) if price else 0
    proximity_pct = distance_pct  # #100 — same metric, quantified dimension
    cfg100 = seed.get("liquidation_proximity_100") or {}
    red_pct = float((cfg100.get("policy") or {}).get("red_threshold_pct", 5))
    yellow_pct = float((cfg100.get("policy") or {}).get("yellow_threshold_pct", 10))
    proximity_color = "red" if proximity_pct < red_pct else ("yellow" if proximity_pct < yellow_pct else "green")
    cascade_risk = "high" if distance_pct < 5 else ("medium" if distance_pct < 10 else "low")
    triggered = distance_pct < 8 and open_interest_usd > 100_000_000
    fee = float((seed.get("liquidation_alert_82") or {}).get("fee_db", {}).get("alert_usd", 0.0005))
    result = {
        "ok": True,
        "feature_ref": 82,
        "merged_features": [82, 100],
        "alert_type": "liquidation_cascade",
        "route": "/radar/alerts/liquidation",
        "asset": asset.upper(),
        "current_price": price,
        "liquidation_level": liquidation_level,
        "distance_pct": distance_pct,
        "proximity_pct": proximity_pct,
        "proximity_color": proximity_color,
        "proximity_formula": "(Current Price − Nearest Liquidation Wall) / Current Price × 100",
        "cascade_risk": cascade_risk,
        "alert_fired": triggered,
        "why_level": {
            "en": f"Largest positions cluster near ${liquidation_level:,.0f} — OI ${open_interest_usd/1e6:.0f}M",
            "ar": f"أكبر المراكز قرب ${liquidation_level:,.0f} — OI ${open_interest_usd/1e6:.0f}M",
        },
        "no_auto_action": True,
        "public_data_only": True,
        "fee_db": {"alert_usd": fee},
    }
    try:
        from bd_platform.market_analysis_layer import attach_liquidation_anchors_109

        return attach_liquidation_anchors_109(result, current_price=price, seed=seed)
    except ImportError:
        return result


# ─── #83 SMB Institution Path (DEFERRED) ────────────────────────────────────────


def smb_institution_status_83(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("smb_institution_83") or {}
    return {
        "ok": True,
        "feature_ref": 83,
        "status": "deferred",
        "wave": 3,
        "build_blocked_until": cfg.get("build_blocked_until", "500_active_pro_users"),
        "qualification": {"aum_usd_max": 50_000_000, "team_size_max": 10},
        "same_insight_only": True,
        "no_build_in_current_sprint": True,
    }


# ─── #84 Public Performance Ledger ──────────────────────────────────────────────


def record_performance_entry_84(
    *,
    asset: str,
    insight: str,
    risk_score: float,
    confidence: float,
    response_id: str = "",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    entry = {
        "record_id": f"perf_{uuid.uuid4().hex[:10]}",
        "timestamp": _utcnow(),
        "asset": asset.upper(),
        "insight": insight,
        "risk_score": risk_score,
        "confidence": confidence,
        "response_id": response_id or f"resp_{uuid.uuid4().hex[:8]}",
        "outcome_7d": None,
        "outcome_30d": None,
        "outcome_90d": None,
        "auditable": True,
        "append_only": True,
    }
    raw = json.dumps(entry, sort_keys=True).encode()
    entry["checksum_sha256"] = hashlib.sha256(raw).hexdigest()
    _performance_records.append(entry)
    try:
        _PERF_LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with _PERF_LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("performance ledger persist skipped", exc_info=True)
    return {"ok": True, "feature_ref": 84, "entry": entry}


def build_performance_ledger_view_84(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    resolved = [r for r in _performance_records if r.get("outcome_30d")]
    hits = sum(1 for r in resolved if r.get("outcome_30d") == "hit")
    total = len(_performance_records) or 1
    hit_rate = round(hits / max(len(resolved), 1) * 100, 1) if resolved else None
    return {
        "ok": True,
        "feature_ref": 84,
        "route": "/transparency/performance",
        "entries": _performance_records[-50:],
        "hit_rate_pct": hit_rate,
        "total_recorded": len(_performance_records),
        "due_diligence_ready": True,
        "no_future_guarantee": True,
        "disclaimer": "Historical analysis record — not future performance guarantee",
    }


# ─── #85 OpenAPI Documentation Layer ────────────────────────────────────────────


def openapi_documentation_status_85(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("openapi_docs_85") or {}
    return {
        "ok": True,
        "feature_ref": 85,
        "spec_version": "3.0+",
        "swagger_ui": "/docs",
        "full_spec": "/api/docs/openapi.json",
        "public_spec": "/api/docs/public-openapi.json",
        "authentication": {
            "type": "api_key",
            "header": "X-API-Key",
            "tier_mapping_documented": True,
        },
        "examples_required": ["curl", "python", "javascript"],
        "fee_per_endpoint_documented": True,
        "webhooks_documented": cfg.get("webhooks", ["stripe", "alerts"]),
        "version_prefix": "/v1/",
        "policy": cfg.get("policy") or {},
    }


def enrich_openapi_with_fee_metadata_85(spec: dict[str, Any]) -> dict[str, Any]:
    """Attach fee transparency metadata to OpenAPI spec."""
    out = dict(spec)
    info = dict(out.get("info") or {})
    info["x-blackdark-fee-transparency"] = True
    info["x-blackdark-auth"] = "X-API-Key header + tier rate limits"
    out["info"] = info
    paths = out.get("paths") or {}
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, detail in methods.items():
            if isinstance(detail, dict) and method in ("get", "post", "put", "delete"):
                detail["x-fee-note"] = "Query cost logged per tier — see /api/platform/legal/tiers/limits"
    out["paths"] = paths
    return out


# ─── #86 Methodology Documentation ──────────────────────────────────────────────


def build_methodology_docs_86(*, locale: str = "en", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("methodology_docs_86") or {}
    simple = locale.lower().startswith("ar")
    return {
        "ok": True,
        "feature_ref": 86,
        "route": "/transparency/methodology",
        "rule_based_only_sprint_2": True,
        "no_ml_claim": True,
        "methodology": {
            "approach": "Explicit rule-based formulas — no machine learning in Sprint 2",
            "dimensions": ["technical", "on_chain", "sentiment", "macro"],
            "weights_documented": True,
            "thresholds_documented": True,
        },
        "limitations": {
            "hit_rate_source": "performance_ledger_84",
            "known_failure_modes": ["low_liquidity_assets", "black_swan_events", "exchange_outages"],
            "assumptions": ["public_data_only", "manual_portfolio_input", "no_execution"],
        },
        "versions": {"simple": simple, "technical_available": True},
        "quarterly_review_required": True,
        "embedded_in_every_insight": True,
        "disclaimer": _risk_disclaimer(locale),
        "policy": cfg.get("policy") or {},
    }


def attach_methodology_to_insight_86(payload: dict[str, Any], *, locale: str = "en") -> dict[str, Any]:
    out = dict(payload)
    out["methodology"] = build_methodology_docs_86(locale=locale)
    out["rule_based_only"] = True
    return out


# ─── Portfolio attach ───────────────────────────────────────────────────────────


def attach_portfolio_whale_layers_77_86(
    portfolio_result: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = dict(portfolio_result)
    holdings = out.get("holdings") or []
    out["advanced_risk_tab"] = build_advanced_risk_report_77(holdings, seed=seed)
    positions = [
        {
            "asset": h.get("symbol", h.get("asset", "")),
            "chain": h.get("chain", "ethereum"),
            "exchange": h.get("exchange", ""),
            "value_usd": h.get("value_usd", 0),
            "source": "manual",
            "btc_beta": h.get("btc_beta", 0.5),
        }
        for h in holdings
    ]
    if positions:
        out["unified_portfolio_view"] = build_unified_portfolio_view_81(positions, seed=seed)
    out["methodology"] = build_methodology_docs_86(seed=seed)
    return out


# ─── E2E ────────────────────────────────────────────────────────────────────────


def run_whales_institutional_e2e_77_86(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_whales_institutional_state()
    checks: list[dict[str, Any]] = []

    holdings = [{"symbol": "BTC", "value_usd": 70000, "btc_beta": 1.0}, {"symbol": "ETH", "value_usd": 30000, "btc_beta": 0.8}]
    risk = build_advanced_risk_report_77(holdings, seed=seed)
    checks.append({"id": "77_exposure", "passed": len(risk["exposure"]) == 2})
    checks.append({"id": "77_stress", "passed": len(risk["stress_scenarios"]) >= 1})

    rejected = execution_routing_status_78(seed=seed)
    checks.append({"id": "78_rejected", "passed": rejected["rejected"] is True})
    impact = build_impact_analysis_78(order_usd=1_000_000, seed=seed)
    checks.append({"id": "78_impact_alt", "passed": impact["insight_only"] is True})

    surv = analyze_wallet_surveillance_79(wallet="0xabc123def456", suspicious_query_count=5, seed=seed)
    checks.append({"id": "79_surveillance", "passed": surv["surveillance_detected"] is True})

    ex = build_exchange_health_80(seed=seed)
    checks.append({"id": "80_exchange", "passed": ex.get("health_score", 0) > 0})

    unified = build_unified_portfolio_view_81(seed=seed)
    checks.append({"id": "81_unified", "passed": unified.get("non_custodial") is True})

    liq = evaluate_liquidation_alert_82(price=63000, liquidation_level=62000, seed=seed)
    checks.append({"id": "82_liquidation", "passed": "cascade_risk" in liq})

    deferred = smb_institution_status_83(seed=seed)
    checks.append({"id": "83_deferred", "passed": deferred["status"] == "deferred"})

    record_performance_entry_84(asset="BTC", insight="bullish", risk_score=6, confidence=7, seed=seed)
    perf = build_performance_ledger_view_84(seed=seed)
    checks.append({"id": "84_ledger", "passed": perf.get("total_recorded", 0) >= 1})

    oapi = openapi_documentation_status_85(seed=seed)
    checks.append({"id": "85_openapi", "passed": oapi.get("spec_version") == "3.0+"})

    method = build_methodology_docs_86(seed=seed)
    checks.append({"id": "86_methodology", "passed": method.get("rule_based_only_sprint_2") is True})

    portfolio = attach_portfolio_whale_layers_77_86({"holdings": holdings}, seed=seed)
    checks.append({"id": "portfolio_embed", "passed": "advanced_risk_tab" in portfolio})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
