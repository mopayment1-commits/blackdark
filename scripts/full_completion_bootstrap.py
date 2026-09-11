#!/usr/bin/env python3
"""Bootstrap FULL_COMPLETION_EXECUTION_REGISTER from 826 inventory + findings."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INVENTORY = ROOT / "docs" / "CAPABILITIES_826_INVENTORY.json"
MASTER = ROOT / "CAPABILITY_MASTER_REGISTER.json"
SPLIT_BRAIN = ROOT / "docs" / "SPLIT_BRAIN_BCD_RECLASSIFICATION_MANIFEST.json"
PHANTOM_DOC = ROOT / "docs" / "REGISTRY_PHANTOM_INCIDENT_REGISTER.md"
OUT_REGISTER = ROOT / "FULL_COMPLETION_EXECUTION_REGISTER.json"
OUT_DEDUP = ROOT / "FULL_COMPLETION_DUPLICATION_REPORT.json"
OUT_SUMMARY = ROOT / "FULL_COMPLETION_PHASE_SUMMARY.json"
BATCH_VERIFY = ROOT / "BATCH_CLOSURE_VERIFY_REPORT.json"

PHASE_ORDER = [
    "P0_TRUTH_BASELINE",
    "P1_DEDUPLICATION",
    "P2_SPLIT_BRAIN",
    "P3_GOVERNANCE_PACKAGES",
    "P4_BATCH_CLOSURE",
    "P5_UI_E2E",
    "P6_PRODUCTION_HARDENING",
    "P7_EXTERNAL_ASSURANCE",
]

EXECUTOR = {
    "AI_AGENT": "automated — cloud agent / scripts",
    "ENGINEERING_TEAM": "human developers required",
    "EXTERNAL_VENDOR": "third party — pentest, SOC2, legal",
    "OWNER": "owner decision / credentials / contracts",
}


def _official_batch(cap_id: int) -> str:
    return f"batch{(cap_id - 1) // 50 + 1:02d}"


def _phase_for(cap_id: int, inv_status: str, master_status: str) -> tuple[str, str]:
    if inv_status == "PRODUCTION-ALIGNED" and master_status == "IMPLEMENTED":
        return "DONE", "AI_AGENT"
    if inv_status == "REUSED-LINK" and master_status == "IMPLEMENTED":
        return "DONE", "AI_AGENT"
    if inv_status == "REUSED-LINK":
        return "P1_DEDUPLICATION", "AI_AGENT"
    if inv_status == "OVERLAP_BATCH01":
        return "P1_DEDUPLICATION", "AI_AGENT"
    if inv_status == "PENDING_SCOPE_REALIGNMENT":
        return "P1_DEDUPLICATION", "ENGINEERING_TEAM"
    if master_status == "MOCK_OR_STUB":
        return "P4_BATCH_CLOSURE", "ENGINEERING_TEAM"
    if master_status == "NOT_VERIFIED":
        return "P4_BATCH_CLOSURE", "AI_AGENT"
    if inv_status == "NOT_COMPLETE":
        return "P4_BATCH_CLOSURE", "ENGINEERING_TEAM"
    return "P4_BATCH_CLOSURE", "AI_AGENT"


def _batch_closure_verified_ids() -> frozenset[int]:
    if not BATCH_VERIFY.exists():
        return frozenset()
    report = json.loads(BATCH_VERIFY.read_text(encoding="utf-8"))
    verified: set[int] = set()
    for batch in report.get("batches", []):
        if batch.get("fail", 1) == 0:
            # Infer ID range from batch name batchNN
            name = str(batch.get("batch") or "")
            if name.startswith("batch") and name[5:].isdigit():
                n = int(name[5:])
                start = (n - 1) * 50 + 1
                end = min(start + 49, 826) if n < 17 else 826
                verified.update(range(start, end + 1))
    return frozenset(verified)


def main() -> int:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    master = json.loads(MASTER.read_text(encoding="utf-8"))
    master_by_id = {int(r["capability_id"].replace("CAP-", "")): r for r in master["capabilities"]}
    batch_verified = _batch_closure_verified_ids()

    split_ids = set()
    if SPLIT_BRAIN.exists():
        manifest = json.loads(SPLIT_BRAIN.read_text(encoding="utf-8"))
        for cat in manifest.get("by_category", {}).values():
            split_ids.update(cat.get("ids", []))

    capabilities = []
    phase_counts: dict[str, int] = {p: 0 for p in PHASE_ORDER}
    phase_counts["DONE"] = 0
    executor_counts: dict[str, int] = {}

    for key, row in sorted(inventory["per_id"].items(), key=lambda kv: int(kv[0])):
        cap_id = int(key)
        master_row = master_by_id.get(cap_id, {})
        master_status = master_row.get("primary_status") or master_row.get("status", "NOT_VERIFIED")
        inv_status = row.get("status", "PENDING")
        phase, executor = _phase_for(cap_id, inv_status, master_status)
        if cap_id in split_ids and phase != "DONE":
            phase = "P2_SPLIT_BRAIN"
            executor = "AI_AGENT"
        batch_ok = cap_id in batch_verified
        dedup_resolved = batch_ok and phase == "P1_DEDUPLICATION"
        split_resolved = batch_ok and phase == "P2_SPLIT_BRAIN"
        if batch_ok and phase not in {"DONE", "P7_EXTERNAL_ASSURANCE"}:
            phase = "DONE"
            executor = "AI_AGENT"
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
        executor_counts[executor] = executor_counts.get(executor, 0) + 1
        capabilities.append(
            {
                "capability_id": cap_id,
                "capability_key": f"CAP-{cap_id:04d}",
                "name": row.get("capability"),
                "official_batch": row.get("official_batch") or _official_batch(cap_id),
                "inventory_status": inv_status,
                "master_status": master_status,
                "phase": phase,
                "executor": executor,
                "target_state": "PRODUCTION_ALIGNED_VERIFIED",
                "completion_pct": 100 if phase == "DONE" else 0,
                "batch_closure_verified": batch_ok,
                "dedup_resolved": dedup_resolved,
                "split_brain_resolved": split_resolved,
            }
        )

    register = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "program": "BLACKDARK_FULL_COMPLETION",
        "total_capabilities": 826,
        "phase_order": PHASE_ORDER,
        "executor_definitions": EXECUTOR,
        "phase_counts": phase_counts,
        "executor_counts": executor_counts,
        "capabilities": capabilities,
    }
    OUT_REGISTER.write_text(json.dumps(register, indent=2, ensure_ascii=False), encoding="utf-8")

    dedup = {
        "generated_at": register["generated_at"],
        "reused_link_ids": [
            c["capability_id"] for c in capabilities if c["inventory_status"] == "REUSED-LINK"
        ],
        "overlap_batch01": [
            c["capability_id"]
            for c in capabilities
            if c["inventory_status"] == "OVERLAP_BATCH01"
            or "overlap" in (c.get("name") or "").lower()
        ],
        "split_brain_ids": sorted(split_ids),
        "split_brain_count": len(split_ids),
        "phantom_remediated": [704, 708, 725, 812, 813, 814, 815],
        "taxonomy": str(ROOT / "docs" / "REUSED_LINK_TAXONOMY.json"),
    }
    OUT_DEDUP.write_text(json.dumps(dedup, indent=2), encoding="utf-8")

    summary = {
        "generated_at": register["generated_at"],
        "batch_closure_verified_count": len(batch_verified),
        "done": phase_counts.get("DONE", 0),
        "remaining": 826 - phase_counts.get("DONE", 0),
        "automatable_remaining": sum(
            1 for c in capabilities if c["executor"] == "AI_AGENT" and c["phase"] != "DONE"
        ),
        "human_team_remaining": sum(
            1 for c in capabilities if c["executor"] == "ENGINEERING_TEAM" and c["phase"] != "DONE"
        ),
        "phase_counts": phase_counts,
        "executor_counts": executor_counts,
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
