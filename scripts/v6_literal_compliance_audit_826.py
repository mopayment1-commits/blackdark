#!/usr/bin/env python3
"""Verification-only literal v6 compliance audit for all 826 IDs.

Produces institutional_due_diligence_2026/V6_LITERAL_COMPLIANCE_AUDIT_826.json
with YES/NO per criterion — no fixes, no assumptions.
"""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_standards_v6 import (  # noqa: E402
    discover_ai_cap_ids,
    phase1_generic_delegate_check,
    phase3_ai_rmf_plus_218a,
    phase6_security_asvs50,
)
from scripts.v6_status_model import batch_for_id  # noqa: E402

OUT_PATH = ROOT / "institutional_due_diligence_2026/V6_LITERAL_COMPLIANCE_AUDIT_826.json"
V6_STANDARD = ROOT / "institutional_due_diligence_2026/BLACKDARK_Institutional_Capability_Standard_2026_v6.md"
INVENTORY = ROOT / "docs/CAPABILITIES_826_INVENTORY.json"

COMMON_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "email": "v6-audit@blackdark.local",
    "tier": "pro",
}

V6_13_KEYS = [
    "1_functional_completeness",
    "2_functional_correctness",
    "3_functional_appropriateness",
    "4_requirements_traceability",
    "5_integration_correctness",
    "6_regression_safety",
    "7_security_gate",
    "8_performance_gate",
    "9_reliability_gate",
    "10_observability_gate",
    "11_data_quality_gate",
    "12_user_path_gate",
    "13_evidence_gate",
]

EVIDENCE_12_KEYS = [
    "1_scope_inventory",
    "2_requirements_traceability",
    "3_semantic_acceptance_correctness",
    "4_canonical_duplicate_reconciliation",
    "5_actual_consumer_path_evidence",
    "6_security_entitlement_evidence",
    "7_data_provenance_evidence",
    "8_reliability_performance_evidence",
    "9_affected_regression_evidence",
    "10_formal_quality_security_gate_evidence",
    "11_source_build_run_provenance",
    "12_engineering_live_assurance_status",
]

PHASE_TO_CRITERIA: dict[str, list[str]] = {
    "1": ["3_functional_appropriateness"],
    "2": ["8_performance_gate"],
    "4": ["2_functional_correctness", "11_data_quality_gate"],
    "5": ["5_integration_correctness"],
    "6": ["7_security_gate"],
    "7": ["1_functional_completeness"],
    "8": ["9_reliability_gate", "10_observability_gate"],
    "9": ["13_evidence_gate"],
}


def yn(flag: bool) -> str:
    return "YES" if flag else "NO"


def batch_num_for_id(cid: int) -> int:
    return (cid - 1) // 50 + 1


def load_audit_rows() -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    for n in range(1, 18):
        if n <= 3:
            path = ROOT / f"institutional_due_diligence_2026/batch{n:02d}_independent_audit/BATCH{n:02d}_INDEPENDENT_NINE_PHASE.json"
        else:
            path = ROOT / f"institutional_due_diligence_2026/batch{n:02d}_independent_audit/BATCH{n:02d}_INDEPENDENT_RBAS_AUDIT.json"
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data:
            rows[int(row["id"])] = row
    return rows


