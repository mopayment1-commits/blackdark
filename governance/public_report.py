"""Public-safe projections of governance artifacts (no secret/token material in sinks)."""

from __future__ import annotations

from typing import Any

_GATE_STATUS_ALLOWLIST = frozenset({"PASS", "PARTIAL", "FAIL", "UNKNOWN"})


def coerce_bool(value: object) -> bool:
    return value is True


def coerce_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def gate_statuses_from_report(report: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, gate in (report.get("gates") or {}).items():
        if not isinstance(gate, dict):
            continue
        status = str(gate.get("status") or "UNKNOWN")
        if status not in _GATE_STATUS_ALLOWLIST:
            status = "UNKNOWN"
        out[str(name)[:80]] = status
    return out


def pre_launch_summary_sink(report: dict[str, Any]) -> dict[str, Any]:
    """Scalars + gate statuses only — safe for JSON file and stdout lines."""
    return {
        "pre_launch_ready": coerce_bool(report.get("pre_launch_ready")),
        "secrets_hygiene_clean": coerce_bool(report.get("secrets_hygiene_clean")),
        "railway_deploy_allowed": coerce_bool(report.get("railway_deploy_allowed")),
        "gate_statuses": gate_statuses_from_report(report),
    }


def pre_launch_stdout_lines(payload: dict[str, Any]) -> list[str]:
    lines = [
        f"pre_launch_ready={'true' if payload.get('pre_launch_ready') else 'false'}",
        f"secrets_hygiene_clean={'true' if payload.get('secrets_hygiene_clean') else 'false'}",
        f"railway_deploy_allowed={'true' if payload.get('railway_deploy_allowed') else 'false'}",
    ]
    for name in sorted(payload.get("gate_statuses") or {}):
        lines.append(f"gate={name} status={(payload.get('gate_statuses') or {})[name]}")
    return lines


def institutional_matrix_summary_sink(matrix: dict[str, Any]) -> dict[str, Any]:
    summary = matrix.get("summary") if isinstance(matrix.get("summary"), dict) else {}
    counts = summary.get("domain_status_counts") if isinstance(summary.get("domain_status_counts"), dict) else {}
    return {
        "institutional_maturity_score_100": coerce_int(summary.get("institutional_maturity_score_100")),
        "final_goal_achieved": coerce_bool(summary.get("final_goal_achieved")),
        "domain_status_counts": {
            "PASS": coerce_int(counts.get("PASS")),
            "PARTIAL": coerce_int(counts.get("PARTIAL")),
            "FAIL": coerce_int(counts.get("FAIL")),
        },
    }


def institutional_matrix_stdout_lines(payload: dict[str, Any]) -> list[str]:
    counts = payload.get("domain_status_counts") or {}
    return [
        f"final_goal_achieved={'true' if payload.get('final_goal_achieved') else 'false'}",
        f"institutional_maturity_score_100={coerce_int(payload.get('institutional_maturity_score_100'))}",
        f"domain_PASS={coerce_int(counts.get('PASS'))}",
        f"domain_PARTIAL={coerce_int(counts.get('PARTIAL'))}",
        f"domain_FAIL={coerce_int(counts.get('FAIL'))}",
    ]


def fds_scan_stdout_line(*, clean: bool, files_scanned: int, pan_finding_count: int, secret_finding_count: int) -> str:
    return (
        "fds_financial_data_scan "
        f"status={'clean' if clean else 'dirty'} "
        f"files_scanned={files_scanned} "
        f"pan_finding_count={pan_finding_count} "
        f"secret_finding_count={secret_finding_count}"
    )


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
