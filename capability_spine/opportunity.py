"""Opportunity lifecycle, scoring, audit, and evidence surfaces."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

METHODOLOGY_VERSION = "capability_spine_opportunity_v1"
_SCORE_VERSION = "opportunity_score_v1"

_LOCK = threading.Lock()
_DISAPPEARANCE_LEDGER = Path(__file__).resolve().parents[1] / "data" / "opportunity_disappearance_ledger.jsonl"
_AUDIT_LEDGER = Path(__file__).resolve().parents[1] / "data" / "opportunity_decision_audit.jsonl"


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


# ── CAP-34 Opportunity Score ───────────────────────────────────────────────────


def compute_opportunity_score(opportunity: dict[str, Any]) -> dict[str, Any]:
    base = float(opportunity.get("opportunity_score") or opportunity.get("confidence") or 50.0)
    net_edge = float(opportunity.get("expected_net_edge_usd") or opportunity.get("net_profit_usdt") or 0)
    edge_adj = min(20.0, max(-20.0, net_edge / 100.0))
    freshness_penalty = 10.0 if opportunity.get("freshness_state") in {"STALE", "UNKNOWN"} else 0.0
    risk_penalty = float((opportunity.get("risk") or {}).get("risk_after") or 0) * 5.0
    score = _clamp_score(base + edge_adj - freshness_penalty - risk_penalty)
    return {
        "ok": True,
        "score": round(score, 2),
        "version": _SCORE_VERSION,
        "components": {
            "base": base,
            "edge_adj": edge_adj,
            "freshness_penalty": freshness_penalty,
            "risk_penalty": risk_penalty,
        },
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-35 Opportunity Score Explanation ───────────────────────────────────────


def explain_opportunity_score(opportunity: dict[str, Any], score_payload: dict[str, Any]) -> dict[str, Any]:
    components = score_payload.get("components") or {}
    gates = opportunity.get("gates") or {}
    failed = [k for k, v in gates.items() if isinstance(v, dict) and not v.get("pass", True)]
    return {
        "ok": True,
        "score": score_payload.get("score"),
        "score_version": score_payload.get("version"),
        "contributions": components,
        "passed_gates": [k for k in gates if k not in failed],
        "failed_gates": failed,
        "why_not_higher": ["freshness_penalty", "risk_penalty"] if components.get("freshness_penalty") else [],
        "missing_evidence": opportunity.get("missing_evidence") or [],
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-36 Opportunity Lifetime Tracker ────────────────────────────────────────


def track_opportunity_lifetime(
    opportunity: dict[str, Any],
    *,
    detected_at: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now_dt = now or datetime.now(UTC)
    detected = detected_at or opportunity.get("detected_at") or now_dt.isoformat()
    last_valid = opportunity.get("last_valid_at") or detected
    expiry = opportunity.get("expires_at")
    invalid = opportunity.get("invalidated_at")
    return {
        "ok": True,
        "detected_at": detected,
        "last_valid_at": last_valid,
        "expires_at": expiry,
        "invalidated_at": invalid,
        "remaining_seconds": opportunity.get("remaining_seconds"),
        "active": invalid is None and (expiry is None or expiry > now_dt.isoformat()),
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-37 Opportunity Survival / Decay Model ──────────────────────────────────


def survival_decay_model(
    *,
    age_seconds: float,
    half_life_seconds: float = 300.0,
) -> dict[str, Any]:
    if half_life_seconds <= 0:
        return {"ok": False, "reason": "invalid_half_life", "methodology_version": METHODOLOGY_VERSION}
    survival = 0.5 ** (age_seconds / half_life_seconds)
    return {
        "ok": True,
        "survival_probability": round(survival, 6),
        "age_seconds": age_seconds,
        "half_life_seconds": half_life_seconds,
        "model": "exponential_decay",
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-38 Historical Opportunity Disappearance Ledger ─────────────────────────


def record_opportunity_disappearance(
    *,
    opportunity_id: str,
    reason: str,
    state: str = "DISAPPEARED",
) -> dict[str, Any]:
    row = {
        "ledger_id": f"odl-{uuid4().hex[:12]}",
        "opportunity_id": opportunity_id,
        "reason": reason,
        "state": state,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    _DISAPPEARANCE_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with _DISAPPEARANCE_LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    return row


def query_disappearance_ledger(*, opportunity_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    if not _DISAPPEARANCE_LEDGER.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in _DISAPPEARANCE_LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if opportunity_id and row.get("opportunity_id") != opportunity_id:
            continue
        rows.append(row)
    return rows[-limit:]


# ── CAP-50 Opportunity Snapshot-at-Detection ───────────────────────────────────


def snapshot_at_detection(opportunity: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "snapshot_id": f"snap-{uuid4().hex[:12]}",
        "captured_at": datetime.now(UTC).isoformat(),
        "immutable": True,
        "price": opportunity.get("price"),
        "book": opportunity.get("book"),
        "fees": opportunity.get("fees") or opportunity.get("trading_fees_usdt"),
        "freshness_state": opportunity.get("freshness_state"),
        "methodology_versions": opportunity.get("methodology_versions") or {},
        "evidence_ids": opportunity.get("evidence_ids") or [],
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-53 Opportunity Failure Classification ──────────────────────────────────


FAILURE_TAXONOMY = {
    "FRESHNESS_STALE": "freshness",
    "LIQUIDITY_INSUFFICIENT": "liquidity",
    "EXECUTION_INFEASIBLE": "execution",
    "RISK_EXCEEDED": "risk",
    "EVIDENCE_MISSING": "evidence",
    "UNKNOWN": "unknown",
}


def classify_opportunity_failure(opportunity: dict[str, Any]) -> dict[str, Any]:
    failed_gates = opportunity.get("failed_gates") or []
    if "freshness" in failed_gates:
        code = "FRESHNESS_STALE"
    elif "liquidity" in failed_gates:
        code = "LIQUIDITY_INSUFFICIENT"
    elif "execution_feasibility" in failed_gates:
        code = "EXECUTION_INFEASIBLE"
    elif "risk" in failed_gates:
        code = "RISK_EXCEEDED"
    elif opportunity.get("missing_evidence"):
        code = "EVIDENCE_MISSING"
    else:
        code = "UNKNOWN"
    return {
        "ok": True,
        "failure_code": code,
        "taxonomy": FAILURE_TAXONOMY.get(code, "unknown"),
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-55 Prediction / Outcome Reconciliation ─────────────────────────────────


def reconcile_prediction_outcome(
    *,
    prediction: str,
    realized: Any,
    horizon: str,
    registered_at: str,
    resolved_at: str | None = None,
) -> dict[str, Any]:
    if realized is None:
        outcome = "UNKNOWN"
    elif str(realized).upper() == str(prediction).upper():
        outcome = "SUCCESS"
    elif str(realized).upper() in {"ABSTAIN", "INVALID"}:
        outcome = "ABSTAIN"
    else:
        outcome = "FAILURE"
    return {
        "ok": True,
        "prediction": prediction,
        "realized": realized,
        "outcome": outcome,
        "horizon": horizon,
        "registered_at": registered_at,
        "resolved_at": resolved_at,
        "temporal_integrity": registered_at <= (resolved_at or datetime.now(UTC).isoformat()),
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-58 Opportunity Explainability ──────────────────────────────────────────


def build_opportunity_explainability(opportunity: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "economics": {
            "expected_net_edge": opportunity.get("expected_net_edge_usd"),
            "capacity": opportunity.get("capacity"),
        },
        "evidence": opportunity.get("evidence_ids") or [],
        "risks": opportunity.get("risk") or {},
        "gates": opportunity.get("gates") or {},
        "uncertainty": opportunity.get("net_edge_interval") or {},
        "invalidation": opportunity.get("invalidation_condition"),
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-59 Missing-Evidence Disclosure ─────────────────────────────────────────


def disclose_missing_evidence(expected: list[str], present: list[str]) -> dict[str, Any]:
    missing = [e for e in expected if e not in present]
    stale = [e for e in present if e.endswith(":STALE")]
    return {
        "ok": True,
        "missing": missing,
        "stale": stale,
        "conflicting": [],
        "disclosure_required": bool(missing or stale),
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-60 Performance Evidence Type ───────────────────────────────────────────


EVIDENCE_TYPES = frozenset({"BACKTESTED", "SIMULATED", "SHADOW", "PRODUCTION", "LIVE_OBSERVATION"})


def classify_performance_evidence(
    *,
    evidence_class: str,
    source_ref: str | None = None,
) -> dict[str, Any]:
    normalized = evidence_class.upper()
    if normalized not in EVIDENCE_TYPES:
        normalized = "UNKNOWN"
    return {
        "ok": True,
        "evidence_type": normalized,
        "source_ref": source_ref,
        "promotion_allowed": False,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-63 Opportunity / Decision Audit Trail ──────────────────────────────────


def append_decision_audit(
    *,
    decision_id: str,
    event_type: str,
    payload: dict[str, Any],
    trace_id: str | None = None,
) -> dict[str, Any]:
    row = {
        "audit_id": f"aud-{uuid4().hex[:12]}",
        "decision_id": decision_id,
        "event_type": event_type,
        "trace_id": trace_id,
        "payload": payload,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    _AUDIT_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with _AUDIT_LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    return {"ok": True, **row}
