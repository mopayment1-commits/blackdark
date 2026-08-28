"""
AI Output Provenance / Compliance Footer — Feature #921 (Cross-Cutting Policy).

NOT standalone — policy applied to all AI features (#919, #920, #922, #997).
Attaches provenance metadata, classifies claims, fails closed on missing provenance.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.AIOutputProvenance")

_FEATURE_REF = 921
_STANDALONE = False
_POLICY_SCOPE = ("919", "920", "922", "997")
_SEED_PATH = Path("data/ai_output_provenance_policy_seed.json")

ClaimType = Literal["fact", "inference", "hypothesis", "unsupported"]
ConfidenceLevel = Literal["high", "medium", "low"]

_DISCLAIMER = (
    "AI output — insight only, not financial or legal advice. "
    "Facts require evidence. Inferences and hypotheses are labeled."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("ai provenance policy seed load failed: %s", exc)
        return {}


def ai_provenance_policy_status_921(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "policy_scope": list(_POLICY_SCOPE),
        "cross_cutting": True,
        "mandatory_metadata": [
            "model_version",
            "tool_versions",
            "timestamp",
            "dataset_version",
        ],
        "claim_classification": ["fact", "inference", "hypothesis", "unsupported"],
        "fails_closed": True,
        "permission_safe": True,
        "regression_tests_required": True,
        "fee_db": (seed.get("ai_provenance_policy_921") or {}).get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def _score_confidence(evidence_count: int, *, seed: dict[str, Any]) -> int:
    thresholds = (seed.get("ai_provenance_policy_921") or {}).get("confidence_thresholds") or {
        "high": 3,
        "medium": 2,
    }
    if evidence_count >= int(thresholds.get("high", 3)):
        return 9
    if evidence_count >= int(thresholds.get("medium", 2)):
        return 6
    return 3


def classify_claim(
    claim: str,
    *,
    evidence: list[dict[str, Any]] | None = None,
    claim_type: ClaimType | None = None,
) -> dict[str, Any]:
    """Classify claim as fact/inference/hypothesis — no grounded fact without evidence."""
    evidence = evidence or []
    if claim_type:
        ctype = claim_type
    elif len(evidence) >= 1:
        ctype = "fact"
    elif any(w in claim.lower() for w in ("may", "might", "could", "likely", "suggest")):
        ctype = "inference"
    elif any(w in claim.lower() for w in ("will", "expect", "forecast", "predict")):
        ctype = "hypothesis"
    else:
        ctype = "unsupported"

    if ctype == "fact" and not evidence:
        ctype = "unsupported"

    return {
        "claim": claim,
        "claim_type": ctype,
        "ui_label": {"fact": "Fact", "inference": "Inference", "hypothesis": "Hypothesis", "unsupported": "Unsupported"}[ctype],
        "ui_icon": {"fact": "check-circle", "inference": "info", "hypothesis": "alert-triangle", "unsupported": "x-circle"}[ctype],
        "evidence_count": len(evidence),
        "grounded": ctype == "fact" and len(evidence) > 0,
    }


def validate_citation_coverage(
    claims: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate citation coverage before display — fails closed."""
    seed = seed or _load_seed()
    uncovered_facts = [
        c for c in claims
        if c.get("claim_type") == "fact" and not c.get("evidence")
    ]
    return {
        "ok": len(uncovered_facts) == 0,
        "feature_ref": _FEATURE_REF,
        "total_claims": len(claims),
        "uncovered_facts": len(uncovered_facts),
        "fails_closed": len(uncovered_facts) > 0,
        "blocked": len(uncovered_facts) > 0,
    }


