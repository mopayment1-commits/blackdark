#!/usr/bin/env python3
"""Governance-only reconciliation for Launch-57 capability #6 register metadata."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
REGISTER_PATH = GOV / "LAUNCH57_REGISTER.json"
AUTHORITY_PATH = GOV / "LAUNCH57_CAPABILITY_6_AUTHORITY_RESOLUTION.json"
B3_IV_PATH = GOV / "B3_6_TRUST_BOUNDARY_INDEPENDENT_VERIFICATION.json"
EVIDENCE_PATH = GOV / "LAUNCH57_CAPABILITY_6_GOVERNANCE_RECONCILIATION.json"
REPORT_PATH = GOV / "LAUNCH57_CAPABILITY_6_GOVERNANCE_RECONCILIATION_REPORT.md"

LAUNCH_NUMBER = 6
CANONICAL_OWNER_MODULE = "launch57.evidence_class_common"
CANONICAL_OWNER_FILE = "launch57/evidence_class_common.py"
CANONICAL_CONSUMER_PATHS = [
    "launch57/evidence_class_common.py",
    "launch57/trust_batch1.py:user_evidence_display",
    "launch57/trust_batch1.py:attach_trust_envelope",
    "launch57/b4_decision_bridge.py:apply_b4_trust_envelope",
]
RUNTIME_ENTRY = [
    "launch57/evidence_class_common.py",
    "launch57/trust_batch1.py",
]
PUBLIC_TAXONOMY = ["LIVE", "DELAYED", "SIM"]


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_register_item(register: dict[str, Any]) -> dict[str, Any]:
    for item in register.get("launch57_register", []):
        if item.get("launch_number") == LAUNCH_NUMBER:
            return item
    raise KeyError(f"launch_number={LAUNCH_NUMBER} not found in LAUNCH57_REGISTER.json")


def _reconcile_register_item(item: dict[str, Any], *, commit_sha: str, now: str, b3_iv: dict[str, Any]) -> dict[str, Any]:
    before = {
        "canonical_implementation": item.get("canonical_implementation"),
        "canonical_owner": item.get("canonical_owner"),
        "actual_consumer_paths": item.get("actual_consumer_paths"),
        "current_engineering_status": item.get("current_engineering_status"),
        "root_cause_if_not_pass_engineering": item.get("root_cause_if_not_pass_engineering"),
        "pass_engineering_reconciliation": item.get("pass_engineering_reconciliation"),
    }

    item["canonical_owner"] = [CANONICAL_OWNER_MODULE]
    item["canonical_implementation"] = [CANONICAL_OWNER_MODULE]
    item["runtime_entry"] = RUNTIME_ENTRY
    item["actual_consumer_paths"] = CANONICAL_CONSUMER_PATHS
    item["current_engineering_status"] = b3_iv.get("B3:#6", "PASS_ENGINEERING")
    item["root_cause_if_not_pass_engineering"] = None
    item["pass_engineering_reconciliation"] = b3_iv.get("B3:#6", "PASS_ENGINEERING")
    item["evidence_found"] = [
        "governance/launch57/B3_6_TRUST_BOUNDARY_INDEPENDENT_VERIFICATION.json",
        "governance/launch57/LAUNCH57_CAPABILITY_6_AUTHORITY_RESOLUTION.json",
        "governance/launch57/B3_TEMPORAL_IMPLEMENTATION_EVIDENCE.json",
        "governance/launch57/PHASE2_BATCH1_EVIDENCE.json",
    ]
    match_evidence = dict(item.get("match_evidence") or {})
    match_evidence["implicit_mapping_basis"] = "launch57_canonical_owner_evidence_class_common"
    match_evidence["implicit_repo_paths"] = [
        CANONICAL_OWNER_FILE,
        "launch57/trust_batch1.py",
        "launch57/b4_decision_bridge.py",
    ]
    item["match_evidence"] = match_evidence
    item["notes"] = (
        "SHARED_CORE cross-cutting item; canonical owner launch57.evidence_class_common "
        "(B3_6 IV PASS_ENGINEERING). Public taxonomy LIVE/DELAYED/SIM."
    )
    item["capability_6_governance_reconciliation"] = {
        "reconciled_at": now,
        "reconciled_commit": commit_sha,
        "authority_resolution_reference": "governance/launch57/LAUNCH57_CAPABILITY_6_AUTHORITY_RESOLUTION.json",
        "authoritative_iv_reference": "governance/launch57/B3_6_TRUST_BOUNDARY_INDEPENDENT_VERIFICATION.json",
        "canonical_owner_module": CANONICAL_OWNER_MODULE,
        "canonical_owner_file": CANONICAL_OWNER_FILE,
        "public_taxonomy": PUBLIC_TAXONOMY,
        "engineering_status": b3_iv.get("B3:#6", "PASS_ENGINEERING"),
        "prior_register_state": before,
        "root_cause": (
            "Phase 2 batch1 generator updated only CAP-backed items (#3-#5) with "
            "canonical_implementation; #6 SHARED_CORE row retained Phase 0 discovery paths. "
            "No post-B3_6 IV register refresh was run."
        ),
    }
    return before


def _verify_item(item: dict[str, Any], b3_iv: dict[str, Any]) -> None:
    assert item["canonical_implementation"] == [CANONICAL_OWNER_MODULE]
    assert item["canonical_owner"] == [CANONICAL_OWNER_MODULE]
    assert CANONICAL_OWNER_FILE in item["actual_consumer_paths"]
    assert item["current_engineering_status"] == "PASS_ENGINEERING"
    assert item["pass_engineering_reconciliation"] == "PASS_ENGINEERING"
    assert item["root_cause_if_not_pass_engineering"] is None
    assert b3_iv.get("B3:#6") == "PASS_ENGINEERING"
    assert b3_iv.get("entry_gate", {}).get("canonical_owner") == CANONICAL_OWNER_MODULE
    stale = {"cap646/evidence_class.py", "decision_truth/evidence_taxonomy.py"}
    assert stale.isdisjoint(set(item["actual_consumer_paths"]))


def main() -> None:
    starting_head = _git_sha()
    now = datetime.now(UTC).isoformat()
    authority = _load_json(AUTHORITY_PATH)
    b3_iv = _load_json(B3_IV_PATH)
    register = _load_json(REGISTER_PATH)

    if authority.get("verdict", {}).get("CAPABILITY_6_AUTHORITY") != "RESOLVED":
        raise SystemExit("Authority resolution must be RESOLVED before governance reconciliation")
    if b3_iv.get("B3:#6") != "PASS_ENGINEERING":
        raise SystemExit("B3_6 IV must grant B3:#6 PASS_ENGINEERING")

    item = _find_register_item(register)
    before = _reconcile_register_item(item, commit_sha=starting_head, now=now, b3_iv=b3_iv)
    _verify_item(item, b3_iv)

    register["capability_6_governance_reconciliation"] = {
        "reconciled_at": now,
        "reconciled_commit": starting_head,
        "launch_number": LAUNCH_NUMBER,
        "canonical_owner_module": CANONICAL_OWNER_MODULE,
        "engineering_status": "PASS_ENGINEERING",
        "iv_reference": "governance/launch57/B3_6_TRUST_BOUNDARY_INDEPENDENT_VERIFICATION.json",
        "authority_resolution_reference": "governance/launch57/LAUNCH57_CAPABILITY_6_AUTHORITY_RESOLUTION.json",
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "artifact": "LAUNCH57_CAPABILITY_6_GOVERNANCE_RECONCILIATION",
        "remediation_type": "governance_metadata_only",
        "starting_head_sha": starting_head,
        "starting_head_sha_short": starting_head[:8],
        "authority_resolution_reference": {
            "artifact": "LAUNCH57_CAPABILITY_6_AUTHORITY_RESOLUTION",
            "commit": "d2bdac0b",
            "CAPABILITY_6_AUTHORITY": "RESOLVED",
        },
        "authoritative_iv": {
            "artifact": "B3_6_TRUST_BOUNDARY_INDEPENDENT_VERIFICATION",
            "B3:#6": b3_iv.get("B3:#6"),
            "canonical_owner": b3_iv.get("entry_gate", {}).get("canonical_owner"),
            "verified_implementation_sha": b3_iv.get("VERIFIED_IMPLEMENTATION_SHA"),
        },
        "register_authority": {
            "primary_view": "governance/launch57/LAUNCH57_REGISTER.json",
            "declared_ssot": "BLACKDARK_CAPABILITY_CURRENT_STATE.json",
            "write_path": "incremental phase generators + governance reconciliation generators",
            "generator": "governance/launch57/generate_capability_6_governance_reconciliation.py",
        },
        "root_cause": {
            "summary": (
                "LAUNCH57_REGISTER.json #6 retained Phase 0 discovery metadata because "
                "generate_phase2_batch1.py only assigned canonical_implementation to CAP-backed "
                "items (#3-#5), not SHARED_CORE #6; no post-B3_6 IV register reconciliation ran."
            ),
            "generator_would_partially_recreate_stale_nested_metadata": True,
            "generator_mitigation": (
                "generate_phase2_batch1.py ITEM_ROWS[6] consumer_paths aligned to Launch-57 owner; "
                "canonical register fields reconciled by this generator from B3_6 IV."
            ),
        },
        "reconciled_fields": {
            "canonical_owner": [CANONICAL_OWNER_MODULE],
            "canonical_implementation": [CANONICAL_OWNER_MODULE],
            "runtime_entry": RUNTIME_ENTRY,
            "actual_consumer_paths": CANONICAL_CONSUMER_PATHS,
            "current_engineering_status": "PASS_ENGINEERING",
            "pass_engineering_reconciliation": "PASS_ENGINEERING",
            "root_cause_if_not_pass_engineering": None,
            "public_taxonomy": PUBLIC_TAXONOMY,
        },
        "prior_register_state": before,
        "final_status": {
            "PRODUCT_CODE_CHANGED": False,
            "CAPABILITY_6_REBUILT": False,
            "OTHER_CAPABILITY_SEMANTIC_METADATA_CHANGED": False,
            "CAPABILITY_6_GOVERNANCE_METADATA_RECONCILED": True,
            "PASS_LIVE_NOT_CLAIMED": True,
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report = f"""# Launch-57 Capability #6 — Governance Metadata Reconciliation

