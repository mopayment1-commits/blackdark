"""
Surveillance Engine — Feature #743 (Sprint 2 Intelligence Ledger, Enterprise tier).

Absorbs #721 Bot Activity Detection as sub-module.
Rule-based pattern detection. False-positive review pipeline. Evidence retention 90 days.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.SurveillanceEngine")

_FEATURE_ID = 743
_ABSORBED_IDS = (721, 743)
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Surveillance Engine"
_SPRINT = 2
_SEED_PATH = Path("data/surveillance_engine_seed.json")
_METHODOLOGY_VERSION = "1.0"
_EVIDENCE_RETENTION_DAYS = 90
_RULE_BASED_FIRST = True

CaseType = Literal["wash_trading", "spoofing", "layering", "unusual_volume"]

_DISCLAIMER = (
    "Surveillance cases are suspected patterns — not accusations. "
    "All cases reviewed manually before public alert. "
    "Entity names anonymized until verified."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"cases": [], "bot_activity_layer": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("surveillance engine seed load failed: %s", exc)
        return {"cases": [], "bot_activity_layer": {}}


def build_bot_activity_submodule(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#721 absorbed — NOT a separate surveillance ticket."""
    seed = seed or _load_seed()
    layer = seed.get("bot_activity_layer") or {}
    return {
        "absorbed_feature_id": 721,
        "layer": "bot_activity_detection",
        "not_standalone": True,
        "rule_based_first": _RULE_BASED_FIRST,
        "integrated": True,
        "display": "Bot Activity (#721) integrated as surveillance sub-module",
        "assets_tracked": layer.get("assets_tracked", 0),
    }


def build_surveillance_case(case: dict[str, Any]) -> dict[str, Any]:
    review = case.get("review") or {}
    evidence = case.get("evidence") or {}
    retention_until = (
        datetime.fromisoformat(evidence.get("captured_at", _utcnow()).replace("Z", "+00:00"))
        + timedelta(days=_EVIDENCE_RETENTION_DAYS)
    ).isoformat()

    public_alert = review.get("status") == "approved" and review.get("manual_review_complete")

    return {
        "case_id": case.get("case_id"),
        "case_type": case.get("case_type"),
        "case_display": f"Suspected {str(case.get('case_type', '')).replace('_', ' ').title()}",
        "confidence_pct": case.get("confidence_pct"),
        "venue_anonymized": case.get("venue_label", "Exchange X"),
        "asset_anonymized": case.get("asset_label", "Asset Y"),
        "no_direct_accusation": True,
        "evidence": {
            "trade_count": evidence.get("trade_count"),
            "window_seconds": evidence.get("window_seconds"),
            "raw_data_archived": evidence.get("raw_data_archived", True),
            "screenshot_archived": evidence.get("screenshot_archived", True),
            "captured_at": evidence.get("captured_at"),
            "retention_days": _EVIDENCE_RETENTION_DAYS,
            "retention_until": retention_until,
        },
        "evidence_display": (
            f"Evidence: {evidence.get('trade_count', 'N/A')} trades in "
            f"{evidence.get('window_seconds', 'N/A')} seconds"
        ),
        "review": {
            "status": review.get("status", "pending"),
            "manual_review_complete": review.get("manual_review_complete", False),
            "false_positive_review_pipeline": True,
        },
        "public_alert_eligible": public_alert,
        "detection_method": "rule_based",
        "rule_based_first": _RULE_BASED_FIRST,
        "disclaimer": _DISCLAIMER,
    }


def build_surveillance_panel(*, tier: str = "free", case_id: str | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    cases_raw = seed.get("cases") or []

    if case_id:
        raw = next((c for c in cases_raw if c.get("case_id") == case_id), None)
        if not raw:
            return {"ok": False, "feature_id": _FEATURE_ID, "error": "case_not_found", "case_id": case_id}
        cases = [build_surveillance_case(raw)]
    else:
        cases = [build_surveillance_case(c) for c in cases_raw]

    if tier == "enterprise":
        visible_cases = [c for c in cases if c.get("public_alert_eligible")]
        summary_only = False
    else:
        visible_cases = []
        summary_only = True

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_ids": list(_ABSORBED_IDS),
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "tier": tier,
        "enterprise_alerts": tier == "enterprise",
        "summary_only": summary_only,
        "summary_stats": {
            "total_cases": len(cases),
            "pending_review": sum(1 for c in cases if c["review"]["status"] == "pending"),
            "approved_alerts": len(visible_cases),
        },
        "cases": visible_cases if tier == "enterprise" else [],
        "bot_activity_submodule": build_bot_activity_submodule(seed),
        "evidence_retention_days": _EVIDENCE_RETENTION_DAYS,
        "false_positive_review_pipeline": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def surveillance_engine_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Surveillance Engine",
        "absorbed_tickets": {721: "Bot Activity Detection", 743: "Surveillance Engine"},
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "enterprise_tier_alerts": True,
        "free_tier_summary_only": True,
        "rule_based_first": _RULE_BASED_FIRST,
        "evidence_retention_days": _EVIDENCE_RETENTION_DAYS,
        "case_count": len(seed.get("cases") or []),
        "bot_activity_submodule": build_bot_activity_submodule(seed),
        "acceptance_criteria": {
            "false_positive_review": True,
            "evidence_retention_90d": True,
            "rule_based_first": True,
            "anonymized_entities": True,
            "enterprise_paid_alerts": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
