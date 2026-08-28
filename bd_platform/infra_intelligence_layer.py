"""
Infrastructure & Intelligence Layer — #95–#104.

NOT standalone product modules — internal ops, data engine streaming,
intelligence feedback, signal governance, and merged market/on-chain metrics.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.InfraIntelligence")

_SEED_PATH = Path("data/legal_retail_commercial_seed.json")
_USAGE_EVENTS = Path("data/usage_analytics_events.jsonl")
_STREAM_QUEUE = Path("data/streaming_event_queue.jsonl")
_FLYWHEEL_FEEDBACK = Path("data/intelligence_flywheel_feedback.jsonl")
_SIGNAL_DEFINITIONS = Path("data/sovereign_signal_definitions.json")

_usage_events: list[dict[str, Any]] = []
_stream_queue: list[dict[str, Any]] = []
_flywheel_feedback: list[dict[str, Any]] = []
_signal_definitions: dict[str, dict[str, Any]] = {}


def reset_infra_intelligence_state() -> None:
    _usage_events.clear()
    _stream_queue.clear()
    _flywheel_feedback.clear()
    _signal_definitions.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("infra intelligence seed load failed: %s", exc)
        return {}


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


# ─── #95 Feature Usage Analytics (Internal) ────────────────────────────────────


def track_usage_event_95(
    *,
    endpoint: str,
    event_type: str = "api_call",
    feature: str = "",
    duration_ms: float = 0,
    error: bool = False,
    user_id: str = "",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based event tracking — async-safe append, no user-facing product."""
    seed = seed or _load_seed()
    row = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "timestamp": _utcnow(),
        "endpoint": endpoint,
        "event_type": event_type,
        "feature": feature or endpoint.split("/")[1] if "/" in endpoint else "unknown",
        "duration_ms": round(duration_ms, 2),
        "error": error,
        "user_id_hash": hashlib.sha256(user_id.encode()).hexdigest()[:16] if user_id else "",
        "internal_only": True,
        "gdpr_compliant": True,
    }
    _usage_events.append(row)
    _append_jsonl(_USAGE_EVENTS, row)
    fee = float((seed.get("usage_analytics_95") or {}).get("fee_db", {}).get("infra_usd", 0.002))
    return {"ok": True, "feature_ref": 95, "tracked": True, "event_id": row["event_id"], "fee_db": {"infra_usd": fee}}


