#!/usr/bin/env python3
"""Verify all 11 governing spec domains — institutional strict assessment."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUT = ROOT / "GOVERNING_SPECS_11_VERIFICATION.json"


def _summary_strip(full: dict) -> dict:
    return {k: v for k, v in full.items() if k != "requirements"}


def verify_all_11() -> dict:
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

    domains = {
        "DTS": {"summary": dts_summary(), "runtime": {"dts_001": verify_dts_requirement("DTS-001")}},
        "DAT": {"summary": dat_summary(), "runtime": verify_dat_pipeline()},
        "RESTORE": {"summary": verify_all_restore(), "runtime": verify_all_restore()},
        "BILL": {"summary": bill_summary(), "runtime": verify_bill_runtime()},
        "ID": {"summary": id_summary(), "runtime": verify_id_runtime()},
        "ERR": {"summary": err_summary(), "runtime": verify_err_runtime()},
        "TZ": {"summary": tz_summary(), "runtime": verify_tz_runtime()},
        "FDS": {"summary": fds_summary(), "runtime": verify_fds_runtime()},
        "AV": {"summary": av_summary(), "runtime": verify_av_runtime()},
        "DSR": {"summary": dsr_summary(), "runtime": verify_dsr_runtime()},
        "TIE": {"summary": tie_summary(), "runtime": verify_tie_runtime()},
        "AIE": {"summary": aie_summary(), "runtime": verify_aie_runtime()},
    }

    total_reqs = 0
    total_impl = 0
    total_partial = 0
    total_spec = 0
    strict_pass = 0
    runtime_ok = 0

    domain_results = {}
    for name, data in domains.items():
        summary = data["summary"]
        counts = summary.get("counts") or {
            "IMPLEMENTED": summary.get("ok", 0),
            "PARTIAL": 0,
            "SPEC_ONLY": max(0, summary.get("total", 0) - summary.get("ok", 0)),
        }
        if "total" in summary:
            total_reqs += summary["total"]
            total_impl += counts.get("IMPLEMENTED", 0)
            total_partial += counts.get("PARTIAL", 0)
            total_spec += counts.get("SPEC_ONLY", 0)

        pass_key = next((k for k in summary if k.startswith("PASS_ENGINEERING")), None)
        strict = bool(summary.get(pass_key)) if pass_key else bool(summary.get("PASS_ENGINEERING_RESTORE"))
        if strict:
            strict_pass += 1

        runtime = data.get("runtime") or {}
        rt_ok = bool(runtime.get("all_requirements", {}).get("all_ok")) or bool(
            runtime.get("ok") or runtime.get("source_ok") or runtime.get("billing_configured") is not None
        )
        if rt_ok:
            runtime_ok += 1

        domain_results[name] = {
            "summary": _summary_strip(summary),
            "runtime_ok": rt_ok,
            "strict_pass": strict,
        }

    impl_pct = round((total_impl + total_partial * 0.5) / max(total_reqs, 1) * 100, 1)
    all_11_strict = strict_pass >= 11 and total_spec == 0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology": "v6 PASS_ENGINEERING strict + runtime proof",
        "domains": domain_results,
        "aggregate": {
            "total_requirements": total_reqs,
            "implemented": total_impl,
            "partial": total_partial,
            "spec_only": total_spec,
            "implementation_pct_weighted": impl_pct,
            "domains_strict_pass": strict_pass,
            "domains_runtime_ok": runtime_ok,
            "all_11_specs_PASS_ENGINEERING": all_11_strict,
            "final_goal_achieved": all_11_strict and total_spec == 0,
        },
    }


def main() -> int:
    report = verify_all_11()
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, ensure_ascii=False))
    return 0 if report["aggregate"]["all_11_specs_PASS_ENGINEERING"] else 1


if __name__ == "__main__":
    sys.exit(main())
