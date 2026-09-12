"""Pre-launch governance requirement spine tests."""

from __future__ import annotations

from decision_truth.requirements import dts_summary, verify_dts_requirement
from data_governance.requirements import dat_summary, verify_dat_pipeline
from data_governance.restore import verify_all_restore
from governance.assessor import assess_pre_launch_gates


def test_dts_spine_has_core_requirements():
    summary = dts_summary()
    assert summary["total"] >= 3
    assert summary["counts"]["IMPLEMENTED"] >= 3
    assert verify_dts_requirement("DTS-001")["ok"]


def test_dat_and_restore_spine():
    dat = dat_summary()
    assert dat["total"] >= 3
    pipeline = verify_dat_pipeline()
    assert pipeline["source_ok"] and pipeline["rights_ok"]
    restore = verify_all_restore()
    assert restore["ok"] >= 8


def test_pre_launch_assessor_emits_gates():
    report = assess_pre_launch_gates()
    assert "G1_TRUTH_BASELINE" in report["gates"]
    assert report["PASS_LIVE_NOT_CLAIMED"] is True
    assert report["railway_deploy_allowed"] is False
