"""Flywheel readiness gate — §15, §26, DSR-024."""

from __future__ import annotations

from typing import Any


def assess_flywheel_gate(checks: dict[str, Any]) -> dict[str, Any]:
    """
    Gate states per v5: READY_NOT_PROVEN / PASS_ENGINEERING / PASS_LIVE / ASSURANCE_READY.
    Local engineering can reach PASS_ENGINEERING; PASS_LIVE requires G6.
    """
    mandatory = [
        "all_material_contracts",
        "rights_enforceable",
        "pit_replay_integrity",
        "signal_decision_trace",
        "no_history_erase",
        "quality_no_silent_stale",
        "restore_evidence",
        "evidence_class_separation",
        "no_unresolved_lineage_conflicts",
    ]
    failed = [k for k in mandatory if not checks.get(k)]
    red_flags = checks.get("red_flags", [])
    blocked_external = checks.get("blocked_external", [])

    if failed or red_flags:
        state = "READY_NOT_PROVEN"
        ready = False
    elif blocked_external:
        state = "PASS_ENGINEERING"
        ready = True
    else:
        state = "PASS_ENGINEERING"
        ready = True

    return {
        "gate": "PROPRIETARY_ASSET_ACCUMULATION_DATA_FLYWHEEL_READINESS",
        "state": state,
        "engineering_pass": len(failed) == 0 and len(red_flags) == 0,
        "ready": ready,
        "failed_checks": failed,
        "red_flags": red_flags,
        "blocked_external": blocked_external,
        "verdict": state if ready else "NOT_READY",
    }
