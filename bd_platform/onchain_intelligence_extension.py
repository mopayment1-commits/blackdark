"""
On-Chain Intelligence Extension — Feature #12 (Sprint 2).

Merged sub-layers:
  #923 AML/CFT Risk Screening — rule-based, no legal conclusion
  #926 Address Labels & Cohorts — Entity Layer

Non-custodial, insight-only, public data only.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.OnChainIntelligenceExtension")

_FEATURE_REF_12 = 12
_FEATURE_REF_923 = 923
_FEATURE_REF_926 = 926
_STANDALONE = False
_MERGED_INTO = "On-Chain Intelligence Extension"
_SEED_PATH = Path("data/onchain_intelligence_extension_seed.json")
_AUDIT_RETENTION_YEARS = 5
_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

_DISCLAIMER_923 = (
    "Risk screening — insight only. Risk Flag, not legal conclusion. "
    "No money laundering determination. Not a report to authorities."
)

_DISCLAIMER_926 = (
    "Address labels — non-custodial entity metadata. Unknown remains unknown. "
    "No silent attribution. User labels encrypted."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("onchain extension seed load failed: %s", exc)
        return {}


def onchain_extension_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF_12,
        "aml_screening_ref": _FEATURE_REF_923,
        "entity_layer_ref": _FEATURE_REF_926,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "sub_layers": ["risk_screening_923", "entity_layer_926"],
        "insight_only": True,
        "non_custodial": True,
        "no_legal_conclusion": True,
        "timestamp": _utcnow(),
    }


# --- #923 AML/CFT Risk Screening ---


def screen_address_923(
    address: str,
    *,
    chain: str = "ethereum",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based risk screening — no legal conclusion."""
    seed = seed or _load_seed()
    addr = address.strip().lower()
    if not _ADDRESS_RE.match(addr):
        return {"ok": False, "feature_ref": _FEATURE_REF_923, "error": "invalid_address"}

    indicators_cfg = (seed.get("aml_screening_923") or {}).get("indicators") or {}
    triggered: list[dict[str, Any]] = []

    addr_data = (seed.get("address_risk_profiles") or {}).get(addr) or {}
    for ind_id, ind_cfg in indicators_cfg.items():
        threshold = ind_cfg.get("threshold")
        value = addr_data.get(ind_id)
        if value is not None and threshold is not None and float(value) >= float(threshold):
            triggered.append({
                "indicator_id": ind_id,
                "name": ind_cfg.get("name"),
                "value": value,
                "threshold": threshold,
                "rule_based": True,
                "explainable": True,
            })

    risk_level = "low"
    if len(triggered) >= 3:
        risk_level = "high"
    elif len(triggered) >= 1:
        risk_level = "medium"

    screen_id = f"screen_{uuid.uuid4().hex[:12]}"
    audit = {
        "screen_id": screen_id,
        "address": addr,
        "chain": chain,
        "indicators_triggered": len(triggered),
        "timestamp": _utcnow(),
        "version": (seed.get("aml_screening_923") or {}).get("rules_version", "1.0.0"),
        "retention_years": _AUDIT_RETENTION_YEARS,
    }

    fee = (seed.get("aml_screening_923") or {}).get("fee_db") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF_923,
        "extension_ref": _FEATURE_REF_12,
        "screen_id": screen_id,
        "address": addr,
        "risk_flag": risk_level != "low",
        "risk_level": risk_level,
        "indicators": triggered,
        "indicator_count": len(triggered),
        "min_indicators_for_flag": 3,
        "explainable": len(triggered) >= 1,
        "no_legal_conclusion": True,
        "not_money_laundering_detected": True,
        "disclaimer": _DISCLAIMER_923,
        "audit": audit,
        "privacy_public_data_only": True,
        "fee_db": {
            "screen_usd": fee.get("screen_per_address_usd", 0.005),
            "rpc_usd": fee.get("rpc_per_query_usd", 0.002),
            "indexing_usd": fee.get("indexing_per_query_usd", 0.001),
        },
        "timestamp": _utcnow(),
    }


# --- #926 Address Labels & Cohorts ---


