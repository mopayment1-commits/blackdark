#!/usr/bin/env python3
"""Audit all historical 'complete evidence' sample IDs for registry reachability."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXTENSION_KNOWN = frozenset({704, 708, 725, 812, 813, 814, 815})
SEVERITY_PANEL = [2, 18, 49, 59, 60, 101, 201, 316, 409, 517]
OPTION_A = frozenset({338, 500, 507, 534})


def _collect_sample_ids() -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}

    for path in sorted(ROOT.glob("docs/HERO_BATCH_*SAMPLE*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        ids: list[int] = []
        items = data if isinstance(data, list) else data.get("samples", [])
        for item in items:
            if isinstance(item, dict) and "capability_id" in item:
                ids.append(int(item["capability_id"]))
        out[path.name] = sorted(set(ids))

    out["SPLIT_BRAIN_ROUTING_SEVERITY_PANEL"] = SEVERITY_PANEL

    for path in sorted(ROOT.glob("docs/HERO_BATCH_*_GAP_REPORT.json")):
        gap = json.loads(path.read_text(encoding="utf-8"))
        ok_ids = []
        for row in gap.get("rows", []):
            if row.get("live_ok") or row.get("status") == "ok":
                ok_ids.append(int(row["capability_id"]))
        if ok_ids:
            out[path.name + "_live_ok"] = sorted(set(ok_ids))

    # Hero manual bindings called out in completion report
    out["HERO_BATCH_01_COMPLETION_REPORT_manual_bindings"] = sorted(
        {629, 382, 111, 812, 813, 814, 815}
    )

    return out


def _probe_registry(capability_id: int) -> dict[str, Any]:
    row: dict[str, Any] = {"capability_id": capability_id}

    try:
        from cap646.catalog import catalog_by_id

        row["in_cap646_catalog"] = capability_id in catalog_by_id()
    except Exception as exc:
        row["in_cap646_catalog"] = False
        row["cap646_catalog_error"] = str(exc)

    try:
        from cap646.backend_registry import binding_for

        row["cap646_binding"] = binding_for(capability_id)
        row["cap646_registry_ok"] = True
    except KeyError:
        row["cap646_registry_ok"] = False
        row["cap646_binding_error"] = "KeyError:not_in_cap646_catalog"
    except Exception as exc:
        row["cap646_registry_ok"] = False
        row["cap646_binding_error"] = str(exc)

    try:
        from pdf_capability_registry import discover_bindings

        pdf = discover_bindings()
        if capability_id in pdf:
            mod, fn = pdf[capability_id]
            row["pdf_registry_path"] = f"{mod}.{fn}"
            row["pdf_registry_ok"] = True
        else:
            row["pdf_registry_ok"] = False
    except Exception as exc:
        row["pdf_registry_ok"] = False
        row["pdf_registry_error"] = str(exc)

    try:
        import asyncio
        from cap646.runtime import execute_capability

        result = asyncio.run(
            execute_capability(capability_id, skip_entitlement=True, params={"symbol": "BTC"})
        )
        row["cap646_runtime_ok"] = bool(result.get("success"))
        row["cap646_runtime_surface"] = result.get("surface")
        row["cap646_runtime_backend"] = (
            f"{result.get('backend_module')}.{result.get('backend_entrypoint')}"
            if result.get("backend_module")
            else None
        )
    except Exception as exc:
        row["cap646_runtime_ok"] = False
        row["cap646_runtime_error"] = str(exc)

    if capability_id in OPTION_A:
        row["expected_status"] = "PRODUCTION-ALIGNED"
    elif capability_id in EXTENSION_KNOWN:
        row["expected_status"] = "EXTENSION-PENDING-CAP646"
    elif not row.get("cap646_registry_ok"):
        row["incident_class"] = "REGISTRY_PHANTOM_SUCCESS"
    elif row.get("cap646_runtime_ok") and row.get("cap646_registry_ok"):
        row["incident_class"] = "RUNTIME_OK_REGISTRY_OK"
    else:
        row["incident_class"] = "REGISTRY_PRESENT_RUNTIME_ISSUE"

    return row


def main() -> None:
    sources = _collect_sample_ids()
    all_ids = sorted({i for ids in sources.values() for i in ids})

    probes = [_probe_registry(cid) for cid in all_ids]
    phantom = [
        p
        for p in probes
        if p.get("incident_class") == "REGISTRY_PHANTOM_SUCCESS"
        or (not p.get("cap646_registry_ok") and p.get("pdf_registry_ok"))
    ]

    out = {
        "audited_at": datetime.now(UTC).isoformat(),
        "scope": "All historical complete-evidence sample IDs across hero batch dossiers + severity panel + batch01 gap live_ok",
        "total_unique_sample_ids": len(all_ids),
        "sources": sources,
        "registry_phantom_count": len(phantom),
        "registry_phantom_ids": [p["capability_id"] for p in phantom],
        "known_extension_ids": sorted(EXTENSION_KNOWN),
        "new_phantom_beyond_known_five": sorted(
            set(p["capability_id"] for p in phantom) - EXTENSION_KNOWN
        ),
        "probes": probes,
        "severity": (
            "Same class as 311/202: audit/pdf_registry reported success while cap646 production registry "
            "has no binding (KeyError). Historical quad-evidence used pdf_capability_registry.execute_capability, "
            "NOT GET /api/cap646/{id}."
        ),
    }

    json_path = ROOT / "docs/REGISTRY_PHANTOM_SUCCESS_AUDIT.json"
    md_path = ROOT / "docs/REGISTRY_PHANTOM_SUCCESS_AUDIT.md"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Registry phantom-success audit — historical evidence samples",
        "",
        f"**Generated:** {out['audited_at']}",
        "",
        "## Executive finding",
        "",
        f"- Sample IDs audited: **{out['total_unique_sample_ids']}**",
        f"- Registry phantom (pdf ok, cap646 KeyError): **{out['registry_phantom_count']}**",
        f"- Known extension pending: `{', '.join(str(i) for i in out['known_extension_ids'])}`",
        f"- **New phantoms beyond known five:** `{', '.join(str(i) for i in out['new_phantom_beyond_known_five']) or 'NONE'}`",
        "",
        "## Phantom / extension rows",
        "",
        "| ID | pdf_registry | cap646 registry | cap646 runtime | Class |",
        "|----|--------------|-----------------|----------------|-------|",
    ]
    for p in probes:
        if p["capability_id"] in EXTENSION_KNOWN or p.get("incident_class") == "REGISTRY_PHANTOM_SUCCESS":
            lines.append(
                f"| {p['capability_id']} | {'YES' if p.get('pdf_registry_ok') else 'NO'} | "
                f"{'YES' if p.get('cap646_registry_ok') else 'NO'} | "
                f"{'YES' if p.get('cap646_runtime_ok') else 'NO'} | {p.get('incident_class','')} |"
            )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"phantom": out["registry_phantom_ids"], "new": out["new_phantom_beyond_known_five"]}, indent=2))


if __name__ == "__main__":
    main()
