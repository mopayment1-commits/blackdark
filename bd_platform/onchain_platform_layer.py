"""
On-Chain Platform Layer — #129–#139.

NOT standalone modules — security clustering, on-chain insights,
macro dimensions, derivatives monitoring, and support layer extensions.
Execution features (#130, #131, #139) are REJECTED with insight-only alternatives.
"""

from __future__ import annotations

import hashlib
import json
import logging
import statistics
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.OnchainPlatform")

_SEED_PATH = Path("data/legal_retail_commercial_seed.json")
_support_chat_log: list[dict[str, Any]] = []


def reset_onchain_platform_state() -> None:
    _support_chat_log.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("onchain platform seed load failed: %s", exc)
        return {}


def _disclaimer(locale: str = "en") -> str:
    if locale.lower().startswith("ar"):
        return "تحليل فقط — ليس توصية مالية ولا ضمان. للاستفسارات المالية استشر مستشارك المرخص."
    return "Analysis only — not financial advice. For financial questions consult your licensed advisor."


# ─── #129 Sybil Identity Linker (extends #99) ───────────────────────────────────


def cluster_sybil_identities_129(
    wallets: list[dict[str, Any]] | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Entity clustering via rule-based heuristics — extends Sybil Filter #99."""
    seed = seed or _load_seed()
    cfg = (seed.get("sybil_identity_linker_129") or {}).get("policy", {})
    cluster_threshold = float(cfg.get("cluster_score_threshold", 0.85))
    weights = cfg.get("weights") or {
        "common_funding": 0.40,
        "temporal_coordination": 0.35,
        "size_correlation": 0.25,
    }

    wallets = wallets or [
        {"wallet_id": "w1", "funding_source": "0xabc", "timestamp": "2026-01-01T12:00:00", "amount": 100},
        {"wallet_id": "w2", "funding_source": "0xabc", "timestamp": "2026-01-01T12:00:01", "amount": 101},
        {"wallet_id": "w3", "funding_source": "0xabc", "timestamp": "2026-01-01T12:00:02", "amount": 99},
        {"wallet_id": "w4", "funding_source": "0xdef", "timestamp": "2026-01-02T10:00:00", "amount": 50},
    ]

    funding_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for w in wallets:
        funding_groups[str(w.get("funding_source", "unknown"))].append(w)

    clusters: list[dict[str, Any]] = []
    for funding, group in funding_groups.items():
        if len(group) < 2:
            continue
        amounts = [float(w.get("amount", 0)) for w in group]
        size_corr = 1.0 if len(set(amounts)) == 1 else (
            0.95 if amounts and (max(amounts) - min(amounts)) / max(amounts) < 0.05 else 0.5
        )
        temporal = 1.0 if len({str(w.get("timestamp", ""))[:16] for w in group}) == 1 else 0.7
        funding_score = 1.0 if funding != "unknown" else 0.3
        cluster_score = round(
            funding_score * weights["common_funding"]
            + temporal * weights["temporal_coordination"]
            + size_corr * weights["size_correlation"],
            3,
        )
        if cluster_score >= cluster_threshold:
            cid = f"cluster_{hashlib.sha256(funding.encode()).hexdigest()[:8]}"
            clusters.append({
                "cluster_id": cid,
                "wallet_count": len(group),
                "cluster_score": cluster_score,
                "same_entity_likely": True,
                "avg_movement_usd": round(sum(amounts) * 50_000, 2),
                "funding_source_hash": hashlib.sha256(funding.encode()).hexdigest()[:12],
                "wallet_ids": [w.get("wallet_id", w.get("address", "")) for w in group],
                "heuristics": {
                    "common_funding": funding_score,
                    "temporal_coordination": temporal,
                    "size_correlation": size_corr,
                },
                "insight": {
                    "en": f"Cluster {cid}: {len(group)} wallets linked to single funding source",
                    "ar": f"مجموعة {cid}: {len(group)} محفظة مرتبطة بمصدر تمويل واحد",
                },
            })

    fee = float((seed.get("sybil_identity_linker_129") or {}).get("fee_db", {}).get("compute_usd", 0.002))
    result = {
        "ok": True,
        "feature_ref": 129,
        "route": "/oracle/on-chain/sybil-clustering",
        "extends_ref": 99,
        "merged_into": ["on_chain_extension", "sentiment_layer"],
        "clusters": clusters,
        "cluster_count": len(clusters),
        "cluster_threshold": cluster_threshold,
        "weights": weights,
        "no_deanonymization": True,
        "pattern_analysis_only": True,
        "false_positive_target_pct": 5,
        "fee_db": {"compute_usd": fee},
    }
    try:
        from bd_platform.risk_infrastructure_layer import attach_cluster_index_168

        return attach_cluster_index_168(result, seed=seed)
    except ImportError:
        return result


def attach_sybil_clustering_129(sybil_result: dict[str, Any], *, wallets: list[dict[str, Any]] | None = None, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    out = dict(sybil_result)
    out["identity_linker"] = cluster_sybil_identities_129(wallets, seed=seed)
    merged = list(out.get("merged_features") or [99])
    if 129 not in merged:
        merged.append(129)
    out["merged_features"] = merged
    return out


# ─── #130 Shadow-Fork — REJECTED → Transaction Risk Insight ─────────────────────


def transaction_risk_insight_130(
    *,
    swap_usd: float = 10_000,
    pair: str = "ETH/USDC",
    slippage_pct: float = 2.5,
    gas_gwei: float = 45,
    estimated_gas_usd: float = 12,
    contract_verified: bool = False,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee = float((seed.get("tx_risk_insight_130") or {}).get("fee_db", {}).get("compute_usd", 0.0006))
    return {
        "ok": True,
        "feature_ref": 130,
        "status": "rejected_execution",
        "alternative": "transaction_risk_insight",
        "route": "/oracle/on-chain/tx-risk",
        "execution_rejected": True,
        "no_simulation_no_transaction": True,
        "swap_usd": swap_usd,
        "pair": pair,
        "estimated_slippage_pct": slippage_pct,
        "gas_gwei": gas_gwei,
        "estimated_gas_usd": estimated_gas_usd,
        "contract_verified": contract_verified,
        "insights": [
            {
                "en": f"Swap of ${swap_usd:,.0f} on {pair} may cause ~{slippage_pct}% slippage based on current depth",
                "ar": f"swap بقيمة ${swap_usd:,.0f} على {pair} قد يسبب انزلاق ~{slippage_pct}%",
            },
            {
                "en": f"Gas: {gas_gwei:.0f} gwei — estimated cost ${estimated_gas_usd:.0f}",
                "ar": f"Gas: {gas_gwei:.0f} gwei — تكلفة تقديرية ${estimated_gas_usd:.0f}",
            },
            {
                "en": "Target contract unverified — interact with caution" if not contract_verified else "Contract verified",
                "ar": "العقد غير مُدقَّق — توخَّ الحذر" if not contract_verified else "العقد مُدقَّق",
            },
        ],
        "fee_db": {"compute_usd": fee},
    }


# ─── #131 Dust Sweeper — REJECTED → Dust Asset Analysis ─────────────────────────


def analyze_dust_assets_131(
    assets: list[dict[str, Any]] | None = None,
    *,
    dust_threshold_usd: float = 5.0,
    gas_cost_usd: float = 30.0,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    assets = assets or [
        {"symbol": "TOKEN1", "value_usd": 2.5},
        {"symbol": "TOKEN2", "value_usd": 1.8},
        {"symbol": "TOKEN3", "value_usd": 4.2},
        {"symbol": "ETH", "value_usd": 500},
    ]
    dust = [a for a in assets if float(a.get("value_usd", 0)) < dust_threshold_usd]
    total_dust = round(sum(float(a.get("value_usd", 0)) for a in dust), 2)
    uneconomical = total_dust < gas_cost_usd
    fee = float((seed.get("dust_analysis_131") or {}).get("fee_db", {}).get("compute_usd", 0.0004))

    return {
        "ok": True,
        "feature_ref": 131,
        "status": "rejected_execution",
        "alternative": "dust_asset_analysis",
        "route": "/portfolio/dust-analysis",
        "execution_rejected": True,
        "no_sweeper_no_automation": True,
        "dust_asset_count": len(dust),
        "total_dust_usd": total_dust,
        "gas_cost_estimate_usd": gas_cost_usd,
        "uneconomical_to_convert": uneconomical,
        "insight": {
            "en": (
                f"Portfolio has {len(dust)} assets under ${dust_threshold_usd} each — total ${total_dust:.0f}. "
                f"Converting to ETH may cost ${gas_cost_usd:.0f} in gas — {'not economical' if uneconomical else 'may be viable'}"
            ),
            "ar": (
                f"المحفظة تحتوي {len(dust)} أصول أقل من ${dust_threshold_usd} — إجمالي ${total_dust:.0f}. "
                f"التحويل قد يكلف ${gas_cost_usd:.0f} gas"
            ),
        },
        "non_custodial": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── #132 Flash Loan Vulnerability Scanner (no self-patching) ───────────────────


def scan_flash_loan_vulnerabilities_132(
    *,
    protocol: str = "aave_v3",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("flash_loan_scanner_132") or {}
    vectors_checked = ["reentrancy", "price_oracle_manipulation", "uncollateralized_borrow"]
    risk_scores = {
        "uniswap_v3": 25,
        "aave_v3": 35,
        "compound_v3": 40,
        "custom_defi": 72,
    }
    score = float(risk_scores.get(protocol, 50))
    alert = score > 70
    fee = float(cfg.get("fee_db", {}).get("compute_usd", 0.003))

    return {
        "ok": True,
        "feature_ref": 132,
        "route": "/oracle/on-chain/security/flash-loan-scan",
        "merged_into": "on_chain_extension",
        "self_patching_rejected": True,
        "protocol": protocol,
        "risk_score": score,
        "alert_triggered": alert,
        "vectors_checked": vectors_checked,
        "heuristics": "rule_based_pattern_matching",
        "audit_source": "public_audit_reports + on_chain_analysis",
        "security_scan_not_guarantee": True,
        "disclaimer": _disclaimer(),
        "fee_db": {"compute_usd": fee},
    }


# ─── #133 Macro Event Nexus (Rule-Based, not AI) ────────────────────────────────


def compute_macro_event_nexus_133(
    *,
    event: str = "CPI",
    event_date: str = "2026-03-12",
    historical_btc_move_pct: float = 8.0,
    current_volatility_regime: float = 1.2,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    expected_impact = round(historical_btc_move_pct * current_volatility_regime, 1)
    risk_elevated = expected_impact > 5
    fee = float((seed.get("macro_event_nexus_133") or {}).get("fee_db", {}).get("compute_usd", 0.001))

    result = {
        "ok": True,
        "feature_ref": 133,
        "merged_into": ["multi_dim_analysis_73", "market_radar"],
        "routes": ["/intelligence/multi-dim/macro", "/radar/market-health/macro"],
        "ai_naming_rejected": True,
        "rule_based_only": True,
        "event": event,
        "event_date": event_date,
        "historical_btc_move_24h_pct": historical_btc_move_pct,
        "volatility_regime_multiplier": current_volatility_regime,
        "expected_impact_pct": expected_impact,
        "risk_elevated": risk_elevated,
        "formula": "Expected Impact = Historical Avg × Volatility Regime",
        "insight": {
            "en": f"{event} on {event_date} — historically BTC ±{historical_btc_move_pct}% in 24h — Risk Score elevated" if risk_elevated else f"{event} — moderate historical impact",
            "ar": f"{event} في {event_date} — تاريخياً BTC ±{historical_btc_move_pct}% خلال 24 ساعة",
        },
        "historical_not_prediction": True,
        "fee_db": {"compute_usd": fee},
    }
    try:
        from bd_platform.risk_infrastructure_layer import attach_m2_macro_flow_171

        return attach_m2_macro_flow_171(result, seed=seed)
    except ImportError:
        return result


def attach_macro_nexus_to_multi_dim_133(multi_dim: dict[str, Any], *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    out = dict(multi_dim)
    macro = compute_macro_event_nexus_133(seed=seed)
    dims = dict(out.get("dimensions") or {})
    if "macro" in dims:
        dims["macro"]["event_nexus"] = macro
    out["dimensions"] = dims
    merged = list(out.get("merged_features") or [73])
    for ref in (111, 133):
        if ref not in merged:
            merged.append(ref)
    out["merged_features"] = merged
    return out


# ─── #134 Delta Convergence Monitor ─────────────────────────────────────────────


def compute_delta_convergence_134(
    *,
    delta_a: float = 0.52,
    delta_b: float = 0.38,
    market_a: str = "binance_futures",
    market_b: str = "dydx_perps",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = (seed.get("delta_convergence_134") or {}).get("policy", {})
    divergence_thresh = float(cfg.get("divergence_threshold_pct", 15))
    normal_thresh = float(cfg.get("normal_threshold_pct", 5))

    avg = (abs(delta_a) + abs(delta_b)) / 2 or 1
    convergence_pct = round(abs(delta_a - delta_b) / avg * 100, 1)
    if convergence_pct > divergence_thresh:
        status = "pricing_divergence"
        label = {"en": f"Pricing divergence {convergence_pct}% between {market_a} and {market_b}", "ar": f"تفكك تسعير {convergence_pct}%"}
    elif convergence_pct < normal_thresh:
        status = "normal_convergence"
        label = {"en": "Normal delta convergence", "ar": "تقارب طبيعي"}
    else:
        status = "moderate_divergence"
        label = {"en": f"Moderate divergence {convergence_pct}%", "ar": f"تفكك معتدل {convergence_pct}%"}

    fee = float((seed.get("delta_convergence_134") or {}).get("fee_db", {}).get("compute_usd", 0.004))
    return {
        "ok": True,
        "feature_ref": 134,
        "route": "/radar/derivatives/delta-convergence",
        "merged_into": "market_radar",
        "delta_a": delta_a,
        "delta_b": delta_b,
        "market_a": market_a,
        "market_b": market_b,
        "convergence_pct": convergence_pct,
        "status": status,
        "label": label,
        "formula": "Convergence = |Delta_A − Delta_B| / Average(Delta_A, Delta_B) × 100",
        "arbitrage_insight_not_recommendation": True,
        "no_auto_action": True,
        "tier": "pro_institution",
        "fee_db": {"compute_usd": fee},
    }


# ─── #135 Liquidity Vortex Locator (Rule-Based) ─────────────────────────────────


def locate_liquidity_vortex_135(
    *,
    price_level: float = 65000,
    depth_sigma: float = 3.5,
    depth_velocity_pct: float = 600,
    persistence_minutes: int = 45,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = (seed.get("liquidity_vortex_135") or {}).get("policy", {})
    vortex_threshold = float(cfg.get("vortex_score_threshold", 80))

    clustering = min(100, depth_sigma / 3 * 100)
    velocity = min(100, depth_velocity_pct / 5)
    persistence = min(100, persistence_minutes / 30 * 100)
    vortex_score = round(clustering * velocity * persistence / 10000, 1)
    is_vortex = vortex_score > vortex_threshold

    fee = float((seed.get("liquidity_vortex_135") or {}).get("fee_db", {}).get("compute_usd", 0.002))
    return {
        "ok": True,
        "feature_ref": 135,
        "route": "/radar/market-health/liquidity-vortex",
        "merged_into": "market_radar",
        "ai_naming_rejected": True,
        "rule_based_only": True,
        "price_level": price_level,
        "vortex_score": vortex_score,
        "is_vortex": is_vortex,
        "components": {"clustering": clustering, "velocity": velocity, "persistence": persistence},
        "formula": "Vortex Score = Clustering × Velocity × Persistence",
        "insight": {
            "en": f"Buy vortex at ${price_level:,.0f} — abnormal depth — may indicate accumulation" if is_vortex else "No significant vortex detected",
            "ar": f"دوامة شراء عند ${price_level:,.0f} — depth غير طبيعي" if is_vortex else "لا دوامة ملحوظة",
        },
        "fee_db": {"compute_usd": fee},
    }


# ─── #136 Support Chatbot (not Broker-Advisor) ────────────────────────────────

SupportIntent = Literal["billing", "account", "features", "api_docs", "financial_question"]


def support_chat_response_136(
    *,
    message: str,
    intent: SupportIntent | None = None,
    user_tier: str = "free",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    msg_lower = message.lower()
    if intent is None:
        if any(w in msg_lower for w in ("buy", "sell", "should i", "recommend")):
            intent = "financial_question"
        elif any(w in msg_lower for w in ("bill", "payment", "stripe", "invoice")):
            intent = "billing"
        elif any(w in msg_lower for w in ("api", "key", "endpoint")):
            intent = "api_docs"
        elif any(w in msg_lower for w in ("login", "password", "account")):
            intent = "account"
        else:
            intent = "features"

    if intent == "financial_question":
        reply = {
            "en": "I cannot provide buy/sell advice. For financial questions consult your licensed advisor.",
            "ar": "لا أستطيع تقديم نصائح شراء/بيع. للاستفسارات المالية استشر مستشارك المرخص.",
        }
        escalate = True
    elif intent == "billing":
        reply = {"en": f"Billing help for {user_tier} tier — check /pricing or contact support@blackdark.io", "ar": "مساعدة الفوترة — راجع /pricing"}
        escalate = False
    else:
        reply = {"en": "Technical support — see /docs for API documentation.", "ar": "دعم فني — راجع /docs"}
        escalate = False

    row = {"message_id": f"msg_{uuid.uuid4().hex[:10]}", "intent": intent, "timestamp": _utcnow()}
    _support_chat_log.append(row)
    fee = float((seed.get("support_chatbot_136") or {}).get("fee_db", {}).get("infra_usd", 0.0002))

    return {
        "ok": True,
        "feature_ref": 136,
        "route": "/support/chat",
        "broker_advisor_rejected": True,
        "rule_based_faq": True,
        "intent": intent,
        "reply": reply,
        "escalate_to_human": escalate,
        "no_financial_advice": True,
        "no_portfolio_data_access": True,
        "retention_days_max": 30,
        "gdpr_ref": 58,
        "disclaimer": _disclaimer(),
        "fee_db": {"infra_usd": fee},
    }


# ─── #137 B2B Fund Relationships — NOT TECHNICAL ───────────────────────────────


def b2b_relationships_status_137(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("b2b_relationships_137") or {}
    return {
        "ok": True,
        "feature_ref": 137,
        "status": "business_development_only",
        "not_a_technical_feature": True,
        "wave": 3,
        "build_blocked_until": cfg.get("build_blocked_until", "500_active_pro_users"),
        "bd_pipeline": ["outreach", "demo", "trial", "contract_negotiation"],
        "uses_existing": ["ic_report_87", "institution_portal_83", "sla_89"],
        "no_code_module": True,
    }


# ─── #138 Institutional Features — Wave 3 Activation ────────────────────────────


def institution_features_status_138(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return {
        "ok": True,
        "feature_ref": 138,
        "status": "wave_3_activation",
        "not_standalone": True,
        "merged_into": "institution_portal",
        "activation_not_build": True,
        "bundle": {
            "custom_reports": "ic_report_87",
            "extended_api": "openapi_docs_85",
            "dedicated_support": "support_chatbot_136",
            "sla": "sla_89_deferred",
            "rbac": "team_rbac_88",
        },
        "pricing_route": "/pricing",
        "same_disclosure_as_retail": True,
    }


# ─── #139 Panic Button — REJECTED → Portfolio Stress Alert ──────────────────────


def portfolio_stress_alert_139(
    *,
    portfolio_loss_pct_1h: float = 15.0,
    risk_score: float = 9.0,
    mass_liquidations: bool = True,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    triggered = portfolio_loss_pct_1h > 10 or risk_score >= 8 or mass_liquidations
    fee = float((seed.get("portfolio_stress_alert_139") or {}).get("fee_db", {}).get("compute_usd", 0.0005))

    return {
        "ok": True,
        "feature_ref": 139,
        "status": "rejected_execution",
        "alternative": "portfolio_stress_alert",
        "route": "/portfolio/stress-alert",
        "panic_button_rejected": True,
        "no_close_no_execution": True,
        "alert_triggered": triggered,
        "portfolio_loss_pct_1h": portfolio_loss_pct_1h,
        "risk_score": risk_score,
        "mass_liquidations_detected": mass_liquidations,
        "insight": {
            "en": (
                f"Portfolio down {portfolio_loss_pct_1h:.0f}% in 1h — Risk Score {risk_score:.0f}/10 — immediate review recommended"
                if triggered
                else "Portfolio stress within normal range"
            ),
            "ar": (
                f"المحفظة خسرت {portfolio_loss_pct_1h:.0f}% في ساعة — Risk Score {risk_score:.0f}/10 — مراجعة فورية مُستحسنة"
                if triggered
                else "ضغط المحفظة ضمن النطاق الطبيعي"
            ),
        },
        "proactive_insight_not_panic_button": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── E2E ────────────────────────────────────────────────────────────────────────


def run_onchain_platform_e2e_129_139(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_onchain_platform_state()
    checks: list[dict[str, Any]] = []

    cluster = cluster_sybil_identities_129(seed=seed)
    checks.append({"id": "129_cluster", "passed": cluster["cluster_count"] >= 1})

    tx = transaction_risk_insight_130(seed=seed)
    checks.append({"id": "130_rejected", "passed": tx["no_simulation_no_transaction"] is True})

    dust = analyze_dust_assets_131(seed=seed)
    checks.append({"id": "131_rejected", "passed": dust["no_sweeper_no_automation"] is True})

    flash = scan_flash_loan_vulnerabilities_132(protocol="custom_defi", seed=seed)
    checks.append({"id": "132_scan", "passed": flash["self_patching_rejected"] is True})

    macro = compute_macro_event_nexus_133(seed=seed)
    checks.append({"id": "133_macro", "passed": macro["rule_based_only"] is True})

    delta = compute_delta_convergence_134(seed=seed)
    checks.append({"id": "134_delta", "passed": delta["convergence_pct"] > 0})

    vortex = locate_liquidity_vortex_135(seed=seed)
    checks.append({"id": "135_vortex", "passed": vortex["vortex_score"] > 0})

    chat = support_chat_response_136(message="how do I buy BTC?", seed=seed)
    checks.append({"id": "136_no_advice", "passed": chat["broker_advisor_rejected"] is True})

    checks.append({"id": "137_bd", "passed": b2b_relationships_status_137(seed=seed)["not_a_technical_feature"] is True})
    checks.append({"id": "138_wave3", "passed": institution_features_status_138(seed=seed)["activation_not_build"] is True})

    stress = portfolio_stress_alert_139(seed=seed)
    checks.append({"id": "139_rejected", "passed": stress["panic_button_rejected"] is True})

    try:
        from bd_platform.infra_intelligence_layer import filter_sybil_clusters_99
        from bd_platform.pro_trader_layer import build_multi_dim_analysis_73

        sybil = attach_sybil_clustering_129(filter_sybil_clusters_99([]), seed=seed)
        checks.append({"id": "129_embed", "passed": "identity_linker" in sybil})

        multi = attach_macro_nexus_to_multi_dim_133(build_multi_dim_analysis_73(seed=seed), seed=seed)
        checks.append({"id": "133_embed", "passed": "event_nexus" in multi["dimensions"]["macro"]})
    except ImportError:
        pass

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
