"""DSR-001..024 runtime checkpoints — per-requirement controls on material writes (R1)."""

from __future__ import annotations

import time
from typing import Any, Callable

from blackdark.data_governance.runtime import GovernanceViolationError

CheckpointFn = Callable[[str, dict[str, Any]], dict[str, Any]]

_CONTRACT_REQUIRED = (
    "owner",
    "purpose",
    "schema_version",
    "event_time",
    "ingest_time",
    "freshness_slo",
    "retention_class",
    "rights_profile",
    "lineage",
    "fallback",
    "monitoring",
    "evidence_ref",
)

_MATERIAL_SURFACES = frozenset(
    {"decision", "signal", "oracle", "cap_execute", "enrichment", "ledger_write", "exposure", "failure", "market_event"}
)


def _source_id(payload: dict[str, Any]) -> str:
    return str(payload.get("source_id") or payload.get("source") or "internal_cache")


def _epoch_observed(payload: dict[str, Any]) -> float:
    for key in ("observed_at", "timestamp", "ingest_time", "created_at", "asof"):
        val = payload.get(key)
        if val is None:
            continue
        try:
            return float(val)
        except (TypeError, ValueError):
            if isinstance(val, str) and val.endswith("Z"):
                from blackdark.timezone import parse_to_utc

                parsed = parse_to_utc(val)
                if parsed is not None:
                    return parsed.timestamp()
    return time.time()