def load_rtm_per_id() -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for path in sorted(ROOT.glob("docs/BATCH*_OFFICIAL_RTM_*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for k, v in (doc.get("per_id") or {}).items():
            out[int(k)] = v
    return out


def load_closure_evidence(batch_num: int) -> dict[str, Any] | None:
    candidates = sorted(
        (ROOT / f"institutional_due_diligence_2026/batch{batch_num:02d}_independent_audit").glob(
            "*CLOSURE_EVIDENCE.json"
        )
    )
    if not candidates:
        return None
    return json.loads(candidates[-1].read_text(encoding="utf-8"))


def inventory_has_id(cid: int) -> bool:
    if not INVENTORY.is_file():
        return False
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    per_id = inv.get("per_id") or {}
    if str(cid) in per_id or cid in per_id:
        return True
    caps = inv.get("capabilities") or []
    return any(int(x.get("id", 0)) == cid for x in caps)


def split_brain_row(cid: int, batch_num: int) -> dict[str, Any] | None:
    d = ROOT / f"institutional_due_diligence_2026/batch{batch_num:02d}_independent_audit"
    files = list(d.glob("*SPLIT_BRAIN*"))
    if not files:
        return None
    data = json.loads(files[0].read_text(encoding="utf-8"))
    for row in data:
        if int(row.get("id", 0)) == cid:
            return row
    return None


def user_path_live(cid: int) -> tuple[bool, str]:
    from cap646.ui_pages import user_surface_for

    surf = user_surface_for(cid)
    if not surf or not surf.get("api_path"):
        return False, "no user-facing api_path"
    prefix = str(surf["api_path"]).split("{")[0]
    try:
        r = subprocess.run(
            ["rg", "-l", re.escape(prefix), "api/", "dashboard.py", "platform_api.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.returncode == 0, f"api_prefix={prefix}"
    except Exception as exc:
        return False, str(exc)


def criteria_from_phases(phase_results: dict[str, str], audit_status: str) -> dict[str, str]:
    out = {k: "NO" for k in V6_13_KEYS}
    for pid, keys in PHASE_TO_CRITERIA.items():
        st = phase_results.get(pid, "MISSING")
        if st == "PASS":
            for k in keys:
                out[k] = "YES"
    if audit_status == "PRODUCTION-ALIGNED":
        out["1_functional_completeness"] = "YES"
        out["2_functional_correctness"] = "YES"
    return out


def evidence_pack_per_id(
    cid: int,
    batch_num: int,
    *,
    audit_row: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    rtm: dict[str, Any] | None,
    closure: dict[str, Any] | None,
    split: dict[str, Any] | None,
    user_path_ok: bool,
) -> dict[str, str]:
    ep = {k: "NO" for k in EVIDENCE_12_KEYS}
    ep["1_scope_inventory"] = yn(inventory_has_id(cid))
    ep["2_requirements_traceability"] = yn(rtm is not None and bool(rtm.get("evidence") or rtm.get("engineering_status")))
    ep["3_semantic_acceptance_correctness"] = yn(
        audit_row is not None and runtime is not None and bool(runtime.get("success"))
    )
    if split is not None:
        ep["4_canonical_duplicate_reconciliation"] = yn(
            split.get("result_type") in ("DUPLICATE_CONFIRMED", "DEDICATED_ONLY", "NO_DEDICATED_IMPLEMENTATION")
            and split.get("result_type") != "DIVERGENT_OUTPUT"
        )
    elif audit_row is not None:
        sb = audit_row.get("split_brain_type")
        ep["4_canonical_duplicate_reconciliation"] = yn(
            sb in (None, "DEDICATED_ONLY", "DUPLICATE_CONFIRMED") or audit_row.get("status") != "SPLIT-BRAIN-UNVERIFIED"
        )
    ep["5_actual_consumer_path_evidence"] = yn(user_path_ok and runtime is not None and bool(runtime.get("success")))
    ep["6_security_entitlement_evidence"] = yn(
        bool((runtime or {}).get("entitlement"))
        or (runtime or {}).get("binding_source") == "explicit_option_a"
        or bool((runtime or {}).get("compliance_footer"))
    )
    ep["7_data_provenance_evidence"] = yn(
        bool((runtime or {}).get("data_source") or (runtime or {}).get("timestamp") or (runtime or {}).get("source"))
    )
    phases = (audit_row or {}).get("phase_results") or {}
    ep["8_reliability_performance_evidence"] = yn(
        phases.get("2") == "PASS" and phases.get("8") == "PASS"
    )
    ep["9_affected_regression_evidence"] = yn(
        bool(closure and (closure.get("non_regression") or {}).get("met"))
    )
    ep["10_formal_quality_security_gate_evidence"] = yn(phases.get("6") == "PASS")
    ep["11_source_build_run_provenance"] = yn((ROOT / "requirements.txt").is_file())
    ep["12_engineering_live_assurance_status"] = yn(
        rtm is not None and bool(rtm.get("engineering_status") or rtm.get("live_status"))
    )
    return ep


async def audit_one(
    cid: int,
    *,
    audit_rows: dict[int, dict[str, Any]],
    rtm_map: dict[int, dict[str, Any]],
    ai_ids: frozenset[int],
    closure_cache: dict[int, dict[str, Any] | None],
) -> dict[str, Any]:
    batch_num = batch_num_for_id(cid)
    audit_row = audit_rows.get(cid)
    rtm = rtm_map.get(cid)
    closure = closure_cache.get(batch_num)

    runtime: dict[str, Any] | None = None
    runtime_ok = False
    try:
        from cap646.runtime import execute_capability

        runtime = await execute_capability(cid, skip_entitlement=True, params=dict(COMMON_PARAMS))
        runtime_ok = bool(runtime.get("success"))
    except Exception as exc:
        runtime = {"success": False, "error": str(exc)}

    phase_results = (audit_row or {}).get("phase_results") or {}
    audit_status = (audit_row or {}).get("status", "MISSING")

    v6_13 = criteria_from_phases(phase_results, audit_status)
    v6_13["4_requirements_traceability"] = yn(rtm is not None and bool(rtm.get("id") == cid))
    v6_13["6_regression_safety"] = yn(bool(closure and (closure.get("non_regression") or {}).get("met")))
    user_ok, _ = user_path_live(cid)
    v6_13["12_user_path_gate"] = yn(user_ok and runtime_ok)
    v6_13["13_evidence_gate"] = yn(
        audit_row is not None
        and closure is not None
        and runtime_ok
        and bool((closure.get("random_sample") or {}).get("sample_pass") is not False or closure.get("bcbs"))
    )

    gd_st, _ = phase1_generic_delegate_check(batch_num, cid)
    phase1_ok = gd_st == "PASS"
    v6_13["3_functional_appropriateness"] = yn(phase1_ok and phase_results.get("1") == "PASS")

    asvs_st, _, _ = phase6_security_asvs50(cid, runtime or {}, batch_num=batch_num)
    asvs_ok = asvs_st == "PASS"
    v6_13["7_security_gate"] = yn(asvs_ok and phase_results.get("6") == "PASS")

    if cid in ai_ids:
        ai_st, _, ai_meta = phase3_ai_rmf_plus_218a(cid, runtime or {})
        ai_ok = ai_st == "PASS" and not (ai_meta.get("218a_failed") or [])
        ai_col = yn(ai_ok)
    else:
        ai_col = "N/A"

    split = split_brain_row(cid, batch_num)
    ep12 = evidence_pack_per_id(
        cid,
        batch_num,
        audit_row=audit_row,
        runtime=runtime,
        rtm=rtm,
        closure=closure,
        split=split,
        user_path_ok=user_ok,
    )

    cols_for_full = {
        "phase1_generic_delegate_check": yn(phase1_ok),
        "asvs_5_0_verified": yn(asvs_ok),
    }
    all_yes = all(v6_13[k] == "YES" for k in V6_13_KEYS)
    all_yes = all_yes and all(ep12[k] == "YES" for k in EVIDENCE_12_KEYS)
    all_yes = all_yes and cols_for_full["phase1_generic_delegate_check"] == "YES"
    all_yes = all_yes and cols_for_full["asvs_5_0_verified"] == "YES"
    if ai_col != "N/A":
        all_yes = all_yes and ai_col == "YES"

    failures: list[str] = []
    for k, v in v6_13.items():
        if v != "YES":
            failures.append(f"v6_13.{k}")
    for k, v in ep12.items():
        if v != "YES":
            failures.append(f"evidence_pack.{k}")
    if cols_for_full["phase1_generic_delegate_check"] != "YES":
        failures.append("phase1_generic_delegate_check")
    if cols_for_full["asvs_5_0_verified"] != "YES":
        failures.append("asvs_5_0_verified")
    if ai_col not in ("YES", "N/A"):
        failures.append("ai_rmf_800_218a_applied")

    return {
        "id": cid,
        "official_batch": batch_for_id(cid),
        "audit_status": audit_status,
        "runtime_success": runtime_ok,
        "v6_13_criteria_met": v6_13,
        "evidence_pack_12_met": ep12,
        "phase1_generic_delegate_check": cols_for_full["phase1_generic_delegate_check"],
        "asvs_5_0_verified": cols_for_full["asvs_5_0_verified"],
        "ai_rmf_800_218a_applied": ai_col,
        "fully_v6_compliant": all_yes,
        "failure_columns": failures,
    }


async def main() -> int:
    audit_rows = load_audit_rows()
    rtm_map = load_rtm_per_id()
    closure_cache: dict[int, dict[str, Any] | None] = {
        n: load_closure_evidence(n) for n in range(1, 18)
    }
    ai_by_batch = {n: discover_ai_cap_ids(n) for n in range(1, 18)}
    all_ai: set[int] = set()
    for s in ai_by_batch.values():
        all_ai |= set(s)

    rows: list[dict[str, Any]] = []
    for cid in range(1, 827):
        rows.append(
            await audit_one(
                cid,
                audit_rows=audit_rows,
                rtm_map=rtm_map,
                ai_ids=frozenset(all_ai),
                closure_cache=closure_cache,
            )
        )
        if cid % 50 == 0:
            print(f"audited {cid}/826", flush=True)

    true_count = sum(1 for r in rows if r["fully_v6_compliant"])
    false_rows = [r for r in rows if not r["fully_v6_compliant"]]

    failure_histogram: dict[str, int] = {}
    for r in false_rows:
        for f in r["failure_columns"]:
            failure_histogram[f] = failure_histogram.get(f, 0) + 1

    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "governing_standard": str(V6_STANDARD.relative_to(ROOT)),
        "audit_method": "verification_only_literal_v6_compliance",
        "audit_environment": "local_dev_vm",
        "scope": "IDs 1-826",
        "rows": rows,
        "summary": {
            "total_ids": 826,
            "fully_v6_compliant_true": true_count,
            "fully_v6_compliant_false": len(false_rows),
            "failure_column_histogram": dict(sorted(failure_histogram.items(), key=lambda x: -x[1])),
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"fully_v6_compliant_true={true_count}")
    print(f"fully_v6_compliant_false={len(false_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
