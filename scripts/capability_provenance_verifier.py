#!/usr/bin/env python3
"""Independent verifier for capability provenance contract invariants (B1-R)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from capability_provenance.verify import verify_contract_loaded, verify_ssot_artifact

SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"


def main() -> int:
    verify_contract_loaded()
    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    result = verify_ssot_artifact(ssot, check_capabilities=True)

    # INV-005: do not treat PASS verdict as proof — verifier recomputes independently.
    result["ssot_verdict_used_as_proof"] = False
    result["engineering_pass_count"] = sum(
        1 for c in ssot.get("canonical_capabilities", []) if c.get("engineering_status") == "PASS_ENGINEERING"
    )

    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
