#!/usr/bin/env python3
"""Final FDS-01..25 reconciliation verifier — artifacts only, no phase re-execution."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "FDS_FULL_SPEC_FINAL_RECONCILIATION.json"
SPEC = ROOT / "docs" / "BLACKDARK_FINANCIAL_DATA_SECURITY_IMPLEMENTATION_SPEC_2026_FINAL.md"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"


def build_evidence() -> dict[str, Any]:
    from governance.fds_full_spec_final_reconciliation import reconcile_fds_full_spec

    result = reconcile_fds_full_spec()
    return {
        "verdict": result["verdict"],
        "generated_at": datetime.now(UTC).isoformat(),
        "governing_spec": {"path": str(SPEC.relative_to(ROOT)), "sha256": _sha256_file(SPEC)},
        **result,
    }


def main() -> int:
    evidence = build_evidence()
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": evidence["verdict"], "artifact": OUT.name, "summary": evidence["summary"]}, indent=2))
    closed = evidence["verdict"].startswith("FDS_FULL_SPEC_ENGINEERING_CLOSED")
    return 0 if closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
