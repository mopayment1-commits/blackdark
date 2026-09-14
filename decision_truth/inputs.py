"""Admission input extraction — no optimistic caller defaults (P1 / DTS-017)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from failure.freshness import FreshnessState
from failure.quality import DataQualityState


@dataclass(frozen=True, slots=True)
class AdmissionInputs:
    freshness_ok: bool | None
    freshness_meta: dict[str, Any]
    data_quality_score: float | None
    data_quality_state: str | None
    evidence_class: str | None
    evidence_class_available: bool
    liquidity_ok: bool | None
    execution_score: float | None
    execution_available: bool
    risk_ok: bool | None
    uncertainty_high: bool | None
    uncertainty_available: bool
    net_edge_reject: bool
    net_edge_available: bool
    data_governance_state: str | None
    data_governance_failed_gates: list[str]
    failure_state: str | None
    missing_critical: tuple[str, ...]
    provenance_context: dict[str, Any]


def _dg(payload: dict[str, Any]) -> dict[str, Any]:
    return dict(payload.get("data_governance") or {})


def _freshness_inputs(payload: dict[str, Any]) -> tuple[bool | None, dict[str, Any]]:
    dg = _dg(payload)
    fresh = dg.get("freshness") or {}
    state = fresh.get("freshness_state") or payload.get("freshness_state")
    if state in {FreshnessState.STALE.value, "STALE"}:
        return False, {"freshness_state": state, "source": "data_governance", "ok": False}
    if state in {FreshnessState.UNKNOWN.value, "UNKNOWN"}:
        return None, {"freshness_state": state, "source": "data_governance", "ok": False, "reason": "unknown_freshness"}
    if state in {FreshnessState.LIVE.value, FreshnessState.NEAR_LIVE.value, FreshnessState.DELAYED.value, "LIVE", "NEAR_LIVE", "DELAYED"}:
        return True, {"freshness_state": state, "source": "data_governance", "ok": True}

    age_ms = payload.get("quote_age_ms", payload.get("age_ms"))
    if age_ms is not None:
        try:
            age = float(age_ms)
        except (TypeError, ValueError):
            age = -1.0
        max_age = float(payload.get("max_quote_age_ms") or 2500.0)
        ok = age >= 0 and age <= max_age
        return ok, {"quote_age_ms": age, "max_quote_age_ms": max_age, "ok": ok, "source": "quote_age"}

    return None, {"ok": False, "reason": "freshness_unverified", "source": "none"}


def _quality_inputs(payload: dict[str, Any]) -> tuple[float | None, str | None]:
    dg = _dg(payload)
    quality = dg.get("quality") or {}
    state = quality.get("quality_state") or payload.get("data_quality_state")
    if "data_quality_score" in payload:
        try:
            return float(payload["data_quality_score"]), state
        except (TypeError, ValueError):
            pass
    if "provenance_score" in payload:
        try:
            return float(payload["provenance_score"]), state
        except (TypeError, ValueError):
            pass
    score = quality.get("quality_score")
    if score is not None:
        try:
            return float(score), state
        except (TypeError, ValueError):
            pass
    return None, state


def _evidence_class(payload: dict[str, Any]) -> tuple[str | None, bool]:
    explicit = payload.get("evidence_class")
    if explicit and str(explicit) not in {"UNAVAILABLE", "UNKNOWN", ""}:
        return str(explicit), True
    try:
        from cap646.evidence_class import infer_evidence_class

        inferred = infer_evidence_class(
            source=str(payload.get("source") or ""),
            explicit=explicit if explicit else None,
        )
        return inferred, True
    except Exception:
        return None, False


def _execution_score(payload: dict[str, Any]) -> tuple[float | None, bool]:
    if "execution_feasibility_score" in payload:
        try:
            return float(payload["execution_feasibility_score"]), True
        except (TypeError, ValueError):
            return None, False
    label = str(payload.get("execution_feasibility") or "").lower()
    if not label:
        return None, False
    mapping = {"high": 85.0, "full": 90.0, "partial": 65.0, "medium": 55.0, "low": 25.0, "below_threshold": 20.0, "not_executable": 10.0, "blocked": 5.0, "rejected": 5.0}
    if label in mapping:
        return mapping[label], True
    return None, False


def _failure_state(payload: dict[str, Any]) -> str | None:
    for key in ("failure_state", "data_failure_state"):
        val = payload.get(key)
        if val:
            return str(val)
    dg_state = payload.get("data_governance_state")
    if dg_state in {"UNAVAILABLE", "INDETERMINATE", "DEGRADED", "STALE", "PARTIAL", "ABSTAINED", "REJECTED"}:
        return str(dg_state)
    return None


def extract_admission_inputs(payload: dict[str, Any], *, net_edge: dict[str, Any]) -> AdmissionInputs:
    freshness_ok, freshness_meta = _freshness_inputs(payload)
    dq_score, dq_state = _quality_inputs(payload)
    evidence_class, evidence_available = _evidence_class(payload)

    liquidity_ok: bool | None
    if "liquidity_ok" in payload:
        liquidity_ok = bool(payload.get("liquidity_ok"))
    else:
        liquidity_ok = None

    execution_score, execution_available = _execution_score(payload)

    risk_ok: bool | None
    if "risk_ok" in payload:
        risk_ok = bool(payload.get("risk_ok"))
    elif payload.get("risk_factors"):
        risk_ok = len(payload.get("risk_factors") or []) == 0
    else:
        risk_ok = None

    uncertainty_high: bool | None = None
    uncertainty_available = False
    if "uncertainty_high" in payload:
        uncertainty_high = bool(payload.get("uncertainty_high"))
        uncertainty_available = True
    elif (payload.get("uncertainty") or {}).get("high") is not None:
        uncertainty_high = bool((payload.get("uncertainty") or {}).get("high"))
        uncertainty_available = True

    net_edge_available = bool(net_edge.get("enabled", True)) and net_edge.get("reason") != "net_edge_unavailable"
    if net_edge.get("label") == "ADVISORY_NOT_EXECUTABLE":
        net_edge_available = False

    dg = _dg(payload)
    prov = dg.get("provenance") or {}
    provenance_context = {
        "source": payload.get("source") or prov.get("source"),
        "freshness": freshness_meta,
        "methodology_versions": {"decision_truth": "dts-p1-spine-1.0", "net_edge": "net_edge_truth_v1"},
        "assumptions": {"surface": payload.get("surface"), "timestamp": payload.get("timestamp")},
        "applicability": payload.get("applicability") or "decision_capable_path",
    }

    missing: list[str] = []
    if freshness_ok is None:
        missing.append("freshness")
    if dq_score is None:
        missing.append("data_quality")
    if not evidence_available:
        missing.append("evidence_class")
    if not execution_available:
        missing.append("execution_feasibility")
    if not uncertainty_available:
        missing.append("uncertainty")
    if risk_ok is None:
        missing.append("risk_context")
    if liquidity_ok is None:
        missing.append("liquidity")

    return AdmissionInputs(
        freshness_ok=freshness_ok,
        freshness_meta=freshness_meta,
        data_quality_score=dq_score,
        data_quality_state=dq_state,
        evidence_class=evidence_class,
        evidence_class_available=evidence_available,
        liquidity_ok=liquidity_ok,
        execution_score=execution_score,
        execution_available=execution_available,
        risk_ok=risk_ok,
        uncertainty_high=uncertainty_high,
        uncertainty_available=uncertainty_available,
        net_edge_reject=bool(net_edge.get("reject")),
        net_edge_available=net_edge_available,
        data_governance_state=payload.get("data_governance_state"),
        data_governance_failed_gates=list(payload.get("data_governance_failed_gates") or []),
        failure_state=_failure_state(payload),
        missing_critical=tuple(missing),
        provenance_context=provenance_context,
    )
