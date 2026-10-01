"""Behavioral coverage for governance.public_report helpers."""

from __future__ import annotations

import governance.public_report as pr


def test_coerce_and_gate_statuses():
    assert pr.coerce_bool(True) is True
    assert pr.coerce_bool("yes") is False
    assert pr.coerce_int(True) == 1
    assert pr.coerce_int(7) == 7
    assert pr.coerce_int(3.9) == 3
    assert pr.coerce_int("x") == 0
    report = {
        "gates": {
            "g1": {"status": "PASS"},
            "g2": {"status": "NOT_A_STATUS"},
            "bad": "not-a-dict",
        }
    }
    statuses = pr.gate_statuses_from_report(report)
    assert statuses["g1"] == "PASS"
    assert statuses["g2"] == "UNKNOWN"


def test_pre_launch_sinks_and_stdout():
    report = {
        "pre_launch_ready": True,
        "secrets_hygiene_clean": False,
        "railway_deploy_allowed": True,
        "gates": {"deploy": {"status": "PARTIAL", "note": "x"}},
    }
    sink = pr.pre_launch_summary_sink(report)
    assert sink["pre_launch_ready"] is True
    lines = pr.pre_launch_stdout_lines(sink)
    assert any("pre_launch_ready=true" in ln for ln in lines)
    assert any("gate=deploy" in ln for ln in lines)


def test_institutional_matrix_and_fds_line():
    matrix = {
        "summary": {
            "institutional_maturity_score_100": 88,
            "final_goal_achieved": True,
            "domain_status_counts": {"PASS": 1, "PARTIAL": 2, "FAIL": 0},
        }
    }
    sink = pr.institutional_matrix_summary_sink(matrix)
    assert sink["institutional_maturity_score_100"] == 88
    lines = pr.institutional_matrix_stdout_lines(sink)
    assert any("domain_PASS=1" in ln for ln in lines)
    clean = pr.fds_scan_stdout_line(clean=True, files_scanned=1, pan_finding_count=0, secret_finding_count=0)
    dirty = pr.fds_scan_stdout_line(clean=False, files_scanned=2, pan_finding_count=1, secret_finding_count=3)
    assert "status=clean" in clean
    assert "status=dirty" in dirty
    assert "pan_finding_count=1" in dirty


def test_pre_launch_public_document_strips_hygiene_payload():
    report = {
        "generated_at": "t",
        "program": "p",
        "pre_launch_ready": False,
        "gates": {"g": {"status": "FAIL", "note": "n"}},
        "honest_summary": {"k": "v"},
        "security_workflows_open": ["wf"],
    }
    doc = pr.pre_launch_public_document(report)
    assert doc["gates"]["g"]["status"] == "FAIL"
    console = pr.pre_launch_console_summary(report)
    assert console["gate_statuses"]["g"] == "FAIL"


def test_institutional_matrix_public_and_console_summary():
    matrix = {
        "generated_at": "t",
        "frameworks": {"f": 1},
        "summary": {
            "domain_status_counts": {"PASS": 2, "PARTIAL": 1, "FAIL": 0},
            "institutional_maturity_score_100": 90,
            "final_goal_achieved": False,
            "final_goal_blocked_by": ["x"],
            "excluded_from_scope": ["y"],
            "automatable_backlog_priority": ["z"],
        },
    }
    doc = pr.institutional_matrix_public_document(matrix)
    assert doc["summary"]["institutional_maturity_score_100"] == 90
    console = pr.institutional_matrix_console_summary(matrix)
    assert console["final_goal_achieved"] is False


def test_gate_public_view_non_dict():
    assert pr._gate_public_view(None)["status"] == "UNKNOWN"
    assert pr._gate_public_view({"status": "PASS", "note": "ok"})["note"] == "ok"
