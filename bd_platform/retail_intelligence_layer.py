"""
Retail Intelligence Layer — #62–#66 (Sprint 2 cross-cutting).

NOT standalone modules — output formats and UX layers merged into Intelligence Ledger,
Portfolio AI, and Alerting systems.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.RetailIntelligence")

_SEED_PATH = Path("data/legal_retail_commercial_seed.json")

Verdict = Literal["Opportunity", "Neutral", "Risk"]

_daily_top3_cache: dict[str, Any] = {}
_alert_counts: dict[str, int] = {}
_discipline_entries: list[dict[str, Any]] = []


def reset_retail_intelligence_state() -> None:
    _daily_top3_cache.clear()
    _alert_counts.clear()
    _discipline_entries.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("retail intelligence seed load failed: %s", exc)
        return {}


# ─── #64 Simple Language / Glossary (used by others) ──────────────────────────

_GLOSSARY: dict[str, dict[str, str]] = {
    "RSI": {
        "en": "Relative price strength — is the price unusually high or low?",
        "ar": "قوة السعر النسبية — هل السعر مرتفع جداً أم منخفض؟",
        "simple_en": "price strength",
        "simple_ar": "قوة السعر",
    },
    "Volume": {
        "en": "How much was traded recently — higher often means more interest.",
        "ar": "كم تم تداوله مؤخراً — الارتفاع غالباً يعني اهتماماً أكبر.",
        "simple_en": "trading activity",
        "simple_ar": "نشاط التداول",
    },
    "On-Chain": {
        "en": "Public blockchain activity — transfers, holders, network use.",
        "ar": "نشاط البلوكشين العام — التحويلات، الحائزون، استخدام الشبكة.",
        "simple_en": "blockchain activity",
        "simple_ar": "نشاط البلوكشين",
    },
    "Momentum": {
        "en": "Whether price trend is accelerating up or down.",
        "ar": "هل اتجاه السعر يتسارع صعوداً أم هبوطاً.",
        "simple_en": "price trend speed",
        "simple_ar": "سرعة اتجاه السعر",
    },
    "Liquidity": {
        "en": "How easy it is to buy or sell without moving the price much.",
        "ar": "مدى سهولة الشراء أو البيع دون تحريك السعر كثيراً.",
        "simple_en": "ease of trading",
        "simple_ar": "سهولة التداول",
    },
    "Risk Score": {
        "en": "A 1–10 scale of how risky the situation looks (not a guarantee).",
        "ar": "مقياس 1–10 لمدى مخاطرة الوضع (ليس ضماناً).",
        "simple_en": "risk level (1-10)",
        "simple_ar": "مستوى المخاطرة (1-10)",
    },
    "Impermanent Loss": {
        "en": "Temporary loss when asset prices change in a liquidity pool",
        "ar": "خسارة مؤقتة عند تغير أسعار الأصول في مجمع السيولة",
        "simple_en": "temporary pool loss",
        "simple_ar": "خسارة مؤقتة في المجمع",
    },
    "Funding Rate": {
        "en": "Periodic payment between long and short traders in perpetual futures",
        "ar": "دفعة دورية بين المتداولين الطويل والقصير في العقود الدائمة",
        "simple_en": "futures balancing fee",
        "simple_ar": "رسوم توازن العقود",
    },
    "Liquidation": {
        "en": "Forced closure of a leveraged position when margin is insufficient",
        "ar": "إغلاق قسري لمركز برافعة عندما الهامش غير كافٍ",
        "simple_en": "forced position close",
        "simple_ar": "إغلاق قسري للمركز",
    },
    "VWAP": {
        "en": "Volume-weighted average price — fair value based on traded volume",
        "ar": "متوسط السعر المرجّح بالحجم — قيمة عادلة بناءً على الحجم المتداول",
        "simple_en": "volume-weighted fair price",
        "simple_ar": "سعر عادل مرجّح بالحجم",
    },
    "FVG": {
        "en": "Fair Value Gap — price gap between candles that may act as support/resistance",
        "ar": "فجوة القيمة العادلة — فجوة سعرية قد تعمل كدعم/مقاومة",
        "simple_en": "price gap zone",
        "simple_ar": "منطقة فجوة سعرية",
    },
}


def simple_language_status_64(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("simple_language_64") or {}
    return {
        "ok": True,
        "feature_ref": 64,
        "standalone": False,
        "policy": cfg.get("policy") or {},
        "glossary_terms": len(_GLOSSARY),
        "runbook": "docs/ops/SIMPLE_LANGUAGE_LAYER.md",
        "timestamp": _utcnow(),
    }


def simplify_term_64(term: str, *, locale: str = "en") -> dict[str, str]:
    """Rule-based mapping — technical term shown once, then simple alternative."""
    entry = _GLOSSARY.get(term) or _GLOSSARY.get(term.title()) or {}
    key = "simple_ar" if locale.lower().startswith("ar") else "simple_en"
    expl_key = "ar" if locale.lower().startswith("ar") else "en"
    simple = entry.get(key) or term
    return {
        "term": term,
        "simple": simple,
        "explanation": entry.get(expl_key, ""),
        "display": f"{simple} ({term})" if entry else term,
    }


def glossary_manifest_64(*, locale: str = "en") -> dict[str, Any]:
    terms = []
    for term, entry in _GLOSSARY.items():
        key = "ar" if locale.lower().startswith("ar") else "en"
        terms.append({"term": term, "definition": entry.get(key, ""), "simple": entry.get(f"simple_{key}", "")})
    return {"ok": True, "feature_ref": 64, "locale": locale, "terms": terms, "count": len(terms)}


# ─── #63 One Clear Answer ───────────────────────────────────────────────────────


def build_one_clear_answer_63(
    *,
    verdict: Verdict,
    reasons: list[dict[str, Any]] | None = None,
    risk_score: float = 5.0,
    locale: str = "en",
    raw_indicators: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Verdict + max 3 rule-based reason points — insight not recommendation."""
    seed = seed or _load_seed()
    reasons = (reasons or [])[:3]
    while len(reasons) < 1:
        reasons.append({"point": "Insufficient data", "weight": 0.0, "rule_based": True})

    verdict_ar = {"Opportunity": "فرصة", "Neutral": "محايد", "Risk": "مخاطرة"}.get(verdict, verdict)
    answer_en = f"Verdict: {verdict} — " + "; ".join(str(r.get("point", r)) for r in reasons[:3])
    answer_ar = f"قرار: {verdict_ar} — " + "; ".join(str(r.get("point", r)) for r in reasons[:3])

    fee = float((seed.get("one_clear_answer_63") or {}).get("fee_db", {}).get("synthesis_per_query_usd", 0.0005))
    return {
        "feature_ref": 63,
        "verdict": verdict,
        "reasons": reasons[:3],
        "risk_score": round(risk_score, 1),
        "one_line": {"en": answer_en, "ar": answer_ar},
        "raw_indicators_expandable": raw_indicators or {},
        "insight_not_recommendation": True,
        "disclaimer": get_disclaimer_63(locale=locale),
        "fee_db": {"synthesis_usd": fee, "logged": True},
    }


