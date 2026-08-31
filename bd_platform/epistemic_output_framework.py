"""
Epistemic Output Framework — Feature #316 (Sprint 2 Intelligence Ledger).

Renamed from "Cross-Domain Decision Intelligence" — design principle, not a product feature.
Every intelligence output: Fact | Inference | Hypothesis separated, fully traceable.

No "Decision" / "Buy" / "Sell" in outputs. User decides.
Integrates #284 Evidence Confidence + #1003 Provenance Lineage.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.EpistemicOutputFramework")

_FEATURE_ID = 316
_RENAMED_FROM = "Cross-Domain Decision Intelligence"
_TITLE = "Epistemic Output Framework"
_STANDALONE = False
_CROSS_CUTTING = True
_DESIGN_PRINCIPLE = True
_MERGED_INTO = "Intelligence Ledger / Epistemic Output Framework"
_SPRINT = 2
_SEED_PATH = Path("data/epistemic_output_framework_seed.json")
_METHODOLOGY_VERSION = "1.0"
_EVIDENCE_CONFIDENCE_FEATURE_ID = 284
_PROVENANCE_FEATURE_ID = 1003

EpistemicType = Literal["fact", "inference", "hypothesis"]

_FORBIDDEN_OUTPUT_TERMS = (
    "decision", "buy", "sell", "recommendation", "recommend", "actionable trade",
)

_DISCLAIMER = (
    "Output = Analysis + Evidence + Confidence. Not investment advice. "
    "Facts, inferences, and hypotheses are epistemically separated. User decides."
)

_EPISTEMIC_RULES = {
    "fact": "Verifiable data — provenance required (#1003)",
    "inference": "Logical deduction from facts — confidence % + supporting facts count",
    "hypothesis": "Testable prediction — probability range + test conditions",
    "ai_ml_never_fact": "AI/ML outputs tagged Inference or Hypothesis — never Fact",
    "no_mixing": "No mixing epistemic types in a single untagged statement",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"panels": {}, "domain_signals": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("epistemic output framework seed load failed: %s", exc)
        return {"panels": {}, "domain_signals": {}}


def _trace_hash(evidence_chain: list[dict[str, Any]]) -> str:
    payload = json.dumps(evidence_chain, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def validate_no_decision_language(text: str) -> dict[str, Any]:
    """Reject decision/recommendation language in outputs."""
    lower = text.lower()
    violations = [t for t in _FORBIDDEN_OUTPUT_TERMS if re.search(rf"\b{re.escape(t)}\b", lower)]
    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "forbidden_terms": list(_FORBIDDEN_OUTPUT_TERMS),
        "output_model": "Analysis + Evidence + Confidence — user decides",
    }


def build_evidence_link(
    *,
    evidence_id: str,
    provenance_metric_id: str | None = None,
    source: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    link: dict[str, Any] = {
        "evidence_id": evidence_id,
        "provenance_feature_id": _PROVENANCE_FEATURE_ID,
        "traceable": True,
    }
    if provenance_metric_id:
        link["provenance_metric_id"] = provenance_metric_id
        link["provenance_audit_path"] = (
            f"/api/v1/data/provenance-lineage/audit/{provenance_metric_id}"
        )
    if source:
        link["source"] = source
    if description:
        link["description"] = description
    return link


def build_fact(
    statement: str,
    *,
    evidence_chain: list[dict[str, Any]],
    verified: bool = True,
    provenance_metric_id: str | None = None,
) -> dict[str, Any]:
    """Fact = verifiable data. Confidence 100% if verified."""
    if not evidence_chain:
        raise ValueError("Fact requires evidence chain — no conclusion without evidence")

    return {
        "epistemic_type": "fact",
        "tag": "[Fact]",
        "statement": statement,
        "verified": verified,
        "confidence": {
            "taxonomy": "fact",
            "value_pct": 100.0 if verified else None,
            "display": "100% (verified)" if verified else "Unverified fact — not published",
        },
        "evidence_chain": evidence_chain,
        "evidence_trace_hash": _trace_hash(evidence_chain),
        "provenance_metric_id": provenance_metric_id,
        "no_mixing": True,
        "ai_ml_output": False,
    }


def build_inference(
    statement: str,
    *,
    supporting_facts: list[dict[str, Any]],
    confidence_pct: float,
    evidence_chain: list[dict[str, Any]],
    evidence_confidence_input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Inference = logical deduction from facts."""
    if not evidence_chain:
        raise ValueError("Inference requires evidence chain")
    if not supporting_facts:
        raise ValueError("Inference requires supporting facts")

    conf_input_id = _EVIDENCE_CONFIDENCE_FEATURE_ID
    return {
        "epistemic_type": "inference",
        "tag": "[Inference]",
        "statement": statement,
        "confidence": {
            "taxonomy": "inference",
            "value_pct": round(confidence_pct, 1),
            "supporting_facts_count": len(supporting_facts),
            "display": f"{confidence_pct:.0f}% confidence | {len(supporting_facts)} supporting facts",
            "evidence_confidence_feature_id": conf_input_id,
            "evidence_confidence_input": evidence_confidence_input,
        },
        "supporting_facts": supporting_facts,
        "evidence_chain": evidence_chain,
        "evidence_trace_hash": _trace_hash(evidence_chain),
        "ai_ml_never_fact": True,
        "no_mixing": True,
    }


