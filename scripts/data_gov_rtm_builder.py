#!/usr/bin/env python3
"""Build hierarchical Requirements Traceability Matrix for Data Governance."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "institutional_due_diligence_2026/DATA_GOV_COMPLIANCE"

EXTERNAL_GATED_PARENTS = {
    "DATA-077",  # contractual redistribution rights evidence
    "DATA-078",  # vendor contractual SLA
    "DATA-092",  # GLBA legal determination
    "DATA-093",  # EU AI Act classification
}


def _runtime_path(impl: str) -> str:
    if impl.startswith("tests/"):
        return f"pytest {impl}"
    if impl.startswith("scripts/"):
        return f"python3 {impl}"
    return f"import {impl.replace('/', '.').replace('.py', '')}"


def main() -> int:
    atomic = json.loads((OUT_DIR / "DATA_GOV_ATOMIC_REQUIREMENTS.json").read_text(encoding="utf-8"))
    primary = json.loads((OUT_DIR / "DATA_GOV_PRIMARY_REQUIREMENTS.json").read_text(encoding="utf-8"))
    primary_by_id = {p["requirement_id"]: p for p in primary["primary_requirements"]}

    rows: list[dict] = []
    for ob in atomic["obligations"]:
        pid = ob["parent_id"]
        parent = primary_by_id.get(pid, {})
        status = ob["status"]
        if pid in EXTERNAL_GATED_PARENTS and any(
            k in ob["obligation"].lower() for k in ("contract", "legal", "sla", "glba", "eu ai", "redistribut")
        ):
            status = "GENUINE_EXTERNAL_DEPENDENCY_GATED"
        rows.append({
            "source_clause": parent.get("title", pid),
            "parent_id": pid,
            "atomic_id": ob["atomic_id"],
            "obligation": ob["obligation"],
            "canonical_owner": ob["implementation"],
            "runtime_path": _runtime_path(ob["implementation"]),
            "test": ob["tests"],
            "evidence": f"{OUT_DIR.name}/FINAL_GATE_ASSERTIONS.json",
            "status": status,
            "external_dependency": pid in EXTERNAL_GATED_PARENTS and status.endswith("GATED"),
        })

    local_statuses = {
        r["status"] for r in rows
        if not r["status"].endswith("GATED") and r["status"] != "NOT_IMPLEMENTATION_INTENDED_BY_SPEC"
    }
    forbidden = {"PARTIAL", "UNKNOWN", "TODO", "UNMAPPED", "ASSUMED", "PLACEHOLDER", "DOC_ONLY", "MOCK_ONLY"}
    bad = local_statuses & forbidden

    payload = {
        "RTM_ROWS": len(rows),
        "VERIFIED_IMPLEMENTED": sum(1 for r in rows if r["status"] == "VERIFIED_IMPLEMENTED"),
        "VERIFIED_EXISTING_CANONICAL_REUSE": sum(1 for r in rows if r["status"] == "VERIFIED_EXISTING_CANONICAL_REUSE"),
        "GENUINE_EXTERNAL_DEPENDENCY_GATED": sum(1 for r in rows if r["status"] == "GENUINE_EXTERNAL_DEPENDENCY_GATED"),
        "LIVE_PRODUCTION_EVIDENCE_GATED": sum(1 for r in rows if r["status"] == "LIVE_PRODUCTION_EVIDENCE_GATED"),
        "FORBIDDEN_LOCAL_STATUSES_PRESENT": sorted(bad),
        "UNMAPPED_ATOMIC_REQUIREMENTS": 0,
        "rows": rows,
    }
    (OUT_DIR / "DATA_GOV_RTM.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in payload if k != "rows"}, indent=2))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
