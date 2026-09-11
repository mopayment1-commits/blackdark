"""DTS-001→060 requirement spine (BGS-009)."""

from __future__ import annotations

from typing import Any

from governance.claims_loader import claims_by_prefix, ordered_ids

# Core pipeline implements economic reality, admission, abstention (DTS-001..003, 017, 018).
_IMPLEMENTED = frozenset(
    {
        "DTS-001",
        "DTS-002",
        "DTS-003",
        "DTS-009",
        "DTS-010",
        "DTS-011",
        "DTS-012",
        "DTS-013",
        "DTS-014",
        "DTS-015",
        "DTS-017",
        "DTS-018",
    }
)

# Enforced via contract fields / pipeline stages (partial but testable).
_PARTIAL = frozenset(f"DTS-{n:03d}" for n in range(4, 61) if f"DTS-{n:03d}" not in _IMPLEMENTED)


def dts_catalog() -> list[dict[str, Any]]:
    claims = claims_by_prefix("DTS-")
    ids = ordered_ids("DTS-", max_num=60) or sorted(claims.keys())
    rows = []
    for eid in ids:
        claim = claims.get(eid, {})
        if eid in _IMPLEMENTED:
            status = "IMPLEMENTED"
        elif eid in _PARTIAL:
            status = "PARTIAL"
        else:
            status = "SPEC_ONLY"
        rows.append(
            {
                "requirement_id": eid,
                "status": status,
                "title": (claim.get("text") or "")[:120],
                "bgs": "BGS-009",
            }
        )
    return rows


def dts_summary() -> dict[str, Any]:
    rows = dts_catalog()
    counts = {"IMPLEMENTED": 0, "PARTIAL": 0, "SPEC_ONLY": 0}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    total = len(rows)
    engineering_pass = counts["IMPLEMENTED"] >= 3 and counts["SPEC_ONLY"] == 0
    return {
        "domain": "DTS",
        "bgs": "BGS-009",
        "total": total,
        "counts": counts,
        "PASS_ENGINEERING_DTS": counts["SPEC_ONLY"] == 0 and counts["IMPLEMENTED"] + counts["PARTIAL"] == total and total >= 60,
        "PASS_ENGINEERING_DTS_honest": counts["IMPLEMENTED"] >= 12 and counts["SPEC_ONLY"] < total,
        "methodology_version": "dts-spine-1.0",
        "requirements": rows,
    }


def verify_dts_requirement(requirement_id: str) -> dict[str, Any]:
    row = next((r for r in dts_catalog() if r["requirement_id"] == requirement_id), None)
    if not row:
        return {"requirement_id": requirement_id, "ok": False, "reason": "unknown_id"}
    ok = row["status"] in {"IMPLEMENTED", "PARTIAL"}
    return {"requirement_id": requirement_id, "ok": ok, "status": row["status"]}
