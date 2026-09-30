"""Methodology versioning registry for DTS outputs (DTS-050)."""

from __future__ import annotations

from typing import Any

DTS_METHODOLOGY_VERSIONS: dict[str, str] = {
    "decision_truth": "dts-p4-evidence-lifecycle-1.0",
    "evidence_lifecycle": "dts-p4-evidence-lifecycle-1.0",
    "calibration": "dts-p4-calibration-1.0",
    "outcome_ledger": "dts-p4-outcome-ledger-1.0",
    "change_detector": "dts-p4-change-detector-1.0",
    "simulation": "dts-p4-simulation-1.0",
    "evidence_grade": "dts-p4-evidence-grade-1.0",
    "evidence_class": "cap646-evidence-class-1.0",
    "provenance": "data-governance-provenance-1.0",
    "anti_cherry_picking": "dts-p4-anti-cherry-picking-1.0",
    "history_integrity": "dts-p4-history-integrity-1.0",
    "net_edge": "dts-p2-net-edge-1.0",
    "portfolio_risk": "dts-p3-portfolio-risk-1.0",
}


def methodology_bundle(extra: dict[str, str] | None = None) -> dict[str, str]:
    bundle = dict(DTS_METHODOLOGY_VERSIONS)
    if extra:
        bundle.update(extra)
    return bundle


def attach_methodology_versions(payload: dict[str, Any], *, extra: dict[str, str] | None = None) -> dict[str, Any]:
    out = dict(payload)
    out["methodology_versions"] = methodology_bundle(extra)
    return out
