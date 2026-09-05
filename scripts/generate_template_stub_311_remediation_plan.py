#!/usr/bin/env python3
"""Generate per-ID remediation plan for 311 TEMPLATE-SEED-STUB capabilities."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MANIFEST = ROOT / "docs/TEMPLATE_STUB_RECLASSIFICATION_MANIFEST.json"
CATALOG = ROOT / "docs/cap978/CAP978_CATALOG.json"
OUT_JSON = ROOT / "docs/TEMPLATE_STUB_311_REMEDIATION_PLAN.json"
OUT_MD = ROOT / "docs/TEMPLATE_STUB_311_REMEDIATION_PLAN.md"

# Explicit option-A candidates: user-facing stub IDs + layer co-located non-stub neighbors under review
OPTION_A_CANDIDATES = frozenset({338, 500, 507, 534})


def _catalog_name(cid: int) -> str:
    try:
        data = json.loads(CATALOG.read_text(encoding="utf-8"))
        for row in data:
            if int(row["id"]) == cid:
                return str(row.get("capability") or row.get("name") or f"ID{cid}")
    except Exception:
        pass
    return f"ID{cid}"


def _user_surface(cid: int) -> dict | None:
    try:
        from cap646.ui_pages import user_surface_for

        return user_surface_for(cid)
    except Exception:
        return None


def decide(cid: int, batch: int, reason: str) -> dict:
    surface = _user_surface(cid)
    if cid in OPTION_A_CANDIDATES:
        decision = "A_BUILD"
        rationale = (
            f"USER_FACING surface ({surface.get('ui_path') if surface else '/cap646'}); "
            "requires dedicated backend wired through cap646.runtime + backend_registry, "
            "independent pytest, and live verify — not template seed metric."
        )
        priority = "P0"
    else:
        decision = "B_DEFERRED"
        rationale = (
            "TEMPLATE-SEED-STUB has no unique domain implementation; "
            "production already serves a generic cap646 handler. "
            "Defer until product owner assigns domain spec + acceptance tests."
        )
        priority = "P2" if not surface else "P1"
    return {
        "capability_id": cid,
        "batch": batch,
        "catalog_name": _catalog_name(cid),
        "decision": decision,
        "priority": priority,
        "user_surface": surface,
        "reclassification_reason": reason,
        "decision_rationale": rationale,
        "acceptance_if_A": [
            "New module entry in cap646/backend_registry.py (not pdf_capability_registry only)",
            "cap646.runtime.execute_capability returns domain-specific payload",
            "Independent pytest (not batch template generator test)",
            "Live verify script output archived in evidence JSONL",
        ],
        "deferral_if_B": {
            "status": "DEFERRED/TEMPLATE-STUB",
            "blocked_by": "missing_domain_spec",
            "allowed_interim": "generic cap646 handler only — no VERIFIED-DEEP claim",
        },
    }


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries: list[dict] = []
    for cid_str, reason in sorted(manifest["entries"].items(), key=lambda x: int(x[0])):
        cid = int(cid_str)
        batch = next(int(b) for b, ids in manifest["by_batch"].items() if cid in ids)
        entries.append(decide(cid, batch, reason))

    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "total": len(entries),
        "option_A_build": sum(1 for e in entries if e["decision"] == "A_BUILD"),
        "option_B_deferred": sum(1 for e in entries if e["decision"] == "B_DEFERRED"),
        "by_batch": {},
        "entries": entries,
    }
    for e in entries:
        b = str(e["batch"])
        summary["by_batch"].setdefault(b, {"A_BUILD": 0, "B_DEFERRED": 0})
        summary["by_batch"][b][e["decision"]] += 1

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# TEMPLATE-SEED-STUB 311 — per-ID remediation plan",
        "",
        f"**Generated:** {summary['generated_at']}",
        "",
        "## Summary",
        "",
        f"- **Option A (real build):** {summary['option_A_build']}",
        f"- **Option B (DEFERRED):** {summary['option_B_deferred']}",
        "",
        "### Per batch",
        "",
        "| Batch | A_BUILD | B_DEFERRED |",
        "|------:|--------:|-----------:|",
    ]
    for b in sorted(summary["by_batch"], key=int):
        row = summary["by_batch"][b]
        md.append(f"| {int(b):02d} | {row['A_BUILD']} | {row['B_DEFERRED']} |")

    md.extend(
        [
            "",
            "## Option A candidates (P0)",
            "",
        ]
    )
    for e in entries:
        if e["decision"] == "A_BUILD":
            md.append(f"- **#{e['capability_id']}** — {e['catalog_name']}: {e['decision_rationale']}")

    md.extend(["", "## Full per-ID decisions", "", "See `docs/TEMPLATE_STUB_311_REMEDIATION_PLAN.json` entries[].", ""])
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("total", "option_A_build", "option_B_deferred", "by_batch")}, indent=2))


if __name__ == "__main__":
    main()
