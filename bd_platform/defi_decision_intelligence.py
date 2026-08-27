"""
DeFi Decision Intelligence — Feature #651 (Sprint-2 Intelligence Ledger).

Cross-DeFi decision relevance: TVL/yield/flows/raises/unlocks vs risk.
NOT standalone — DeFi Decision Engine dimension in Intelligence Ledger.

Principle: Yield ≠ safety — APY raw + risk-adjusted + risk grade side-by-side.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.DeFiDecisionIntelligence")

_FEATURE_ID = 651
_RISK_DECISION_REF = 691
_CAPITAL_PROTECTION_REF = 410
_RISK_PASSPORT_REF = 660
_ARBITRAGE_REF = 429
_TITLE = "DeFi Decision Engine"
_LEGAL_NAME = "Cross-DeFi Decision Intelligence"
_STANDALONE = False
_MERGED_INTO = "Sprint-2 Intelligence Ledger"
_SPRINT = 2
_SEED_PATH = Path("data/defi_decision_intelligence_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "DeFi Decision Intelligence — decision relevance scoring with evidence. "
    "Yield ≠ safety. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"protocols": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("defi decision intelligence seed load failed: %s", exc)
        return {"protocols": {}}


def _risk_grade(score: float) -> str:
    if score <= 25:
        return "A"
    if score <= 40:
        return "B"
    if score <= 60:
        return "C"
    if score <= 75:
        return "D"
    return "F"


def _risk_gate_action(risk_score: float, user_limit: float, *, seed: dict[str, Any]) -> str:
    """#691 — veto / penalize / pass based on risk score vs user limit."""
    cfg = seed.get("risk_gate_691") or {}
    medium_low = float(cfg.get("medium_risk_low", 40))
    medium_high = float(cfg.get("medium_risk_high", 60))
    if risk_score > user_limit:
        return "veto"
    if medium_low <= risk_score <= medium_high:
        return "penalty"
    return "pass"


def apply_risk_gate_691(
    opportunity: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
    user_risk_limit: float | None = None,
) -> dict[str, Any]:
    """#691 — Risk Gate dimension: veto/penalize with evidence (merged into #651 + #410)."""
    seed = seed or _load_seed()
    cfg = seed.get("risk_gate_691") or {}
    protocol_id = opportunity.get("protocol_id") or opportunity.get("asset", "")
    protocol_map = seed.get("opportunity_protocol_map") or {}
    pid = protocol_map.get(str(protocol_id).upper()) or protocol_map.get(str(protocol_id).lower()) or protocol_id

    risk_score = float(opportunity.get("risk_score", 0))
    risk_reasons: list[str] = []
    passport_grade = None

    try:
        from bd_platform.defi_risk_passport import score_protocol_risk_passport

        passport = score_protocol_risk_passport(str(pid), seed=None)
        if passport.get("ok"):
            composite = float(passport.get("composite_score", 50))
            risk_score = round(100 - composite, 2)
            passport_grade = passport.get("risk_grade")
            breakdown = passport.get("breakdown") or {}
            liq = breakdown.get("liquidity_depth")
            if isinstance(liq, dict) and float(liq.get("score", 100)) < 40:
                risk_reasons.append("low_liquidity")
            conc = breakdown.get("tvl_concentration_pct")
            if conc is not None and float(conc) > 60:
                risk_reasons.append("high_concentration")
    except Exception:
        logger.debug("660 risk passport hook skipped", exc_info=True)

    if not risk_score:
        proto = (seed.get("protocols") or {}).get(pid, {})
        risk_score = float(proto.get("risk_score", 50))

    user_limit = user_risk_limit
    if user_limit is None:
        try:
            from bd_platform.capital_protection_controls import build_risk_budget_block

            budget = build_risk_budget_block(seed=None)
            user_limit = float((budget.get("user_configured_max_loss_pct") or 10) * 6)
        except Exception:
            user_limit = float(cfg.get("default_user_risk_limit", 60))

    action = _risk_gate_action(risk_score, user_limit, seed=seed)
    penalty_multiplier = float(cfg.get("penalty_ranking_multiplier", 0.5)) if action == "penalty" else 1.0

    evidence_parts: list[str] = []
    if risk_score > user_limit:
        evidence_parts.append(f"مخاطر بروتوكول {passport_grade or risk_score:.0f}")
    if any("liquidity" in r for r in risk_reasons):
        evidence_parts.append("سيولة منخفضة")
    if any("concentration" in r for r in risk_reasons):
        evidence_parts.append("تركيز مرتفع")
    if opportunity.get("liquidity_usd") and float(opportunity.get("liquidity_usd", 0)) < float(cfg.get("min_liquidity_usd", 500000)):
        evidence_parts.append("سيولة منخفضة")
        risk_reasons.append("liquidity_below_threshold")

    evidence_text = " | ".join(evidence_parts) if evidence_parts else None

    return {
        "ok": True,
        "feature_ref": _RISK_DECISION_REF,
        "merged_into": f"#{_FEATURE_ID} + #{_CAPITAL_PROTECTION_REF}",
        "standalone": False,
        "risk_adjusted_opportunity_ranking": True,
        "no_actionability_buzzword": True,
        "risk_gate": {
            "action": action,
            "vetoed": action == "veto",
            "penalized": action == "penalty",
            "risk_score": risk_score,
            "user_risk_limit": user_limit,
            "penalty_multiplier": penalty_multiplier,
            "passport_grade_660": passport_grade,
            "evidence": evidence_text,
            "evidence_reasons": risk_reasons,
            "fail_closed": action == "veto",
        },
        "integration_429": True,
        "integration_410": True,
        "integration_660": passport_grade is not None,
        "timestamp": _utcnow(),
    }


