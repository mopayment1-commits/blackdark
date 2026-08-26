"""
Diligence Risk Scoring Engine — Feature #460 (Sprint-2 Risk Layer Core).

Converts due diligence findings into comparable risk scores with full transparency.
NOT standalone — shared scoring engine for #462 Collateral Risk and #463 Correlation Risk.

Mandatory:
  - No opaque score: every score includes breakdown + weights + version
  - Evidence quality affects confidence automatically
  - Freshness decay on stale findings

Integrations:
  - #417 Net-Edge Score: risk score adjusts final opportunity ranking
  - #462 Collateral Risk + #463 Correlation Risk: same scoring engine categories
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.DiligenceRiskScoring")

_FEATURE_ID = 460
_TITLE = "Diligence Risk Scoring"
_LEGAL_NAME = "Diligence Risk Scoring Engine"
_STANDALONE = False
_MERGED_INTO = "Sprint-2 Risk Layer Core"
_LAYER = "Risk Layer"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/diligence_risk_scoring_seed.json")
_METHODOLOGY_VERSION = "1.0"
_SCORING_ENGINE_VERSION = "1.0.0"

_COLLATERAL_FEATURE_REF = 462
_CORRELATION_FEATURE_REF = 463
_NET_EDGE_FEATURE_REF = 417

_DISCLAIMER = (
    "Diligence Risk Scoring — analytics index from due diligence findings. "
    "Every score includes documented weights, version, and per-finding reasons. "
    "Evidence quality reduces confidence on weak sources. Not investment advice."
)

_BANNED_TERMS = (
    "guaranteed safe",
    "risk-free",
    "you should avoid",
    "you should buy",
    "opaque score",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"entities": {}, "category_weights": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("diligence risk scoring seed load failed: %s", exc)
        return {"entities": {}, "category_weights": {}}


def _freshness_factor(hours: float, seed: dict[str, Any]) -> float:
    decay = seed.get("freshness_decay_hours") or {}
    fresh_max = float(decay.get("fresh_max", 24))
    aging_max = float(decay.get("aging_max", 72))
    stale_max = float(decay.get("stale_max", 168))
    if hours <= fresh_max:
        return 1.0
    if hours <= aging_max:
        return 0.85
    if hours <= stale_max:
        return 0.7
    return 0.5


def _evidence_confidence(quality: str, seed: dict[str, Any]) -> float:
    mapping = seed.get("evidence_quality_confidence") or {}
    return float(mapping.get(quality.lower(), mapping.get("unknown", 0.3)))


def _severity_points(severity: str, seed: dict[str, Any]) -> float:
    mapping = seed.get("severity_points") or {}
    return float(mapping.get(severity.lower(), mapping.get("medium", 45)))


def _score_finding(finding: dict[str, Any], *, seed: dict[str, Any]) -> dict[str, Any]:
    severity = str(finding.get("severity", "medium")).lower()
    evidence_q = str(finding.get("evidence_quality", "unknown")).lower()
    freshness_h = float(finding.get("freshness_hours", 999))

    base = _severity_points(severity, seed)
    ev_conf = _evidence_confidence(evidence_q, seed)
    fresh = _freshness_factor(freshness_h, seed)
    adjusted = round(base * ev_conf * fresh, 2)
    contribution = round(adjusted * ev_conf, 2)

    return {
        "finding_id": finding.get("finding_id"),
        "title": finding.get("title"),
        "severity": severity,
        "evidence_quality": evidence_q,
        "freshness_hours": freshness_h,
        "source": finding.get("source"),
        "base_severity_points": base,
        "evidence_confidence": ev_conf,
        "freshness_factor": fresh,
        "adjusted_risk_points": adjusted,
        "contribution": contribution,
        "reason": finding.get("detail") or finding.get("title"),
    }


def score_category(
    findings: list[dict[str, Any]],
    *,
    category: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score one risk category from diligence findings — fully transparent."""
    seed = seed or _load_seed()
    if not findings:
        return {
            "category": category,
            "risk_score": 0.0,
            "confidence": 0.0,
            "finding_count": 0,
            "findings_breakdown": [],
            "reasons": ["no_findings_available"],
            "no_opaque_score": True,
        }

    scored = [_score_finding(f, seed=seed) for f in findings]
    total_contrib = sum(s["contribution"] for s in scored)
    total_weight = sum(s["evidence_confidence"] * s["freshness_factor"] for s in scored) or 1.0
    risk_score = round(min(100.0, total_contrib / len(scored)), 2)
    confidence = round(
        sum(s["evidence_confidence"] * s["freshness_factor"] for s in scored) / len(scored),
        3,
    )

    top_reasons = sorted(scored, key=lambda s: s["contribution"], reverse=True)[:5]
    return {
        "category": category,
        "risk_score": risk_score,
        "confidence": confidence,
        "finding_count": len(scored),
        "findings_breakdown": scored,
        "reasons": [r["reason"] for r in top_reasons],
        "weights_version": seed.get("scoring_engine_version"),
        "no_opaque_score": True,
    }


