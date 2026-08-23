#!/usr/bin/env python3
"""Close SEC-008 when production pentest attestation is verified (ID645 slot)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pentest_attestation import verify_pentest_attestation  # noqa: E402
from scripts._pentest_rvm_common import (  # noqa: E402
    verify_production_pentest,
    write_rvm_artifacts,
)


def main() -> int:
    if not verify_pentest_attestation():
        raise SystemExit(
            "local_pentest_attestation_missing_or_invalid — deposit via POST /api/institutional/pentest/deposit"
        )

    evidence = verify_production_pentest()
    print(json.dumps(evidence, indent=2))

    summary = evidence.get("pentest", {}).get("attestation_summary") or {}
    note = (
        f"SEC-008 pentest control satisfied via verified attestation; "
        f"ref={summary.get('report_reference')}"
    )
    write_rvm_artifacts(req_id="SEC-008", evidence=evidence, note=note)
    print("SEC-008 closed PASS in RVM artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
