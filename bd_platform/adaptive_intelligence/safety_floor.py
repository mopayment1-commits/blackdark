"""Safety Floor — spec §5/§12; never hide decision-critical context (AIE-003)."""

from __future__ import annotations

from typing import Any

from bd_platform.adaptive_intelligence.trust_dimensions import TrustDimensionVector


_REQUIRED_KEYS = (
    "freshness",
    "evidence_state",
    "uncertainty",
    "critical_limitation",
    "invalidation_or_next_check",
)


def enforce_safety_floor(payload: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed if Safety Floor fields missing on decision-critical surfaces."""
    out = dict(payload)
    missing = [k for k in _REQUIRED_KEYS if not str(out.get(k) or "").strip()]
    if missing and out.get("decision_critical"):
        raise ValueError(f"safety_floor_incomplete:{','.join(missing)}")
    trust = TrustDimensionVector.from_payload(out)
    out.setdefault("freshness", trust.freshness)
    out.setdefault("evidence_state", trust.evidence_class)
    out.setdefault("uncertainty", out.get("uncertainty") or "medium")
    out.setdefault("critical_limitation", out.get("critical_limitation") or "Advisory only; verify ledger.")
    out.setdefault(
        "invalidation_or_next_check",
        out.get("invalidation_or_next_check") or out.get("next_check") or "recheck_on_stale_or_regime_change",
    )
    out["safety_floor_enforced"] = True
    out["trust_dimensions"] = trust.to_dict()
    return out
