#!/usr/bin/env python3
"""Update Batch04 RTM closure statuses for final institutional delivery."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RTM = ROOT / "docs/BATCH04_RTM_151_200.json"
INVENTORY = ROOT / "docs/CAPABILITIES_826_INVENTORY.json"
ACCEPTANCE = ROOT / "docs/BATCH04_ACCEPTANCE_151_200.json"

PRODUCTION_ALIGNED = frozenset(
    {
        151,
        152,
        153,
        154,
        155,
        156,
        157,
        158,
        160,
        163,
        164,
        167,
        168,
        169,
        170,
        171,
        172,
        183,
        184,
        185,
        186,
        189,
        192,
        193,
        194,
        195,
        196,
        197,
        198,
        199,
        200,
    }
)

PAID_VENDOR = frozenset({187, 188, 190})
PAID_API_SUBSCRIPTION = frozenset({165})  # DeFiLlama /raises HTTP 402 (2026-09-04 live probe)

STRANGLER_BUILDERS = frozenset(
    {
        152, 153, 154, 155, 156, 157, 158, 160, 163, 164, 165, 167, 169, 170, 172,
        184, 185, 189, 192, 193, 194, 195, 196, 197, 198, 199, 200,
    }
)

BLOCKED_DEPENDENCY = {
    166: "#591 sentiment_analysis_engine_591",
    173: "#594 narrative_alert_system_594",
    174: "#450 narrative_driven_research_450",
    176: "#592 social_sentiment_engine_592",
    177: "#591 sentiment_analysis_engine_591",
    178: "#219 metric_availability_registry_219",
    179: "#421 developer_activity_421",
    180: "#352 core_developers_352",
}

PARTIAL_MISNAMED = {
    181: "IC Committee Packets Status",
    182: "White-Label Infrastructure Status",
    198: "On-Chain Dormancy Proxy",
    199: "Invested-Age Proxy",
}

NOT_COMPLETE = {
    159: "BLOCKER-159-103 — awaits #103 maturity or DISTINCT ADR",
    161: "Elite-gated institutional entitlements — spine wired, PA pending owner gate-zero",
    162: "BLOCKER-162-106 — REUSED-LINK pending #106 PA",
    175: "REUSED_ALIAS batch01 overlap — routes via batch01_production",
    191: "No known free technical solution for exchange user activity metrics",
}

NOT_COMPLETE_TECHNICAL = frozenset({191})

CATALOG_RENAMES = {
    198: "On-Chain Dormancy Proxy",
    199: "Invested-Age Proxy",
}


def _patch_row(row: dict) -> None:
    cid = row["id"]
    if cid in PRODUCTION_ALIGNED:
        row["closure_status"] = "PRODUCTION-ALIGNED"
        row["status"] = "PRODUCTION-ALIGNED"
        row["miswire_remediation"] = "STRANGLER_IMPLEMENTED"
        row["binding_file"] = "cap646/batch04_dedicated.py"
        row["binding_function"] = f"_cap{cid}" if cid in STRANGLER_BUILDERS or cid in {151, 159, 161, 162, 168, 171, 183, 186, 189} else f"_cap{cid}"
        row["canonical_module_function"] = (
            f"cap646.batch04_dedicated._cap{cid} → cap646.batch04_strangler_spine"
            if cid in STRANGLER_BUILDERS
            else row.get("canonical_module_function")
        )
        row.pop("owner_note", None)
        if cid in (198, 199):
            row["capability"] = CATALOG_RENAMES[cid]
            row["semantic_alignment_status"] = "PARTIAL_MISNAMED_RESOLVED"
            row["metric_type"] = "PARTIAL_MISNAMED"
            row["accuracy_disclaimer"] = "Heuristic local proxy — NOT Glassnode original metric."
    elif cid in PAID_VENDOR or cid in PAID_API_SUBSCRIPTION:
        row["closure_status"] = "NOT_COMPLETE"
        row["status"] = "NOT_COMPLETE"
        row["owner_note"] = (
            "AWAITING_DEFILLAMA_API_SUBSCRIPTION"
            if cid in PAID_API_SUBSCRIPTION
            else "AWAITING_OWNER_PAYMENT_DECISION"
        )
        row["vendor_status"] = "PAID_VENDOR_DESIGNED"
        if cid in PAID_API_SUBSCRIPTION:
            row["miswire_remediation"] = "PAID_API_SUBSCRIPTION"
            row["live_probe"] = "HTTP 402 https://api.llama.fi/raises"
    elif cid in BLOCKED_DEPENDENCY:
        row["closure_status"] = "NOT_COMPLETE"
        row["status"] = "NOT_COMPLETE"
        row["blocker"] = f"BLOCKER-{cid}-DEP"
        row["blocker_type"] = "BLOCKED_DEPENDENCY"
        row["owner_note"] = f"AWAITING_DEPENDENCY: {BLOCKED_DEPENDENCY[cid]} (inventory PENDING)"
        row["miswire_remediation"] = "BLOCKED_DEPENDENCY"
    elif cid in PARTIAL_MISNAMED:
        row["closure_status"] = "NOT_COMPLETE"
        row["status"] = "NOT_COMPLETE"
        row["miswire_remediation"] = "PARTIAL_MISNAMED_RESOLVED"
        row["semantic_alignment_status"] = "PARTIAL_MISNAMED_RESOLVED"
        row["catalog_display_name"] = PARTIAL_MISNAMED[cid]
    elif cid in NOT_COMPLETE:
        row["closure_status"] = "NOT_COMPLETE"
        row["status"] = "NOT_COMPLETE"
        row["owner_note"] = NOT_COMPLETE[cid]
        if cid in NOT_COMPLETE_TECHNICAL:
            row["miswire_remediation"] = "NOT_COMPLETE_TECHNICAL"


def main() -> None:
    rtm = json.loads(RTM.read_text(encoding="utf-8"))
    rtm["build_phase"] = "BUILD_PHASE_LIFTED_EXCEPT_PAID_VENDOR"
    rtm["generated_at"] = datetime.now(UTC).isoformat()
    pa_count = 0
    for row in rtm["rows"]:
        _patch_row(row)
        if row.get("closure_status") == "PRODUCTION-ALIGNED":
            pa_count += 1
    rtm["production_aligned_count"] = pa_count
    rtm["progress_826_note"] = f"batch04 PA count={pa_count} (excludes paid vendor + blocked deps)"
    RTM.write_text(json.dumps(rtm, indent=2) + "\n", encoding="utf-8")

    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    for cid, name in CATALOG_RENAMES.items():
        key = str(cid)
        if key in inv:
            inv[key]["capability"] = name
            inv[key]["notes"] = (
                f"PARTIAL_MISNAMED — {name}; heuristic local proxy, not Glassnode original."
            )
    INVENTORY.write_text(json.dumps(inv, indent=2) + "\n", encoding="utf-8")

    acc = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    for row in acc["rows"]:
        cid = row["capability_id"]
        if cid in CATALOG_RENAMES:
            row["capability_name"] = CATALOG_RENAMES[cid]
            row["build_decision"] = "PARTIAL_MISNAMED — catalog rename + local heuristic proxy"
    ACCEPTANCE.write_text(json.dumps(acc, indent=2) + "\n", encoding="utf-8")

    print(f"RTM updated — PRODUCTION-ALIGNED: {pa_count}/50")


if __name__ == "__main__":
    main()