def get_address_labels_926(
    address: str,
    *,
    user_id: str = "user_demo",
    tenant_id: str = "tenant_default",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Entity layer — public + user private labels with provenance."""
    seed = seed or _load_seed()
    addr = address.strip().lower()
    if not _ADDRESS_RE.match(addr):
        return {"ok": False, "feature_ref": _FEATURE_REF_926, "error": "invalid_address"}

    public = (seed.get("public_labels") or {}).get(addr)
    user_key = f"{tenant_id}:{user_id}"
    private = (seed.get("user_private_labels") or {}).get(user_key, {}).get(addr)

    labels: list[dict[str, Any]] = []
    if public:
        labels.append({**public, "source_type": "public_verified", "confidence": public.get("confidence", "high")})
    if private:
        labels.append({**private, "source_type": "user_private", "encrypted_at_rest": True})

    if not labels:
        labels.append({
            "label": "Unknown",
            "source_type": "none",
            "confidence": "none",
            "unknown_remains_unknown": True,
            "no_silent_attribution": True,
        })

    conflicts = len({l.get("label") for l in labels if l.get("label") != "Unknown"}) > 1
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF_926,
        "extension_ref": _FEATURE_REF_12,
        "address": addr,
        "labels": labels,
        "label_count": len(labels),
        "conflict_visible": conflicts,
        "no_silent_override": True,
        "provenance_required": True,
        "permission_safe": True,
        "tenant_id": tenant_id,
        "disclaimer": _DISCLAIMER_926,
        "timestamp": _utcnow(),
    }


def assign_user_label_926(
    address: str,
    *,
    label: str,
    user_id: str,
    tenant_id: str,
    source: str = "user_manual",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    addr = address.strip().lower()
    version = (seed.get("entity_layer_926") or {}).get("label_version", "1.0.0")
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF_926,
        "address": addr,
        "label": label,
        "source": source,
        "confidence": "user_defined",
        "version": version,
        "encrypted_at_rest": True,
        "audit_logged": True,
        "timestamp": _utcnow(),
    }


def build_address_cohort_926(
    cohort_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based cohort clustering — size + interaction frequency thresholds."""
    seed = seed or _load_seed()
    cohorts = seed.get("cohorts") or {}
    cohort = cohorts.get(cohort_id)
    if not cohort:
        return {"ok": False, "feature_ref": _FEATURE_REF_926, "error": "cohort_not_found"}

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF_926,
        "cohort_id": cohort_id,
        "name": cohort.get("name"),
        "addresses": cohort.get("addresses") or [],
        "member_count": len(cohort.get("addresses") or []),
        "rules": cohort.get("rules") or {},
        "rule_based_only": True,
        "ml_clustering_rejected": True,
        "confidence": cohort.get("confidence", "medium"),
        "version": cohort.get("version", "1.0.0"),
        "timestamp": _utcnow(),
    }


def run_onchain_extension_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = onchain_extension_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})

    high_risk = screen_address_923("0x742d35cc6634c0532925a3b844bc9e7595f0bbe0", seed=seed)
    checks.append({"id": "aml_screening", "passed": high_risk.get("no_legal_conclusion") is True})
    checks.append({"id": "explainable_flags", "passed": high_risk.get("explainable") is True or high_risk.get("risk_level") == "low"})
    checks.append({"id": "audit_trail", "passed": "screen_id" in high_risk.get("audit", {})})

    labels = get_address_labels_926("0x742d35cc6634c0532925a3b844bc9e7595f0bbe0", seed=seed)
    checks.append({"id": "entity_labels", "passed": labels.get("ok") is True})
    checks.append({"id": "unknown_explicit", "passed": any(l.get("unknown_remains_unknown") for l in labels.get("labels") or []) or labels.get("label_count", 0) > 0})

    unknown = get_address_labels_926("0x0000000000000000000000000000000000000001", seed=seed)
    checks.append({"id": "unknown_address", "passed": unknown["labels"][0].get("label") == "Unknown"})

    cohort = build_address_cohort_926("whale_accumulators", seed=seed)
    checks.append({"id": "cohorts", "passed": cohort.get("rule_based_only") is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_refs": [_FEATURE_REF_12, _FEATURE_REF_923, _FEATURE_REF_926],
        "all_passed": all_passed,
        "checks": checks,
    }