**Remediation type:** governance metadata only (no product code)

**Starting HEAD:** `{starting_head}`

## Register authority / write path

- **Primary view:** `governance/launch57/LAUNCH57_REGISTER.json`
- **Declared SSOT:** `BLACKDARK_CAPABILITY_CURRENT_STATE.json` (historical phase snapshots)
- **Write path:** incremental phase generators + `generate_capability_6_governance_reconciliation.py`

## Root cause

Phase 0 discovery assigned #6 to `cap646/evidence_class.py`. Phase 2 batch 1 added `phase2_batch1_build` for #6 but `generate_phase2_batch1.py` only set top-level `canonical_implementation` for CAP-backed items (#3–#5). B3_6 IV later verified `launch57.evidence_class_common` as canonical owner (`B3:#6=PASS_ENGINEERING`), but the register row was never reconciled.

## Reconciled #6 metadata

| Field | Value |
| --- | --- |
| canonical_owner | `{CANONICAL_OWNER_MODULE}` |
| canonical_implementation | `{CANONICAL_OWNER_MODULE}` |
| runtime_entry | `{", ".join(RUNTIME_ENTRY)}` |
| actual_consumer_paths | Launch-57 paths only (see evidence JSON) |
| current_engineering_status | `PASS_ENGINEERING` |
| pass_engineering_reconciliation | `PASS_ENGINEERING` |
| public taxonomy | `LIVE`, `DELAYED`, `SIM` |

## Files changed

- `governance/launch57/LAUNCH57_REGISTER.json` (launch_number=6 only)
- `governance/launch57/generate_capability_6_governance_reconciliation.py`
- `governance/launch57/LAUNCH57_CAPABILITY_6_GOVERNANCE_RECONCILIATION.json`
- `governance/launch57/LAUNCH57_CAPABILITY_6_GOVERNANCE_RECONCILIATION_REPORT.md`

## Final status

```text
PRODUCT_CODE_CHANGED = false
CAPABILITY_6_REBUILT = false
OTHER_CAPABILITY_SEMANTIC_METADATA_CHANGED = false
CAPABILITY_6_GOVERNANCE_METADATA_RECONCILED = true
PASS_LIVE_NOT_CLAIMED = true
```
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Reconciled #6 register metadata @ {starting_head[:8]}")


if __name__ == "__main__":
    main()