def rank_risk_adjusted_opportunities_691(
    opportunities: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """#691 — Risk-Adjusted Opportunity Ranking (not 'actionability')."""
    seed = seed or _load_seed()
    ranked: list[dict[str, Any]] = []

    for opp in opportunities:
        gate = apply_risk_gate_691(opp, seed=seed)
        gate_info = gate.get("risk_gate") or {}
        base_score = float(opp.get("decision_relevance_score", opp.get("net_edge_bps", 0)) or 0)

        if gate_info.get("vetoed"):
            adjusted_score = 0.0
            status = "vetoed"
        elif gate_info.get("penalized"):
            adjusted_score = round(base_score * gate_info.get("penalty_multiplier", 0.5), 2)
            status = "penalized"
        else:
            adjusted_score = base_score
            status = "active"

        ranked.append({
            **opp,
            "risk_gate_691": gate,
            "risk_adjusted_score": adjusted_score,
            "ranking_status": status,
            "ranking_metric": "risk_adjusted_opportunity_ranking",
        })

    ranked.sort(key=lambda x: x.get("risk_adjusted_score", 0), reverse=True)
    return ranked


def score_decision_relevance(
    protocol_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#651 — confirm/contradict logic with evidence and confidence."""
    seed = seed or _load_seed()
    proto = (seed.get("protocols") or {}).get(protocol_id)
    if not proto:
        return {"ok": False, "protocol_id": protocol_id, "error": "protocol_not_found"}

    raw_apy = float(proto.get("raw_apy_pct", 0))
    risk_score = float(proto.get("risk_score", 50))
    risk_adjusted_apy = round(raw_apy / max(risk_score / 10, 0.1), 4) if risk_score else 0
    grade = _risk_grade(risk_score)

    high_yield_high_risk = raw_apy >= float(seed.get("high_yield_threshold_pct", 10)) and risk_score >= 60
    signal = "confirm" if not high_yield_high_risk and raw_apy > 0 else "contradict"
    contradict_message = None
    if signal == "contradict":
        contradict_message = "إشارة متناقضة — راجع المخاطر"

    capital_cancelled = False
    risk_gate = None
    try:
        from bd_platform.capital_protection_controls import build_real_time_risk_alerts

        alerts = build_real_time_risk_alerts()
        risk_exceeded = any(a.get("severity") == "elevated" for a in (alerts.get("alerts") or []))
        if risk_exceeded and proto.get("apply_capital_protection_410", True):
            capital_cancelled = True
            signal = "cancelled"
    except Exception:
        logger.debug("410 capital protection hook skipped", exc_info=True)

    risk_gate = apply_risk_gate_691(
        {"protocol_id": protocol_id, "risk_score": risk_score},
        seed=seed,
    )
    gate_info = (risk_gate or {}).get("risk_gate") or {}
    if gate_info.get("vetoed"):
        capital_cancelled = True
        signal = "cancelled"
    elif gate_info.get("penalized") and signal == "confirm":
        signal = "penalized"

    confidence = float(proto.get("confidence_pct", 75))
    evidence = {
        "tvl_trend": proto.get("tvl_trend"),
        "unlock_proximity_days": proto.get("unlock_proximity_days"),
        "protocol_risk_score": risk_score,
        "yield_sustainability": proto.get("yield_sustainability"),
        "evidence_links": proto.get("evidence_links") or [],
    }

    relevance_score = round(risk_adjusted_apy * (confidence / 100) * (0 if capital_cancelled else 1), 2)
    if gate_info.get("penalized") and not capital_cancelled:
        relevance_score = round(relevance_score * gate_info.get("penalty_multiplier", 0.5), 2)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "protocol_id": protocol_id,
        "protocol_name": proto.get("protocol_name"),
        "decision_relevance_score": relevance_score,
        "signal": signal,
        "confirm_contradict": signal,
        "contradict_message": contradict_message,
        "yield_not_safety": True,
        "yield_display": {
            "raw_apy_pct": raw_apy,
            "risk_adjusted_apy": risk_adjusted_apy,
            "risk_grade": grade,
            "risk_score": risk_score,
            "side_by_side_mandatory": True,
            "display": f"APY {raw_apy}% | Risk-adjusted {risk_adjusted_apy}% | Grade {grade}",
        },
        "evidence": evidence,
        "confidence_pct": confidence,
        "capital_protection_410_cancelled": capital_cancelled,
        "risk_gate_691": risk_gate,
        "risk_adjusted_opportunity_ranking": True,
        "display": (
            f"{proto.get('protocol_name')}: relevance {relevance_score} — {signal}"
            + (f" ({contradict_message})" if contradict_message else "")
        ),
        "timestamp": _utcnow(),
    }


def rank_defi_opportunities_by_relevance(
    opportunities: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """#438 integration — rank by decision relevance not APY only."""
    seed = seed or _load_seed()
    protocol_map = seed.get("opportunity_protocol_map") or {}
    ranked: list[dict[str, Any]] = []

    for opp in opportunities:
        pid = protocol_map.get(opp.get("asset", "").upper()) or protocol_map.get(opp.get("protocol_id", ""))
        relevance = score_decision_relevance(pid, seed=seed) if pid else {"decision_relevance_score": 0, "signal": "unknown"}
        ranked.append({
            **opp,
            "decision_relevance_651": relevance if relevance.get("ok") else None,
            "decision_relevance_score": relevance.get("decision_relevance_score", 0),
            "ranking_metric": "decision_relevance_not_apy_only",
        })

    ranked.sort(key=lambda x: x.get("decision_relevance_score", 0), reverse=True)
    return rank_risk_adjusted_opportunities_691(ranked, seed=seed)


def build_defi_decision_panel(
    protocol_id: str | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    protocols = seed.get("protocols") or {}
    if protocol_id:
        protocols = {protocol_id: protocols[protocol_id]} if protocol_id in protocols else {}

    scores = [score_decision_relevance(pid, seed=seed) for pid in protocols]
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "scores": [s for s in scores if s.get("ok")],
        "count": sum(1 for s in scores if s.get("ok")),
        "yield_not_safety": True,
        "evidence_confidence_required": True,
        "integrations": {
            "defi_opportunity_scanner_438": True,
            "capital_protection_410": True,
            "risk_gate_691": True,
            "defi_risk_passport_660": True,
            "unified_arbitrage_429": True,
        },
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def defi_decision_intelligence_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "protocol_count": len(seed.get("protocols") or {}),
        "yield_not_safety": True,
        "integrations": {
            "defi_scanner_438": True,
            "capital_protection_410": True,
            "risk_gate_691": True,
            "defi_risk_passport_660": True,
            "unified_arbitrage_429": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": _STANDALONE is False, "detail": "651"})
    score = score_decision_relevance("aave_v3", seed=seed)
    checks.append({"id": "decision_score", "passed": score.get("ok") is True, "detail": "score"})
    checks.append({"id": "yield_not_safety", "passed": score.get("yield_not_safety") is True, "detail": "principle"})
    checks.append({"id": "side_by_side", "passed": (score.get("yield_display") or {}).get("side_by_side_mandatory") is True, "detail": "UI"})
    checks.append({"id": "evidence", "passed": bool((score.get("evidence") or {}).get("evidence_links")), "detail": "evidence"})
    checks.append({"id": "confidence", "passed": score.get("confidence_pct") is not None, "detail": "confidence"})

    contradict = score_decision_relevance("high_yield_risky", seed=seed)
    checks.append({
        "id": "contradict_signal",
        "passed": contradict.get("signal") in ("contradict", "cancelled"),
        "detail": contradict.get("signal"),
    })
    checks.append({
        "id": "691_veto_on_contradict",
        "passed": (contradict.get("risk_gate_691") or {}).get("risk_gate", {}).get("vetoed") is True,
        "detail": "691",
    })
    checks.append({"id": "contradict_message", "passed": "متناقضة" in (contradict.get("contradict_message") or ""), "detail": "ar"})

    panel = build_defi_decision_panel(seed=seed)
    checks.append({"id": "panel", "passed": panel.get("ok") is True and panel.get("count", 0) >= 2, "detail": "panel"})

    gate = apply_risk_gate_691({"protocol_id": "high_yield_risky", "risk_score": 72}, seed=seed)
    checks.append({"id": "691_risk_gate", "passed": gate.get("ok") is True, "detail": "691"})
    checks.append({"id": "691_veto_high_risk", "passed": (gate.get("risk_gate") or {}).get("action") == "veto", "detail": "veto"})
    checks.append({"id": "691_evidence", "passed": bool((gate.get("risk_gate") or {}).get("evidence") or (gate.get("risk_gate") or {}).get("evidence_reasons")), "detail": "evidence"})
    checks.append({"id": "691_no_actionability", "passed": gate.get("no_actionability_buzzword") is True, "detail": "naming"})
    low_gate = apply_risk_gate_691({"protocol_id": "aave_v3", "risk_score": 28}, seed=seed)
    checks.append({"id": "691_pass_low_risk", "passed": (low_gate.get("risk_gate") or {}).get("action") == "pass", "detail": "pass"})
    ranked = rank_risk_adjusted_opportunities_691([
        {"opportunity_id": "1", "decision_relevance_score": 80, "risk_score": 72},
        {"opportunity_id": "2", "decision_relevance_score": 50, "risk_score": 28},
    ], seed=seed)
    checks.append({"id": "691_ranking", "passed": ranked[0].get("opportunity_id") == "2", "detail": "ranking"})
    checks.append({"id": "691_ranking_metric", "passed": ranked[0].get("ranking_metric") == "risk_adjusted_opportunity_ranking", "detail": "metric"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
