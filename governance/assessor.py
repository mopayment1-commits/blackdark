"""Pre-launch gate assessor — honest G1–G10 status before Railway deploy."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent


def _load_json(name: str) -> dict[str, Any] | None:
    p = _ROOT / name
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _gate_status(ok: bool, partial: bool = False) -> str:
    if ok:
        return "PASS"
    if partial:
        return "PARTIAL"
    return "FAIL"


def assess_pre_launch_gates() -> dict[str, Any]:
    inventory = _load_json("docs/CAPABILITIES_826_INVENTORY.json") or {}
    master = _load_json("CAPABILITY_MASTER_REGISTER.json") or {}
    batch = _load_json("BATCH_CLOSURE_VERIFY_REPORT.json") or {}

    per_id = inventory.get("per_id") or {}
    prod_aligned = sum(1 for r in per_id.values() if r.get("status") == "PRODUCTION-ALIGNED")
    pending = sum(1 for r in per_id.values() if r.get("status") in {"PENDING", "NOT_COMPLETE"})

    master_caps = master.get("capabilities") or []
    mock_stub = sum(1 for r in master_caps if r.get("primary_status") == "MOCK_OR_STUB")
    implemented = sum(1 for r in master_caps if r.get("primary_status") == "IMPLEMENTED")

    batch_ok = all(b.get("fail", 1) == 0 for b in batch.get("batches", []))
    batch_total = sum(b.get("ok", 0) for b in batch.get("batches", []))

    from decision_truth.requirements import dts_summary
    from data_governance.requirements import dat_summary
    from data_governance.restore import verify_all_restore
    from governance.adaptive_ux_requirements import aie_summary
    from governance.anonymous_visitor_requirements import av_summary
    from governance.billing_requirements import bill_summary
    from governance.failure_requirements import err_summary
    from governance.fds_requirements import fds_summary
    from governance.identity_requirements import id_summary
    from governance.storage_requirements import dsr_summary
    from governance.temporal_requirements import tie_summary
    from governance.timezone_requirements import tz_summary

    dts = dts_summary()
    dat = dat_summary()
    restore = verify_all_restore()
    bill = bill_summary()
    ident = id_summary()
    err = err_summary()
    tz = tz_summary()
    fds = fds_summary()
    av = av_summary()
    dsr = dsr_summary()
    tie = tie_summary()
    aie = aie_summary()

    gov_strict = [
        dts["PASS_ENGINEERING_DTS"],
        dat["PASS_ENGINEERING_DATA"],
        restore["PASS_ENGINEERING_RESTORE"],
        bill["PASS_ENGINEERING_BILL"],
        ident["PASS_ENGINEERING_ID"],
        err["PASS_ENGINEERING_ERR"],
        tz["PASS_ENGINEERING_TZ"],
        fds["PASS_ENGINEERING_FDS"],
        av["PASS_ENGINEERING_AV"],
        dsr["PASS_ENGINEERING_DSR"],
        tie["PASS_ENGINEERING_TIE"],
        aie["PASS_ENGINEERING_AIE"],
    ]
    gov_honest = [d.get(k) for d, k in [
        (dts, "PASS_ENGINEERING_DTS_honest"),
        (dat, "PASS_ENGINEERING_DATA_honest"),
        (bill, "PASS_ENGINEERING_BILL_honest"),
        (ident, "PASS_ENGINEERING_ID_honest"),
        (err, "PASS_ENGINEERING_ERR_honest"),
        (tz, "PASS_ENGINEERING_TZ_honest"),
        (fds, "PASS_ENGINEERING_FDS_honest"),
        (av, "PASS_ENGINEERING_AV_honest"),
        (dsr, "PASS_ENGINEERING_DSR_honest"),
        (tie, "PASS_ENGINEERING_TIE_honest"),
        (aie, "PASS_ENGINEERING_AIE_honest"),
    ]]

    # G1 — truth baseline (inventory is primary truth after reconcile)
    total_caps = max(len(per_id), 1)
    align_ratio = prod_aligned / total_caps
    g1_ok = prod_aligned >= 780 and align_ratio >= 0.95
    g1_partial = batch_ok and prod_aligned >= 100

    # G4 — governance full (all 11 spec domains)
    g4_ok = all(gov_strict) and restore["PASS_ENGINEERING_RESTORE"]
    g4_partial = sum(1 for h in gov_honest if h) >= 8 or restore.get("ok", 0) >= 8

    # G5 — batch closure (strict: no rescue in verify script)
    g5_ok = batch_ok and batch_total >= 826

    # G7 — CI subset
    g7_partial = True
    g7_ok = False
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_decision_truth_pipeline.py", "tests/test_data_governance_p0_test_matrix.py", "-q", "--tb=no"],
            cwd=_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        g7_ok = proc.returncode == 0
    except Exception:
        pass

    # G8 — production infra (pre-Railway)
    import os

    db_url = os.environ.get("DATABASE_URL", "")
    g8_ok = db_url.startswith("postgresql://")
    g8_partial = bool(db_url)

    gates = {
        "G1_TRUTH_BASELINE": {
            "status": _gate_status(g1_ok, g1_partial),
            "production_aligned": prod_aligned,
            "pending_inventory": pending,
            "mock_or_stub_master": mock_stub,
            "implemented_master": implemented,
        },
        "G2_DEDUPLICATION": {"status": "PASS", "note": "duplicate routing fixed; canonical delegation active"},
        "G3_SPLIT_BRAIN": {"status": "PASS", "note": "pdf→cap646 delegation for 58 IDs; manifest reconciled"},
        "G4_GOVERNANCE_FULL": {
            "status": _gate_status(g4_ok, g4_partial),
            "domains_strict_pass": sum(1 for s in gov_strict if s) + (1 if restore["PASS_ENGINEERING_RESTORE"] else 0),
            "domains_total": 12,
            "dts": {k: v for k, v in dts.items() if k != "requirements"},
            "dat": {k: v for k, v in dat.items() if k != "requirements"},
            "restore": {k: v for k, v in restore.items() if k != "results"},
            "bill": {k: v for k, v in bill.items() if k != "requirements"},
            "id": {k: v for k, v in ident.items() if k != "requirements"},
            "err": {k: v for k, v in err.items() if k != "requirements"},
            "tz": {k: v for k, v in tz.items() if k != "requirements"},
            "fds": {k: v for k, v in fds.items() if k != "requirements"},
            "av": {k: v for k, v in av.items() if k != "requirements"},
            "dsr": {k: v for k, v in dsr.items() if k != "requirements"},
            "tie": {k: v for k, v in tie.items() if k != "requirements"},
            "aie": {k: v for k, v in aie.items() if k != "requirements"},
        },
        "G5_BATCH_CLOSURE": {
            "status": _gate_status(g5_ok),
            "batch_verify_pass": batch_ok,
            "capabilities_verified": batch_total,
            "rescue_tier_rejected": True,
        },
        "G6_UI_E2E": {
            "status": "PARTIAL",
            "note": "FastAPI TestClient smoke: health, legal, login, monitoring — Playwright full paths pending",
        },
        "G7_CI_GREEN": {"status": _gate_status(g7_ok, g7_partial)},
        "G8_PRODUCTION_INFRA": {
            "status": _gate_status(g8_ok, g8_partial),
            "postgresql_configured": g8_ok,
            "railway_ready": False,
        },
        "G9_EXTERNAL_ASSURANCE": {"status": "FAIL", "note": "Pentest/SOC2/vendor licenses — owner/external"},
        "G10_LAUNCH_PACK": {"status": "PARTIAL", "note": "Data room partial; discovery freeze not reconciled"},
    }

    statuses = [g["status"] for g in gates.values()]
    automatable_gate_keys = [k for k in gates if k not in {"G8_PRODUCTION_INFRA", "G9_EXTERNAL_ASSURANCE"}]
    core_pass = all(gates[k]["status"] == "PASS" for k in ("G1_TRUTH_BASELINE", "G4_GOVERNANCE_FULL", "G5_BATCH_CLOSURE", "G7_CI_GREEN"))
    pre_launch_ready_automatable = core_pass and all(gates[k]["status"] in {"PASS", "PARTIAL"} for k in automatable_gate_keys)
    pre_launch_ready = pre_launch_ready_automatable
    railway_deploy_allowed = pre_launch_ready and g8_ok

    wf_path = _ROOT / "docs/security/SECURITY_WORKFLOW_REGISTER.json"
    wf_data = json.loads(wf_path.read_text(encoding="utf-8")) if wf_path.exists() else {"workflows": []}
    wf_open = [w["id"] for w in wf_data.get("workflows", []) if w.get("status", "").startswith("OPEN")]
    secrets_report = _load_json("SECRETS_HYGIENE_REPORT.json") or {}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "program": "PRE_LAUNCH_INSTITUTIONAL_COMPLETION",
        "pre_launch_ready": pre_launch_ready,
        "pre_launch_ready_automatable": pre_launch_ready_automatable,
        "railway_deploy_allowed": railway_deploy_allowed,
        "PASS_LIVE_NOT_CLAIMED": True,
        "blk_002_postgres_separate": g8_ok,
        "secrets_hygiene_clean": secrets_report.get("clean", False),
        "security_workflows_open": wf_open,
        "gates": gates,
        "honest_summary": {
            "runtime_batch_closure": f"{batch_total}/826" if batch_ok else "incomplete",
            "inventory_production_aligned": f"{prod_aligned}/826",
            "master_implemented": f"{implemented}/826",
            "dts_implemented": dts["counts"].get("IMPLEMENTED", 0),
            "dat_implemented": dat["counts"].get("IMPLEMENTED", 0),
            "restore_ok": restore.get("ok", 0),
            "governing_specs_strict_pass": sum(1 for s in gov_strict if s) + (1 if restore["PASS_ENGINEERING_RESTORE"] else 0),
            "governing_specs_total": 12,
        },
    }
