"""SPEC_11 — Global Time Temporal Consistency adversarial tests."""

from __future__ import annotations

import json
from pathlib import Path

from launch57.global_time_temporal_consistency_spec_common import (
    DOMAIN,
    build_final_status,
    build_requirements_register,
    build_runtime_truth_table,
    independent_verification,
)


def test_requirements_register_nonempty():
    reqs = build_requirements_register()
    assert len(reqs) >= 20
    assert all(r["mandatory"] for r in reqs)


def test_runtime_truth_all_yes():
    truth = build_runtime_truth_table()
    nos = [r for r in truth if r["status"] != "YES"]
    assert not nos, nos


def test_canonical_unchanged_under_cairo_vs_utc():
    from launch57.global_time_temporal_consistency_common import verify_canonical_unchanged_under_display_tz

    check = verify_canonical_unchanged_under_display_tz()
    assert check["ok"] is True
    assert check["display_differs_by_zone"] is True
    assert check["canonical_independent_of_display"] is True


def test_naive_datetime_fail_closed():
    from launch57.global_time_temporal_consistency_common import verify_naive_datetime_fail_closed

    check = verify_naive_datetime_fail_closed()
    assert check["fail_closed"] is True
    assert check["naive_rejected"] is True


def test_available_at_not_fabricated():
    from launch57.global_time_temporal_consistency_common import verify_available_at_not_fabricated

    check = verify_available_at_not_fabricated()
    assert check["ok"] is True
    assert check["unknown_without_observation"] is True


def test_untrusted_decision_time_rejected():
    from launch57.global_time_temporal_consistency_common import verify_untrusted_decision_time_rejected

    check = verify_untrusted_decision_time_rejected()
    assert check["gate_ok"] is True


def test_expired_not_presented_as_current():
    from launch57.global_time_temporal_consistency_common import verify_expired_not_presented_as_current

    check = verify_expired_not_presented_as_current()
    assert check["ok"] is True
    assert check["alert_stale_not_current"] is True
    assert check["net_edge_stale_not_current"] is True
    assert check["shareable_stale_not_current"] is True


def test_file06_file08_temporal_alignment():
    from launch57.global_time_temporal_consistency_common import verify_file06_file08_temporal_alignment

    alignment = verify_file06_file08_temporal_alignment()
    assert alignment["aligned"] is True


def test_b1_b15_batch_coverage():
    from launch57.global_time_temporal_consistency_common import verify_b1_b15_batch_coverage

    batches = verify_b1_b15_batch_coverage()
    assert batches["ok"] is True
    assert batches["all_batches_pass_engineering"] is True
    assert batches["b15_global_pass"] is True


def test_runtime_temporal_paths_wired():
    from launch57.global_time_temporal_consistency_common import verify_runtime_temporal_path_wiring

    wiring = verify_runtime_temporal_path_wiring()
    assert wiring["runtime_enforcement_ok"] is True
    assert wiring["wired_paths"]["decision_timing_wired"] is True
    assert wiring["wired_paths"]["alert_timing_wired"] is True


def test_machine_readable_temporal_export():
    from launch57.global_time_temporal_consistency_common import build_machine_readable_temporal_export

    export = build_machine_readable_temporal_export()
    assert export["artifact"] == "LAUNCH57_GLOBAL_TIME_TEMPORAL_CONSISTENCY_EXPORT"
    assert export["temporal_canonical_ok"] is True
    assert export["pass_live_not_claimed"] is True


def test_acceptance_criteria_all_pass():
    from launch57.global_time_temporal_consistency_common import acceptance_criteria_status

    ac = acceptance_criteria_status()
    required = (
        "ac01_canonical_utc_aware",
        "ac02_no_naive_datetime_path",
        "display_tz_canonical_invariant",
        "untrusted_decision_time_rejected",
        "expired_not_presented_as_current",
        "runtime_paths_wired",
        "b1_b15_batches_closed",
        "temporal_canonical_ok",
        "ac30_no_false_pass_live",
    )
    missing = [k for k in required if not ac.get(k)]
    assert not missing, missing


def test_independent_verification_passes():
    iv = independent_verification()
    assert iv["INDEPENDENT_VERIFICATION_PASS"] is True
    assert iv["PASS_LIVE_NOT_CLAIMED"] is True


def test_final_status_closed_local():
    status = build_final_status(skip_tests=True)
    assert status["closure_status"] == "CLOSED_LOCAL"
    assert status["PASS_ENGINEERING"] is True
    assert status["LOCAL_ENGINEERING_GAP_COUNT"] == 0
    assert status["temporal_canonical_ok"] is True
    assert status["launch57_only_ok"] is True
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True


def test_spec11_artifact_paths_exist():
    gov = Path("governance/launch57/SPEC_11_GLOBAL_TIME_TEMPORAL_CONSISTENCY")
    for name in (
        "REQUIREMENTS_REGISTER.json",
        "RUNTIME_TRUTH_TABLE.md",
        "LOCAL_CLOSURE_REPORT.md",
        "INDEPENDENT_VERIFICATION.json",
        "FINAL_STATUS.json",
    ):
        path = gov / name
        assert path.exists(), f"missing {path}"
        if name.endswith(".json") and name == "FINAL_STATUS.json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload.get("domain") == DOMAIN
