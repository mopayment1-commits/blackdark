"""Shared requirement spine factory for all 11 governing spec domains."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from governance.claims_loader import claims_by_prefix, ordered_ids

_ROOT = Path(__file__).resolve().parent.parent


def _format_id(prefix: str, num: int, width: int) -> str:
    return f"{prefix}{num:0{width}d}"


def build_catalog(
    *,
    prefix: str,
    bgs: str,
    implemented: frozenset[str],
    partial: frozenset[str],
    max_num: int | None = None,
    id_width: int = 3,
    title_source: str | None = None,
    section_pattern: str | None = None,
) -> list[dict[str, Any]]:
    """Build requirement catalog from claims JSON or markdown section parser."""
    rows: list[dict[str, Any]] = []
    titles: dict[str, str] = {}

    if title_source and section_pattern:
        spec_path = _ROOT / title_source
        if spec_path.exists():
            text = spec_path.read_text(encoding="utf-8")
            pat = re.compile(section_pattern, re.MULTILINE)
            for m in pat.finditer(text):
                eid = m.group(1)
                titles[eid] = (m.group(2) if m.lastindex and m.lastindex >= 2 else "").strip()[:120]

    claims = claims_by_prefix(prefix)
    ids = ordered_ids(prefix, max_num=max_num) if claims else []
    if not ids and titles:
        ids = sorted(titles.keys(), key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 0)
    if not ids and max_num:
        ids = [_format_id(prefix, n, id_width) for n in range(1, max_num + 1)]

    for eid in ids:
        if eid in implemented:
            status = "IMPLEMENTED"
        elif eid in partial:
            status = "PARTIAL"
        else:
            status = "SPEC_ONLY"
        claim = claims.get(eid, {})
        title = titles.get(eid) or (claim.get("text") or "")[:120] or eid
        rows.append({"requirement_id": eid, "status": status, "title": title, "bgs": bgs})
    return rows


def build_summary(
    *,
    domain: str,
    bgs: str,
    rows: list[dict[str, Any]],
    honest_min_implemented: int = 3,
    strict_min_implemented: int = 10,
    methodology_version: str = "spine-1.0",
) -> dict[str, Any]:
    counts = {"IMPLEMENTED": 0, "PARTIAL": 0, "SPEC_ONLY": 0}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    total = len(rows)
    strict_key = f"PASS_ENGINEERING_{domain}"
    honest_key = f"{strict_key}_honest"
    return {
        "domain": domain,
        "bgs": bgs,
        "total": total,
        "counts": counts,
        strict_key: counts["SPEC_ONLY"] == 0 and total > 0 and counts["IMPLEMENTED"] + counts["PARTIAL"] == total,
        honest_key: counts["IMPLEMENTED"] >= honest_min_implemented and counts["SPEC_ONLY"] < total,
        "methodology_version": methodology_version,
        "requirements": rows,
    }


def verify_requirement(rows: list[dict[str, Any]], requirement_id: str) -> dict[str, Any]:
    row = next((r for r in rows if r["requirement_id"] == requirement_id), None)
    if not row:
        return {"requirement_id": requirement_id, "ok": False, "reason": "unknown_id"}
    ok = row["status"] in {"IMPLEMENTED", "PARTIAL"}
    return {"requirement_id": requirement_id, "ok": ok, "status": row["status"]}


def verify_all_requirements(rows: list[dict[str, Any]]) -> dict[str, Any]:
    results = [verify_requirement(rows, r["requirement_id"]) for r in rows]
    ok_count = sum(1 for r in results if r["ok"])
    return {
        "total": len(results),
        "ok": ok_count,
        "all_ok": ok_count == len(results) and len(results) > 0,
        "results": results,
    }
