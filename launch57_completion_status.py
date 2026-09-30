"""Load Launch-57 CISA completion rollup for authenticated APIs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent
_STATUS_JSON = _ROOT / "governance" / "launch57" / "LAUNCH57_COMPLETION_STATUS.json"
_INDEX_JSON = _ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"


def completion_status_attachment() -> dict[str, Any]:
    """Attach honest inventory rollup (no certification claims)."""
    docs = {
        "completion_md": "governance/launch57/LAUNCH57_REMEDIATION_COMPLETION_STATUS.md",
        "completion_json": "governance/launch57/LAUNCH57_COMPLETION_STATUS.json",
        "evidence_index": "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json",
        "pr_merge_checklist": "docs/governance/LAUNCH57_PR_MERGE_CHECKLIST.md",
        "engineering_closure_declaration": "docs/governance/LAUNCH57_ENGINEERING_CLOSURE_DECLARATION.md",
        "finding_inventory_lock": "governance/launch57/FINDING_INVENTORY_LOCK.json",
        "gate_index": "governance/launch57/LAUNCH57_REMEDIATION_GATE_INDEX.json",
        "open_ops_closure_package": "governance/launch57/LAUNCH57_OPEN_OPS_CLOSURE_PACKAGE.json",
        "program_integrity_gate": "scripts/verify_launch57_program_integrity_report.py",
        "preflight_transitions": "scripts/preflight_launch57_open_finding_transitions.py",
        "ci_assurance_manifest": "governance/launch57/LAUNCH57_CI_ASSURANCE_MANIFEST.json",
        "engineering_verification_suite": "scripts/run_launch57_engineering_verification_suite.py",
    }
    if _STATUS_JSON.is_file():
        data = json.loads(_STATUS_JSON.read_text(encoding="utf-8"))
        rollup = data.get("rollup") or {}
        return {
            "loaded": True,
            "source": str(_STATUS_JSON.relative_to(_ROOT)),
            "remediation_sha": data.get("remediation_sha"),
            "phase": data.get("phase"),
            "finding_count": len(data.get("findings") or {}),
            "rollup": rollup,
            "open_finding_ids": rollup.get("open_finding_ids") or [],
            "program_complete": bool(rollup.get("program_complete")),
            "documents": docs,
        }
    finding_count = 0
    if _INDEX_JSON.is_file():
        finding_count = len(json.loads(_INDEX_JSON.read_text(encoding="utf-8")).get("findings") or {})
    return {
        "loaded": False,
        "source": None,
        "remediation_sha": None,
        "phase": None,
        "finding_count": finding_count,
        "rollup": None,
        "open_finding_ids": [],
        "program_complete": False,
        "documents": docs,
        "note": "Run scripts/generate_launch57_completion_status.py to refresh JSON rollup",
    }
