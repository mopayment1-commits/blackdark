#!/usr/bin/env python3
"""Item 6 — Stamp SRE PRR readiness package with current git commit and artifact refs."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "docs/BATCH05_SRE_PRR_READINESS_PACKAGE.json"


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> None:
    doc = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    doc["generated_at"] = datetime.now(UTC).isoformat()
    doc["git_commit"] = git_commit()

    ent = json.loads((ROOT / "docs/BATCH05_ENTITLEMENT_GATEWAY_PROOF.json").read_text(encoding="utf-8"))
    disp = json.loads((ROOT / "docs/BATCH05_REUSED_LINK_PARTIAL_DISPOSITION.json").read_text(encoding="utf-8"))
    doc["entitlement_summary"]["all_verified"] = ent.get("all_verified")
    doc["entitlement_summary"]["strangler_gateway_proofs"] = ent.get("strangler_test_case_count")
    doc["reused_link_disposition"] = {
        "closed": [r["capability_id"] for r in disp["rows"] if r["disposition"] == "CLOSED"],
        "tolerate": [
            {"id": r["capability_id"], "ceiling": r.get("tolerate_ceiling")}
            for r in disp["rows"]
            if r["disposition"] == "TOLERATE"
        ],
    }
    OUT_JSON.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"Stamped {OUT_JSON.name} @ {doc['git_commit'][:12]}")


if __name__ == "__main__":
    main()