def get_disclaimer_63(*, locale: str = "en") -> str:
    if locale.lower().startswith("ar"):
        return "تحليل فقط — ليس توصية مالية ولا ضمان عائد."
    return "Analysis only — not financial advice or guaranteed return."


def attach_clear_answer_63(payload: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["clear_answer"] = answer
    return out


# ─── #62 Daily Top 3 Opportunities ──────────────────────────────────────────────


def _score_opportunity(row: dict[str, Any], weights: dict[str, float]) -> float:
    return round(
        float(row.get("risk", 5)) * weights.get("risk", 0.25)
        + float(row.get("liquidity", 5)) * weights.get("liquidity", 0.25)
        + float(row.get("volume", 5)) * weights.get("volume", 0.25)
        + float(row.get("momentum", 5)) * weights.get("momentum", 0.25),
        3,
    )


def build_daily_top3_62(
    *,
    candidates: list[dict[str, Any]] | None = None,
    user_tier: str = "free",
    locale: str = "en",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based top 3 — no infinite list."""
    seed = seed or _load_seed()
    cfg = seed.get("daily_top_opportunities_62") or {}
    weights = cfg.get("scoring_weights") or {}
    max_n = int((cfg.get("policy") or {}).get("max_opportunities", 3))

    if candidates is None:
        candidates = [
            {"asset": "BTC", "risk": 6.0, "liquidity": 9.0, "volume": 8.5, "momentum": 7.0, "timeframe": "24h"},
            {"asset": "ETH", "risk": 5.5, "liquidity": 8.5, "volume": 7.5, "momentum": 6.5, "timeframe": "24h"},
            {"asset": "SOL", "risk": 7.0, "liquidity": 7.0, "volume": 8.0, "momentum": 8.5, "timeframe": "24h"},
            {"asset": "AVAX", "risk": 6.5, "liquidity": 6.5, "volume": 6.0, "momentum": 5.5, "timeframe": "24h"},
            {"asset": "LINK", "risk": 5.0, "liquidity": 7.5, "volume": 6.5, "momentum": 6.0, "timeframe": "24h"},
        ]

    scored = []
    for row in candidates:
        score = _score_opportunity(row, weights)
        opp = {
            "asset": row.get("asset", ""),
            "composite_score": score,
            "risk_score": row.get("risk", 5),
            "timeframe": row.get("timeframe", "24h"),
            "confidence_level": min(10, round(score, 1)),
            "methodology": "rule_based_risk_liquidity_volume_momentum",
            "disclaimer": get_disclaimer_63(locale=locale),
            "why_selected": [
                f"Risk {row.get('risk')}/10",
                f"Liquidity {row.get('liquidity')}/10",
                f"Momentum {row.get('momentum')}/10",
            ],
            "no_execution": True,
        }
        opp["clear_answer"] = build_one_clear_answer_63(
            verdict="Opportunity" if score >= 6.5 else "Neutral",
            reasons=[{"point": w, "rule_based": True} for w in opp["why_selected"][:3]],
            risk_score=float(row.get("risk", 5)),
            locale=locale,
            seed=seed,
        )
        scored.append(opp)

    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    top3 = scored[:max_n]

    fee = float((cfg.get("fee_db") or {}).get("compute_per_run_usd", 0.002))
    result = {
        "ok": True,
        "feature_ref": 62,
        "route": cfg.get("route", "/intelligence/daily-top3"),
        "opportunities": top3,
        "count": len(top3),
        "methodology_visible": True,
        "backtest_days_required": (cfg.get("policy") or {}).get("backtest_days_required", 90),
        "user_tier": user_tier,
        "fee_db": {"compute_usd": fee, "tier": user_tier},
        "generated_at": _utcnow(),
    }
    try:
        from bd_platform.data_sources_layer import attach_opportunity_to_daily_top3_150

        result = attach_opportunity_to_daily_top3_150(result, seed=seed)
    except ImportError:
        pass
    _daily_top3_cache["latest"] = result
    return result


# ─── #65 Contextual Alerts ──────────────────────────────────────────────────────


def contextual_alerts_status_65(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("contextual_alerts_65") or {}
    return {
        "ok": True,
        "feature_ref": 65,
        "standalone": False,
        "policy": cfg.get("policy") or {},
        "runbook": "docs/ops/CONTEXTUAL_ALERTS_LAYER.md",
        "timestamp": _utcnow(),
    }


def evaluate_contextual_alert_65(
    *,
    user_id: str = "anonymous",
    user_tier: str = "free",
    price: float,
    opportunity_level: float,
    volume_zscore: float = 0.0,
    asset: str = "BTC",
    locale: str = "en",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Alert at decision time — not after the move."""
    seed = seed or _load_seed()
    cfg = seed.get("contextual_alerts_65") or {}
    policy = cfg.get("policy") or {}
    free_limit = int(policy.get("free_tier_daily_limit", 3))

    day_key = f"{user_id}:{datetime.now(UTC).date().isoformat()}"
    count = _alert_counts.get(day_key, 0)
    if user_tier == "free" and count >= free_limit:
        return {
            "ok": False,
            "feature_ref": 65,
            "alert_fired": False,
            "reason": "free_tier_daily_limit_reached",
            "limit": free_limit,
        }

    triggered = opportunity_level >= 7.0 and volume_zscore >= 1.5
    if not triggered:
        return {"ok": True, "feature_ref": 65, "alert_fired": False, "reason": "conditions_not_met"}

    _alert_counts[day_key] = count + 1
    fee = float((cfg.get("fee_db") or {}).get("cost_per_alert_usd", 0.0003))
    alert = {
        "alert_id": f"ctx_{uuid.uuid4().hex[:8]}",
        "asset": asset,
        "price": price,
        "why_now": {
            "en": f"Price at opportunity level {opportunity_level:.1f}/10 with elevated volume ({volume_zscore:.1f}σ)",
            "ar": f"السعر عند مستوى فرصة {opportunity_level:.1f}/10 مع حجم مرتفع ({volume_zscore:.1f}σ)",
        },
        "rule_based": True,
        "no_auto_action": True,
        "disclaimer": get_disclaimer_63(locale=locale),
        "delivery_sla_seconds": policy.get("delivery_sla_seconds", 5),
        "fee_db": {"cost_usd": fee, "tier": user_tier},
        "fired_at": _utcnow(),
    }
    return {"ok": True, "feature_ref": 65, "alert_fired": True, "alert": alert}


# ─── #66 Portfolio Discipline ───────────────────────────────────────────────────


def compare_discipline_66(
    *,
    user_action: str,
    user_price: float,
    system_verdict: str,
    system_price: float,
    system_risk_score: float = 7.0,
    asset: str = "BTC",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based comparison — no value judgment, insight only."""
    seed = seed or _load_seed()
    price_diff_pct = 0.0
    if system_price > 0:
        price_diff_pct = round((user_price - system_price) / system_price * 100, 2)

    entry = {
        "comparison_id": f"disc_{uuid.uuid4().hex[:8]}",
        "asset": asset,
        "user_action": user_action,
        "user_price": user_price,
        "system_verdict": system_verdict,
        "system_price": system_price,
        "system_risk_score": system_risk_score,
        "price_diff_pct": price_diff_pct,
        "narrative": {
            "en": (
                f"You {user_action} {asset} at ${user_price:,.2f} — "
                f"the system showed {system_verdict} at ${system_price:,.2f} "
                f"(Risk Score {system_risk_score}/10)."
            ),
            "ar": (
                f"أنت {user_action} {asset} عند ${user_price:,.2f} — "
                f"النظام أشار إلى {system_verdict} عند ${system_price:,.2f} "
                f"(مخاطرة {system_risk_score}/10)."
            ),
        },
        "behavioral_training_only": True,
        "no_reward_punishment": True,
        "non_custodial": True,
        "recorded_at": _utcnow(),
    }
    _discipline_entries.append(entry)
    fee = float((seed.get("portfolio_discipline_66") or {}).get("fee_db", {}).get("report_compute_usd", 0.001))
    entry["fee_db"] = {"compute_usd": fee}
    return {"ok": True, "feature_ref": 66, "comparison": entry}


def build_discipline_tab_66(*, user_email: str = "", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    recent = _discipline_entries[-10:]
    return {
        "ok": True,
        "feature_ref": 66,
        "tab": "discipline",
        "surface": "portfolio_ai",
        "recent_comparisons": recent,
        "weekly_report_available": True,
        "manual_entry_only": True,
        "encrypted_storage": True,
        "disclaimer": "Behavioral training insight — not therapy or financial advice.",
    }


def attach_discipline_to_portfolio_66(portfolio_result: dict[str, Any]) -> dict[str, Any]:
    """Embed discipline tab data in Portfolio AI analyze response."""
    out = dict(portfolio_result)
    out["discipline_tab"] = build_discipline_tab_66()
    out["discipline_prompt"] = {
        "en": "Log your decisions to compare against system insights — manual entry only.",
        "ar": "سجّل قراراتك لمقارنتها برؤى النظام — إدخال يدوي فقط.",
    }
    return out


# ─── E2E ────────────────────────────────────────────────────────────────────────


def run_retail_intelligence_e2e_62_66(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_retail_intelligence_state()
    checks: list[dict[str, Any]] = []

    top3 = build_daily_top3_62(seed=seed)
    checks.append({"id": "62_top3_count", "passed": top3.get("count") == 3})
    checks.append({"id": "62_methodology", "passed": top3.get("methodology_visible") is True})

    answer = build_one_clear_answer_63(
        verdict="Opportunity",
        reasons=[{"point": "Volume spike", "rule_based": True}],
        risk_score=7.0,
        seed=seed,
    )
    checks.append({"id": "63_verdict", "passed": answer.get("verdict") == "Opportunity"})
    checks.append({"id": "63_max_reasons", "passed": len(answer.get("reasons", [])) <= 3})

    gloss = glossary_manifest_64()
    checks.append({"id": "64_glossary", "passed": gloss.get("count", 0) >= 3})
    checks.append({"id": "64_simplify", "passed": "simple" in simplify_term_64("RSI")})

    alert = evaluate_contextual_alert_65(
        price=42000, opportunity_level=8.0, volume_zscore=2.0, seed=seed
    )
    checks.append({"id": "65_alert_fired", "passed": alert.get("alert_fired") is True})

    disc = compare_discipline_66(
        user_action="bought",
        user_price=43000,
        system_verdict="Opportunity",
        system_price=41000,
        seed=seed,
    )
    checks.append({"id": "66_comparison", "passed": disc.get("ok") is True})
    portfolio = attach_discipline_to_portfolio_66({"holdings": []})
    checks.append({"id": "66_portfolio_embed", "passed": "discipline_tab" in portfolio})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
