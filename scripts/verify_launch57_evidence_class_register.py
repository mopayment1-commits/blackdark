#!/usr/bin/env python3
"""Program §3.2/§6 — evidence class register matches inventory; repo satisfies E-ART where indexed."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "governance" / "launch57" / "LAUNCH57_EVIDENCE_CLASS_REGISTER.json"
INDEX = ROOT / "governance/launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"
LOCK = ROOT / "governance/launch57/FINDING_INVENTORY_LOCK.json"
SKIP = ("GET ", "POST ")


def main() -> int:
    if not all(p.is_file() for p in (REGISTER, INDEX, LOCK)):
        print("MISSING register, index, or lock", file=sys.stderr)
        return 1
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    allowed = set(reg.get("allowed_evidence_classes") or [])
    lock_ids = list(json.loads(LOCK.read_text(encoding="utf-8")).get("expected_ids") or [])
    reg_findings = reg.get("findings") or {}
    index_findings = json.loads(INDEX.read_text(encoding="utf-8")).get("findings") or {}
    errors: list[str] = []
    if sorted(reg_findings.keys()) != sorted(lock_ids):
        errors.append("evidence class register keys differ from inventory lock")
    for fid in lock_ids:
        if fid not in index_findings:
            errors.append(f"{fid}: missing from evidence index")
            continue
        classes = reg_findings.get(fid, {}).get("required_for_full_closure") or []
        for cid in classes:
            if cid not in allowed:
                errors.append(f"{fid}: unknown evidence class {cid}")
        irow = index_findings[fid]
        evidence = [e for e in (irow.get("evidence") or []) if isinstance(e, str) and not e.startswith(SKIP)]
        if "E-ART" in classes and not evidence:
            errors.append(f"{fid}: E-ART required but no repo evidence paths in index")
        for rel in evidence:
            if not (ROOT / rel).is_file():
                errors.append(f"{fid}: missing E-ART path {rel}")
        st = str(irow.get("status", ""))
        if st.startswith("OPEN") and not (irow.get("closure_requires") or irow.get("note")):
            errors.append(f"{fid}: OPEN status requires closure_requires or note in index")
    if errors:
        print("EVIDENCE_CLASS_REGISTER_FAIL:", file=sys.stderr)
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(f"PASS: {len(lock_ids)} findings mapped to program §3.2 evidence classes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())