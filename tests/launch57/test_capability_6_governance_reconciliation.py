"""Governance metadata reconciliation for Launch-57 capability #6."""

from __future__ import annotations

import json
from pathlib import Path

GOV = Path("governance/launch57")
REGISTER = GOV / "LAUNCH57_REGISTER.json"
B3_IV = GOV / "B3_6_TRUST_BOUNDARY_INDEPENDENT_VERIFICATION.json"
AUTHORITY = GOV / "LAUNCH57_CAPABILITY_6_AUTHORITY_RESOLUTION.json"
EVIDENCE = GOV / "LAUNCH57_CAPABILITY_6_GOVERNANCE_RECONCILIATION.json"


def _item_6() -> dict:
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    for item in register["launch57_register"]:
        if item["launch_number"] == 6:
            return item
    raise AssertionError("launch_number 6 missing")


def test_capability_6_register_matches_authority_resolution():
    item = _item_6()
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    b3_iv = json.loads(B3_IV.read_text(encoding="utf-8"))

    assert authority["verdict"]["CAPABILITY_6_AUTHORITY"] == "RESOLVED"
    assert b3_iv["B3:#6"] == "PASS_ENGINEERING"
    assert item["canonical_implementation"] == ["launch57.evidence_class_common"]
    assert item["canonical_owner"] == ["launch57.evidence_class_common"]
    assert item["current_engineering_status"] == "PASS_ENGINEERING"
    assert item["pass_engineering_reconciliation"] == "PASS_ENGINEERING"
    assert item["root_cause_if_not_pass_engineering"] is None
    assert "launch57/evidence_class_common.py" in item["actual_consumer_paths"]
    assert "cap646/evidence_class.py" not in item["actual_consumer_paths"]
    assert "decision_truth/evidence_taxonomy.py" not in item["actual_consumer_paths"]


def test_capability_6_governance_reconciliation_evidence_present():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["final_status"]["CAPABILITY_6_GOVERNANCE_METADATA_RECONCILED"] is True
    assert evidence["final_status"]["PRODUCT_CODE_CHANGED"] is False
    assert evidence["reconciled_fields"]["public_taxonomy"] == ["LIVE", "DELAYED", "SIM"]
