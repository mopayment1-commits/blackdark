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

    dts = dts_summary()
    dat = dat_summary()
    restore = verify_all_restore()

    # G1 — truth baseline
    g1_ok = prod_aligned >= 100 and mock_stub < 200
    g1_partial = batch_ok and prod_aligned < 826

    # G4 — governance full
    g4_ok = dts["PASS_ENGINEERING_DTS"] and dat["PASS_ENGINEERING_DATA"] and restore["PASS_ENGINEERING_RESTORE"]
    g4_partial = dts["PASS_ENGINEERING_DTS_honest"] or dat["PASS_ENGINEERING_DATA_honest"]

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
        "G2_DEDUPLICATION": {"status": "PARTIAL", "note": "duplicate routing fixed; REUSED-LINK taxonomy open"},
        "G3_SPLIT_BRAIN": {"status": "PARTIAL", "note": "pdf→cap646 delegation for 58 IDs; manifest not fully cleared"},
        "G4_GOVERNANCE_FULL": {
            "status": _gate_status(g4_ok, g4_partial),
            "dts": {k: v for k, v in dts.items() if k != "requirements"},
            "dat": {k: v for k, v in dat.items() if k != "requirements"},
            "restore": {k: v for k, v in restore.items() if k != "results"},
        },
        "G5_BATCH_CLOSURE": {
            "status": _gate_status(g5_ok),
            "batch_verify_pass": batch_ok,
            "capabilities_verified": batch_total,
            "rescue_tier_rejected": True,
        },
        "G6_UI_E2E": {"status": "FAIL", "note": "No Playwright/browser E2E for signup/pay/decision paths"},
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
    pre_launch_ready = all(s == "PASS" for s in statuses)
    railway_deploy_allowed = pre_launch_ready and g8_ok

    wf_path = _ROOT / "docs/security/SECURITY_WORKFLOW_REGISTER.json"
    wf_data = json.loads(wf_path.read_text(encoding="utf-8")) if wf_path.exists() else {"workflows": []}
    wf_open = [w["id"] for w in wf_data.get("workflows", []) if w.get("status", "").startswith("OPEN")]
    secrets_report = _load_json("SECRETS_HYGIENE_REPORT.json") or {}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "program": "PRE_LAUNCH_INSTITUTIONAL_COMPLETION",
        "pre_launch_ready": pre_launch_ready,
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
        },
    }
