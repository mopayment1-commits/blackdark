"""
BLACKDARK — Data / Storage / Tracking Governance (v4_v2 DSR compliance).

Shared infrastructure for Data Asset Contracts, lineage, rights, receipts,
PIT evidence, retention, restore evidence, and compliance gate assessment.
"""

from blackdark.data_governance.audit import assess_compliance, run_compliance_audit
from blackdark.data_governance.contracts import (
    CANONICAL_CONTRACTS,
    get_contract,
    list_contracts,
    validate_contract,
)
from blackdark.data_governance.gate import assess_flywheel_gate
from blackdark.data_governance.intelligence_receipt import issue_intelligence_receipt
from blackdark.data_governance.lineage import inherit_evidence_origin, propagate_lineage

__all__ = [
    "CANONICAL_CONTRACTS",
    "assess_compliance",
    "assess_flywheel_gate",
    "get_contract",
    "inherit_evidence_origin",
    "issue_intelligence_receipt",
    "list_contracts",
    "propagate_lineage",
    "run_compliance_audit",
    "validate_contract",
]
