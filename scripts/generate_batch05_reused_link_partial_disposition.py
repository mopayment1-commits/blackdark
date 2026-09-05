#!/usr/bin/env python3
"""Item 2 — Final disposition of Batch05 REUSED-LINK pentagonal partials (#214, #232, #245).

Close with full evidence or explicit TOLERATE + ceiling date + ADR reference.
Does NOT elevate independent or production_aligned.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_batch03_institutional_pentagonal import (  # noqa: E402
    evaluate_domain_rules,
    load_json,
)

ACCEPTANCE = ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json"
OUT_JSON = ROOT / "docs/BATCH05_REUSED_LINK_PARTIAL_DISPOSITION.json"
OUT_MD = ROOT / "docs/BATCH05_REUSED_LINK_PARTIAL_DISPOSITION.md"

PARTIAL_IDS = (214, 232, 245)
TOLERATE_CEILING = "2026-12-31"


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


async def probe_runtime(cid: int) -> dict[str, Any]:
    from cap646.runtime import execute_capability

    return await execute_capability(cid, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})


async def probe_facade(cid: int) -> dict[str, Any]:
    from cap646.batch05_dedicated import execute

    return await execute(cid, params={"symbol": "BTC", "tier": "pro"})


def disposition_for(cid: int, runtime_probe: dict, facade_probe: dict, acceptance: dict) -> dict[str, Any]:
    runtime_rules = evaluate_domain_rules(runtime_probe, acceptance)
    facade_rules = evaluate_domain_rules(facade_probe, acceptance)
    runtime_pass = all(r["pass"] for r in runtime_rules)
    facade_pass = all(r["pass"] for r in facade_rules)

    if cid == 232:
        return {
            "capability_id": cid,
            "capability_name": acceptance["capability_name"],
            "disposition": "CLOSED",
            "disposition_rationale": (
                "Acceptance catalog_link.binding aligned to strangler spine "
                "(build_open_interest_205); facade + runtime probes pass 8/8 domain rules"
            ),
            "adr": "docs/ADR_BATCH05_232_REUSED_LINK_205.md",
            "tolerate_ceiling": None,
            "runtime_probe": {
                "domain_all_pass": runtime_pass,
                "rules_passed": sum(1 for r in runtime_rules if r["pass"]),
                "rules_total": len(runtime_rules),
            },
            "facade_probe": {
                "domain_all_pass": facade_pass,
                "rules_passed": sum(1 for r in facade_rules if r["pass"]),
                "rules_total": len(facade_rules),
            },
            "pentagonal_partial_resolved": True,
            "production_aligned": False,
            "batch05_independent": False,
            "12207_phase": "Validation (local REUSED-LINK contract) — Transition blocked",
            "next_action": "None — #232 REUSED-LINK closed at facade contract level; PA still blocked globally",
        }

    # #214 and #245 — runtime batch01 path lacks catalog_link by ADR design
    adr = "docs/ADR_BATCH05_214_245_REUSED_LINK_BATCH01.md"
    partial_reason = (
        "Public GET/runtime routes batch01 spine before batch05 facade; catalog_link stamped only on "
        "batch05_dedicated facade path (ADR precedence — same pattern as batch04 #175)"
    )
    if cid == 245:
        partial_reason += "; internal capability_id stamp 630 on batch01 freshness path (OVERLAP-PARTIAL)"

    return {
        "capability_id": cid,
        "capability_name": acceptance["capability_name"],
        "disposition": "TOLERATE",
        "disposition_rationale": partial_reason,
        "adr": adr,
        "tolerate_ceiling": TOLERATE_CEILING,
        "tolerate_conditions": [
            "Facade contract tests must remain green (catalog_link stamped on batch05_production path)",
            "Runtime batch01 path remains authoritative for public GET until Gate Zero live probe",
            "No hero-layer production routing for this ID",
            f"Re-evaluate at ceiling {TOLERATE_CEILING} or upon Gate Zero deploy evidence",
        ],
        "runtime_probe": {
            "domain_all_pass": runtime_pass,
            "rules_passed": sum(1 for r in runtime_rules if r["pass"]),
            "rules_total": len(runtime_rules),
            "failed_fields": [r["field"] for r in runtime_rules if not r["pass"]],
        },
        "facade_probe": {
            "domain_all_pass": facade_pass,
            "rules_passed": sum(1 for r in facade_rules if r["pass"]),
            "rules_total": len(facade_rules),
        },
        "pentagonal_partial_resolved": False,
        "pentagonal_probe_path_note": "Pentagonal generator uses runtime path — partial domain rules expected for #214/#245",
        "production_aligned": False,
        "batch05_independent": False,
        "12207_phase": "Validation (TOLERATE with ceiling) — Transition blocked",
        "next_action": f"Owner review at {TOLERATE_CEILING}: align pentagonal probe path or accept dual-path contract",
    }


def render_markdown(doc: dict[str, Any]) -> str:
    lines = [
        "# Batch05 REUSED-LINK Partial Disposition (#214, #232, #245)",
        "",
        f"**Generated:** {doc['generated_at']} | **Commit:** `{doc['git_commit'][:12]}`",
        f"**Sequence item:** 2 | **Tolerate ceiling:** {TOLERATE_CEILING}",
        "",
        "هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. لا إعلان اكتمال حوكمة · لا Batch05 complete · لا جاهزية حية 100%.",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| ID | Disposition | Runtime pass | Facade pass | PA elevated |",
        "|----|-------------|--------------|-------------|-------------|",
    ]
    for row in doc["rows"]:
        lines.append(
            f"| {row['capability_id']} | **{row['disposition']}** | "
            f"{row['runtime_probe']['rules_passed']}/{row['runtime_probe'].get('rules_total', '—')} | "
            f"{row['facade_probe']['rules_passed']}/{row['facade_probe'].get('rules_total', '—')} | **NO** |"
        )
    lines.extend(
        [
            "",
            f"- Closed: **{doc['summary']['closed_count']}** · Tolerated: **{doc['summary']['tolerate_count']}**",
            f"- `production_aligned_count`: **{doc['production_aligned_count']}**",
            f"- `batch05_independent`: **{doc['batch05_independent']}**",
            "",
            "---",
            "",
            "## Per-ID decisions",
            "",
        ]
    )
    for row in doc["rows"]:
        lines.append(f"### #{row['capability_id']} — {row['capability_name']}")
        lines.append(f"- **Disposition:** {row['disposition']}")
        lines.append(f"- **Rationale:** {row['disposition_rationale']}")
        lines.append(f"- **ADR:** `{row['adr']}`")
        if row.get("tolerate_ceiling"):
            lines.append(f"- **Ceiling:** {row['tolerate_ceiling']}")
        lines.append("")
    lines.append(
        "هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. "
        "لا إعلان اكتمال حوكمة · لا Batch05 complete · لا جاهزية حية 100%."
    )
    lines.append("")
    return "\n".join(lines)


async def main() -> None:
    acceptance_by_id = {r["capability_id"]: r for r in load_json(ACCEPTANCE)["rows"]}
    rows: list[dict[str, Any]] = []
    for cid in PARTIAL_IDS:
        acc = acceptance_by_id[cid]
        runtime_probe = await probe_runtime(cid)
        facade_probe = await probe_facade(cid)
        rows.append(disposition_for(cid, runtime_probe, facade_probe, acc))

    closed = sum(1 for r in rows if r["disposition"] == "CLOSED")
    tolerated = sum(1 for r in rows if r["disposition"] == "TOLERATE")
    assert closed == 1 and tolerated == 2
    by_id = {r["capability_id"]: r for r in rows}
    assert by_id[232]["disposition"] == "CLOSED"
    assert by_id[232]["facade_probe"]["domain_all_pass"] is True
    assert by_id[232]["runtime_probe"]["domain_all_pass"] is True
    assert by_id[214]["facade_probe"]["rules_passed"] >= 7
    assert by_id[245]["facade_probe"]["rules_passed"] >= 7

    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "sequence_item": 2,
        "scope": "REUSED-LINK pentagonal partial disposition #214 #232 #245",
        "build_phase": "OPEN",
        "batch05_independent": 0,
        "progress_826": 179,
        "production_aligned_count": 0,
        "pa_elevated_count": 0,
        "tolerate_ceiling_default": TOLERATE_CEILING,
        "summary": {"closed_count": closed, "tolerate_count": tolerated, "partial_ids": list(PARTIAL_IDS)},
        "policy": "Close with evidence or TOLERATE with hard ceiling + ADR. No PA elevation.",
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(doc), encoding="utf-8")
    print(f"Wrote {OUT_JSON.name} — closed={closed} tolerate={tolerated}")


if __name__ == "__main__":
    asyncio.run(main())
