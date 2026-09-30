#!/usr/bin/env python3
"""Regenerate LAUNCH57_OPEN_FINDINGS_REGISTER.md from evidence index (honest)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"
PKG = ROOT / "governance/launch57/LAUNCH57_OPEN_OPS_CLOSURE_PACKAGE.json"
OUT = ROOT / "governance/launch57/LAUNCH57_OPEN_FINDINGS_REGISTER.md"

NON_CLOSED = frozenset({"CLOSED"})


def main() -> int:
    if not INDEX.is_file():
        return 1
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    pkg = json.loads(PKG.read_text(encoding="utf-8")) if PKG.is_file() else {}
    pkg_rows = pkg.get("open_or_partial_findings") or {}
    lines = [
        "# Launch-57 — Open findings register (honest)",
        "",
        "Generated from `CISA_REMEDIATION_EVIDENCE_INDEX.json`. **Not** a certification.",
        "",
        "| ID | Status | Owner | Closure action |",
        "|----|--------|-------|----------------|",
    ]
    for fid in sorted((idx.get("findings") or {}).keys()):
        row = idx["findings"][fid]
        st = str(row.get("status", ""))
        if st == "CLOSED":
            continue
        pspec = pkg_rows.get(fid) or {}
        owner = pspec.get("owner") or "—"
        action = row.get("closure_requires") or row.get("note") or pspec.get("closure_requires") or "—"
        lines.append(f"| {fid} | {st} | {owner} | {action} |")
    lines.extend(
        [
            "",
            "**Ops closure package (SSOT):** `governance/launch57/LAUNCH57_OPEN_OPS_CLOSURE_PACKAGE.json`",
            "",
            "**Aggregate report:** `python scripts/launch57_closure_report.py`",
            "**PR merge gates:** `python scripts/verify_launch57_pr_merge_checklist_gates.py`",
            "",
            "Regenerate: `python scripts/generate_launch57_open_findings_register.py`",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
