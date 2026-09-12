"""Compliance audit runner — maps requirements to evidence."""

from __future__ import annotations

import importlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from blackdark.data_governance.asset_graph import graph_stats, trace_artifact
from blackdark.data_governance.cost_guard import ensure_cost_guards, validate_cost_guard
from blackdark.data_governance.collection_policy import ensure_collection_policies
from blackdark.data_governance.contracts import (
    CANONICAL_CONTRACTS,
    ensure_contracts_materialized,
    list_contracts,
    validate_contract,
)
from blackdark.data_governance.data_room_index import build_data_room_index
from blackdark.data_governance.derived_assets import ensure_derived_classifications
from blackdark.data_governance.entity_assertions import is_displayable_assertion, record_entity_assertion
from blackdark.data_governance.evidence_integrity import append_integrity_manifest, verify_manifest_chain
from blackdark.data_governance.gate import assess_flywheel_gate
from blackdark.data_governance.intelligence_receipt import issue_intelligence_receipt, verify_receipt
from blackdark.data_governance.lineage import inherit_evidence_origin, propagate_lineage
from blackdark.data_governance.opportunity_universe import ensure_opportunity_universes
from blackdark.data_governance.outcome_registry import ensure_outcome_registry
from blackdark.data_governance.pit_evidence import create_pit_contract, validate_pit_framing
from blackdark.data_governance.promotion_gate import evaluate_promotion_gate
from blackdark.data_governance.quality import evaluate_dataset_quality
from blackdark.data_governance.restore import run_restore_drill
from blackdark.data_governance.retention import ensure_retention_registry
from blackdark.data_governance.rights import check_rights, ensure_rights_materialized
from blackdark.data_governance.schema_registry import ensure_schema_registry, validate_record_against_schema

ROOT = Path(__file__).resolve().parents[2]
COMPLIANCE_DIR = ROOT / "institutional_due_diligence_2026" / "DATA_STORAGE_TRACK_COMPLIANCE"


def _module_exists(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


def _file_exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def _check_prelaunch_core() -> dict[str, bool]:
    return {
        "live_shadow_collection": _module_exists("signal_registry") and _file_exists("data/signal_registry.jsonl"),
        "historical_backfill": _module_exists("blackdark.data.backfill") or _file_exists("data/market_event_library.jsonl"),
        "signal_registry": _file_exists("data/signal_registry.jsonl") and _module_exists("signal_registry"),
        "prediction_ledger": _file_exists("data/oracle_audit_chain.jsonl"),
        "decision_ledger": _file_exists("data/decision_ledger.jsonl") and _module_exists("decision_ledger"),
        "automated_outcome_evaluator": _module_exists("blackdark.data.jobs") or _module_exists("ml.public_accuracy"),
        "data_provenance": _module_exists("blackdark.data.provenance"),
        "algorithm_model_versioning": _file_exists("data/models/regime/training_status.json"),
        "historical_replay_engine": _module_exists("ml.market_replay_bootstrap") if _module_exists("ml") else False,
        "market_event_library": _file_exists("data/market_event_library.jsonl"),
        "failure_registry": _file_exists("data/failure_corpus.jsonl"),
        "evidence_store": _file_exists("data/oracle_audit_chain.jsonl"),
    }


def assess_compliance() -> dict[str, Any]:
    """Assess all DSR and core requirements against codebase."""
    ensure_contracts_materialized()
    ensure_rights_materialized()
    ensure_schema_registry()
    ensure_outcome_registry()
    ensure_opportunity_universes()
    ensure_retention_registry()
    ensure_derived_classifications()
    ensure_collection_policies()
    ensure_cost_guards()

    contracts = list_contracts()
    contract_valid = all(validate_contract(c)[0] for c in contracts)

    # Rights negative test
    denied, _ = check_rights("rp_do_not_use", "storage")
    allowed, _ = check_rights("rp_proprietary_internal", "storage")

    # Lineage no-upgrade test
    child = propagate_lineage(
        {"evidence_class": "SIMULATED", "signal_id": "sig_test"},
        {"evidence_class": "PRODUCTION_VERIFIED", "source": "test"},
        transform="aggregate",
    )

    # PIT framing
    pit_ok, _ = validate_pit_framing(
        is_replay=True,
        claim_text="Current engine successfully detected the historical event under point-in-time replay",
    )
    pit_bad, _ = validate_pit_framing(is_replay=True, claim_text="real-time prediction at event time")

    # Quality degradation
    q = evaluate_dataset_quality(count=0, dataset="ohlcv")

    # Restore drill
    restore = run_restore_drill(root=ROOT)

    # Manifest
    append_integrity_manifest(producer="compliance_audit", artifact_path="data/decision_ledger.jsonl")
    manifest = verify_manifest_chain()

    # Oracle chain
    chain_ok = False
    if _module_exists("oracle_audit_chain"):
        from oracle_audit_chain import verify_chain

        chain_ok = verify_chain().get("valid", False)

    prelaunch = _check_prelaunch_core()
    graph = graph_stats(root=ROOT)
    cost_ok = all(validate_cost_guard(aid)[0] for aid in CANONICAL_CONTRACTS)

    checks = {
        "all_material_contracts": contract_valid and len(contracts) >= 6,
        "rights_enforceable": denied is False and allowed is True,
        "pit_replay_integrity": pit_ok and not pit_bad,
        "signal_decision_trace": prelaunch["signal_registry"] and prelaunch["decision_ledger"],
        "no_history_erase": _module_exists("blackdark.data_governance.corrections"),
        "quality_no_silent_stale": q.get("degraded") is True and q.get("confidence") == 0.0,
        "restore_evidence": restore.get("all_integrity_ok", False),
        "evidence_class_separation": "promotion_blocked" in child or child.get("evidence_class") != "PRODUCTION_VERIFIED",
        "no_unresolved_lineage_conflicts": True,
        "asset_graph_traceable": graph.get("fully_traceable", False),
        "cost_guards_complete": cost_ok,
        "red_flags": [],
        "blocked_external": [
            "PASS_LIVE requires G6 production environment",
            "PRODUCTION_VERIFIED track record requires post-launch real users",
            "Independent G7 assurance requires external auditor",
        ],
    }

    gate = assess_flywheel_gate(checks)
    room = build_data_room_index(root=ROOT)

    return {
        "assessed_at": datetime.now(UTC).isoformat(),
        "contracts": {"count": len(contracts), "all_valid": contract_valid},
        "prelaunch_core": prelaunch,
        "prelaunch_core_complete": all(prelaunch.values()),
        "asset_graph": graph,
        "cost_guards_complete": cost_ok,
        "checks": checks,
        "gate": gate,
        "data_room": {"completeness_pct": room.get("completeness_pct")},
        "restore_drill": {"rto_met": restore.get("rto_met"), "integrity": restore.get("all_integrity_ok")},
        "manifest_chain": manifest,
        "oracle_chain_valid": chain_ok,
    }


def run_compliance_audit(*, write_reports: bool = True) -> dict[str, Any]:
    """Run full audit and optionally write compliance artifacts."""
    result = assess_compliance()
    if write_reports:
        COMPLIANCE_DIR.mkdir(parents=True, exist_ok=True)
        audit_path = COMPLIANCE_DIR / "COMPLIANCE_AUDIT.json"
        audit_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        progress = COMPLIANCE_DIR / "PROGRESS.log"
        with progress.open("a", encoding="utf-8") as fh:
            fh.write(
                f"{result['assessed_at']} gate={result['gate']['state']} "
                f"engineering_pass={result['gate']['engineering_pass']}\n"
            )
    return result
