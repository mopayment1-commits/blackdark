#!/usr/bin/env python3
"""Program §8.2 — lock allowed release attestation wording; detect forbidden CISA claims in governed paths."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTEST = ROOT / "governance" / "launch57" / "LAUNCH57_RELEASE_ATTESTATION_82.json"
PROGRAM = ROOT / "docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md"
SCAN_ROOTS = (
    ROOT / "api/routers",
)
SCAN_FILES = (
    ROOT / "security_posture.py",
    ROOT / "launch57_assurance_closure.py",
)
SCAN_DOC_GOVERNANCE = (
    ROOT / "docs/governance/LAUNCH57_REMEDIATION_EXECUTIVE_SUMMARY_AR.md",
    ROOT / "docs/governance/LAUNCH57_ENGINEERING_CLOSURE_DECLARATION.md",
    ROOT / "docs/governance/SECURE_BY_DESIGN_PROGRESS_2026.md",
)


def _extract_program_82_quote(text: str) -> str | None:
    marker = "### 8.2 Release attestation (allowed wording)"
    if marker not in text:
        return None
    block = text.split(marker, 1)[1]
    if ">" not in block:
        return None
    quote = block.split(">", 1)[1].split("\n", 1)[0].strip()
    if quote.startswith("“"):
        quote = quote[1:]
    if quote.endswith("”"):
        quote = quote[:-1]
    return quote


def _scan_forbidden(paths: list[Path], phrases: list[str]) -> list[str]:
    hits: list[str] = []
    for base in paths:
        if base.is_file():
            files = [base]
        elif base.is_dir():
            files = [p for p in base.rglob("*") if p.suffix in {".md", ".json", ".py"} and p.is_file()]
        else:
            continue
        for path in files:
            if "LAUNCH57_RELEASE_ATTESTATION_82.json" in str(path):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                lower = line.lower()
                if "not cisa certification" in lower or "cisa_certification_claimed" in lower:
                    continue
                if "forbidden_phrases" in line or "non-goals" in lower or "claiming" in lower:
                    continue
                if "ممنوع" in line or "§1.2" in line:
                    continue
                for phrase in phrases:
                    if phrase.lower() in lower:
                        hits.append(f"{path.relative_to(ROOT)}:{line_no}: {phrase}")
    return hits


def main() -> int:
    if not ATTEST.is_file() or not PROGRAM.is_file():
        print("MISSING attestation register or program", file=sys.stderr)
        return 1
    reg = json.loads(ATTEST.read_text(encoding="utf-8"))
    if reg.get("cisa_certification_claimed"):
        print("REGISTER must keep cisa_certification_claimed false", file=sys.stderr)
        return 1
    program_text = PROGRAM.read_text(encoding="utf-8")
    quote = _extract_program_82_quote(program_text)
    allowed = str(reg.get("allowed_attestation_en", ""))
    if not quote or quote != allowed:
        print("ATTESTATION_82_DRIFT: allowed text must match program §8.2 blockquote exactly", file=sys.stderr)
        return 1
    idx_rel = reg.get("evidence_index_path")
    if not idx_rel or not (ROOT / idx_rel).is_file():
        print(f"missing evidence index {idx_rel}", file=sys.stderr)
        return 1
    phrases = list(reg.get("forbidden_phrases") or [])
    scan_paths = list(SCAN_ROOTS) + list(SCAN_FILES) + list(SCAN_DOC_GOVERNANCE)
    hits = _scan_forbidden(scan_paths, phrases)
    if hits:
        print("FORBIDDEN_CISA_CLAIM_SCAN:", file=sys.stderr)
        for h in hits[:40]:
            print(f"  - {h}", file=sys.stderr)
        if len(hits) > 40:
            print(f"  ... and {len(hits) - 40} more", file=sys.stderr)
        return 1
    print(json.dumps({"pass": True, "program_section": reg.get("program_section"), "cisa_certification_claimed": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
