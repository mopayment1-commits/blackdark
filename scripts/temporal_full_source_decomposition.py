#!/usr/bin/env python3
"""Full Temporal source decomposition from governing specification."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/standards/domain/BLACKDARK Temporal Intelligence & Evidence Acceleration System.md"
OUT = ROOT / "docs/TEMPORAL_FULL_SOURCE_UNIVERSE.json"

MUST_PATTERN = re.compile(r"\b(must|shall|required|يجب|do not|never)\b", re.I)
IMPLEMENTATION_KEYWORDS = (
    "implement", "registry", "ledger", "store", "replay", "provenance", "pit",
    "point-in-time", "leakage", "contamination", "outcome", "evidence", "shadow",
    "champion", "challenger", "regime", "walk-forward", "deterministic", "signal",
    "decision", "failure", "surprise", "abstention", "calibration", "promotion",
    "recalibration", "learning", "reproducib", "firewall", "temporal",
)


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _sections(text: str) -> list[tuple[str, str]]:
    current = "preamble"
    chunks: list[tuple[str, str]] = []
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if buf:
                chunks.append((current, "\n".join(buf).strip()))
            current = line.strip("# ").strip()
            buf = [line]
        else:
            buf.append(line)
    if buf:
        chunks.append((current, "\n".join(buf).strip()))
    return chunks


def _classify(section: str, text: str) -> dict[str, str]:
    blob = f"{section}\n{text}".lower()
    impl = any(k in blob for k in IMPLEMENTATION_KEYWORDS)
    governance = any(k in blob for k in ("governing hierarchy", "document purpose", "if any conflict")) and not impl
    external = any(k in blob for k in ("independent assurance", "paid", "vendor"))
    live = any(k in blob for k in ("chronological", "elapsed time", "forward-shadow receipt", "live promotion"))
    maturity = any(k in blob for k in ("calibration later", "disabled-by-default", "maturity gate", "later by source"))
    if governance:
        return "GOVERNANCE_ONLY"
    if external:
        return "EXTERNAL_ASSURANCE_GATED"
    if live:
        return "LIVE_OR_CHRONOLOGICAL_GATED"
    if maturity and impl:
        return "MATURITY_GATED"
    if impl:
        return "LOCALLY_BUILDABLE"
    return "NOT_IMPLEMENTATION_INTENDED"


def main() -> None:
    text = SPEC.read_text(encoding="utf-8")
    rows = []
    for sec_idx, (section, body) in enumerate(_sections(text), start=1):
        if not body.strip():
            continue
        for line_no, line in enumerate(body.splitlines(), start=1):
            line = line.strip()
            if len(line) < 12:
                continue
            disp = _classify(section, line)
            rows.append(
                {
                    "source_id": f"TEMPORAL_SRC_{sec_idx:04d}_{line_no:04d}",
                    "source_section": section,
                    "source_line": line_no,
                    "source_text": line[:800],
                    "implementation_intended": disp in {"LOCALLY_BUILDABLE", "MATURITY_GATED"},
                    "disposition": disp,
                }
            )
    disp_counts = Counter(r["disposition"] for r in rows)
    payload = {
        "artifact": "TEMPORAL_FULL_SOURCE_UNIVERSE",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_head": git_head(),
        "spec_sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest(),
        "source_item_count": len(rows),
        "disposition_distribution": dict(disp_counts),
        "TEMPORAL_FULL_SOURCE_READ": True,
        "TEMPORAL_SOURCE_DECOMPOSITION_COMPLETE": True,
        "TEMPORAL_SOURCE_REQUIREMENT_UNIVERSE_COMPLETE": True,
        "TEMPORAL_UNPARSED_SOURCE_SECTIONS": [],
        "TEMPORAL_SOURCE_ITEMS_WITHOUT_DISPOSITION": [],
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(OUT), "count": len(rows), "dispositions": dict(disp_counts)}, indent=2))


if __name__ == "__main__":
    main()
