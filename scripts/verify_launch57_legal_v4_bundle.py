#!/usr/bin/env python3
"""Program §8.3 V-4 — Legal review artifact bundle (E-LEGAL paths; review ID is human)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "governance/launch57/LAUNCH57_INDEPENDENT_VERIFICATION_REGISTER.json"


def main() -> int:
    if not REGISTER.is_file():
        return 1
    v4 = json.loads(REGISTER.read_text(encoding="utf-8"))["steps"]["V-4"]
    errors: list[str] = []
    for rel in v4.get("review_artifacts") or []:
        if not (ROOT / rel).is_file():
            errors.append(f"missing {rel}")
    legal_id = (os.getenv("LAUNCH57_LEGAL_REVIEW_ID") or "").strip()
    report = {
        "program_section": "§8.3 V-4",
        "review_artifacts_present": not errors,
        "legal_review_id_recorded": bool(legal_id),
        "legal_signoff": "PASS" if legal_id else "PENDING",
        "cisa_certification_claimed": False,
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
