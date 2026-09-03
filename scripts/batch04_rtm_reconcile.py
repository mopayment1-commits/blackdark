#!/usr/bin/env python3
"""Reconcile Batch04 RTM — single closure_status source; remove classification_runtime."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Per-ID MISWIRED remediation: catalog goal valid → STRANGLER_FIXABLE; catalog misnamed → PARTIAL_MISNAMED
MISWIRE_REMEDIATION: dict[int, str] = {
    152: "STRANGLER_FIXABLE",
    153: "STRANGLER_FIXABLE",
    154: "PARTIAL_MISNAMED",
    155: "STRANGLER_FIXABLE",
    156: "STRANGLER_FIXABLE",
    157: "PARTIAL_MISNAMED",
    158: "PARTIAL_MISNAMED",
    160: "STRANGLER_FIXABLE",
    163: "STRANGLER_FIXABLE",
    164: "STRANGLER_FIXABLE",
    165: "STRANGLER_FIXABLE",
    166: "STRANGLER_FIXABLE",
    167: "STRANGLER_FIXABLE",
    168: "STRANGLER_FIXABLE",
    169: "STRANGLER_FIXABLE",
    170: "STRANGLER_FIXABLE",
    171: "STRANGLER_FIXABLE",
    172: "STRANGLER_FIXABLE",
    173: "STRANGLER_FIXABLE",
    174: "STRANGLER_FIXABLE",
    176: "STRANGLER_FIXABLE",
    177: "STRANGLER_FIXABLE",
    178: "STRANGLER_FIXABLE",
    179: "STRANGLER_FIXABLE",
    180: "STRANGLER_FIXABLE",
    181: "PARTIAL_MISNAMED",
    182: "PARTIAL_MISNAMED",
    184: "STRANGLER_FIXABLE",
    185: "STRANGLER_FIXABLE",
    186: "STRANGLER_FIXABLE",
    187: "STRANGLER_FIXABLE",
    188: "STRANGLER_FIXABLE",
    189: "STRANGLER_FIXABLE",
    190: "STRANGLER_FIXABLE",
    191: "STRANGLER_FIXABLE",
    192: "STRANGLER_FIXABLE",
    193: "STRANGLER_FIXABLE",
    194: "STRANGLER_FIXABLE",
    195: "STRANGLER_FIXABLE",
    196: "STRANGLER_FIXABLE",
    197: "STRANGLER_FIXABLE",
    198: "STRANGLER_FIXABLE",
    199: "STRANGLER_FIXABLE",
}


def _commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> None:
    prebuild = json.loads((ROOT / "docs/BATCH04_PREBUILD_CLASSIFICATION_151_200.json").read_text())
    closure_by_id = {r["id"]: r["closure_status"] for r in prebuild["matrix"]}

    rtm_path = ROOT / "docs/BATCH04_RTM_151_200.json"
    rtm = json.loads(rtm_path.read_text())

    for row in rtm["rows"]:
        cap_id = row["id"]
        row["closure_status"] = closure_by_id[cap_id]
        probe = row.get("runtime_probe") or {}
        probe.pop("classification_runtime", None)
        row["runtime_probe"] = probe
        sem = row.get("semantic_alignment_status")
        if sem == "MISWIRED":
            row["miswire_remediation"] = MISWIRE_REMEDIATION[cap_id]
        elif sem in ("ALIGNED", "PARTIAL_ALIGNMENT"):
            row["miswire_remediation"] = None
        else:
            row["miswire_remediation"] = None

    cs = [r["closure_status"] for r in rtm["rows"]]
    mr = [r.get("miswire_remediation") for r in rtm["rows"] if r.get("miswire_remediation")]
    rtm["reconciled_at"] = datetime.now(UTC).isoformat()
    rtm["reconcile_commit"] = _commit()
    rtm["closure_status_authoritative"] = True
    rtm["classification_runtime_removed"] = True
    rtm["hold_acknowledgment"] = {
        "build_phase": "BUILD_PHASE_HOLD",
        "partial_hold_violation_commits": ["728b59a", "e78c3e2", "c74abb0"],
        "hold_document_commit": "cf475c9",
        "statement": "Implementation commits 728b59a, e78c3e2, c74abb0 landed on branch after HOLD doc cf475c9 — acknowledged partial second gate breach; no further non-documentation commits until explicit owner approval.",
        "non_doc_commits_frozen": True,
    }
    rtm["summary"]["closure_status"] = {k: cs.count(k) for k in sorted(set(cs))}
    rtm["summary"]["miswire_remediation"] = {
        "STRANGLER_FIXABLE": mr.count("STRANGLER_FIXABLE"),
        "PARTIAL_MISNAMED": mr.count("PARTIAL_MISNAMED"),
    }

    rtm_path.write_text(json.dumps(rtm, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rtm["summary"], indent=2))


if __name__ == "__main__":
    main()
