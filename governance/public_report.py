"""Public-safe projections of governance artifacts (no secret/token material in sinks)."""

from __future__ import annotations

from typing import Any


def _gate_public_view(gate: Any) -> dict[str, str]:
    if not isinstance(gate, dict):
        return {"status": "UNKNOWN"}
    out: dict[str, str] = {"status": str(gate.get("status") or "UNKNOWN")}
    note = gate.get("note")
    if note:
        out["note"] = str(note)[:500]
    return out


def pre_launch_public_document(report: dict[str, Any]) -> dict[str, Any]:
    """JSON artifact safe for disk — gate statuses only, no hygiene scan payloads."""
    gates_in = report.get("gates") or {}
    gates_out = {str(name): _gate_public_view(gate) for name, gate in gates_in.items()}
    honest = report.get("honest_summary") or {}
    honest_out = {str(k): str(v) for k, v in honest.items()}
    workflows = [str(w) for w in (report.get("security_workflows_open") or [])[:50]]
    return {
        "generated_at": str(report.get("generated_at") or ""),
        "program": str(report.get("program") or ""),
        "pre_launch_ready": bool(report.get("pre_launch_ready")),
        "pre_launch_ready_automatable": bool(report.get("pre_launch_ready_automatable")),
        "railway_deploy_allowed": bool(report.get("railway_deploy_allowed")),
        "PASS_LIVE_NOT_CLAIMED": bool(report.get("PASS_LIVE_NOT_CLAIMED")),
        "blk_002_postgres_separate": bool(report.get("blk_002_postgres_separate")),
        "secrets_hygiene_clean": bool(report.get("secrets_hygiene_clean")),
        "security_workflows_open": workflows,
        "gates": gates_out,
        "honest_summary": honest_out,
    }


def pre_launch_console_summary(report: dict[str, Any]) -> dict[str, Any]:
    doc = pre_launch_public_document(report)
    return {
        "generated_at": doc["generated_at"],
        "pre_launch_ready": doc["pre_launch_ready"],
        "secrets_hygiene_clean": doc["secrets_hygiene_clean"],
        "railway_deploy_allowed": doc["railway_deploy_allowed"],
        "gate_statuses": {name: body.get("status") for name, body in doc["gates"].items()},
    }


def institutional_matrix_public_document(matrix: dict[str, Any]) -> dict[str, Any]:
    summary = matrix.get("summary") or {}
    counts = summary.get("domain_status_counts") or {}
    return {
        "generated_at": str(matrix.get("generated_at") or ""),
        "frameworks": matrix.get("frameworks") or {},
        "nist_ssdf": matrix.get("nist_ssdf") or {},
        "owasp_asvs_l2": matrix.get("owasp_asvs_l2") or {},
        "iso_25010": matrix.get("iso_25010") or {},
        "project_specific": matrix.get("project_specific") or {},
        "summary": {
            "domain_status_counts": {
                "PASS": int(counts.get("PASS") or 0),
                "PARTIAL": int(counts.get("PARTIAL") or 0),
                "FAIL": int(counts.get("FAIL") or 0),
            },
            "institutional_maturity_score_100": int(summary.get("institutional_maturity_score_100") or 0),
            "final_goal_achieved": bool(summary.get("final_goal_achieved")),
            "final_goal_blocked_by": [str(x) for x in (summary.get("final_goal_blocked_by") or [])],
            "excluded_from_scope": [str(x) for x in (summary.get("excluded_from_scope") or [])],
            "automatable_backlog_priority": [
                str(x) for x in (summary.get("automatable_backlog_priority") or [])
            ],
        },
    }


def institutional_matrix_console_summary(matrix: dict[str, Any]) -> dict[str, Any]:
    doc = institutional_matrix_public_document(matrix)
    return dict(doc["summary"])
