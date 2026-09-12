"""Data Asset Contracts — DSR-001, DSR-002, Table 16."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from blackdark.data_governance._paths import CONTRACTS_DIR, ensure_governance_dirs

REQUIRED_FIELDS = (
    "asset_id",
    "canonical_name",
    "owner",
    "purpose",
    "consumers",
    "schema_version",
    "event_time_field",
    "ingest_time_field",
    "freshness_sla_seconds",
    "completeness_threshold",
    "validity_rules",
    "uniqueness_key",
    "reconciliation_policy",
    "missing_corrupt_behavior",
    "lineage_upstream",
    "rights_profile_id",
    "retention_class",
    "fallback_policy",
    "monitoring_hooks",
    "evidence_refs",
    "storage_tier",
    "security_classification",
    "failure_behavior",
)

CANONICAL_CONTRACTS: dict[str, dict[str, Any]] = {
    "dac_signal_registry": {
        "asset_id": "dac_signal_registry",
        "canonical_name": "Signal Registry",
        "owner": "platform-intelligence",
        "purpose": "Accumulate governed signal lexicon with provenance for compounding intelligence",
        "consumers": ["decision_ledger", "oracle", "cap646", "evidence_room"],
        "schema_version": "1.0.0",
        "event_time_field": "asof",
        "ingest_time_field": "recorded_at",
        "freshness_sla_seconds": 300,
        "completeness_threshold": 0.95,
        "validity_rules": {"required": ["signal_id", "signal_type", "evidence_class"]},
        "uniqueness_key": "signal_id",
        "reconciliation_policy": "append_only_dedupe_by_id",
        "missing_corrupt_behavior": "degrade_confidence_no_silent_zero",
        "lineage_upstream": ["oracle", "arbitrage_engine", "whale_signal_classifier"],
        "rights_profile_id": "rp_proprietary_internal",
        "retention_class": "rc_operational_hot",
        "fallback_policy": "return_empty_with_data_state",
        "monitoring_hooks": ["signal_registry.registry_stats"],
        "evidence_refs": ["data/signal_registry.jsonl", "signal_registry.py"],
        "storage_tier": "HOT",
        "security_classification": "internal",
        "failure_behavior": "degrade_not_fake_live",
        "physical_path": "data/signal_registry.jsonl",
    },
    "dac_decision_ledger": {
        "asset_id": "dac_decision_ledger",
        "canonical_name": "Decision Ledger",
        "owner": "platform-intelligence",
        "purpose": "Link prediction→decision→exposure→outcome with evidence class",
        "consumers": ["gips_audit", "user_exposure", "cap646", "track_record"],
        "schema_version": "1.0.0",
        "event_time_field": "created_at",
        "ingest_time_field": "created_at",
        "freshness_sla_seconds": 60,
        "completeness_threshold": 1.0,
        "validity_rules": {"required": ["decision_id", "prediction_id", "decision_action", "evidence_class"]},
        "uniqueness_key": "decision_id",
        "reconciliation_policy": "append_only",
        "missing_corrupt_behavior": "reject_decision_path",
        "lineage_upstream": ["oracle_predictions", "decision_certificate"],
        "rights_profile_id": "rp_proprietary_internal",
        "retention_class": "rc_evidence_archive",
        "fallback_policy": "none_decision_blocking",
        "monitoring_hooks": ["decision_ledger.ledger_stats"],
        "evidence_refs": ["data/decision_ledger.jsonl", "decision_ledger.py"],
        "storage_tier": "HOT",
        "security_classification": "internal",
        "failure_behavior": "block_not_silent",
        "physical_path": "data/decision_ledger.jsonl",
    },
    "dac_oracle_audit_chain": {
        "asset_id": "dac_oracle_audit_chain",
        "canonical_name": "Oracle Audit Chain",
        "owner": "platform-trust",
        "purpose": "Tamper-evident append-only prediction/outcome chain",
        "consumers": ["track_record", "evidence_room", "dd_bundle"],
        "schema_version": "1.0.0",
        "event_time_field": "timestamp",
        "ingest_time_field": "appended_at",
        "freshness_sla_seconds": 120,
        "completeness_threshold": 1.0,
        "validity_rules": {"required": ["chain_hash", "prev_hash", "evidence_class"]},
        "uniqueness_key": "chain_hash",
        "reconciliation_policy": "hash_chain_verify",
        "missing_corrupt_behavior": "invalidate_chain_report",
        "lineage_upstream": ["oracle_predictions"],
        "rights_profile_id": "rp_proprietary_internal",
        "retention_class": "rc_evidence_archive",
        "fallback_policy": "verify_before_use",
        "monitoring_hooks": ["oracle_audit_chain.verify_chain"],
        "evidence_refs": ["data/oracle_audit_chain.jsonl", "oracle_audit_chain.py"],
        "storage_tier": "HOT",
        "security_classification": "internal",
        "failure_behavior": "fail_closed_on_tamper",
        "physical_path": "data/oracle_audit_chain.jsonl",
    },
    "dac_market_event_library": {
        "asset_id": "dac_market_event_library",
        "canonical_name": "Market Event Library",
        "owner": "platform-intelligence",
        "purpose": "Searchable versioned market event knowledge base",
        "consumers": ["oracle", "replay_engine", "cap646"],
        "schema_version": "1.0.0",
        "event_time_field": "recorded_at",
        "ingest_time_field": "recorded_at",
        "freshness_sla_seconds": 3600,
        "completeness_threshold": 0.9,
        "validity_rules": {"required": ["event_id", "event_name", "category"]},
        "uniqueness_key": "event_id",
        "reconciliation_policy": "append_only",
        "missing_corrupt_behavior": "degrade_similarity_search",
        "lineage_upstream": ["market_data", "on_chain_events"],
        "rights_profile_id": "rp_market_data_derived",
        "retention_class": "rc_operational_warm",
        "fallback_policy": "empty_with_state",
        "monitoring_hooks": ["market_event_library.event_library_stats"],
        "evidence_refs": ["data/market_event_library.jsonl", "market_event_library.py"],
        "storage_tier": "WARM",
        "security_classification": "internal",
        "failure_behavior": "degrade_not_fake",
        "physical_path": "data/market_event_library.jsonl",
    },
    "dac_failure_corpus": {
        "asset_id": "dac_failure_corpus",
        "canonical_name": "Failure Corpus",
        "owner": "platform-quality",
        "purpose": "Unified failure intelligence with regression protection",
        "consumers": ["kill_rate_board", "cap646", "regression_tests"],
        "schema_version": "1.0.0",
        "event_time_field": "recorded_at",
        "ingest_time_field": "recorded_at",
        "freshness_sla_seconds": 600,
        "completeness_threshold": 0.95,
        "validity_rules": {"required": ["failure_id", "source", "reason", "category"]},
        "uniqueness_key": "failure_id",
        "reconciliation_policy": "append_only",
        "missing_corrupt_behavior": "log_and_continue",
        "lineage_upstream": ["truth_gates", "provenance_score", "circuit_breaker"],
        "rights_profile_id": "rp_proprietary_internal",
        "retention_class": "rc_evidence_archive",
        "fallback_policy": "mirror_kill_rate",
        "monitoring_hooks": ["failure_corpus.corpus_stats"],
        "evidence_refs": ["data/failure_corpus.jsonl", "failure_corpus.py"],
        "storage_tier": "WARM",
        "security_classification": "internal",
        "failure_behavior": "never_silent",
        "physical_path": "data/failure_corpus.jsonl",
    },
    "dac_user_exposure_log": {
        "asset_id": "dac_user_exposure_log",
        "canonical_name": "User Exposure Log",
        "owner": "platform-product",
        "purpose": "Track user exposure to decisions with evidence class",
        "consumers": ["decision_ledger", "gips", "analytics"],
        "schema_version": "1.0.0",
        "event_time_field": "shown_at",
        "ingest_time_field": "shown_at",
        "freshness_sla_seconds": 300,
        "completeness_threshold": 0.99,
        "validity_rules": {"required": ["exposure_id", "decision_id", "evidence_class"]},
        "uniqueness_key": "exposure_id",
        "reconciliation_policy": "append_only",
        "missing_corrupt_behavior": "reject_exposure",
        "lineage_upstream": ["decision_ledger"],
        "rights_profile_id": "rp_user_telemetry_minimized",
        "retention_class": "rc_user_telemetry",
        "fallback_policy": "none",
        "monitoring_hooks": [],
        "evidence_refs": ["data/user_exposure_log.jsonl"],
        "storage_tier": "HOT",
        "security_classification": "pii_limited",
        "failure_behavior": "degrade_not_fake",
        "physical_path": "data/user_exposure_log.jsonl",
    },
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def ensure_contracts_materialized() -> None:
    ensure_governance_dirs()
    for asset_id, contract in CANONICAL_CONTRACTS.items():
        path = CONTRACTS_DIR / f"{asset_id}.json"
        if not path.exists():
            payload = dict(contract)
            payload["contract_version"] = "1.0.0"
            payload["materialized_at"] = _utcnow()
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def list_contracts() -> list[dict[str, Any]]:
    ensure_contracts_materialized()
    out: list[dict[str, Any]] = []
    for p in sorted(CONTRACTS_DIR.glob("dac_*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def get_contract(asset_id: str) -> dict[str, Any] | None:
    ensure_contracts_materialized()
    path = CONTRACTS_DIR / f"{asset_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return CANONICAL_CONTRACTS.get(asset_id)


def validate_contract(contract: dict[str, Any]) -> tuple[bool, list[str]]:
    missing = [f for f in REQUIRED_FIELDS if f not in contract or contract[f] is None]
    physical = contract.get("physical_path")
    if physical:
        p = Path(physical)
        if not p.is_absolute():
            p = Path(__file__).resolve().parents[2] / physical
        if not p.exists():
            missing.append(f"physical_path_missing:{physical}")
    return len(missing) == 0, missing