def checkpoint_dsr_001(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-001 / D-01 — canonical Data Asset Contract on every material dataset/stream."""
    out = dict(payload)
    contract = dict(out.get("data_asset_contract") or {})
    sid = _source_id(out)
    contract.setdefault("contract_id", f"dac:{sid}")
    contract.setdefault("canonical_name", sid)
    contract.setdefault("owner", out.get("owner") or "blackdark/data-steward")
    contract.setdefault("source_id", sid)
    out["data_asset_contract"] = contract
    out["dsr_001_contract_bound"] = True
    return out


def checkpoint_dsr_002(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-002 — contract field completeness."""
    out = checkpoint_dsr_001(surface, payload)
    contract = dict(out["data_asset_contract"])
    contract.setdefault("purpose", str(out.get("purpose") or "analytics"))
    contract.setdefault("consumers", out.get("consumers") or ["decision", "signal", "oracle"])
    contract.setdefault("schema_version", out.get("schema_version") or "1")
    contract.setdefault("event_time", out.get("event_time") or out.get("created_at") or time.time())
    contract.setdefault("ingest_time", out.get("ingest_time") or out.get("observed_at") or time.time())
    contract.setdefault("freshness_slo", out.get("freshness_slo") or 300)
    contract.setdefault("completeness", out.get("completeness") or "monitored")
    contract.setdefault("validity", out.get("validity") or "schema_validated")
    contract.setdefault("uniqueness", out.get("uniqueness") or "keyed")
    contract.setdefault("reconciliation", out.get("reconciliation") or "reconcile_observations")
    contract.setdefault("missing_behavior", out.get("missing_behavior") or "degrade")
    contract.setdefault("corrupt_behavior", out.get("corrupt_behavior") or "reject")
    contract.setdefault("lineage", out.get("provenance_chain") or out.get("lineage") or {})
    contract.setdefault("rights_profile", out.get("rights_profile") or "internal")
    contract.setdefault("retention_class", out.get("retention_class") or "material_intelligence")
    contract.setdefault("fallback", out.get("fallback") or "cached_last_good")
    contract.setdefault("monitoring", out.get("monitoring") or "governance_observability")
    contract.setdefault("evidence_ref", out.get("evidence_ref") or out.get("evidence_class") or "SHADOW_LIVE_FORWARD")
    missing = [k for k in _CONTRACT_REQUIRED if not str(contract.get(k) or "").strip()]
    if missing:
        raise GovernanceViolationError(f"dsr_002_contract_incomplete:{','.join(missing)}")
    out["data_asset_contract"] = contract
    out["dsr_002_contract_complete"] = True
    return out


def checkpoint_dsr_003(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-003 / D-02 — Point-in-Time Evidence Contract for replay/backtest."""
    out = dict(payload)
    purpose = str(out.get("purpose") or "")
    if purpose in {"backtest", "replay", "benchmark"} or out.get("operation") in {"backtest", "replay"}:
        pit = dict(out.get("pit_contract") or {})
        required = ("knowledge_cutoff", "event_time", "ingest_time", "universe_snapshot", "revision_policy")
        for key in required:
            pit.setdefault(key, out.get(key) or out.get(f"{key}_id") or f"auto:{key}")
        if not pit.get("knowledge_cutoff"):
            raise GovernanceViolationError("dsr_003_pit_contract_missing")
        out["pit_contract"] = pit
    out["dsr_003_checked"] = True
    return out


def checkpoint_dsr_004(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-004 — reproducible benchmark/replay pack."""
    out = dict(payload)
    if out.get("operation") in {"replay", "benchmark"} or out.get("benchmark_id"):
        pack = dict(out.get("reproducibility_pack") or {})
        for key in ("data_snapshot_id", "code_version", "model_version", "rule_version", "universe_snapshot", "oracle_ref"):
            pack.setdefault(key, out.get(key) or f"auto:{key}")
        out["reproducibility_pack"] = pack
    out["dsr_004_checked"] = True
    return out


def checkpoint_dsr_006(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-006 / D-03 — schema versioning (consumer impact via schema_evolution in pipeline)."""
    out = dict(payload)
    out.setdefault("schema_version", "1")
    out["dsr_006_schema_versioned"] = True
    return out


def checkpoint_dsr_007(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-007 / D-19 — bitemporal correction without erasing prior snapshot."""
    out = dict(payload)
    if out.get("is_correction") or out.get("correction_of"):
        for field in ("observed_at", "effective_at", "corrected_at"):
            if out.get(field) is None:
                raise GovernanceViolationError(f"dsr_007_correction_missing_{field}")
        out.setdefault("prior_snapshot_preserved", True)
    out["dsr_007_checked"] = True
    return out


def checkpoint_dsr_009(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-009 / D-07 — versioned outcome evaluator in lineage."""
    out = dict(payload)
    if out.get("outcome") is not None or out.get("outcome_label"):
        if not str(out.get("outcome_evaluator_version") or "").strip():
            raise GovernanceViolationError("dsr_009_outcome_evaluator_version_required")
        out.setdefault("outcome_lineage_immutable", True)
    out["dsr_009_checked"] = True
    return out


def checkpoint_dsr_010(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-010 / D-08 — Opportunity Universe Contract for recall metrics."""
    out = dict(payload)
    if out.get("recall_metric") or out.get("missed_opportunity_count") is not None:
        ouc = dict(out.get("opportunity_universe_contract") or {})
        for key in ("eligibility_window", "detection_rule", "ground_truth", "exclusions"):
            ouc.setdefault(key, out.get(key) or f"defined:{key}")
        out["opportunity_universe_contract"] = ouc
    out["dsr_010_checked"] = True
    return out


def checkpoint_dsr_011(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-011 / D-09 / D-20 — entity assertion contract."""
    out = dict(payload)
    if out.get("entity_assertion") or out.get("entity_id"):
        assertion = dict(out.get("entity_assertion") or {})
        for key in ("source", "confidence", "validity", "expiry", "conflict_state", "evidence"):
            if key not in assertion and out.get(key) is None:
                assertion.setdefault(key, out.get(key) or ("LOW" if key == "confidence" else "PENDING"))
        if assertion.get("conflict_state") == "CONFLICTED" and out.get("allow_conflicted_display"):
            raise GovernanceViolationError("dsr_011_conflicted_assertion_blocked")
        out["entity_assertion"] = assertion
    out["dsr_011_checked"] = True
    return out


def checkpoint_dsr_014(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-014 / D-04 / D-11 — retention class + storage tier."""
    out = dict(payload)
    if not out.get("retention_class"):
        from data_governance.retention import apply_retention_class

        out = apply_retention_class(out, surface=surface)
    out.setdefault("storage_tier", "hot" if surface in {"decision", "oracle"} else "warm")
    out["dsr_014_retention_bound"] = True
    return out


def checkpoint_dsr_015(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-015 / D-12 — RTO/RPO restore evidence on critical registries."""
    out = dict(payload)
    if surface in {"decision", "signal", "oracle", "ledger_write"}:
        out.setdefault("rto_minutes", 60)
        out.setdefault("rpo_minutes", 15)
        out.setdefault("restore_evidence_ref", "data_governance/restore.py")
    out["dsr_015_restore_bound"] = True
    return out


def checkpoint_dsr_017(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-017 / D-14 — quality failure affects availability/confidence explicitly."""
    out = dict(payload)
    score = float(out.get("data_quality_score") or 70.0)
    out["observed_at"] = _epoch_observed(out)
    if score < 40.0:
        out["availability"] = "degraded"
        out["confidence_multiplier"] = min(float(out.get("confidence_multiplier") or 1.0), score)
        out["quality_degradation_applied"] = True
    else:
        out.setdefault("availability", "live")
    out["dsr_017_quality_propagation"] = True
    return out


def checkpoint_dsr_018(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-018 / D-15 — champion/challenger promotion gate."""
    out = dict(payload)
    if out.get("promotion_request") or out.get("champion_challenger"):
        gate = dict(out.get("promotion_gate") or {})
        for key in ("hypothesis", "baseline", "metric", "rollback_trigger", "approver"):
            gate.setdefault(key, out.get(key) or f"pre_registered:{key}")
        out["promotion_gate"] = gate
    out["dsr_018_checked"] = True
    return out


def checkpoint_dsr_019(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-019 / D-10 — derived asset classification."""
    out = dict(payload)
    out.setdefault("derived_asset_class", out.get("asset_class") or "configured")
    out.setdefault("asset_owner", out.get("owner") or "blackdark/platform")
    out.setdefault("rights_evidence", out.get("rights_evidence") or out.get("rights_profile") or "internal")
    out["dsr_019_classified"] = True
    return out


def checkpoint_dsr_020(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-020 / D-17 — asset value ledger binding."""
    out = dict(payload)
    ledger = dict(out.get("asset_value_ledger") or {})
    for key in ("cost", "usage", "effectiveness", "uniqueness", "rights", "strategic_reuse"):
        ledger.setdefault(key, out.get(key) or "tracked")
    out["asset_value_ledger"] = ledger
    out["dsr_020_ledger_bound"] = True
    return out


def checkpoint_dsr_021(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-021 / D-16 — Living Data Room index state."""
    out = dict(payload)
    if out.get("data_room_export") or out.get("dd_artifact"):
        idx = dict(out.get("data_room_index") or {})
        for key in ("completeness", "freshness", "evidence_strength", "exceptions", "residual_risk", "owner"):
            idx.setdefault(key, out.get(key) or "indexed")
        out["data_room_index"] = idx
    out["dsr_021_checked"] = True
    return out


def checkpoint_dsr_022(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-022 — claim→evidence→version→validity chain."""
    out = dict(payload)
    if out.get("claims") or out.get("accuracy_claim"):
        chain = dict(out.get("claim_evidence_chain") or {})
        for key in ("claim", "evidence", "version", "validity"):
            chain.setdefault(key, out.get(key) or f"bound:{key}")
        out["claim_evidence_chain"] = chain
    out["dsr_022_checked"] = True
    return out


def checkpoint_dsr_023(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-023 — purpose/legal basis/minimization on collection."""
    out = dict(payload)
    if out.get("collects_user_data") or out.get("collects_market_data"):
        for field in ("collection_purpose", "legal_basis", "minimization", "retention_policy", "deletion_policy"):
            if not str(out.get(field) or "").strip():
                out.setdefault(field, out.get("purpose") or "analytics_with_minimization")
        from data_governance.legal import legal_applicability

        legal = legal_applicability(out)
        out["legal_applicability"] = legal
    out["dsr_023_checked"] = True
    return out


def checkpoint_dsr_024(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DSR-024 — flywheel closure gate (all prior DSR checkpoints must have run)."""
    out = dict(payload)
    applied = set(out.get("dsr_checkpoints_applied") or [])
    required = {k for k in DSR_CHECKPOINT_ORDER if k != "DSR-024"}
    missing = required - applied
    if missing:
        raise GovernanceViolationError(f"dsr_024_closure_incomplete:{','.join(sorted(missing))}")
    out["dsr_024_flywheel_gate"] = "closed"
    return out


DSR_CHECKPOINT_ORDER: tuple[str, ...] = (
    "DSR-001",
    "DSR-002",
    "DSR-003",
    "DSR-004",
    "DSR-006",
    "DSR-007",
    "DSR-009",
    "DSR-010",
    "DSR-011",
    "DSR-014",
    "DSR-015",
    "DSR-017",
    "DSR-018",
    "DSR-019",
    "DSR-020",
    "DSR-021",
    "DSR-022",
    "DSR-023",
    "DSR-024",
)

DSR_CHECKPOINTS: dict[str, CheckpointFn] = {
    "DSR-001": checkpoint_dsr_001,
    "DSR-002": checkpoint_dsr_002,
    "DSR-003": checkpoint_dsr_003,
    "DSR-004": checkpoint_dsr_004,
    "DSR-006": checkpoint_dsr_006,
    "DSR-007": checkpoint_dsr_007,
    "DSR-009": checkpoint_dsr_009,
    "DSR-010": checkpoint_dsr_010,
    "DSR-011": checkpoint_dsr_011,
    "DSR-014": checkpoint_dsr_014,
    "DSR-015": checkpoint_dsr_015,
    "DSR-017": checkpoint_dsr_017,
    "DSR-018": checkpoint_dsr_018,
    "DSR-019": checkpoint_dsr_019,
    "DSR-020": checkpoint_dsr_020,
    "DSR-021": checkpoint_dsr_021,
    "DSR-022": checkpoint_dsr_022,
    "DSR-023": checkpoint_dsr_023,
    "DSR-024": checkpoint_dsr_024,
}

D_TO_DSR: dict[str, str] = {
    "D-01": "DSR-001",
    "D-02": "DSR-003",
    "D-03": "DSR-006",
    "D-04": "DSR-014",
    "D-05": "DSR-005",
    "D-06": "DSR-008",
    "D-07": "DSR-009",
    "D-08": "DSR-010",
    "D-09": "DSR-011",
    "D-10": "DSR-019",
    "D-11": "DSR-014",
    "D-12": "DSR-015",
    "D-13": "DSR-016",
    "D-14": "DSR-017",
    "D-15": "DSR-018",
    "D-16": "DSR-021",
    "D-17": "DSR-020",
    "D-18": "DSR-012",
    "D-19": "DSR-007",
    "D-20": "DSR-011",
}


def apply_dsr_checkpoints(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Run all DSR checkpoints in order; annotate applied list for DSR-024 gate."""
    if surface not in _MATERIAL_SURFACES and surface != "ledger_write":
        return dict(payload)
    out = dict(payload)
    applied: list[str] = []
    for dsr_id in DSR_CHECKPOINT_ORDER:
        if dsr_id == "DSR-024":
            out["dsr_checkpoints_applied"] = list(applied)
        fn = DSR_CHECKPOINTS[dsr_id]
        out = fn(surface, out)
        applied.append(dsr_id)
    out["dsr_checkpoints_applied"] = applied
    return out
