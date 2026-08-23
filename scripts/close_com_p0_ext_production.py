#!/usr/bin/env python3
"""Close COM-P0-EXT when all P0 external evidence items are PASS in production RVM."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._pentest_rvm_common import (  # noqa: E402
    PROD,
    fetch_json,
    recompute_summary,
    write_rvm_artifacts,
)

P0_IDS = ["CAP-644", "CAP-645", "SEC-006", "SEC-008", "REL-002"]


def verify_production_p0() -> dict:
    open_items: list[str] = []
    checks: dict[str, dict] = {}
    for pid in P0_IDS:
        if pid.startswith("CAP-"):
            cap_id = pid.replace("CAP-", "")
            row = fetch_json(f"{PROD}/api/cap646/verify/{cap_id}")
        else:
            row = fetch_json(f"{PROD}/api/rvm/verify/control/{pid}")
        status = str(row.get("status") or row.get("verdict") or "").upper()
        checks[pid] = row
        if status != "PASS" and status != "VERIFIED_COMPLETE":
            open_items.append(pid)

    gate = fetch_json(f"{PROD}/api/rvm/verify/gate/COM-P0-EXT")
    if open_items:
        raise SystemExit(f"p0_not_closed_on_production: open={open_items} gate={gate}")

    build = fetch_json(f"{PROD}/api/build-info")
    return {
        "verified_at": datetime.now(UTC).isoformat(),
        "production_url": PROD,
        "build_commit": build.get("git_commit"),
        "p0_checks": checks,
        "com_p0_ext_gate": gate,
        "evidence": [f"p0_closed={P0_IDS}", f"commit={str(build.get('git_commit', ''))[:12]}"],
    }


def main() -> int:
    evidence = verify_production_p0()
    print(json.dumps(evidence, indent=2))

    note = "All P0 external evidence items closed on production (644, 645, SEC-006, SEC-008, REL-002)"
    write_rvm_artifacts(req_id="COM-P0-EXT", evidence=evidence, note=note)

    # Refresh p0_external_remaining after COM-P0-EXT patch
    rvm_path = ROOT / "docs" / "rvm" / "RVM.json"
    rvm = json.loads(rvm_path.read_text(encoding="utf-8"))
    counts = recompute_summary(rvm.get("requirements") or [])
    rvm["p0_external_remaining"] = counts["p0_external_remaining"]
    rvm_path.write_text(json.dumps(rvm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("COM-P0-EXT closed PASS in RVM artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
