"""Data governance admission gates for Decision Truth integration."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from failure.freshness import FreshnessState
from failure.quality import DataQualityState


class DataGovernanceState(StrEnum):
    ADMITTED = "ADMITTED"
    DEGRADED = "DEGRADED"
    ABSTAINED = "ABSTAINED"
    REJECTED = "REJECTED"


GATE_NAMES = (
    "provenance",
    "freshness",
    "quality",
    "historical_sufficiency",
    "execution_depth",
    "source_rights",
    "reliability",
    "reconciliation",
)


def evaluate_data_gates(payload: dict[str, Any]) -> dict[str, Any]:
    dg = payload.get("data_governance") or {}
    fresh = dg.get("freshness") or {}
    quality = dg.get("quality") or {}
    hist = dg.get("historical_depth") or {}
    l2l3 = dg.get("l2_l3_policy") or {}
    prov = dg.get("provenance") or {}
    recon = dg.get("reconciliation") or payload.get("reconciliation") or {}
    rights = dg.get("source_rights") or {}
    rel = dg.get("reliability") or {}

    gates: dict[str, dict[str, Any]] = {}
    prov_score = prov.get("provenance_score")
    gates["provenance"] = {
        "pass": prov.get("traceable") and (prov_score is None or float(prov_score) >= 40),
        "score": prov_score,
    }
    gates["freshness"] = {
        "pass": fresh.get("freshness_state") not in {FreshnessState.STALE.value, FreshnessState.UNKNOWN.value},
        "state": fresh.get("freshness_state"),
    }
    gates["quality"] = {
        "pass": quality.get("quality_state") not in {DataQualityState.CONFLICTING.value, DataQualityState.INSUFFICIENT.value},
        "state": quality.get("quality_state"),
    }
    gates["historical_sufficiency"] = {"pass": hist.get("sufficient", True), "available_days": hist.get("available_days")}
    gates["execution_depth"] = {"pass": l2l3.get("sufficient", True), "l2_required": l2l3.get("l2_required")}
    gates["source_rights"] = {"pass": rights.get("allowed", True), "reason": rights.get("reason")}
    gates["reliability"] = {
        "pass": float(rel.get("reliability_score") or 50) >= 40,
        "score": rel.get("reliability_score"),
    }
    gates["reconciliation"] = {"pass": not recon.get("conflict"), "conflict": recon.get("conflict")}

    failed = [n for n, g in gates.items() if not g.get("pass")]
    if "freshness" in failed and fresh.get("freshness_state") == FreshnessState.UNKNOWN.value:
        state = DataGovernanceState.ABSTAINED
    elif "quality" in failed or "reconciliation" in failed:
        state = DataGovernanceState.ABSTAINED if recon.get("conflict") else DataGovernanceState.DEGRADED
    elif failed:
        state = DataGovernanceState.DEGRADED
    else:
        state = DataGovernanceState.ADMITTED

    return {
        "data_governance_state": state.value,
        "gates": gates,
        "failed_gates": failed,
        "abstain_on_insufficient": state == DataGovernanceState.ABSTAINED,
    }
