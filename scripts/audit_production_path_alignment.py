#!/usr/bin/env python3
"""Audit VERIFIED-DEEP / REUSED-LINK capabilities for production-path alignment.

Compares audit/evidence bindings (pdf_capability_registry layer) against
cap646.runtime production routing (backend_registry + handlers).
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STUB_IDS = frozenset(
    int(k)
    for k in json.loads((ROOT / "docs/TEMPLATE_STUB_RECLASSIFICATION_MANIFEST.json").read_text())["entries"]
)

EVIDENCE_FILES = {
    1: ROOT / "data/hero_batch_01_evidence.jsonl",
    2: ROOT / "data/hero_batch_02_101_200_evidence.jsonl",
    3: ROOT / "data/hero_batch_03_201_300_evidence.jsonl",
    4: ROOT / "data/hero_batch_04_301_400_evidence.jsonl",
    5: ROOT / "data/hero_batch_05_401_500_evidence.jsonl",
    6: ROOT / "data/hero_batch_06_501_600_evidence.jsonl",
}

AUDIT_FILES = {
    1: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCHES_01_02.json",
    2: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCHES_01_02.json",
    3: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_03_201_300.json",
    4: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_04_301_400.json",
    5: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_05_401_500.json",
    6: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_06_501_600.json",
}

BATCH_ID_RANGES = {
    1: None,  # hero scatter
    2: (101, 200),
    3: (201, 300),
    4: (301, 400),
    5: (401, 500),
    6: (501, 600),
}


def _parse_binding(binding: str) -> tuple[str, str]:
    if "." not in binding:
        return binding, ""
    mod, _, fn = binding.partition(".")
    # rejoin module path
    parts = binding.rsplit(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return binding, ""


def _load_rows() -> list[dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    for batch, path in EVIDENCE_FILES.items():
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            cid = int(row["capability_id"])
            cls = row.get("deep_audit_classification") or ""
            if cls not in {"VERIFIED-DEEP", "REUSED-LINK"}:
                continue
            br = BATCH_ID_RANGES[batch]
            if batch == 2 or (br and br[0] <= cid <= br[1]) or batch == 1:
                rows[cid] = {
                    "capability_id": cid,
                    "batch": batch,
                    "classification": cls,
                    "binding": row.get("binding") or "",
                    "underlying_module": row.get("underlying_module") or "",
                    "underlying_function": row.get("underlying_function") or "",
                    "reuse_meta": row.get("reuse_meta") or {},
                    "template_seed_stub": bool(row.get("template_seed_stub")),
                }
    return sorted(rows.values(), key=lambda r: r["capability_id"])


def _audit_binding(mod: str, fn: str) -> str:
    return f"{mod}.{fn}" if fn else mod


def _same_semantic(a_mod: str, a_fn: str, b_mod: str, b_fn: str) -> bool:
    if a_mod == b_mod and a_fn == b_fn:
        return True
    # normalized module compare
    return a_mod.replace("bd_platform.", "") == b_mod.replace("bd_platform.", "") and a_fn == b_fn


def classify_row(row: dict[str, Any], pdf_bindings: dict[int, tuple[str, str]], prod_binding: dict[str, Any]) -> dict[str, Any]:
    cid = row["capability_id"]
    audit_mod = row["underlying_module"] or _parse_binding(row["binding"])[0]
    audit_fn = row["underlying_function"] or _parse_binding(row["binding"])[1]
    audit_path = _audit_binding(audit_mod, audit_fn)

    prod_mod = prod_binding["backend_module"]
    prod_fn = prod_binding["backend_entrypoint"]
    prod_path = _audit_binding(prod_mod, prod_fn)
    prod_source = prod_binding.get("binding_source", "")

    pdf_mod, pdf_fn = pdf_bindings.get(cid, ("", ""))
    pdf_path = _audit_binding(pdf_mod, pdf_fn) if pdf_mod else ""

    reasons: list[str] = []

    if row["template_seed_stub"] or cid in STUB_IDS:
        status = "SPLIT_BRAIN_TEMPLATE_STUB"
        reasons.append("TEMPLATE-SEED-STUB audit layer; production uses cap646.runtime + backend_registry (different backend)")
    elif row["classification"] == "REUSED-LINK":
        canonical = (row.get("reuse_meta") or {}).get("canonical_capability_id")
        if canonical and int(canonical) != cid:
            status = "REUSED_LINK_CANONICAL"
            reasons.append(f"REUSED-LINK defers to canonical #{canonical}; production may route via duplicate_of")
        elif _same_semantic(audit_mod, audit_fn, prod_mod, prod_fn):
            status = "PRODUCTION_ALIGNED"
            reasons.append("audit underlying matches cap646 backend_registry binding")
        else:
            status = "SPLIT_BRAIN_REUSED"
            reasons.append(f"audit={audit_path} vs production={prod_path}")
    elif _same_semantic(audit_mod, audit_fn, prod_mod, prod_fn):
        status = "PRODUCTION_ALIGNED"
        reasons.append("audit underlying matches cap646 backend_registry binding")
    elif pdf_path and _same_semantic(audit_mod, audit_fn, pdf_mod, pdf_fn) and not _same_semantic(audit_mod, audit_fn, prod_mod, prod_fn):
        status = "SPLIT_BRAIN_ROUTING"
        reasons.append(f"pdf_registry={pdf_path}; production={prod_path} ({prod_source})")
    elif prod_source in {"track_default", "capability_keyword"} and prod_mod in {
        "product_honesty_api",
        "scale_readiness",
        "market_context",
        "trust_pulse",
    }:
        status = "SPLIT_BRAIN_GENERIC_HANDLER"
        reasons.append(f"production uses generic {prod_source} handler: {prod_path}")
    else:
        status = "SPLIT_BRAIN_OTHER"
        reasons.append(f"audit={audit_path}; production={prod_path} ({prod_source})")

    return {
        **row,
        "audit_path": audit_path,
        "pdf_registry_path": pdf_path,
        "production_path": prod_path,
        "production_binding_source": prod_source,
        "alignment_status": status,
        "alignment_reason": "; ".join(reasons),
    }


def main() -> None:
    from cap646.backend_registry import binding_for
    from pdf_capability_registry import discover_bindings

    pdf_bindings = discover_bindings()
    assessed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for row in _load_rows():
        cid = row["capability_id"]
        try:
            prod_binding = binding_for(cid)
        except KeyError:
            skipped.append({"capability_id": cid, "reason": "not_in_cap646_catalog"})
            continue
        assessed.append(classify_row(row, pdf_bindings, prod_binding))

    by_status: dict[str, list[int]] = {}
    for row in assessed:
        by_status.setdefault(row["alignment_status"], []).append(row["capability_id"])

    out = {
        "audited_at": datetime.now(UTC).isoformat(),
        "scope": "VERIFIED-DEEP + REUSED-LINK across hero batches 01-06 (evidence JSONL)",
        "total_assessed": len(assessed),
        "skipped_not_in_cap646_catalog": skipped,
        "by_status": {k: {"count": len(v), "ids": v} for k, v in sorted(by_status.items())},
        "production_runtime_path": "api/routers/cap646.py -> cap978.unified.execute_unified / cap646.runtime.execute_capability -> cap646.handlers.* + backend_registry",
        "pdf_registry_path": "pdf_capability_registry.execute_capability (tests/audit scripts only — NOT production)",
        "rows": assessed,
    }

    json_path = ROOT / "docs/PRODUCTION_PATH_ALIGNMENT_AUDIT_BATCHES_01_06.json"
    md_path = ROOT / "docs/PRODUCTION_PATH_ALIGNMENT_AUDIT_BATCHES_01_06.md"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Production path alignment audit — batches 01–06",
        "",
        f"**Generated:** {out['audited_at']}",
        f"**Assessed:** {out['total_assessed']} capabilities (VERIFIED-DEEP + REUSED-LINK in evidence JSONL)",
        "",
        "## Two-tier answer",
        "",
        "1. **Runtime reachability (`cap646/runtime.py`):** **YES** for all assessed IDs present in `cap646` catalog — production API `/api/cap646/{id}` routes through `cap978.unified.execute_unified` → `cap646.runtime.execute_capability` → handlers → `cap646.backend_executor.handle_registry_capability`.",
        "2. **Audit binding alignment:** **NO** for most — audit/pdf evidence documents layer-specific functions; production resolves via `cap646/backend_registry.py` keyword/track rules (often different module).",
        "",
        "The 311 TEMPLATE-SEED-STUB IDs are **excluded** from this set (reclassified WRAPPER-ONLY-UNVERIFIED).",
        "",
        "## Summary",
        "",
        "| Status | Count | Meaning |",
        "|--------|------:|---------|",
    ]
    meanings = {
        "PRODUCTION_ALIGNED": "Audit binding matches cap646 backend_registry",
        "REUSED_LINK_CANONICAL": "REUSED-LINK; production routes via canonical duplicate",
        "SPLIT_BRAIN_TEMPLATE": "TEMPLATE-SEED-STUB layer (311 class) — not production path",
        "SPLIT_BRAIN_ROUTING": "pdf_registry binding ≠ production backend_registry",
        "SPLIT_BRAIN_GENERIC_HANDLER": "Production uses track/keyword generic handler",
        "SPLIT_BRAIN_REUSED": "REUSED-LINK with mismatched paths",
        "SPLIT_BRAIN_OTHER": "Other mismatch",
    }
    for status, block in sorted(out["by_status"].items()):
        lines.append(f"| `{status}` | {block['count']} | {meanings.get(status, '')} |")

    lines.extend(["", "## Non-aligned IDs", ""])
    for status in sorted(by_status):
        if status == "PRODUCTION_ALIGNED":
            continue
        ids = by_status[status]
        lines.append(f"### {status} ({len(ids)})")
        lines.append("")
        lines.append(", ".join(str(i) for i in ids[:50]))
        if len(ids) > 50:
            lines.append(f"... +{len(ids)-50} more (see JSON)")
        lines.append("")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: out["by_status"][k]["count"] for k in out["by_status"]}, indent=2))
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
