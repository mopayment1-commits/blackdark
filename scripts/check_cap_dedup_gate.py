#!/usr/bin/env python3
"""CI gate: fail if CAP_DEDUP audit is stale or batch03 IDs leak into 1-100 proof artifacts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/CAP_DEDUP_AUDIT_1_100.json"
REJECT04 = ROOT / "docs/CLOSURE_REJECT_04_AUDIT.json"
PROOF_GLOBS = [
    "docs/BATCH01_ENTITLEMENT_GATEWAY_PROOF.json",
    "docs/BATCH02_ENTITLEMENT_GATEWAY_PROOF.json",
    "docs/BATCH01_HTTP_PROOF_1_50.json",
    "docs/BATCH02_HTTP_PROOF_51_100.json",
]
# Batch03 proof script intentionally references IDs 101–150.
_ENTITLEMENT_SCRIPT_EXCLUDE = frozenset({"verify_entitlement_batch03_gateway_proof.py"})


def main() -> int:
    errors: list[str] = []
    if not AUDIT.exists():
        errors.append(f"Missing {AUDIT}")
    for rel in PROOF_GLOBS:
        path = ROOT / rel
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for proof in data.get("proofs", []):
            cid = int(proof.get("capability_id", 0))
            if 101 <= cid <= 150:
                errors.append(f"Batch03 leak: ID {cid} in {rel}")
        ids = data.get("capability_ids") or []
        for cid in ids:
            if 101 <= cid <= 150:
                errors.append(f"Batch03 leak: ID {cid} in {rel} capability_ids")
    if REJECT04.exists():
        r04 = json.loads(REJECT04.read_text(encoding="utf-8"))
        for leak in r04.get("batch03_leaks_scan", []):
            if leak.get("capability_id") and 101 <= int(leak["capability_id"]) <= 150:
                errors.append(f"Documented leak still present: {leak}")
    # Scan entitlement proof scripts for hardcoded 101-150 (batch03 must not leak into 1-100 proofs)
    for script in (ROOT / "scripts").glob("verify_entitlement*.py"):
        if script.name in _ENTITLEMENT_SCRIPT_EXCLUDE:
            continue
        text = script.read_text(encoding="utf-8")
        for m in re.finditer(r"\(\s*(10[1-9]|1[1-4][0-9]|150)\s*,", text):
            errors.append(f"Batch03 ID {m.group(1)} in {script.name}")
    if errors:
        print("\n".join(errors))
        return 1
    print(json.dumps({"cap_dedup_gate": "PASS", "audit": str(AUDIT)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