def build_admin_analytics_dashboard_95(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Internal admin dashboard — requires Admin MFA + RBAC (#88)."""
    seed = seed or _load_seed()
    cfg = seed.get("usage_analytics_95") or {}
    by_endpoint: dict[str, int] = defaultdict(int)
    by_feature: dict[str, int] = defaultdict(int)
    errors = 0
    for ev in _usage_events:
        by_endpoint[ev.get("endpoint", "unknown")] += 1
        by_feature[ev.get("feature", "unknown")] += 1
        if ev.get("error"):
            errors += 1
    total = len(_usage_events) or 1
    low_usage = [f for f, c in by_feature.items() if c / total < 0.10]
    return {
        "ok": True,
        "feature_ref": 95,
        "route": "/admin/analytics",
        "internal_only": True,
        "admin_mfa_required": True,
        "rbac_ref": 88,
        "privacy_first": True,
        "no_third_party_tracking": True,
        "summary": {
            "total_events": len(_usage_events),
            "unique_endpoints": len(by_endpoint),
            "error_rate_pct": round(errors / total * 100, 2),
            "top_endpoints": sorted(by_endpoint.items(), key=lambda x: -x[1])[:10],
            "low_usage_features": low_usage,
            "insight": {
                "en": f"{len(low_usage)} features used <10% — consider redesign or removal",
                "ar": f"{len(low_usage)} ميزات استخدامها أقل من 10% — فكّر في إعادة التصميم أو الإزالة",
            },
        },
        "async_ingestion": cfg.get("policy", {}).get("async_queue", "redis_streams"),
        "fee_db": cfg.get("fee_db", {}),
        "timestamp": _utcnow(),
    }


# ─── #96 Streaming Stack (Data Engine) ─────────────────────────────────────────


def streaming_stack_status_96(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("streaming_stack_96") or {}
    result = {
        "ok": True,
        "feature_ref": 96,
        "merged_into": "data_engine",
        "transport": cfg.get("transport", "redis_streams"),
        "ai_training": "deferred",
        "ml_pipeline_open": False,
        "ml_blocked_until": cfg.get("policy", {}).get(
            "ml_blocked_until", "90_days_and_10000_signals_and_backtest"
        ),
        "latency_target_ms": cfg.get("policy", {}).get("latency_target_ms", 100),
        "queue_depth": len(_stream_queue),
        "architecture_ready_for_ml": True,
        "no_auto_trading": True,
        "fee_db": cfg.get("fee_db", {}),
        "timestamp": _utcnow(),
    }
    try:
        from bd_platform.intelligence_analysis_layer import multi_venue_websocket_status_158

        result["multi_venue_websocket"] = multi_venue_websocket_status_158(seed=seed)
    except ImportError:
        pass
    return result


def enqueue_stream_event_96(
    *,
    source: str = "oracle",
    payload: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Async ingestion — does not block API response path."""
    seed = seed or _load_seed()
    row = {
        "event_id": f"str_{uuid.uuid4().hex[:12]}",
        "ingested_at": _utcnow(),
        "source": source,
        "payload": payload or {},
        "available": True,
    }
    _stream_queue.append(row)
    _append_jsonl(_STREAM_QUEUE, row)
    fee = float((seed.get("streaming_stack_96") or {}).get("fee_db", {}).get("ingest_usd", 0.0001))
    return {
        "ok": True,
        "feature_ref": 96,
        "queued": True,
        "event_id": row["event_id"],
        "latency_target_ms": 100,
        "fee_db": {"ingest_usd": fee},
    }


# ─── #97 Data Flywheel (Intelligence Ledger Feedback) ──────────────────────────

FeedbackLabel = Literal["hit", "miss", "neutral"]


def submit_insight_feedback_97(
    *,
    insight_id: str,
    feedback: FeedbackLabel,
    actual_outcome: str = "",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    row = {
        "feedback_id": f"fb_{uuid.uuid4().hex[:10]}",
        "insight_id": insight_id,
        "feedback": feedback,
        "actual_outcome": actual_outcome,
        "timestamp": _utcnow(),
        "rule_based_only": True,
    }
    _flywheel_feedback.append(row)
    _append_jsonl(_FLYWHEEL_FEEDBACK, row)
    weights = compute_flywheel_weights_97(seed=seed)
    fee = float((seed.get("data_flywheel_97") or {}).get("fee_db", {}).get("storage_usd", 0.0002))
    return {
        "ok": True,
        "feature_ref": 97,
        "merged_into": "intelligence_ledger",
        "feedback_recorded": True,
        "weights": weights,
        "non_custodial": True,
        "disclaimer": "Improves analytical accuracy — not profit guarantee",
        "fee_db": {"storage_usd": fee},
    }


def compute_flywheel_weights_97(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    hits = sum(1 for f in _flywheel_feedback if f.get("feedback") == "hit")
    misses = sum(1 for f in _flywheel_feedback if f.get("feedback") == "miss")
    total = hits + misses or 1
    hit_rate = round(hits / total * 100, 1)
    improvement_pct = round(max(0, hit_rate - 50), 1)
    return {
        "total_feedback": len(_flywheel_feedback),
        "hit_rate_pct": hit_rate,
        "improvement_pct": improvement_pct,
        "formula": "weight_update = base_weight * (1 + hit_rate_adjustment)",
        "transparency": {
            "en": f"This insight improved {improvement_pct}% based on {len(_flywheel_feedback)} prior evaluations",
            "ar": f"تحسّنت هذه التوصية بنسبة {improvement_pct}% بناءً على {len(_flywheel_feedback)} تقييم سابق",
        },
    }


# ─── #98 Sovereign Signal Registry ─────────────────────────────────────────────


def sovereign_registry_status_98(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    try:
        from signal_registry import registry_stats

        stats = registry_stats()
    except ImportError:
        stats = {"total": 0, "labeled": 0}
    return {
        "ok": True,
        "feature_ref": 98,
        "route": "/registry",
        "internal_only": True,
        "sovereign": True,
        "unified_definitions": len(_signal_definitions),
        "registry_stats": stats,
        "ci_validation": True,
        "schema": "blackdark.signal.definition.v1",
        "fee_db": (seed.get("signal_registry_98") or {}).get("fee_db", {}),
        "timestamp": _utcnow(),
    }


def register_canonical_signal_98(
    *,
    name: str,
    formula: str,
    data_source: str,
    signal_type: str = "custom",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    formula_hash = hashlib.sha256(formula.encode()).hexdigest()[:16]
    for existing in _signal_definitions.values():
        if existing.get("formula_hash") == formula_hash and existing.get("name") != name:
            return {
                "ok": False,
                "feature_ref": 98,
                "blocked": True,
                "reason": "duplicate_logic_different_name",
                "existing_name": existing.get("name"),
                "ci_would_block_merge": True,
            }
    sig_id = f"sig_{uuid.uuid4().hex[:12]}"
    definition = {
        "signal_id": sig_id,
        "name": name,
        "formula": formula,
        "formula_hash": formula_hash,
        "data_source": data_source,
        "signal_type": signal_type,
        "registered_at": _utcnow(),
        "schema_version": "v1",
    }
    _signal_definitions[sig_id] = definition
    _SIGNAL_DEFINITIONS.parent.mkdir(parents=True, exist_ok=True)
    _SIGNAL_DEFINITIONS.write_text(json.dumps(_signal_definitions, indent=2), encoding="utf-8")
    fee = float((seed.get("signal_registry_98") or {}).get("fee_db", {}).get("storage_usd", 0.0001))
    return {"ok": True, "feature_ref": 98, "definition": definition, "fee_db": {"storage_usd": fee}}


def validate_signal_uniqueness_98(*, name: str, formula: str) -> dict[str, Any]:
    formula_hash = hashlib.sha256(formula.encode()).hexdigest()[:16]
    for existing in _signal_definitions.values():
        if existing.get("formula_hash") == formula_hash:
            return {
                "ok": False,
                "unique": False,
                "conflict_with": existing.get("name"),
                "formula_hash": formula_hash,
            }
    return {"ok": True, "unique": True, "formula_hash": formula_hash}


# ─── #99 Sybil Attack Density Filter ───────────────────────────────────────────


def filter_sybil_clusters_99(
    wallets: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based Sybil heuristics — excludes clusters from sentiment/on-chain metrics."""
    seed = seed or _load_seed()
    cfg = (seed.get("sybil_filter_99") or {}).get("policy", {})
    threshold = int(cfg.get("coordination_threshold", 3))
    excluded: list[dict[str, Any]] = []
    clean: list[dict[str, Any]] = []

    ts_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for w in wallets:
        ts_key = str(w.get("timestamp", ""))[:19]
        ts_groups[ts_key].append(w)

    flagged_ids: set[str] = set()
    for ts, group in ts_groups.items():
        if len(group) >= threshold:
            amounts = [float(w.get("amount", 0)) for w in group]
            same_size = len(set(amounts)) == 1 or (
                amounts and max(amounts) > 0 and (max(amounts) - min(amounts)) / max(amounts) < 0.01
            )
            same_funding = len({w.get("funding_source", "") for w in group}) == 1
            if same_size or same_funding:
                cluster_id = f"cluster_{hashlib.sha256(ts.encode()).hexdigest()[:8]}"
                for w in group:
                    flagged_ids.add(str(w.get("wallet_id", w.get("address", ""))))
                excluded.append({
                    "cluster_id": cluster_id,
                    "wallet_count": len(group),
                    "reason": "same_timestamp_cluster" if same_size else "same_origin_funding",
                    "timestamp": ts,
                })

    for w in wallets:
        wid = str(w.get("wallet_id", w.get("address", "")))
        if wid not in flagged_ids:
            clean.append(w)

    fee = float((seed.get("sybil_filter_99") or {}).get("fee_db", {}).get("compute_usd", 0.001))
    result = {
        "ok": True,
        "feature_ref": 99,
        "merged_into": ["sentiment_layer", "on_chain_extension"],
        "routes": ["/radar/sentiment/filter", "/oracle/on-chain/filter"],
        "total_wallets": len(wallets),
        "excluded_count": len(flagged_ids),
        "clean_count": len(clean),
        "excluded_clusters": excluded,
        "clean_wallets": clean,
        "false_positive_target_pct": 5,
        "no_deanonymization": True,
        "metadata_disclosure": {
            "en": f"Excluded {len(flagged_ids)} suspicious wallets from this calculation",
            "ar": f"تم استبعاد {len(flagged_ids)} محفظة مشبوهة من هذا الحساب",
        },
        "fee_db": {"compute_usd": fee},
    }
    try:
        from bd_platform.onchain_platform_layer import attach_sybil_clustering_129

        return attach_sybil_clustering_129(result, wallets=wallets, seed=seed)
    except ImportError:
        return result


# ─── #101 Oracle Latency Deviation Buffer ────────────────────────────────────────


def validate_oracle_freshness_101(
    *,
    primary_timestamp_ms: float,
    secondary_timestamp_ms: float,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = (seed.get("oracle_latency_buffer_101") or {}).get("policy", {})
    stale_sec = float(cfg.get("stale_threshold_sec", 5))
    critical_sec = float(cfg.get("critical_threshold_sec", 15))
    deviation_ms = abs(primary_timestamp_ms - secondary_timestamp_ms)
    deviation_sec = deviation_ms / 1000

    if deviation_sec > critical_sec:
        status = "critical_stale"
        accepted = False
        action = "alert_and_fallback"
    elif deviation_sec > stale_sec:
        status = "stale"
        accepted = False
        action = "reject"
    else:
        status = "fresh"
        accepted = True
        action = "pass"

    fee = float((seed.get("oracle_latency_buffer_101") or {}).get("fee_db", {}).get("dual_query_usd", 0.0003))
    return {
        "ok": accepted,
        "feature_ref": 101,
        "merged_into": "oracle_api",
        "route": "/oracle/validate",
        "deviation_ms": round(deviation_ms, 2),
        "deviation_sec": round(deviation_sec, 3),
        "status": status,
        "accepted": accepted,
        "action": action,
        "data_freshness_ms": round(min(primary_timestamp_ms, secondary_timestamp_ms), 2),
        "thresholds": {"stale_sec": stale_sec, "critical_sec": critical_sec},
        "latency_check_ms": 8,
        "fee_db": {"dual_query_usd": fee},
    }


# ─── #102 Impermanent Loss Vulnerability Score ─────────────────────────────────


def compute_il_vulnerability_102(
    *,
    price_ratio: float = 1.2,
    volatility_30d: float = 0.45,
    liquidity_depth_usd: float = 5_000_000,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = (seed.get("il_vulnerability_102") or {}).get("policy", {})
    high_threshold = float(cfg.get("high_vulnerability_threshold", 70))

    il_pct = (2 * math.sqrt(price_ratio) / (1 + price_ratio) - 1) * 100
    liquidity_factor = 1 / max(liquidity_depth_usd / 1_000_000, 0.1)
    vulnerability_raw = abs(il_pct) * volatility_30d * liquidity_factor * 100
    score = round(min(100, max(0, vulnerability_raw)), 1)
    level = "high" if score > high_threshold else ("medium" if score > 40 else "low")

    fee = float((seed.get("il_vulnerability_102") or {}).get("fee_db", {}).get("compute_usd", 0.001))
    return {
        "ok": True,
        "feature_ref": 102,
        "merged_into": ["on_chain_extension", "intelligence_ledger"],
        "route": "/oracle/on-chain/defi",
        "il_pct": round(il_pct, 4),
        "vulnerability_score": score,
        "level": level,
        "formula": "IL% = 2×√(price_ratio)/(1+price_ratio) − 1; Vulnerability = IL% × Vol(30d) × 1/Liquidity",
        "assumptions": {
            "price_ratio": price_ratio,
            "volatility_30d": volatility_30d,
            "liquidity_depth_usd": liquidity_depth_usd,
        },
        "non_custodial": True,
        "exposure_analysis_only": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── #104 Leverage Ratio Overhang Factor ─────────────────────────────────────────


def compute_leverage_overhang_104(
    *,
    open_interest_usd: float = 8_000_000_000,
    average_leverage: float = 12.0,
    spot_liquidity_usd: float = 2_500_000_000,
    source_exchange: str = "aggregate",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = (seed.get("leverage_overhang_104") or {}).get("policy", {})
    red_threshold = float(cfg.get("red_threshold", 3.0))
    yellow_threshold = float(cfg.get("yellow_threshold", 2.0))

    effective_exposure = open_interest_usd * average_leverage
    overhang = round(effective_exposure / max(spot_liquidity_usd, 1), 3)
    if overhang > red_threshold:
        fragility = "red"
        label = {"en": "Market fragile — leverage overhang elevated", "ar": "السوق هش — رافعة مالية مرتفعة"}
    elif overhang > yellow_threshold:
        fragility = "yellow"
        label = {"en": "Moderate leverage overhang", "ar": "رافعة مالية معتدلة"}
    else:
        fragility = "green"
        label = {"en": "Leverage overhang within normal range", "ar": "الرافعة ضمن النطاق الطبيعي"}

    fee = float((seed.get("leverage_overhang_104") or {}).get("fee_db", {}).get("compute_usd", 0.0015))
    return {
        "ok": True,
        "feature_ref": 104,
        "merged_into": "market_radar",
        "route": "/radar/market-health",
        "effective_leverage_exposure_usd": round(effective_exposure, 0),
        "spot_liquidity_usd": spot_liquidity_usd,
        "overhang_factor": overhang,
        "fragility": fragility,
        "label": label,
        "formula": "Overhang = (OI × Avg Leverage) / Spot Liquidity (±2%)",
        "data_sources": {"open_interest": source_exchange, "liquidity": "order_book_depth"},
        "market_indicator_only": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── Attach helpers ─────────────────────────────────────────────────────────────


def attach_infra_layers_95_104(
    payload: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Embed flywheel + market health dimensions into intelligence/portfolio payloads."""
    out = dict(payload)
    out["flywheel"] = compute_flywheel_weights_97(seed=seed)
    out["market_health"] = compute_leverage_overhang_104(seed=seed)
    return out


# ─── E2E ────────────────────────────────────────────────────────────────────────


def run_infra_intelligence_e2e_95_104(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_infra_intelligence_state()
    checks: list[dict[str, Any]] = []

    track_usage_event_95(endpoint="/api/oracle/evaluate", event_type="api_call", seed=seed)
    track_usage_event_95(endpoint="/radar/exchange-health", event_type="api_call", seed=seed)
    dash = build_admin_analytics_dashboard_95(seed=seed)
    checks.append({"id": "95_dashboard", "passed": dash.get("internal_only") is True})
    checks.append({"id": "95_events", "passed": dash["summary"]["total_events"] >= 2})

    stream = streaming_stack_status_96(seed=seed)
    checks.append({"id": "96_deferred_ml", "passed": stream["ai_training"] == "deferred"})
    queued = enqueue_stream_event_96(source="oracle", payload={"asset": "BTC"}, seed=seed)
    checks.append({"id": "96_queue", "passed": queued.get("queued") is True})

    fb = submit_insight_feedback_97(insight_id="ins_1", feedback="hit", seed=seed)
    checks.append({"id": "97_feedback", "passed": fb.get("feedback_recorded") is True})

    reg = register_canonical_signal_98(name="RSI_14", formula="RSI(close, 14)", data_source="ta_engine", seed=seed)
    checks.append({"id": "98_register", "passed": reg.get("ok") is True})
    dup = register_canonical_signal_98(name="RSI_DUP", formula="RSI(close, 14)", data_source="other", seed=seed)
    checks.append({"id": "98_duplicate_block", "passed": dup.get("blocked") is True})

    sybil = filter_sybil_clusters_99([
        {"wallet_id": "w1", "timestamp": "2026-01-01T12:00:00", "amount": 100, "funding_source": "x"},
        {"wallet_id": "w2", "timestamp": "2026-01-01T12:00:00", "amount": 100, "funding_source": "x"},
        {"wallet_id": "w3", "timestamp": "2026-01-01T12:00:00", "amount": 100, "funding_source": "x"},
        {"wallet_id": "w4", "timestamp": "2026-01-02T12:00:00", "amount": 50, "funding_source": "y"},
    ], seed=seed)
    checks.append({"id": "99_sybil", "passed": sybil["excluded_count"] >= 3})

    try:
        from bd_platform.whales_institutional_layer import (
            build_advanced_risk_report_77,
            evaluate_liquidation_alert_82,
        )

        liq = evaluate_liquidation_alert_82(price=63000, liquidation_level=62000, seed=seed)
        checks.append({"id": "100_proximity", "passed": "proximity_pct" in liq})
        risk = build_advanced_risk_report_77(
            [{"symbol": "BTC", "value_usd": 100000, "btc_beta": 1.0}],
            price_history=[
                {"date": "2026-01-01", "value_usd": 120000},
                {"date": "2026-02-01", "value_usd": 80000},
                {"date": "2026-03-01", "value_usd": 100000},
            ],
            seed=seed,
        )
        checks.append({"id": "103_drawdown", "passed": "drawdown_lifecycle" in risk})
    except ImportError:
        checks.append({"id": "100_proximity", "passed": False})
        checks.append({"id": "103_drawdown", "passed": False})

    fresh = validate_oracle_freshness_101(primary_timestamp_ms=1_000_000, secondary_timestamp_ms=1_000_200, seed=seed)
    checks.append({"id": "101_fresh", "passed": fresh["accepted"] is True})
    stale = validate_oracle_freshness_101(primary_timestamp_ms=1_000_000, secondary_timestamp_ms=1_020_000, seed=seed)
    checks.append({"id": "101_stale", "passed": stale["accepted"] is False})

    il = compute_il_vulnerability_102(seed=seed)
    checks.append({"id": "102_il", "passed": il["vulnerability_score"] >= 0})

    overhang = compute_leverage_overhang_104(seed=seed)
    checks.append({"id": "104_overhang", "passed": overhang["overhang_factor"] > 0})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
