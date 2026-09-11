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
    "summary_fn,strict_key,honest_key,min_total",
    [
        (dts_summary, "PASS_ENGINEERING_DTS", "PASS_ENGINEERING_DTS_honest", 60),
        (dat_summary, "PASS_ENGINEERING_DATA", "PASS_ENGINEERING_DATA_honest", 18),
        (bill_summary, "PASS_ENGINEERING_BILL", "PASS_ENGINEERING_BILL_honest", 60),
        (id_summary, "PASS_ENGINEERING_ID", "PASS_ENGINEERING_ID_honest", 70),
        (err_summary, "PASS_ENGINEERING_ERR", "PASS_ENGINEERING_ERR_honest", 50),
        (tz_summary, "PASS_ENGINEERING_TZ", "PASS_ENGINEERING_TZ_honest", 35),
        (fds_summary, "PASS_ENGINEERING_FDS", "PASS_ENGINEERING_FDS_honest", 24),
        (av_summary, "PASS_ENGINEERING_AV", "PASS_ENGINEERING_AV_honest", 29),
        (dsr_summary, "PASS_ENGINEERING_DSR", "PASS_ENGINEERING_DSR_honest", 23),
        (tie_summary, "PASS_ENGINEERING_TIE", "PASS_ENGINEERING_TIE_honest", 19),
        (aie_summary, "PASS_ENGINEERING_AIE", "PASS_ENGINEERING_AIE_honest", 19),
    ],
)
def test_governing_spec_spine_no_spec_only(summary_fn, strict_key, honest_key, min_total):
    summary = summary_fn()
    assert summary["total"] >= min_total
    assert summary["counts"]["SPEC_ONLY"] == 0
    assert summary[strict_key] is True
    assert summary[honest_key] is True


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


@pytest.mark.parametrize(
    "runtime_fn",
    [
        verify_bill_runtime,
        verify_id_runtime,
        verify_err_runtime,
        verify_tz_runtime,
        verify_fds_runtime,
        verify_av_runtime,
        verify_dsr_runtime,
        verify_tie_runtime,
        verify_aie_runtime,
    ],
)
def test_domain_runtime_proof(runtime_fn):
    result = runtime_fn()
    assert result["all_requirements"]["all_ok"] is True
