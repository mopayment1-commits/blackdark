"""Canonical paths for data governance artifacts."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
GOVERNANCE = DATA / "governance"
CONTRACTS_DIR = GOVERNANCE / "contracts"
RIGHTS_DIR = GOVERNANCE / "rights"
PIT_DIR = GOVERNANCE / "pit_evidence"
SCHEMA_DIR = GOVERNANCE / "schema_registry"
CORRECTIONS_PATH = GOVERNANCE / "correction_ledger.jsonl"
OUTCOME_REGISTRY_PATH = GOVERNANCE / "outcome_evaluator_registry.json"
OPPORTUNITY_UNIVERSE_PATH = GOVERNANCE / "opportunity_universe_contracts.json"
ENTITY_ASSERTIONS_PATH = GOVERNANCE / "entity_assertions.jsonl"
RETENTION_PATH = GOVERNANCE / "retention_classes.json"
RESTORE_EVIDENCE_PATH = GOVERNANCE / "restore_evidence.jsonl"
EVIDENCE_MANIFEST_PATH = GOVERNANCE / "evidence_integrity_manifest.jsonl"
PROMOTION_GATES_PATH = GOVERNANCE / "promotion_gates.jsonl"
DERIVED_ASSETS_PATH = GOVERNANCE / "derived_asset_classifications.json"
ASSET_VALUE_LEDGER_PATH = GOVERNANCE / "asset_value_ledger.jsonl"
DATA_ROOM_INDEX_PATH = GOVERNANCE / "data_room_index.json"
CLAIMS_REGISTRY_PATH = GOVERNANCE / "claims_registry.jsonl"
COLLECTION_POLICY_PATH = GOVERNANCE / "collection_policies.json"
RECEIPTS_PATH = GOVERNANCE / "intelligence_receipts.jsonl"
COMPLIANCE_DIR = ROOT / "institutional_due_diligence_2026" / "DATA_STORAGE_TRACK_COMPLIANCE"


def ensure_governance_dirs() -> None:
    for d in (GOVERNANCE, CONTRACTS_DIR, RIGHTS_DIR, PIT_DIR, SCHEMA_DIR):
        d.mkdir(parents=True, exist_ok=True)
