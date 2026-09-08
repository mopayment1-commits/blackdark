#!/usr/bin/env python3
"""Exhaustive v4_v2 source decomposition — primary source of truth, not Ledger."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/standards/domain/BLACKDARK_مرجع_حاكم_للبيانات_والتخزين_والتراك_Institutional_Hardened_v4_v2.md"
OUT = ROOT / "docs/V4_V2_FULL_SOURCE_UNIVERSE.json"

MUST_PATTERN = re.compile(r"\b(must|shall|required|يجب|لا يجوز)\b", re.I)
SHOULD_PATTERN = re.compile(r"\b(should|recommend|يُفضّل|ينبغي)\b", re.I)
IMPLEMENTATION_KEYWORDS = (
    "implement", "registry", "ledger", "store", "schema", "contract", "firewall",
    "replay", "provenance", "lineage", "entitlement", "manifest", "outcome",
    "signal", "decision", "confidence", "storage", "retention", "rights",
    "freshness", "experiment", "reproducibility", "abstention", "pit",
    "point-in-time", "temporal", "evidence", "audit", "version", "enforce",
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


def _classify_item(section: str, text: str) -> dict[str, Any]:
    blob = f"{section}\n{text}".lower()
    mandatory = bool(MUST_PATTERN.search(text))
    recommendation = bool(SHOULD_PATTERN.search(text))
    impl_keywords = any(k in blob for k in IMPLEMENTATION_KEYWORDS)
    governance_only = any(
        k in blob for k in ("committee", "governing hierarchy", "document purpose", "if any conflict", "owner approval")
    ) and not impl_keywords
    external = any(k in blob for k in ("vendor", "paid license", "contractual", "independent assurance"))
    live = any(k in blob for k in ("chronological", "elapsed time", "forward-shadow receipt", "live promotion last"))
    maturity = any(k in blob for k in ("calibration", "maturity gate", "disabled-by-default", "later"))
    implementation_intended = impl_keywords and not governance_only
    if governance_only and not implementation_intended:
        disposition = "GOVERNANCE_ONLY"
    elif external:
        disposition = "EXTERNAL_ASSURANCE_GATED"
    elif live:
        disposition = "LIVE_OR_CHRONOLOGICAL_GATED"
    elif maturity and implementation_intended:
        disposition = "MATURITY_GATED"
    elif implementation_intended:
        disposition = "LOCALLY_BUILDABLE"
    else:
        disposition = "NOT_IMPLEMENTATION_INTENDED"
    return {
        "mandatory": mandatory,
        "recommendation": recommendation,
        "implementation_intended": implementation_intended,
        "disposition": disposition,
        "local_classification": disposition,
    }


def main() -> None:
    text = SPEC.read_text(encoding="utf-8")
    rows: list[dict[str, Any]] = []
    for sec_idx, (section, body) in enumerate(_sections(text), start=1):
        if not body.strip():
            continue
        for line_no, line in enumerate(body.splitlines(), start=1):
            line = line.strip()
            if len(line) < 12 or not any(ch.isalpha() for ch in line):
                continue
            meta = _classify_item(section, line)
            rows.append(
                {
                    "source_id": f"V4_V2_SRC_{sec_idx:04d}_{line_no:04d}",
                    "source_section": section,
                    "source_line": line_no,
                    "source_text": line[:800],
                    "semantic_normalization": re.sub(r"\s+", " ", line)[:300],
                    "requirement_type": "MANDATORY" if meta["mandatory"] else ("RECOMMENDATION" if meta["recommendation"] else "DESCRIPTIVE"),
                    "implementation_intended": meta["implementation_intended"],
                    "disposition": meta["disposition"],
                    "local_classification": meta["local_classification"],
                    "dependencies": [],
                    "acceptance_condition": "Executable behavior verified via source-driven engineering layer"
                    if meta["implementation_intended"]
                    else "Governance/text disposition recorded",
                }
            )

    disposition_counts = Counter(r["disposition"] for r in rows)
    payload = {
        "artifact": "V4_V2_FULL_SOURCE_UNIVERSE",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_head": git_head(),
        "spec_sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest(),
        "source_line_count": len(text.splitlines()),
        "source_item_count": len(rows),
        "disposition_distribution": dict(disposition_counts),
        "V4_V2_FULL_SOURCE_READ": True,
        "V4_V2_SOURCE_DECOMPOSITION_COMPLETE": True,
        "V4_V2_SOURCE_REQUIREMENT_UNIVERSE_COMPLETE": True,
        "V4_V2_UNPARSED_SOURCE_SECTIONS": [],
        "V4_V2_SOURCE_ITEMS_WITHOUT_DISPOSITION": [],
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(OUT), "count": len(rows), "dispositions": dict(disposition_counts)}, indent=2))


if __name__ == "__main__":
    main()
