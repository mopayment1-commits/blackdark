#!/usr/bin/env python3
"""Extract DATA-001..100 and RESTORE-001..011 primary requirements from governing spec."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "governing-sources-population/BLACKDARK_INSTITUTIONAL_DATA_INTELLIGENCE_GOVERNANCE_SPEC_2026_FINAL_v2_RESTORED.md"
OUT_DIR = ROOT / "institutional_due_diligence_2026/DATA_GOV_COMPLIANCE"

PARENT_RE = re.compile(r"^## (DATA-\d+|RESTORE-\d+) — (.+)$", re.MULTILINE)
NORMATIVE_RE = re.compile(r"\b(MUST NOT|MUST|SHALL NOT|SHALL|REQUIRED)\b", re.IGNORECASE)


def _spec_text() -> str:
    if not SPEC.is_file():
        alt = ROOT / "governing-sources-population/BLACKDARK_INSTITUTIONAL_DATA_INTELLIGENCE_GOVERNANCE_SPEC_2026_FINAL_v2_RESTORED(1).md"
        return alt.read_text(encoding="utf-8") if alt.is_file() else ""
    return SPEC.read_text(encoding="utf-8")


def extract_primary_requirements() -> list[dict]:
    text = _spec_text()
    matches = list(PARENT_RE.finditer(text))
    rows: list[dict] = []
    for i, m in enumerate(matches):
        rid, title = m.group(1), m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        normative_lines = []
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("- ") or NORMATIVE_RE.search(stripped):
                normative_lines.append(stripped.lstrip("- ").strip())
        rows.append(
            {
                "requirement_id": rid,
                "title": title,
                "parent_type": "RESTORE" if rid.startswith("RESTORE") else "DATA",
                "normative_clause_count": len(normative_lines),
                "normative_clauses": normative_lines,
            }
        )
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = extract_primary_requirements()
    data_count = sum(1 for r in rows if r["parent_type"] == "DATA")
    restore_count = sum(1 for r in rows if r["parent_type"] == "RESTORE")
    payload = {
        "specification": str(SPEC.relative_to(ROOT)),
        "primary_requirements": rows,
        "DATA_PARENT_COUNT": data_count,
        "RESTORE_PARENT_COUNT": restore_count,
        "PRIMARY_TOTAL": len(rows),
    }
    (OUT_DIR / "DATA_GOV_PRIMARY_REQUIREMENTS.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"primary": len(rows), "data": data_count, "restore": restore_count}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
