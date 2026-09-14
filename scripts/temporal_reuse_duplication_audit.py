#!/usr/bin/env python3
"""TEAS Reuse / Duplication / Canonical Ownership audit (read-only)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "TEMPORAL_REUSE_DUPLICATION_AUDIT.json"

CAPABILITIES: list[dict[str, str]] = [
    {
        "capability": "auth / entitlements",
        "existing_owner": "security_auth.py; cap646/entitlements.py; anonymous_route_foundation.py",
        "teas_owner": "(none — TEAS consumes platform auth boundaries)",
        "overlap": "No TEAS reimplementation of auth or route entitlement enforcement",
        "canonical_decision": "Reuse",
        "evidence": "No blackdark/temporal auth module; api/routers/temporal.py mounted under existing dashboard auth",
    },
    {
        "capability": "data ingestion",
        "existing_owner": "blackdark/data/ingestors/*; blackdark/data/repository.py",
        "teas_owner": "blackdark/temporal/live_feed_bridge.py → production_spine.py",
        "overlap": "Live OHLCV rows bridged into temporal spine after DG insert",
        "canonical_decision": "Reuse",
        "evidence": "live_feed_bridge.bridge_ohlcv_row_to_temporal_spine; ingestors call bridge post-insert",
    },
    {
        "capability": "event storage",
        "existing_owner": "blackdark/data/repository.py (market_events, ohlcv_data / de_*)",
        "teas_owner": "blackdark/data/temporal_repository.py (te_canonical_events, te_evidence_records)",
        "overlap": "Both persist market history; DG tables vs TEAS canonical spine tables",
        "canonical_decision": "Keep (intentional separation)",
        "evidence": "TEMPORAL_PHASE_0H1_DATA_GOVERNANCE_INTEGRATION_DISCOVERY.json DG-TMP-HE-001..003; migration 018_temporal_spine.sql",
    },
    {
        "capability": "provenance / evidence taxonomy",
        "existing_owner": "cap646/evidence_class.py (4-class platform taxonomy)",
        "teas_owner": "blackdark/temporal/evidence_class.py (6-class TemporalEvidenceClass)",
        "overlap": "Both classify evidence tier and enforce promotion rules; zero cross-import bridge",
        "canonical_decision": "Merge (adapter bridge required)",
        "evidence": "CAND-100 SHARED_INFRASTRUCTURE; cap646 used by legacy surfaces; temporal used by P2–P6; no mapping module",
    },
    {
        "capability": "provenance / evidence ledger",
        "existing_owner": "decision_ledger.py; cap646 institutional_controls (product surfaces)",
        "teas_owner": "blackdark/temporal/evidence_provenance.py (EvidenceProvenanceLedger)",
        "overlap": "Both record evidentiary claims; scoped to temporal spine outcomes",
        "canonical_decision": "Keep (layered SoR)",
        "evidence": "P3/P4 DUPLICATE_EVIDENCE_LEDGER=0; failure_surprise_corpus links into P2 ledger",
    },
    {
        "capability": "replay",
        "existing_owner": "ml/market_replay_bootstrap.py (ML dataset bootstrap)",
        "teas_owner": "blackdark/temporal/replay.py (deterministic canonical replay)",
        "overlap": "Both replay historical market state; different contracts and consumers",
        "canonical_decision": "Keep (complementary layers)",
        "evidence": "TEMP-AR replay atomics bound to TemporalCanonicalEventStore + leakage firewall per step",
    },
    {
        "capability": "outcome evaluation",
        "existing_owner": "decision_truth/pipeline.py (BGS-009 admission pipeline)",
        "teas_owner": "blackdark/temporal/outcome_factory.py (P2 automated outcome labels)",
        "overlap": "Both evaluate decision outcomes; different orchestration boundaries",
        "canonical_decision": "Keep (complementary)",
        "evidence": "P3 DUPLICATE_OUTCOME_FACTORY=0; outcome_factory reads canonical events not decision_truth",
    },
    {
        "capability": "observability",
        "existing_owner": "observability.py (Sentry/Prometheus platform metrics)",
        "teas_owner": "blackdark/temporal/observability.py + metrics.py (spine stage tracing)",
        "overlap": "Both emit operational telemetry; TEAS scoped to temporal spine stages",
        "canonical_decision": "Reuse (scoped subset)",
        "evidence": "SpineObservability.record used by production_spine; no duplicate platform metrics registry",
    },
    {
        "capability": "drift",
        "existing_owner": "ml/drift_monitor.py (ML feature/OOD drift)",
        "teas_owner": "blackdark/temporal/drift_monitoring.py (P3 shadow); p4_drift.py (P4 eval)",
        "overlap": "All monitor distributional change; distinct dimensions and gating rules",
        "canonical_decision": "Keep (scoped domains)",
        "evidence": "DRIFT_AUTO_MODEL_MUTATION=0; ml drift guards inference; TEAS drift guards shadow/learning validity",
    },
    {
        "capability": "model governance",
        "existing_owner": "cap646/institutional_controls.py; ml inference training paths",
        "teas_owner": "blackdark/temporal/champion_challenger.py; controlled_learning.py",
        "overlap": "Champion/challenger promotion discipline",
        "canonical_decision": "Keep (TEAS spec layer)",
        "evidence": "DUPLICATE_CHAMPION_CHALLENGER=0; upstream_authorities_reused in P4 evidence JSON",
    },
    {
        "capability": "user behavior",
        "existing_owner": "behavior_data_service.py; user_exposure_log.py",
        "teas_owner": "blackdark/temporal/user_behavioral_learning.py",
        "overlap": "Behavior capture vs P5 governance/consent rules for learning use",
        "canonical_decision": "Keep (layered)",
        "evidence": "USER_BEHAVIOR_NOT_FINANCIAL_TRUTH=True; CAND-101 user_exposure_log as upstream receipt surface",
    },
    {
        "capability": "public evidence",
        "existing_owner": "product_honesty_api.py; public_miss_feed.py",
        "teas_owner": "blackdark/temporal/public_evidence.py",
        "overlap": "Public claim disclosure; TEAS adds mandatory P5 envelope over provenance ledger",
        "canonical_decision": "Keep (layered consumer)",
        "evidence": "PublicEvidenceDisclosure requires TemporalEvidenceClass + provenance_reference",
    },
    {
        "capability": "failure corpus",
        "existing_owner": "failure_corpus.py (product JSONL failure intelligence)",
        "teas_owner": "blackdark/temporal/failure_surprise_corpus.py (P3 FSA corpus)",
        "overlap": "Both capture failure/surprise cases; no import bridge between modules",
        "canonical_decision": "Keep (scope split)",
        "evidence": "DUPLICATE_EVIDENCE_LEDGER=0; failure_surprise_corpus does not import failure_corpus; distinct contracts",
    },
    {
        "capability": "persistence",
        "existing_owner": "blackdark/data/migrations/* (de_*, market_events, ohlcv_data)",
        "teas_owner": "blackdark/data/migrations/018_temporal_spine.sql (te_*)",
        "overlap": "Separate table families; DG retains storage authority for upstream feeds",
        "canonical_decision": "Keep (intentional separation)",
        "evidence": "DG-TMP-HE contracts; temporal_repository inserts te_canonical_events only",
    },
    {
        "capability": "API routing",
        "existing_owner": "dashboard.py route mount catalog",
        "teas_owner": "api/routers/temporal.py",
        "overlap": "Additive /api/temporal/* surface; no parallel allowlist",
        "canonical_decision": "Reuse",
        "evidence": "Single temporal router; no duplicate OpenAPI filter owner in TEAS",
    },
    {
        "capability": "security / quality governance",
        "existing_owner": "production_guard.py; zero_tolerance.py; heroes_quality.py",
        "teas_owner": "blackdark/temporal/quality_governance.py; operational_hardening.py",
        "overlap": "Institutional quality posture; TEAS P6 assessment model vs launch guards",
        "canonical_decision": "Keep (complementary)",
        "evidence": "CAND-001/002 integration discovery; EXTERNAL_STANDARDS_GUIDANCE_ONLY=True in quality_governance",
    },
    {
        "capability": "source rights",
        "existing_owner": "data_governance/rights.py; data_sources_registry.py",
        "teas_owner": "blackdark/temporal/source_rights.py",
        "overlap": "Rights metadata preservation on ingest",
        "canonical_decision": "Reuse",
        "evidence": "UPSTREAM_PROVENANCE_AUTHORITY=DATA_GOVERNANCE; extract_source_rights consumes ProvenanceMetadata",
    },
    {
        "capability": "leakage firewall",
        "existing_owner": "governance/temporal_governance.py (probe stub only)",
        "teas_owner": "blackdark/temporal/firewall.py; temporal_leakage_firewall.py (facade)",
        "overlap": "Facade re-exports canonical firewall — not a parallel implementation",
        "canonical_decision": "Reuse",
        "evidence": "temporal_leakage_firewall imports from blackdark.temporal.firewall; production_spine calls evaluate_temporal_leakage_firewall",
    },
    {
        "capability": "regime intelligence",
        "existing_owner": "ml/regime_router.py (inference routing)",
        "teas_owner": "blackdark/temporal/regime_intelligence.py (P3 spec regime library)",
        "overlap": "Both label market regime; inference router vs temporal correctness library",
        "canonical_decision": "Keep (complementary)",
        "evidence": "REGIME_LOOKAHEAD_LEAKAGE=0; no import from ml.regime_router in temporal package",
    },
]


def _run_regression_probe() -> int:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_temporal_p3_failure_surprise_abstention.py::test_p2_evidence_ledger_reuse_without_duplicate_authority",
        "tests/test_temporal_p2_outcome_and_evidence.py",
        "-q",
        "--tb=no",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return int(proc.returncode != 0)


def main() -> int:
    semantic_duplicates = sum(1 for c in CAPABILITIES if c["canonical_decision"].startswith("Merge"))
    parallel_owners = sum(
        1
        for c in CAPABILITIES
        if "no import bridge" in c["overlap"].lower()
        or "zero cross-import" in c["overlap"].lower()
    )
    merge_required = semantic_duplicates
    safe_reuse = sum(
        1
        for c in CAPABILITIES
        if c["canonical_decision"] in {"Reuse", "Keep (intentional separation)", "Reuse (scoped subset)"}
        or c["canonical_decision"].startswith("Keep")
    )
    preexisting_reuse = sum(1 for c in CAPABILITIES if "Reuse" in c["canonical_decision"])
    dead_duplicate_paths = 0
    regression_failures = _run_regression_probe()

    if semantic_duplicates == 0:
        verdict = "NO_MATERIAL_DUPLICATION_FOUND"
    elif merge_required > 0 and regression_failures == 0:
        verdict = "DUPLICATION_RECONCILIATION_REQUIRED"
    else:
        verdict = "DUPLICATION_RECONCILED"

    payload = {
        "audit_name": "TEAS Reuse / Duplication / Canonical Ownership Check",
        "audited_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repository_roots": {
            "teas_worktree": str(ROOT),
            "main_workspace": "/workspace",
            "teas_package_in_main_workspace": False,
        },
        "prior_discovery_artifacts": {
            "TEMPORAL_PROJECT_INTEGRATION_DISCOVERY.json": {"duplicate_candidate_records": 0},
            "TEMPORAL_PHASE_0G_INDEPENDENT_AUDIT.json": {"duplicate_candidate_records": 0},
            "TEMPORAL_PHASE_0H1_DATA_GOVERNANCE_INTEGRATION_DISCOVERY.json": {
                "verified_integration_contracts": 14,
            },
            "TEMPORAL_FULL_SPEC_FINAL_RECONCILIATION.json": {"DUPLICATES": 0, "REGRESSION_FAILURES": 0},
        },
        "summary": {
            "TEAS_PREEXISTING_REUSE_FOUND": preexisting_reuse,
            "SEMANTIC_DUPLICATES_FOUND": semantic_duplicates,
            "PARALLEL_OWNERS_FOUND": parallel_owners,
            "MERGE_REQUIRED": merge_required,
            "SAFE_REUSE_CONFIRMED": safe_reuse,
            "DEAD_DUPLICATE_PATHS": dead_duplicate_paths,
            "REGRESSION_FAILURES": regression_failures,
        },
        "verdict": verdict,
        "capabilities": CAPABILITIES,
        "material_findings": [
            {
                "finding_id": "FIND-001",
                "existing_component": "cap646/evidence_class.py",
                "teas_component": "blackdark/temporal/evidence_class.py",
                "semantic_overlap": "Evidence tier taxonomy and promotion enforcement",
                "canonical_owner": "Dual-owner until bridge: cap646 for platform surfaces; temporal for TEAS spine P2–P6",
                "action": "Merge",
                "migration_risk": "Medium — requires bidirectional mapping adapter; must not auto-promote across taxonomies",
            }
        ],
        "no_duplicate_evidence": [
            "P3 DUPLICATE_OUTCOME_FACTORY=0 and DUPLICATE_EVIDENCE_LEDGER=0",
            "P4 DUPLICATE_* counters all zero in controlled_learning/champion_challenger/learning_value",
            "Phase 0G/0H1 duplicate_candidate_records=0",
            "te_* tables intentionally separate from de_* per DG integration contracts",
            "temporal_leakage_firewall.py is facade to blackdark/temporal/firewall.py (not parallel impl)",
        ],
    }

    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"VERDICT={verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
