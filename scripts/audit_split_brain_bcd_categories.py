#!/usr/bin/env python3
"""Live audit of SPLIT_BRAIN_REUSED / OTHER / GENERIC_HANDLER categories (58 IDs).

Methodology mirrors SPLIT_BRAIN_ROUTING severity report:
audit binding vs production backend + user outcome verdict; ≥10 samples per category.
"""

from __future__ import annotations

import asyncio
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CATEGORIES = (
    "SPLIT_BRAIN_REUSED",
    "SPLIT_BRAIN_OTHER",
    "SPLIT_BRAIN_GENERIC_HANDLER",
)

GENERIC_SURFACES = frozenset(
    {"platform_codepath", "generic", "unknown", "scale_readiness", "product_honesty"}
)


def _load_audit_rows() -> dict[str, list[dict[str, Any]]]:
    data = json.loads((ROOT / "docs/PRODUCTION_PATH_ALIGNMENT_AUDIT_BATCHES_01_06.json").read_text())
    by_cat: dict[str, list[dict[str, Any]]] = {c: [] for c in CATEGORIES}
    for row in data["rows"]:
        status = row.get("alignment_status")
        if status in by_cat:
            by_cat[status].append(row)
    return by_cat


def _sample(rows: list[dict[str, Any]], n: int = 10) -> list[dict[str, Any]]:
    if len(rows) <= n:
        return rows
    rng = random.Random(646)
    return sorted(rng.sample(rows, n), key=lambda r: r["capability_id"])


def _audit_executed_in_prod(audit_path: str, prod_result: dict[str, Any], prod_binding: dict[str, Any]) -> bool:
    if not audit_path:
        return False
    audit_mod, _, audit_fn = audit_path.rpartition(".")
    prod_mod = str(prod_result.get("backend_module") or prod_binding.get("backend_module") or "")
    prod_fn = str(prod_result.get("backend_entrypoint") or prod_binding.get("backend_entrypoint") or "")
    if audit_mod and audit_fn and audit_mod == prod_mod and audit_fn == prod_fn:
        return True
    handler = str(prod_result.get("handler") or "")
    if audit_fn and audit_fn in handler:
        return True
    surface = str(prod_result.get("surface") or "")
    if audit_fn and audit_fn in surface:
        return True
    return False


def _user_outcome(catalog_name: str, audit_path: str, prod_result: dict[str, Any], prod_binding: dict[str, Any]) -> str:
    if _audit_executed_in_prod(audit_path, prod_result, prod_binding):
        return "ALIGNED"

    name = catalog_name.lower()
    surface = str(prod_result.get("surface") or prod_binding.get("surface") or "").lower()
    prod_mod = str(prod_result.get("backend_module") or prod_binding.get("backend_module") or "").lower()

    name_tokens = {t for t in name.replace("&", " ").replace("/", " ").split() if len(t) > 3}
    surface_tokens = set(surface.replace("_", " ").split())
    overlap = name_tokens & surface_tokens

    if any(k in name for k in ("alert", "smart alert")) and "alert" in surface:
        return "PARTIAL"
    if any(k in name for k in ("options", "ohlcv", "cvd", "funding")) and any(
        k in surface or k in prod_mod for k in ("options", "ohlcv", "cvd", "funding", "derivatives")
    ):
        return "PARTIAL"
    if overlap:
        return "PARTIAL"
    if surface in GENERIC_SURFACES or prod_mod in {"scale_readiness", "product_honesty_api", "trust_pulse"}:
        return "WRONG"
    if not prod_result.get("success"):
        return "WRONG"
    return "WRONG"


