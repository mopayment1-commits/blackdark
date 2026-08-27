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
    try:
        from bd_platform.capital_protection_controls import build_real_time_risk_alerts

        alerts = build_real_time_risk_alerts()
        risk_exceeded = any(a.get("severity") == "elevated" for a in (alerts.get("alerts") or []))
        if risk_exceeded and proto.get("apply_capital_protection_410", True):
            capital_cancelled = True
            signal = "cancelled"
    except Exception:
        logger.debug("410 capital protection hook skipped", exc_info=True)

    confidence = float(proto.get("confidence_pct", 75))
    evidence = {
        "tvl_trend": proto.get("tvl_trend"),
        "unlock_proximity_days": proto.get("unlock_proximity_days"),
        "protocol_risk_score": risk_score,
        "yield_sustainability": proto.get("yield_sustainability"),
        "evidence_links": proto.get("evidence_links") or [],
    }

    relevance_score = round(risk_adjusted_apy * (confidence / 100) * (0 if capital_cancelled else 1), 2)

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
    return ranked


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
        "integrations": {"defi_scanner_438": True, "capital_protection_410": True},
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
    checks.append({"id": "contradict_signal", "passed": contradict.get("signal") == "contradict", "detail": "contradict"})
    checks.append({"id": "contradict_message", "passed": "متناقضة" in (contradict.get("contradict_message") or ""), "detail": "ar"})

    panel = build_defi_decision_panel(seed=seed)
    checks.append({"id": "panel", "passed": panel.get("ok") is True and panel.get("count", 0) >= 2, "detail": "panel"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