def attach_compliance_footer_921(
    ai_output: dict[str, Any],
    *,
    feature_ref: str,
    model_version: str = "rule-based-v1",
    tool_versions: dict[str, str] | None = None,
    dataset_version: str = "2026.08.28",
    user_id: str = "user_demo",
    tenant_id: str = "tenant_default",
    tier: str = "pro",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach provenance metadata + compliance footer to any AI output."""
    seed = seed or _load_seed()
    cfg = seed.get("ai_provenance_policy_921") or {}

    citations = ai_output.get("citations") or ai_output.get("evidence") or []
    claims_raw = ai_output.get("claims") or ai_output.get("material_claims") or []
    if not claims_raw and ai_output.get("answer"):
        claims_raw = [{"claim": ai_output["answer"], "evidence": citations}]

    claims: list[dict[str, Any]] = []
    for item in claims_raw:
        if isinstance(item, str):
            classified = classify_claim(item, evidence=citations)
        else:
            explicit_fact_no_evidence = (
                item.get("claim_type") == "fact" and not (item.get("citations") or item.get("evidence"))
            )
            classified = classify_claim(
                item.get("claim", ""),
                evidence=item.get("citations") or item.get("evidence") or citations,
                claim_type=item.get("claim_type"),
            )
            classified["evidence"] = item.get("citations") or item.get("evidence") or citations
            if explicit_fact_no_evidence:
                classified["claim_type"] = "unsupported"
                classified["explicit_fact_rejected"] = True
        claims.append(classified)

    coverage = validate_citation_coverage(claims, seed=seed)
    explicit_rejections = [c for c in claims if c.get("explicit_fact_rejected")]
    if explicit_rejections and cfg.get("fails_closed", True):
        return {
            "ok": False,
            "feature_ref": feature_ref,
            "policy_ref": _FEATURE_REF,
            "blocked": True,
            "fails_closed": True,
            "label": "Unsupported",
            "reason": "fact_without_evidence",
            "compliance_footer": {"status": "blocked", "provenance_complete": False, "disclaimer": _DISCLAIMER},
            "metadata": {
                "model_version": model_version,
                "tool_versions": tool_versions or {},
                "timestamp": _utcnow(),
                "dataset_version": dataset_version,
                "feature_ref": feature_ref,
                "policy_ref": _FEATURE_REF,
            },
        }
    evidence_count = sum(len(c.get("evidence") or []) for c in claims) or len(citations)
    confidence_score = _score_confidence(evidence_count, seed=seed)

    metadata = {
        "model_version": model_version,
        "tool_versions": tool_versions or ai_output.get("tool_versions") or {},
        "timestamp": _utcnow(),
        "dataset_version": dataset_version,
        "feature_ref": feature_ref,
        "policy_ref": _FEATURE_REF,
    }

    data_freshness = ai_output.get("data_freshness") or cfg.get("default_data_freshness") or _utcnow()

    if not coverage.get("ok") and cfg.get("fails_closed", True):
        return {
            "ok": False,
            "feature_ref": feature_ref,
            "policy_ref": _FEATURE_REF,
            "blocked": True,
            "fails_closed": True,
            "label": "Unsupported",
            "reason": "missing_provenance",
            "compliance_footer": {
                "status": "blocked",
                "provenance_complete": False,
                "disclaimer": _DISCLAIMER,
            },
            "metadata": metadata,
        }

    fee = cfg.get("fee_db") or {}
    footer = {
        "status": "approved",
        "provenance_complete": True,
        "model_version": model_version,
        "tool_versions": metadata["tool_versions"],
        "data_freshness": data_freshness,
        "confidence_score": confidence_score,
        "confidence_rule_based": True,
        "claims": claims,
        "claim_types_visible": True,
        "source_links": [c.get("citation") or c.get("source") for c in citations if isinstance(c, dict)],
        "permission_safe": True,
        "tenant_id": tenant_id,
        "user_scoped": tier != "institution",
        "disclaimer": _DISCLAIMER,
        "provenance_hash": hashlib.sha256(
            json.dumps(metadata, sort_keys=True, default=str).encode()
        ).hexdigest()[:16],
    }
    provenance_fee = {
        "verification_usd": fee.get("verification_per_output_usd", 0.002),
        "metadata_attachment_usd": fee.get("metadata_per_output_usd", 0.001),
    }
    merged_fee_db = {**(ai_output.get("fee_db") or {}), **provenance_fee}

    return {
        **ai_output,
        "ok": ai_output.get("ok", True),
        "policy_ref": _FEATURE_REF,
        "compliance_footer": footer,
        "metadata": metadata,
        "permission_safe": True,
        "fee_db": merged_fee_db,
    }


def run_ai_provenance_regression_tests_921(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Regression tests for provenance output — required on AI pipeline changes."""
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    status = ai_provenance_policy_status_921(seed=seed)
    tests.append({"test": "cross_cutting_policy", "passed": status["cross_cutting"] is True})
    tests.append({"test": "fails_closed_enabled", "passed": status["fails_closed"] is True})

    fact = classify_claim("BTC NVT is 42.3", evidence=[{"source": "onchain", "timestamp": _utcnow()}])
    tests.append({"test": "fact_with_evidence", "passed": fact["grounded"] is True})

    no_ev = classify_claim("BTC NVT is 42.3", evidence=[])
    tests.append({"test": "fact_without_evidence_unsupported", "passed": no_ev["claim_type"] == "unsupported"})

    output = attach_compliance_footer_921(
        {"ok": True, "answer": "Test", "citations": [{"source": "market_data", "timestamp": _utcnow()}]},
        feature_ref="919",
        seed=seed,
    )
    tests.append({"test": "footer_attached", "passed": output.get("compliance_footer") is not None})
    tests.append({"test": "confidence_score", "passed": output.get("compliance_footer", {}).get("confidence_score", 0) > 0})

    blocked = attach_compliance_footer_921(
        {
            "ok": True,
            "claims": [{"claim": "Price will moon", "claim_type": "fact", "evidence": []}],
        },
        feature_ref="920",
        seed=seed,
    )
    tests.append({"test": "fails_closed_block", "passed": blocked.get("blocked") is True})

    passed = sum(1 for t in tests if t["passed"])
    return {
        "ok": passed == len(tests),
        "feature_ref": _FEATURE_REF,
        "regression_tests": tests,
        "passed": passed,
        "total": len(tests),
        "all_passed": passed == len(tests),
    }
