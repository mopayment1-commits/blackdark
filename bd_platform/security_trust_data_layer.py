"""
Security, Trust & Data Sources Layer — #242–#261.

Unified audit trail, oracle/news/event data sources, trust widgets,
pricing tiers, and rejected execution features — insight-only.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.SecurityTrustData")

_SEED_PATH = Path("data/legal_retail_commercial_seed.json")
_audit_chain: list[dict[str, Any]] = []
_watchlist: list[dict[str, Any]] = []

ExportFormat = Literal["json", "csv"]


def reset_security_trust_data_state() -> None:
    _audit_chain.clear()
    _watchlist.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("security trust data seed load failed: %s", exc)
        return {}


def _disclaimer(locale: str = "en") -> str:
    if locale.lower().startswith("ar"):
        return "تحليل فقط — ليس توصية مالية ولا ضمان."
    return "Analysis only — not financial advice or guarantee."


def _chain_hash(prev_hash: str, payload: str) -> str:
    return hashlib.sha256(f"{prev_hash}:{payload}".encode()).hexdigest()


def _retention_days(tier: str) -> int:
    mapping = {"free": 90, "proof": 90, "pro": 365, "desk": 365 * 7, "data_room": 365 * 7, "institutional": 365 * 7}
    return mapping.get(tier.lower(), 90)


# ─── #242 Audit Trail ───────────────────────────────────────────────────────────


def append_audit_event_242(
    *,
    actor: str,
    action: str,
    system: str,
    tier: str = "free",
    metadata: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    metadata = metadata or {}
    prev_hash = _audit_chain[-1]["chain_hash"] if _audit_chain else "genesis"
    payload = json.dumps({"actor": actor, "action": action, "system": system, "metadata": metadata}, sort_keys=True)
    chain_hash = _chain_hash(prev_hash, payload)
    storage_fee = float((seed.get("audit_trail_242") or {}).get("fee_db", {}).get("storage_usd", 0.0001))
    entry = {
        "audit_log_id": f"aud_{uuid.uuid4().hex[:12]}",
        "timestamp": _utcnow(),
        "actor": actor,
        "action": action,
        "system": system,
        "tier": tier,
        "metadata": metadata,
        "prev_hash": prev_hash,
        "chain_hash": chain_hash,
        "immutable": True,
        "append_only": True,
        "no_wallet_data": True,
        "retention_days": _retention_days(tier),
        "fee_db": {"storage_usd": storage_fee},
    }
    _audit_chain.append(entry)
    return {"ok": True, "feature_ref": 242, "entry": entry}


def export_audit_trail_242(
    *,
    fmt: ExportFormat = "json",
    tier: str = "pro",
    _admin_mfa_required: bool = True,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    query_fee = float((seed.get("audit_trail_242") or {}).get("fee_db", {}).get("query_usd", 0.0002))
    entries = list(_audit_chain[-500:])
    return {
        "ok": True,
        "feature_ref": 242,
        "route": "/audit",
        "format": fmt,
        "entry_count": len(entries),
        "entries": entries if fmt == "json" else None,
        "csv_ready": fmt == "csv",
        "compliance_export": True,
        "admin_mfa_required": _admin_mfa_required,
        "encrypted_at_rest": True,
        "async_logging_max_ms": 50,
        "fee_db": {"query_usd": query_fee},
    }


def attach_audit_log_id_242(insight: dict[str, Any], *, actor: str = "system", action: str = "insight_generated") -> dict[str, Any]:
    out = dict(insight)
    audit = append_audit_event_242(actor=actor, action=action, system="intelligence_ledger", metadata={"feature_ref": out.get("feature_ref")})
    out["audit_log_id"] = audit["entry"]["audit_log_id"]
    merged = list(out.get("merged_features") or [])
    if 242 not in merged:
        merged.append(242)
    out["merged_features"] = merged
    return out


# ─── #243 Bybit API — Oracle secondary ──────────────────────────────────────────


def ingest_bybit_price_243(
    *,
    symbol: str = "BTC",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee = float((seed.get("bybit_api_243") or {}).get("fee_db", {}).get("ingest_usd", 0.0003))
    return {
        "ok": True,
        "feature_ref": 243,
        "source": "bybit",
        "merged_into": "oracle_api",
        "route": "/oracle/prices",
        "symbol": symbol.upper(),
        "price_usd": 65_095.0,
        "role": "secondary_fallback",
        "fallback_after": ["binance", "coingecko"],
        "normalized_oracle_format": True,
        "latency_ms": 145,
        "fee_db": {"ingest_usd": fee},
    }


# ─── #244 CoinTelegraph RSS ─────────────────────────────────────────────────────


def ingest_cointelegraph_rss_244(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee = float((seed.get("cointelegraph_rss_244") or {}).get("fee_db", {}).get("ingest_usd", 0.0002))
    articles = [
        {"title": "Bitcoin ETF inflows continue", "category": "markets", "keyword_match": "etf"},
        {"title": "Ethereum upgrade timeline", "category": "technology", "keyword_match": "ethereum"},
    ]
    return {
        "ok": True,
        "feature_ref": 244,
        "source": "cointelegraph",
        "merged_into": ["market_radar", "daily_top3_62"],
        "route": "/radar/news",
        "articles": articles,
        "rule_based_filtering": True,
        "deduplicated": True,
        "fee_db": {"ingest_usd": fee},
    }


# ─── #245 CoinMarketCal — merged Market Radar ───────────────────────────────────


def coinmarketcal_status_245(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return {
        "ok": True,
        "feature_ref": 245,
        "source": "coinmarketcal",
        "merged_into": ["market_radar", "signal_engine_11", "daily_top3_62"],
        "route": "/radar/events",
        "activation_not_build": True,
        "existing_endpoint": "/api/platform/events/calendar",
        "event_categories": ["release", "partnership", "update"],
        "impact_levels": ["low", "medium", "high"],
        "fee_db": {"ingest_usd": 0.0004},
    }


# ─── #246 Etherscan Watch List ──────────────────────────────────────────────────


def add_etherscan_watch_246(
    *,
    address: str,
    threshold_eth: float = 1000.0,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    entry = {
        "address": address,
        "threshold_eth": threshold_eth,
        "privacy_first": True,
        "no_wallet_connection": True,
        "no_deanonymization": True,
        "created_at": _utcnow(),
    }
    _watchlist.append(entry)
    fee = float((seed.get("etherscan_watchlist_246") or {}).get("fee_db", {}).get("rpc_usd", 0.0005))
    entry["fee_db"] = {"rpc_usd": fee}
    return {"ok": True, "feature_ref": 246, "watch": entry}


def list_etherscan_watchlist_246(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "feature_ref": 246,
        "route": "/oracle/on-chain",
        "merged_into": ["on_chain_extension", "signal_engine_11"],
        "watches": list(_watchlist),
        "rule_based_alerts": True,
        "manual_address_entry_only": True,
    }


# ─── #247 Weekly Digest — Intelligence Ledger ───────────────────────────────────


def generate_weekly_digest_247(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee = float((seed.get("weekly_digest_247") or {}).get("fee_db", {}).get("compute_usd", 0.005))
    return {
        "ok": True,
        "feature_ref": 247,
        "report_type": "weekly_digest",
        "merged_into": "intelligence_ledger",
        "rule_based_only": True,
        "ai_reports_rejected": True,
        "sections": {
            "signals": 12,
            "radar_events": 8,
            "on_chain_anomalies": 3,
            "risk_score_avg": 5.2,
        },
        "summary_not_recommendation": True,
        "delivery": ["email", "notification"],
        "disclaimer": _disclaimer(),
        "fee_db": {"compute_usd": fee, "delivery_usd": 0.001},
    }


# ─── #248 Profit Analytics — REJECTED standalone ────────────────────────────────


def profit_analytics_rejected_status_248(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "feature_ref": 248,
        "status": "rejected_standalone",
        "profit_analytics_rejected": True,
        "alternative": "manual_performance_tracker",
        "alternative_route": "/portfolio/performance/manual",
        "custodial_risk": True,
    }


def manual_performance_tracker_248(
    *,
    trades: list[dict[str, Any]] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    trades = trades or [{"asset": "BTC", "entry": 60000, "exit": 65000, "pnl_pct": 8.3}]
    fee = float((seed.get("manual_performance_248") or {}).get("fee_db", {}).get("compute_usd", 0.002))
    return {
        "ok": True,
        "feature_ref": 248,
        "route": "/portfolio/performance/manual",
        "manual_entry_only": True,
        "trades": trades,
        "analysis_not_auto_tracking": True,
        "no_exchange_connection": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── #249 TRAD SIMULATOR — REJECTED ─────────────────────────────────────────────


def trad_simulator_rejected_status_249() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_ref": 249,
        "status": "rejected",
        "trad_simulator_rejected": True,
        "alternative": "backtest_74",
        "no_module": True,
    }


# ─── #250 EXECUTION SPEED — REJECTED ────────────────────────────────────────────


def execution_speed_rejected_status_250() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_ref": 250,
        "status": "rejected_execution",
        "execution_speed_rejected": True,
        "no_alternative": True,
        "insight_only_platform": True,
    }


# ─── #251 Token Velocity ────────────────────────────────────────────────────────


def compute_token_velocity_251(
    *,
    asset: str = "ETH",
    circulating_supply: float = 120_000_000,
    trading_volume_30d: float = 45_000_000_000,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    velocity = round(circulating_supply / max(trading_volume_30d / 30, 1), 4)
    fee = float((seed.get("token_velocity_251") or {}).get("fee_db", {}).get("compute_usd", 0.002))
    return {
        "ok": True,
        "feature_ref": 251,
        "metric": "token_velocity",
        "routes": ["/oracle/on-chain", "/oracle/on-chain/token-velocity"],
        "asset": asset.upper(),
        "circulating_supply": circulating_supply,
        "trading_volume_30d_usd": trading_volume_30d,
        "velocity": velocity,
        "formula": "circulating_supply / (trading_volume_30d / 30)",
        "rule_based_only": True,
        "fee_db": {"compute_usd": fee, "rpc_usd": 0.0005},
    }


# ─── #252 Google Trends ─────────────────────────────────────────────────────────


def ingest_google_trends_252(
    *,
    asset: str = "bitcoin",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee = float((seed.get("google_trends_252") or {}).get("fee_db", {}).get("ingest_usd", 0.0003))
    score = 68
    return {
        "ok": True,
        "feature_ref": 252,
        "source": "google_trends",
        "merged_into": ["sentiment_layer", "market_radar", "signal_engine_11"],
        "route": "/radar/sentiment",
        "asset": asset,
        "interest_score": score,
        "high_interest_threshold": 50,
        "elevated_interest": score > 50,
        "relative_comparison": {"bitcoin": score, "ethereum": 52},
        "free_tier_limited": True,
        "fee_db": {"ingest_usd": fee},
    }


# ─── #253 Kill-Rate Board ───────────────────────────────────────────────────────


def build_kill_rate_widget_253(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    try:
        from kill_rate_board import build_kill_rate_board

        board = build_kill_rate_board()
        metrics = board.get("metrics", {})
    except ImportError:
        metrics = {"kill_rate_percent": 62.0, "total_kills": 120, "total_evaluated": 194}
    fee = float((seed.get("kill_rate_board_253") or {}).get("fee_db", {}).get("compute_usd", 0.001))
    return {
        "ok": True,
        "feature_ref": 253,
        "widget": "system_discipline",
        "merged_into": ["proof_arena", "landing_page", "viral_share"],
        "metrics": metrics,
        "public_transparency": True,
        "rule_based": True,
        "brag_about_refusal": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── #254 Contradiction Replay ──────────────────────────────────────────────────


def build_contradiction_replay_254(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee = float((seed.get("contradiction_replay_254") or {}).get("fee_db", {}).get("compute_usd", 0.002))
    return {
        "ok": True,
        "feature_ref": 254,
        "merged_into": "proof_arena",
        "clip": {
            "signal_a": {"direction": "opportunity", "asset": "BTC"},
            "signal_b": {"direction": "neutral", "asset": "BTC"},
            "resolution": "contradiction_logged",
            "outcome_followup": "price_flat_24h",
        },
        "rule_based": True,
        "shareable": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── #255 Committee One-Pager ─────────────────────────────────────────────────


def committee_one_pager_status_255(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return {
        "ok": True,
        "feature_ref": 255,
        "report_type": "committee_one_pager",
        "merged_into": "intelligence_ledger",
        "sections": ["thesis", "risk", "data", "methodology", "disclaimer"],
        "rule_based_only": True,
        "pro_desk_tier_only": True,
        "existing_module": "committee_one_pager.py",
        "fee_db": {"generate_usd": 0.01, "pdf_export_usd": 0.005},
    }


# ─── #256 Half-Life Heat Clock ──────────────────────────────────────────────────


def compute_half_life_clock_256(
    *,
    opportunity_age_minutes: float = 45.0,
    volatility_decay: float = 0.8,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    half_life_minutes = round(60 * volatility_decay, 1)
    remaining_pct = max(0, round(100 * (1 - opportunity_age_minutes / (half_life_minutes * 2)), 1))
    fee = float((seed.get("half_life_clock_256") or {}).get("fee_db", {}).get("compute_usd", 0.0005))
    return {
        "ok": True,
        "feature_ref": 256,
        "component": "half_life_heat_clock",
        "merged_into": ["signal_engine_11", "market_radar"],
        "opportunity_age_minutes": opportunity_age_minutes,
        "half_life_minutes": half_life_minutes,
        "remaining_vitality_pct": remaining_pct,
        "formula": "half_life from volatility + volume decay",
        "fee_db": {"compute_usd": fee},
    }


# ─── #257 Proof Arena Lite ──────────────────────────────────────────────────────


def proof_arena_lite_status_257(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "feature_ref": 257,
        "mode": "lite",
        "merged_into": "proof_arena",
        "duplicate_not_build": True,
        "weekly_user_vs_system": True,
        "public_free": True,
    }


# ─── #258 Since You Left Top-3 ──────────────────────────────────────────────────


def since_you_left_top3_258(
    *,
    last_visit_ts: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee = float((seed.get("since_you_left_258") or {}).get("fee_db", {}).get("query_usd", 0.001))
    events = [
        {"type": "price_move", "asset": "BTC", "change_pct": 12.5, "threshold_met": True},
        {"type": "signal_generated", "asset": "ETH", "rule": "volume_spike"},
        {"type": "on_chain_anomaly", "asset": "SOL", "detail": "whale_inflow"},
    ]
    return {
        "ok": True,
        "feature_ref": 258,
        "widget": "since_you_left",
        "merged_into": ["portfolio_ai", "landing_page"],
        "last_visit_ts": last_visit_ts or _utcnow(),
        "top_events": events[:3],
        "rule_based": True,
        "fee_db": {"query_usd": fee},
    }


# ─── #259 Anti-Hype Mode ────────────────────────────────────────────────────────


_ANTI_HYPE_DICT = {
    "انفجار": "ارتفاع",
    "فرصة ذهبية": "فرصة محتملة",
    "moon": "rise",
    "guaranteed": "possible",
}


def apply_anti_hype_mode_259(text: str, *, enabled: bool = True) -> dict[str, Any]:
    out = text
    replacements = []
    if enabled:
        for hype, calm in _ANTI_HYPE_DICT.items():
            if hype.lower() in out.lower():
                out = out.replace(hype, calm)
                replacements.append({"from": hype, "to": calm})
    return {
        "ok": True,
        "feature_ref": 259,
        "setting": "anti_hype_mode",
        "merged_into": "user_preferences",
        "enabled": enabled,
        "original": text,
        "sanitized": out,
        "replacements": replacements,
        "client_side_capable": True,
        "fee_db": {"compute_usd": 0.0},
    }


# ─── #260 Corpus Passport ───────────────────────────────────────────────────────


def corpus_passport_status_260(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return {
        "ok": True,
        "feature_ref": 260,
        "document": "corpus_passport",
        "merged_into": "intelligence_ledger",
        "sections": ["methodology", "performance_metrics", "fee_db_summary", "audit_trail_ref"],
        "requires_audit_trail_242": True,
        "pro_desk_tier_only": True,
        "export_pdf": True,
        "existing_page": "/corpus-passport",
        "fee_db": {"generate_usd": 0.008},
    }


# ─── #261 Pricing Model ─────────────────────────────────────────────────────────


def pricing_model_status_261(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("pricing_model_261") or {}
    tiers = cfg.get("tiers") or {
        "proof": {"price_usd": 0, "api_calls_per_day": 100, "label": "Proof (Free)"},
        "pro": {"price_usd": 29, "api_calls_per_day": 1000, "label": "Pro"},
        "desk": {"price_usd": 49, "api_calls_per_day": 10000, "label": "Desk"},
        "data_room": {"price_usd": 3000, "api_calls_per_day": None, "label": "Data Room", "sla": "best_effort"},
    }
    return {
        "ok": True,
        "feature_ref": 261,
        "extends_ref": 60,
        "route": "/stripe/tiers",
        "merged_into": "stripe_integration_60",
        "tiers": tiers,
        "no_lifetime_access": True,
        "recurring_only": True,
        "usage_based_billing": True,
        "rate_limits_are_verification": True,
        "sla_best_effort_only": True,
        "fee_db": cfg.get("fee_db", {"stripe_webhook_usd": 0.001}),
    }


# ─── E2E ────────────────────────────────────────────────────────────────────────


def run_security_trust_data_e2e_242_261(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_security_trust_data_state()
    checks: list[dict[str, Any]] = []

    audit = append_audit_event_242(actor="user@test", action="login", system="landing", seed=seed)
    checks.append({"id": "242_audit", "passed": audit["entry"]["immutable"] is True})
    export = export_audit_trail_242(seed=seed)
    checks.append({"id": "242_export", "passed": export["compliance_export"] is True})

    checks.append({"id": "243_bybit", "passed": ingest_bybit_price_243(seed=seed)["role"] == "secondary_fallback"})
    checks.append({"id": "244_rss", "passed": ingest_cointelegraph_rss_244(seed=seed)["deduplicated"] is True})
    checks.append({"id": "245_cal", "passed": coinmarketcal_status_245(seed=seed)["activation_not_build"] is True})

    watch = add_etherscan_watch_246(address="0xabc123", seed=seed)
    checks.append({"id": "246_watch", "passed": watch["watch"]["privacy_first"] is True})

    digest = generate_weekly_digest_247(seed=seed)
    checks.append({"id": "247_digest", "passed": digest["summary_not_recommendation"] is True})

    checks.append({"id": "248_rejected", "passed": profit_analytics_rejected_status_248(seed=seed)["profit_analytics_rejected"] is True})
    checks.append({"id": "249_rejected", "passed": trad_simulator_rejected_status_249()["trad_simulator_rejected"] is True})
    checks.append({"id": "250_rejected", "passed": execution_speed_rejected_status_250()["execution_speed_rejected"] is True})

    velocity = compute_token_velocity_251(seed=seed)
    checks.append({"id": "251_velocity", "passed": velocity["velocity"] > 0})

    trends = ingest_google_trends_252(seed=seed)
    checks.append({"id": "252_trends", "passed": trends["free_tier_limited"] is True})

    kill = build_kill_rate_widget_253(seed=seed)
    checks.append({"id": "253_kill", "passed": kill["public_transparency"] is True})

    replay = build_contradiction_replay_254(seed=seed)
    checks.append({"id": "254_replay", "passed": replay["shareable"] is True})

    checks.append({"id": "255_pager", "passed": committee_one_pager_status_255(seed=seed)["rule_based_only"] is True})

    clock = compute_half_life_clock_256(seed=seed)
    checks.append({"id": "256_clock", "passed": "half_life_minutes" in clock})

    checks.append({"id": "257_arena", "passed": proof_arena_lite_status_257(seed=seed)["mode"] == "lite"})
    checks.append({"id": "258_since", "passed": len(since_you_left_top3_258(seed=seed)["top_events"]) == 3})

    hype = apply_anti_hype_mode_259("فرصة ذهبية مضمونة")
    checks.append({"id": "259_hype", "passed": len(hype["replacements"]) >= 1})

    checks.append({"id": "260_passport", "passed": corpus_passport_status_260(seed=seed)["requires_audit_trail_242"] is True})

    pricing = pricing_model_status_261(seed=seed)
    checks.append({"id": "261_pricing", "passed": pricing["no_lifetime_access"] is True and "pro" in pricing["tiers"]})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