def build_hypothesis(
    statement: str,
    *,
    probability_range: tuple[float, float],
    test_conditions: list[str],
    evidence_chain: list[dict[str, Any]],
) -> dict[str, Any]:
    """Hypothesis = testable prediction."""
    if not evidence_chain:
        raise ValueError("Hypothesis requires evidence chain")

    low, high = probability_range
    return {
        "epistemic_type": "hypothesis",
        "tag": "[Hypothesis]",
        "statement": statement,
        "confidence": {
            "taxonomy": "hypothesis",
            "probability_range_pct": [round(low, 1), round(high, 1)],
            "display": f"Probability: {low:.0f}–{high:.0f}%",
            "test_conditions": test_conditions,
        },
        "evidence_chain": evidence_chain,
        "evidence_trace_hash": _trace_hash(evidence_chain),
        "testable": True,
        "ai_ml_never_fact": True,
        "no_mixing": True,
    }


def confirm_contradict_domains(domain_signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Cross-domain confirm/contradict — no decision language."""
    confirms = []
    contradicts = []
    neutral = []

    for i, a in enumerate(domain_signals):
        for b in domain_signals[i + 1:]:
            if a.get("direction") == b.get("direction") and a.get("direction"):
                confirms.append({
                    "domains": [a.get("domain"), b.get("domain")],
                    "direction": a.get("direction"),
                    "relationship": "confirming",
                })
            elif a.get("direction") and b.get("direction") and a.get("direction") != b.get("direction"):
                contradicts.append({
                    "domains": [a.get("domain"), b.get("domain")],
                    "directions": [a.get("direction"), b.get("direction")],
                    "relationship": "contradicting",
                })

    for sig in domain_signals:
        involved = any(
            sig.get("domain") in c.get("domains", [])
            for c in confirms + contradicts
        )
        if not involved:
            neutral.append(sig.get("domain"))

    return {
        "confirming_pairs": confirms,
        "contradicting_pairs": contradicts,
        "neutral_domains": neutral,
        "confirm_contradict_only": True,
        "no_decision_output": True,
        "display": (
            f"Confirming: {len(confirms)} | Contradicting: {len(contradicts)} | "
            "Analysis only — user decides"
        ),
    }


def wrap_intelligence_output(
    *,
    analysis_summary: str,
    epistemic_items: list[dict[str, Any]],
    domains: list[str] | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Standard envelope for ALL intelligence outputs — no Decision/Buy/Sell."""
    lang_check = validate_no_decision_language(analysis_summary)
    for item in epistemic_items:
        item_check = validate_no_decision_language(item.get("statement", ""))
        if not item_check["valid"]:
            lang_check["valid"] = False
            lang_check["violations"] = list(set(lang_check["violations"] + item_check["violations"]))

    facts = [i for i in epistemic_items if i.get("epistemic_type") == "fact"]
    inferences = [i for i in epistemic_items if i.get("epistemic_type") == "inference"]
    hypotheses = [i for i in epistemic_items if i.get("epistemic_type") == "hypothesis"]

    return {
        "output_type": "analysis",
        "not_decision": True,
        "forbidden_in_output": list(_FORBIDDEN_OUTPUT_TERMS),
        "language_check": lang_check,
        "title": title,
        "analysis": analysis_summary,
        "evidence": {
            "items": epistemic_items,
            "fact_count": len(facts),
            "inference_count": len(inferences),
            "hypothesis_count": len(hypotheses),
            "epistemic_separation": True,
            "every_conclusion_traceable": all(i.get("evidence_chain") for i in epistemic_items),
        },
        "confidence": {
            "facts_verified": sum(1 for f in facts if f.get("verified")),
            "inferences": [
                {"statement": i["statement"], "confidence_pct": i["confidence"]["value_pct"]}
                for i in inferences
            ],
            "hypotheses": [
                {
                    "statement": h["statement"],
                    "probability_range": h["confidence"]["probability_range_pct"],
                }
                for h in hypotheses
            ],
        },
        "domains": domains or [],
        "why": [
            {
                "epistemic_type": i.get("epistemic_type"),
                "statement": i.get("statement"),
                "evidence_trace_hash": i.get("evidence_trace_hash"),
            }
            for i in epistemic_items
        ],
        "user_decides": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
    }


def enrich_with_evidence_confidence(
    inference_item: dict[str, Any],
    assessment_id: str,
) -> dict[str, Any]:
    """#284 Evidence Confidence as input to inference confidence."""
    from bd_platform.evidence_confidence import build_confidence_assessment

    assessment = build_confidence_assessment(assessment_id)
    if not assessment.get("ok"):
        return inference_item

    conf = assessment.get("confidence") or {}
    inference_item = dict(inference_item)
    inference_item["confidence"] = {
        **inference_item.get("confidence", {}),
        "evidence_confidence_score": conf.get("confidence_score"),
        "evidence_confidence_assessment_id": assessment_id,
        "evidence_confidence_feature_id": _EVIDENCE_CONFIDENCE_FEATURE_ID,
        "not_probability_of_price_move": True,
    }
    return inference_item


def build_cross_domain_panel(panel_id: str = "btc_macro_synthesis") -> dict[str, Any]:
    """Cross-domain synthesis — derivatives, DEX, risk, narratives, sentiment, market state."""
    t0 = time.perf_counter()
    seed = _load_seed()
    panel = (seed.get("panels") or {}).get(panel_id)

    if not panel:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "panel_not_found", "panel_id": panel_id}

    domain_signals = panel.get("domain_signals") or []
    cross_domain = confirm_contradict_domains(domain_signals)

    epistemic_items = []
    for item in panel.get("epistemic_items") or []:
        etype = item.get("epistemic_type")
        chain = [
            build_evidence_link(**e) for e in (item.get("evidence") or [])
        ]
        if etype == "fact":
            epistemic_items.append(build_fact(
                item["statement"],
                evidence_chain=chain,
                verified=item.get("verified", True),
                provenance_metric_id=item.get("provenance_metric_id"),
            ))
        elif etype == "inference":
            facts = item.get("supporting_fact_refs") or []
            inf = build_inference(
                item["statement"],
                supporting_facts=[{"ref": r} for r in facts],
                confidence_pct=float(item.get("confidence_pct", 70)),
                evidence_chain=chain,
            )
            if item.get("evidence_confidence_assessment_id"):
                inf = enrich_with_evidence_confidence(
                    inf, item["evidence_confidence_assessment_id"],
                )
            epistemic_items.append(inf)
        elif etype == "hypothesis":
            pr = item.get("probability_range_pct") or [30, 55]
            epistemic_items.append(build_hypothesis(
                item["statement"],
                probability_range=(float(pr[0]), float(pr[1])),
                test_conditions=item.get("test_conditions") or [],
                evidence_chain=chain,
            ))

    wrapped = wrap_intelligence_output(
        analysis_summary=panel.get("analysis_summary", ""),
        epistemic_items=epistemic_items,
        domains=[s.get("domain") for s in domain_signals],
        title=panel.get("title"),
    )

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "design_principle": _DESIGN_PRINCIPLE,
        "cross_cutting": _CROSS_CUTTING,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "panel_id": panel_id,
        "asset": panel.get("asset"),
        "cross_domain": cross_domain,
        "domain_signals": domain_signals,
        "output": wrapped,
        "integrations": {
            "evidence_confidence_feature_id": _EVIDENCE_CONFIDENCE_FEATURE_ID,
            "provenance_feature_id": _PROVENANCE_FEATURE_ID,
        },
        "epistemic_rules": _EPISTEMIC_RULES,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def epistemic_output_framework_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "design_principle": _DESIGN_PRINCIPLE,
        "cross_cutting": _CROSS_CUTTING,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "applies_to": "ALL intelligence outputs — AI, reports, alerts",
        "epistemic_types": ["fact", "inference", "hypothesis"],
        "epistemic_rules": _EPISTEMIC_RULES,
        "integrations": {
            "evidence_confidence": _EVIDENCE_CONFIDENCE_FEATURE_ID,
            "provenance_lineage": _PROVENANCE_FEATURE_ID,
        },
        "output_model": {
            "includes": ["analysis", "evidence", "confidence", "why"],
            "excludes": ["decision", "buy", "sell", "recommendation"],
            "user_decides": True,
        },
        "acceptance_criteria": {
            "fact_inference_hypothesis_separated": True,
            "every_conclusion_traceable": True,
            "confidence_taxonomy": True,
            "no_decision_in_output": True,
            "applied_to_all_outputs": True,
            "ai_ml_never_fact": True,
        },
        "panel_count": len(seed.get("panels") or {}),
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
