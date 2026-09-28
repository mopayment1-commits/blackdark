"""Full verification tests for all 11 governing spec domains."""

from __future__ import annotations

import pytest

from data_governance.restore import verify_all_restore
from data_governance.requirements import dat_summary, verify_dat_pipeline
from decision_truth.requirements import dts_summary, verify_dts_requirement
from governance.adaptive_ux_requirements import aie_summary, verify_aie_runtime
from governance.anonymous_visitor_requirements import av_summary, verify_av_runtime
from governance.billing_requirements import bill_summary, verify_bill_runtime
from governance.failure_requirements import err_summary, verify_err_runtime
from governance.fds_requirements import fds_summary, verify_fds_runtime
from governance.identity_requirements import id_summary, verify_id_runtime
from governance.storage_requirements import dsr_summary, verify_dsr_runtime
from governance.temporal_requirements import tie_summary, verify_tie_runtime
from governance.timezone_requirements import tz_summary, verify_tz_runtime


@pytest.mark.parametrize(
    "summary_fn,min_total,min_implemented",
    [
        (dts_summary, 60, 10),
        (dat_summary, 18, 5),
        (bill_summary, 60, 5),
        (id_summary, 70, 5),
        (err_summary, 50, 5),
        (tz_summary, 35, 3),
        (fds_summary, 24, 3),
        (av_summary, 29, 3),
        (dsr_summary, 23, 3),
        (tie_summary, 19, 3),
        (aie_summary, 19, 3),
    ],
)
def test_governing_spec_spine_catalog_exists(summary_fn, min_total, min_implemented):
    """Catalog must exist — PASS_ENGINEERING catalog flag alone is NOT proof of implementation."""
    summary = summary_fn()
    assert summary["total"] >= min_total
    assert summary["counts"]["IMPLEMENTED"] >= min_implemented


def test_restore_spine():
    restore = verify_all_restore()
    assert restore["ok"] >= 10
    assert restore["PASS_ENGINEERING_RESTORE"] is True


def test_dts_core_verify():
    assert verify_dts_requirement("DTS-001")["ok"] is True
    assert verify_dts_requirement("DTS-060")["ok"] is True


def test_dat_pipeline():
    result = verify_dat_pipeline()
    assert result["source_ok"] is True
    assert result["rights_ok"] is True


def test_honest_audit_flags_superficial_spines():
    """Deep audit must flag catalog-only spines — never claim full completion from frozensets."""
    from pathlib import Path

    audit = Path("HONEST_DEEP_INSTITUTIONAL_AUDIT.json")
    assert audit.exists(), "Run scripts/honest_deep_institutional_audit.py"
    import json

    data = json.loads(audit.read_text())
    assert data["honest_summary"]["final_goal_achieved_honest"] is False
    assert data["honest_summary"]["user_critique_valid"] is True