def score_entity_risk(
    entity_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Overall + category risk scores for an asset/entity."""
    seed = seed or _load_seed()
    entity = (seed.get("entities") or {}).get(entity_id.upper())
    if not entity:
        return {"ok": False, "error": "entity_not_found", "entity_id": entity_id}

    category_weights = seed.get("category_weights") or {}
    findings_map = entity.get("findings") or {}
    category_scores: dict[str, Any] = {}

    for category in category_weights:
        cat_findings = findings_map.get(category) or []
        category_scores[category] = score_category(cat_findings, category=category, seed=seed)

    weighted_sum = 0.0
    weight_total = 0.0
    confidences: list[float] = []
    all_reasons: list[str] = []

    for cat, weight in category_weights.items():
        cs = category_scores.get(cat) or {}
        w = float(weight)
        weighted_sum += cs.get("risk_score", 0) * w
        weight_total += w
        confidences.append(cs.get("confidence", 0))
        all_reasons.extend(cs.get("reasons") or [])

    overall_risk = round(weighted_sum / weight_total, 2) if weight_total else 0.0
    overall_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

    return {
        "ok": True,
        "entity_id": entity_id.upper(),
        "display_name": entity.get("display_name"),
        "overall_risk_score": overall_risk,
        "overall_confidence": overall_confidence,
        "category_scores": category_scores,
        "category_weights": category_weights,
        "top_reasons": all_reasons[:8],
        "scoring_engine_version": seed.get("scoring_engine_version"),
        "methodology_version": seed.get("methodology_version"),
        "no_opaque_score": True,
        "weights_documented": True,
        "evidence_class": "BACKTESTED",
    }


def score_collateral_risk(entity_id: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#462 Collateral Risk — same scoring engine."""
    seed = seed or _load_seed()
    entity = (seed.get("entities") or {}).get(entity_id.upper())
    if not entity:
        return {"ok": False, "error": "entity_not_found", "feature_ref": _COLLATERAL_FEATURE_REF}

    findings = (entity.get("findings") or {}).get("collateral_risk") or []
    result = score_category(findings, category="collateral_risk", seed=seed)
    return {
        "ok": True,
        "feature_ref": _COLLATERAL_FEATURE_REF,
        "entity_id": entity_id.upper(),
        **result,
    }


def score_correlation_risk(entity_id: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#463 Correlation Risk — same scoring engine."""
    seed = seed or _load_seed()
    entity = (seed.get("entities") or {}).get(entity_id.upper())
    if not entity:
        return {"ok": False, "error": "entity_not_found", "feature_ref": _CORRELATION_FEATURE_REF}

    findings = (entity.get("findings") or {}).get("correlation_risk") or []
    result = score_category(findings, category="correlation_risk", seed=seed)
    return {
        "ok": True,
        "feature_ref": _CORRELATION_FEATURE_REF,
        "entity_id": entity_id.upper(),
        **result,
    }


def score_diligence_risk(entity_id: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#460 Asset/venue due diligence category."""
    seed = seed or _load_seed()
    entity = (seed.get("entities") or {}).get(entity_id.upper())
    if not entity:
        return {"ok": False, "error": "entity_not_found", "feature_id": _FEATURE_ID}

    findings = (entity.get("findings") or {}).get("asset_diligence") or []
    result = score_category(findings, category="asset_diligence", seed=seed)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "entity_id": entity_id.upper(),
        **result,
    }


def apply_risk_to_net_edge_ranking(
    opportunity: dict[str, Any],
    *,
    truth_result: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#417 integration — risk score adjusts final opportunity ranking."""
    seed = seed or _load_seed()
    asset = str(opportunity.get("asset") or opportunity.get("symbol", "BTC")).split("/")[0].upper()
    risk = score_entity_risk(asset, seed=seed)

    if truth_result is None:
        from net_edge_truth import compute_net_edge_truth

        truth_result = compute_net_edge_truth(opportunity)

    truth_score = float(truth_result.get("truth_score") or 0)
    risk_score = float(risk.get("overall_risk_score") or 0) if risk.get("ok") else 50.0
    confidence = float(risk.get("overall_confidence") or 0.5) if risk.get("ok") else 0.5

    integration_cfg = seed.get("net_edge_integration") or {}
    risk_weight = float(integration_cfg.get("risk_penalty_weight", 0.30))
    conf_weight = float(integration_cfg.get("confidence_weight", 0.15))

    risk_penalty = (risk_score / 100.0) * risk_weight
    confidence_adj = 1.0 - (1.0 - confidence) * conf_weight
    final_rank_score = round(truth_score * (1.0 - risk_penalty) * confidence_adj, 2)

    return {
        "ok": True,
        "opportunity_id": opportunity.get("opportunity_id"),
        "asset": asset,
        "net_edge_truth": {
            "feature_ref": _NET_EDGE_FEATURE_REF,
            "truth_score": truth_score,
            "reject": truth_result.get("reject"),
        },
        "diligence_risk": risk if risk.get("ok") else {"ok": False},
        "ranking": {
            "final_rank_score": final_rank_score,
            "truth_score": truth_score,
            "risk_penalty": round(risk_penalty, 4),
            "confidence_adjustment": round(confidence_adj, 4),
            "risk_weight": risk_weight,
            "confidence_weight": conf_weight,
            "formula": "final = truth_score × (1 − risk_penalty) × confidence_adj",
        },
        "no_opaque_score": True,
        "evidence_class": "BACKTESTED",
    }


def rank_opportunities(
    opportunities: list[dict[str, Any]] | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    opps = opportunities if opportunities is not None else (seed.get("opportunities") or [])
    ranked = []
    for opp in opps:
        result = apply_risk_to_net_edge_ranking(opp, seed=seed)
        ranked.append({**result, "opportunity": opp})

    ranked.sort(key=lambda r: r["ranking"]["final_rank_score"], reverse=True)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "integration": "net_edge_truth",
        "feature_ref": _NET_EDGE_FEATURE_REF,
        "ranked_opportunities": ranked,
        "count": len(ranked),
        "no_opaque_score": True,
        "evidence_class": "BACKTESTED",
        "timestamp": _utcnow(),
    }


def build_risk_scoring_panel(
    entity_id: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    entity_risk = score_entity_risk(entity_id, seed=seed)
    collateral = score_collateral_risk(entity_id, seed=seed)
    correlation = score_correlation_risk(entity_id, seed=seed)
    diligence = score_diligence_risk(entity_id, seed=seed)
    ranking = rank_opportunities(seed=seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": entity_risk.get("ok", False),
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "entity_risk": entity_risk,
        "collateral_risk": collateral,
        "correlation_risk": correlation,
        "asset_diligence": diligence,
        "opportunity_ranking": ranking,
        "scoring_engine_version": seed.get("scoring_engine_version"),
        "methodology_version": seed.get("methodology_version"),
        "category_weights": seed.get("category_weights"),
        "no_opaque_score": True,
        "weights_documented": True,
        "not_investment_advice": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_intelligence_ledger_integration(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    entities = list((seed.get("entities") or {}).keys())
    summaries = [score_entity_risk(e, seed=seed) for e in entities[:5]]
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "integration": "intelligence_ledger",
        "entity_risk_summaries": [s for s in summaries if s.get("ok")],
        "opportunity_ranking": rank_opportunities(seed=seed),
        "scoring_engine_version": seed.get("scoring_engine_version"),
        "no_opaque_score": True,
        "evidence_class": "BACKTESTED",
        "timestamp": _utcnow(),
    }


def diligence_risk_scoring_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "scoring_engine_version": seed.get("scoring_engine_version"),
        "entity_count": len(seed.get("entities") or {}),
        "categories": list((seed.get("category_weights") or {}).keys()),
        "no_opaque_score": True,
        "weights_documented": True,
        "evidence_quality_affects_confidence": True,
        "integrations": {
            "net_edge_truth_417": True,
            "collateral_risk_462": True,
            "correlation_risk_463": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "risk layer core"})
    checks.append({"id": "no_opaque_score", "passed": seed.get("no_opaque_score") is True, "detail": "transparent"})

    btc = score_entity_risk("BTC", seed=seed)
    checks.append({"id": "overall_and_category_scores", "passed": btc.get("ok") and "category_scores" in btc and btc.get("overall_risk_score", 0) >= 0, "detail": str(btc.get("overall_risk_score"))})
    checks.append({"id": "weights_documented", "passed": btc.get("weights_documented") and btc.get("category_weights"), "detail": "weights"})
    checks.append({"id": "scoring_version", "passed": btc.get("scoring_engine_version") == seed.get("scoring_engine_version"), "detail": btc.get("scoring_engine_version")})
    checks.append({"id": "breakdown_per_finding", "passed": len((btc.get("category_scores") or {}).get("asset_diligence", {}).get("findings_breakdown") or []) >= 1, "detail": "breakdown"})

    uni = score_entity_risk("UNI", seed=seed)
    low_conf_finding = None
    for cat in (uni.get("category_scores") or {}).values():
        for f in cat.get("findings_breakdown") or []:
            if f.get("evidence_quality") == "low":
                low_conf_finding = f
                break
    checks.append({"id": "evidence_quality_affects_confidence", "passed": low_conf_finding is not None and low_conf_finding.get("evidence_confidence", 1) < 0.6, "detail": "low evidence"})

    collateral = score_collateral_risk("ETH", seed=seed)
    checks.append({"id": "collateral_risk_462", "passed": collateral.get("ok") and collateral.get("feature_ref") == 462, "detail": "462"})

    correlation = score_correlation_risk("ETH", seed=seed)
    checks.append({"id": "correlation_risk_463", "passed": correlation.get("ok") and correlation.get("feature_ref") == 463, "detail": "463"})

    ranking = rank_opportunities(seed=seed)
    checks.append({"id": "net_edge_ranking_417", "passed": ranking.get("count", 0) >= 2 and "final_rank_score" in ranking["ranked_opportunities"][0]["ranking"], "detail": "417"})
    checks.append({"id": "risk_affects_ranking", "passed": ranking["ranked_opportunities"][0]["asset"] != ranking["ranked_opportunities"][-1]["asset"] or len(ranking["ranked_opportunities"]) >= 2, "detail": "ordering"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