async def _live_row(row: dict[str, Any]) -> dict[str, Any]:
    from cap646.backend_registry import binding_for
    from cap646.catalog import catalog_by_id
    from cap646.runtime import execute_capability

    cid = int(row["capability_id"])
    catalog_name = catalog_by_id().get(cid, {}).get("capability", "")
    prod_binding = binding_for(cid)
    try:
        prod_result = await execute_capability(cid, skip_entitlement=True, params={"symbol": "BTC"})
    except Exception as exc:
        prod_result = {"success": False, "error": str(exc)}

    audit_path = row.get("audit_path") or ""
    executed = _audit_executed_in_prod(audit_path, prod_result, prod_binding)
    outcome = _user_outcome(catalog_name, audit_path, prod_result, prod_binding)
    dedicated = str(prod_result.get("surface") or "") not in GENERIC_SURFACES and prod_binding.get(
        "binding_source"
    ) not in {"track_default"}

    return {
        "capability_id": cid,
        "catalog_name": catalog_name,
        "audit_path": audit_path,
        "production_path": row.get("production_path") or f"{prod_binding['backend_module']}.{prod_binding['backend_entrypoint']}",
        "production_binding_source": prod_binding.get("binding_source"),
        "live_surface": prod_result.get("surface"),
        "live_backend_module": prod_result.get("backend_module"),
        "live_backend_entrypoint": prod_result.get("backend_entrypoint"),
        "audit_executed_in_prod": executed,
        "real_dedicated_execution": dedicated and bool(prod_result.get("success")),
        "user_outcome_verdict": outcome,
        "success": bool(prod_result.get("success")),
    }


async def _audit_category(status: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    panel = _sample(rows, 10)
    live = [await _live_row(r) for r in panel]
    executed = sum(1 for r in live if r["audit_executed_in_prod"])
    dedicated = sum(1 for r in live if r["real_dedicated_execution"])
    outcomes: dict[str, int] = {}
    for r in live:
        outcomes[r["user_outcome_verdict"]] = outcomes.get(r["user_outcome_verdict"], 0) + 1
    return {
        "category": status,
        "population_count": len(rows),
        "sample_size": len(panel),
        "audit_binding_executed_in_prod_pct": round(100.0 * executed / max(1, len(live)), 1),
        "real_dedicated_execution_pct": round(100.0 * dedicated / max(1, len(live)), 1),
        "user_outcome_counts": outcomes,
        "panel": live,
    }


async def main() -> None:
    by_cat = _load_audit_rows()
    results = []
    for cat in CATEGORIES:
        results.append(await _audit_category(cat, by_cat[cat]))

    out = {
        "audited_at": datetime.now(UTC).isoformat(),
        "methodology": (
            "audit binding vs cap646.runtime production backend + live execute_capability; "
            "user outcome verdict (ALIGNED/PARTIAL/WRONG)"
        ),
        "categories": results,
        "totals": {
            "SPLIT_BRAIN_REUSED": len(by_cat["SPLIT_BRAIN_REUSED"]),
            "SPLIT_BRAIN_OTHER": len(by_cat["SPLIT_BRAIN_OTHER"]),
            "SPLIT_BRAIN_GENERIC_HANDLER": len(by_cat["SPLIT_BRAIN_GENERIC_HANDLER"]),
            "combined": sum(len(by_cat[c]) for c in CATEGORIES),
        },
    }

    json_path = ROOT / "docs/SPLIT_BRAIN_BCD_CATEGORIES_AUDIT.json"
    md_path = ROOT / "docs/SPLIT_BRAIN_BCD_CATEGORIES_AUDIT.md"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# SPLIT_BRAIN categories B/C/D — live audit (58 capabilities)",
        "",
        f"**Generated:** {out['audited_at']}",
        "",
        "| Category | Population | Sample | Audit fn in prod % | Dedicated exec % | Outcomes |",
        "|----------|----------:|-------:|-------------------:|-----------------:|----------|",
    ]
    for block in results:
        oc = ", ".join(f"{k}:{v}" for k, v in sorted(block["user_outcome_counts"].items()))
        lines.append(
            f"| `{block['category']}` | {block['population_count']} | {block['sample_size']} | "
            f"{block['audit_binding_executed_in_prod_pct']}% | {block['real_dedicated_execution_pct']}% | {oc} |"
        )
    lines.extend(["", "## Sample panels", ""])
    for block in results:
        lines.append(f"### {block['category']} (n={block['sample_size']})")
        lines.append("")
        lines.append("| ID | Catalog | Audit path | Production path | Audit in prod? | Verdict |")
        lines.append("|----|---------|------------|-----------------|----------------|---------|")
        for r in block["panel"]:
            lines.append(
                f"| {r['capability_id']} | {r['catalog_name'][:40]} | `{r['audit_path']}` | "
                f"`{r['production_path']}` | {'YES' if r['audit_executed_in_prod'] else 'NO'} | {r['user_outcome_verdict']} |"
            )
        lines.append("")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"totals": out["totals"], "categories": [c["category"] for c in results]}, indent=2))
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    asyncio.run(main())
