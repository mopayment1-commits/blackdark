"""B15 temporal batch — Phase 8 integrated reconciliation (SPEC §37–§42)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
GENERATOR = GOV / "generate_b15_temporal_reconciliation.py"
RECON_PATH = GOV / "BLACKDARK_LAUNCH57_TEMPORAL_CONSISTENCY_RECONCILIATION.json"
REPORT_PATH = GOV / "BLACKDARK_LAUNCH57_TEMPORAL_CONSISTENCY_REPORT.md"

IV_FILES = {
    "B1": "B1_TEMPORAL_INDEPENDENT_VERIFICATION.json",
    "B2": "B2_40_INDEPENDENT_VERIFICATION.json",
    "B3": "B3_6_TRUST_BOUNDARY_INDEPENDENT_VERIFICATION.json",
    "B4": "B4_TEMPORAL_INDEPENDENT_VERIFICATION.json",
    "B5": "B5_TEMPORAL_INDEPENDENT_VERIFICATION.json",
    "B6": "B6_TEMPORAL_INDEPENDENT_VERIFICATION.json",
    "B7": "B7_TEMPORAL_INDEPENDENT_VERIFICATION.json",
    "B8": "B8_TEMPORAL_INDEPENDENT_VERIFICATION.json",
    "B9": "B9_TEMPORAL_INDEPENDENT_VERIFICATION.json",
    "B10": "B10_TEMPORAL_INDEPENDENT_VERIFICATION.json",
    "B11": "B11_TEMPORAL_INDEPENDENT_VERIFICATION.json",
    "B12": "B12_TEMPORAL_INDEPENDENT_VERIFICATION.json",
    "B13": "B13_TEMPORAL_INDEPENDENT_VERIFICATION.json",
    "B14": "B14_TEMPORAL_INDEPENDENT_VERIFICATION.json",
}

VERDICT_KEYS = {
    "B1": "B1_INDEPENDENT_VERDICT",
    "B2": "B2_INDEPENDENT_VERDICT",
    "B3": "B3_INDEPENDENT_VERDICT",
    "B4": "B4_INDEPENDENT_VERDICT",
    "B5": "B5_INDEPENDENT_VERDICT",
    "B6": "B6_INDEPENDENT_VERDICT",
    "B7": "B7_INDEPENDENT_VERDICT",
    "B8": "B8_INDEPENDENT_VERDICT",
    "B9": "B9_INDEPENDENT_VERDICT",
    "B10": "B10_INDEPENDENT_VERDICT",
    "B11": "B11_INDEPENDENT_VERDICT",
    "B12": "B12_INDEPENDENT_VERDICT",
    "B13": "B13_INDEPENDENT_VERDICT",
    "B14": "B14_INDEPENDENT_VERDICT",
}

REPORT_SECTIONS = list("ABCDEFGHIJKLMNOPQRSTU")
B15_IV_PATH = GOV / "B15_TEMPORAL_INDEPENDENT_VERIFICATION.json"

FINDING_BUCKETS = [
    "naive_datetime_findings",
    "timezone_errors",
    "stale_live_inconsistencies",
    "ordering_failures",
    "point_in_time_violations",
    "lookahead_violations",
    "dst_failures",
    "chart_inconsistencies",
    "alert_timing_failures",
    "decision_timestamp_failures",
    "timestamp_precision_unit_violations",
    "equal_time_ordering_defects",
    "provider_clock_skew_defects",
    "host_clock_skew_defects",
    "availability_time_unknown_or_fabrication_findings",
    "dst_gap_fold_failures",
    "tzdb_version_update_findings",
    "recurrence_failures",
    "leap_second_policy_failures",
    "api_database_serialization_defects",
]


def test_all_b1_b14_iv_artifacts_exist():
    for batch, fname in IV_FILES.items():
        assert (GOV / fname).is_file(), f"missing IV artifact for {batch}"


def test_all_b1_b14_iv_verdicts_pass_engineering():
    for batch, fname in IV_FILES.items():
        iv = json.loads((GOV / fname).read_text(encoding="utf-8"))
        key = VERDICT_KEYS[batch]
        verdict = iv.get(key) or iv.get("verdict_table", {}).get(key)
        assert verdict == "PASS_ENGINEERING", f"{batch} verdict={verdict}"


def test_b14_entry_gate_met():
    iv = json.loads((GOV / "B14_TEMPORAL_INDEPENDENT_VERIFICATION.json").read_text(encoding="utf-8"))
    assert iv["B14_INDEPENDENT_VERDICT"] == "PASS_ENGINEERING"
    assert iv["entry_gate"]["B13_INDEPENDENT_VERDICT"] == "PASS_ENGINEERING"


@pytest.mark.parametrize("batch", list(IV_FILES.keys()))
def test_iv_artifacts_reference_pass_live_not_claimed(batch: str):
    iv = json.loads((GOV / IV_FILES[batch]).read_text(encoding="utf-8"))
    if "PASS_LIVE_NOT_CLAIMED" in iv:
        assert iv["PASS_LIVE_NOT_CLAIMED"] is True


def _expected_final_verdict_fields() -> dict:
    """Expected §42 fields: IV closure when B15 IV PASS exists, else builder pending."""
    if B15_IV_PATH.is_file():
        iv = json.loads(B15_IV_PATH.read_text(encoding="utf-8"))
        if (
            iv.get("B15_INDEPENDENT_VERDICT") == "PASS_ENGINEERING"
            and iv.get("LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING") is True
        ):
            return {
                "LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING": True,
                "LAUNCH57_TEMPORAL_CONSISTENCY_READY_FOR_LOCAL_USE": iv.get(
                    "LAUNCH57_TEMPORAL_CONSISTENCY_READY_FOR_LOCAL_USE", True
                ),
                "PASS_LIVE_NOT_CLAIMED": True,
                "PASS_ENGINEERING_NOT_CLAIMED": False,
                "B15_IMPLEMENTATION_STATUS": iv.get("B15_IMPLEMENTATION_STATUS", "PASS_ENGINEERING"),
                "B15_INDEPENDENT_VERDICT": "PASS_ENGINEERING",
                "final_status": "B15_INTEGRATED_RECONCILIATION_PASS_ENGINEERING",
            }
    return {
        "LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING": False,
        "LAUNCH57_TEMPORAL_CONSISTENCY_READY_FOR_LOCAL_USE": False,
        "PASS_LIVE_NOT_CLAIMED": True,
        "PASS_ENGINEERING_NOT_CLAIMED": True,
        "B15_IMPLEMENTATION_STATUS": "PENDING_VERIFICATION",
        "B15_INDEPENDENT_VERDICT": "PENDING_VERIFICATION",
        "final_status": "B15_INTEGRATED_RECONCILIATION_PENDING_VERIFICATION",
    }


def test_generator_produces_reconciliation_artifacts():
    proc = subprocess.run(
        ["python3", str(GENERATOR)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert RECON_PATH.is_file()
    assert REPORT_PATH.is_file()


def test_reconciliation_json_required_fields():
    subprocess.run(["python3", str(GENERATOR)], cwd=ROOT, check=True)
    recon = json.loads(RECON_PATH.read_text(encoding="utf-8"))
    expected = _expected_final_verdict_fields()
    assert recon["artifact"] == "BLACKDARK_LAUNCH57_TEMPORAL_CONSISTENCY_RECONCILIATION"
    assert recon["batch"] == "B15"
    assert recon["all_batches_b1_b14_pass_engineering"] is True
    assert recon["LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING"] == expected[
        "LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING"
    ]
    assert recon["PASS_LIVE_NOT_CLAIMED"] is True
    assert recon["PASS_ENGINEERING_NOT_CLAIMED"] == expected["PASS_ENGINEERING_NOT_CLAIMED"]
    assert recon["B15_IMPLEMENTATION_STATUS"] == expected["B15_IMPLEMENTATION_STATUS"]
    assert recon["B15_INDEPENDENT_VERDICT"] == expected["B15_INDEPENDENT_VERDICT"]
    assert recon["final_status"] == expected["final_status"]
    for bucket in FINDING_BUCKETS:
        assert bucket in recon
    assert recon["integrated_temporal_reconciliation_pass"] is True
    assert recon["unresolved_cross_batch_timestamp_conflicts"] == []


def test_reconciliation_matches_b15_iv_when_closure_active():
    if not B15_IV_PATH.is_file():
        pytest.skip("B15 IV artifact not present")
    iv = json.loads(B15_IV_PATH.read_text(encoding="utf-8"))
    if iv.get("B15_INDEPENDENT_VERDICT") != "PASS_ENGINEERING":
        pytest.skip("B15 IV closure not active")
    subprocess.run(["python3", str(GENERATOR)], cwd=ROOT, check=True)
    recon = json.loads(RECON_PATH.read_text(encoding="utf-8"))
    assert recon["B15_INDEPENDENT_VERDICT"] == iv["B15_INDEPENDENT_VERDICT"]
    assert recon["LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING"] == iv[
        "LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING"
    ]
    assert recon["PASS_LIVE_NOT_CLAIMED"] is True
    assert len(recon["external_blockers"]) == 6
    assert all(b["status"] == "NEEDS_EXTERNAL_VERIFICATION" for b in recon["external_blockers"])


def test_report_contains_sections_a_through_u():
    subprocess.run(["python3", str(GENERATOR)], cwd=ROOT, check=True)
    report = REPORT_PATH.read_text(encoding="utf-8")
    for section in REPORT_SECTIONS:
        assert f"## {section}." in report


def test_integrated_b1_b14_test_suite_passes():
    cmd = ["python3", "-m", "pytest"] + [f"tests/launch57/test_temporal_batch{n}.py" for n in range(1, 15)] + ["-q"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "failed" not in proc.stdout.lower() or "0 failed" in proc.stdout
