"""
Runtime governance enforcement — v4_v2 mandatory controls on live paths.

Every material write (signal/decision/exposure/failure/event/oracle-chain) and
cap646/oracle execute MUST pass through this module. Fail-closed on violation.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from cap646.evidence_class import assert_promotion_allowed, infer_evidence_class

from blackdark.data_governance.collection_policy import ensure_collection_policies
from blackdark.data_governance.contracts import (
    ensure_contracts_materialized,
    get_contract,
    validate_contract,
)
from blackdark.data_governance.intelligence_receipt import issue_intelligence_receipt
from blackdark.data_governance.lineage import inherit_evidence_origin, propagate_lineage
from blackdark.data_governance.pit_evidence import validate_pit_framing
from blackdark.data_governance.retention import get_retention_class
from blackdark.data_governance.rights import check_rights
from blackdark.data_governance.schema_registry import validate_record_against_schema
from blackdark.data.response_metadata import DATA_STATE_LIVE, resolve_data_state

ROOT = Path(__file__).resolve().parents[2]
RESTORE_EVIDENCE = ROOT / "data" / "governance" / "restore_evidence.jsonl"

ASSET_CONTRACT_MAP: dict[str, str] = {
    "signal": "dac_signal_registry",
    "decision": "dac_decision_ledger",
    "exposure": "dac_user_exposure_log",
    "failure": "dac_failure_corpus",
    "market_event": "dac_market_event_library",
    "oracle_chain": "dac_oracle_audit_chain",
}

SCHEMA_MAP: dict[str, str] = {
    "signal": "signal_registry",
    "decision": "decision_ledger",
    "oracle_chain": "oracle_audit_chain",
}


class GovernanceViolationError(RuntimeError):
    """Raised when a mandatory governance control fails on a live path."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"governance_violation:{code}:{detail}")


def _disabled() -> bool:
    return os.getenv("BLACKDARK_GOVERNANCE_ENFORCE", "1").lower() in {"0", "false", "no"}


def _latest_restore_evidence() -> dict[str, Any] | None:
    if not RESTORE_EVIDENCE.exists():
        return None
    lines = [ln for ln in RESTORE_EVIDENCE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return None


def _enforce_cost_guards() -> None:
    """REQ-0024 — cost guard must exist for every canonical contract before live execute."""
    from blackdark.data_governance.contracts import CANONICAL_CONTRACTS
    from blackdark.data_governance.cost_guard import ensure_cost_guards, validate_cost_guard

    ensure_cost_guards()
    for asset_id in CANONICAL_CONTRACTS:
        ok, missing = validate_cost_guard(asset_id)
        if not ok:
            raise GovernanceViolationError("cost_guard_invalid", f"{asset_id}:{','.join(missing)}")


def assert_governance_subsystem_ready(*, surface: str) -> None:
    """DSR-001/015/024 — contracts + restore evidence must exist before live execute."""
    if _disabled():
        return
    ensure_contracts_materialized()
    ensure_collection_policies()
    _enforce_cost_guards()
    contract = get_contract("dac_decision_ledger")
    if not contract:
        raise GovernanceViolationError("missing_contract", "dac_decision_ledger")
    ok, missing = validate_contract(contract)
    if not ok:
        raise GovernanceViolationError("invalid_contract", ",".join(missing))
    restore = _latest_restore_evidence()
    if not restore or not restore.get("all_integrity_ok"):
        from blackdark.data_governance.restore import run_restore_drill

        restore = run_restore_drill(root=ROOT)
        if not restore.get("all_integrity_ok"):
            raise GovernanceViolationError("restore_evidence_failed", surface)
    started = restore.get("started_at")
    if started:
        try:
            ts = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
            if datetime.now(UTC) - ts.astimezone(UTC) > timedelta(days=30):
                raise GovernanceViolationError("restore_evidence_expired", surface)
        except ValueError:
            pass


def enforce_rights_for_contract(contract_id: str, action: str = "storage") -> None:
    """DSR-005 — machine-enforceable rights before material storage."""
    if _disabled():
        return
    contract = get_contract(contract_id)
    if not contract:
        raise GovernanceViolationError("unknown_contract", contract_id)
    profile_id = str(contract.get("rights_profile_id") or "")
    allowed, reason = check_rights(profile_id, action)
    if not allowed:
        raise GovernanceViolationError("rights_denied", reason)


def enforce_replay_framing(
    *,
    source: str | None,
    claim_text: str | None = None,
    record: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """§8 / DSR-003 — replay sources must not be framed as live predictions."""
    if _disabled():
        return None
    src = (source or "").lower()
    is_replay = any(h in src for h in ("replay", "backtest", "historical_seed", "market_replay"))
    if not is_replay:
        return None
    text = claim_text or ""
    ok, reason = validate_pit_framing(is_replay=True, claim_text=text or "point-in-time replay")
    if not ok:
        raise GovernanceViolationError("pit_framing_violation", reason)
    from blackdark.data_governance.pit_evidence import create_pit_contract

    rec = record or {}
    reconstructed = bool(rec.get("reconstructed_with_later_data"))
    if reconstructed and "reconstructed-with-later-data" not in text.lower():
        raise GovernanceViolationError("pit_reconstruction_unlabeled", "reconstructed_with_later_data")
    pit = create_pit_contract(
        replay_id=str(rec.get("replay_id") or source or "replay"),
        knowledge_cutoff=str(rec.get("created_at") or rec.get("timestamp") or datetime.now(UTC).isoformat()),
        model_version=str(rec.get("model_version")) if rec.get("model_version") else None,
        oracle=str(rec.get("source") or source or "replay"),
        reconstructed_with_later_data=reconstructed,
    )
    return pit


def _stamp_provenance(*, asset_kind: str, record: dict[str, Any], artifact_id: str) -> dict[str, str]:
    """REQ-0816 — provenance hash on material writes (decision/signal chain)."""
    from blackdark.data.provenance import hash_payload

    payload = json.dumps(
        {
            "asset_kind": asset_kind,
            "artifact_id": artifact_id,
            "source": record.get("source"),
            "evidence_class": record.get("evidence_class"),
            "lineage": record.get("lineage"),
        },
        sort_keys=True,
        default=str,
    )
    return {
        "provenance_hash": hash_payload(payload),
        "provenance_chain": f"{asset_kind}:{artifact_id}",
    }


def _register_material_claim(*, asset_kind: str, artifact_id: str, receipt_id: str, record: dict[str, Any]) -> str:
    """REQ-DSR-022 — claim linked to receipt evidence on every material write."""
    from blackdark.data_governance.claims_registry import register_claim

    claim_row = register_claim(
        claim=f"{asset_kind}:{artifact_id}:material_write",
        evidence_ref=str(receipt_id),
        version=str(record.get("model_version") or record.get("governance", {}).get("policy") or "v4_v2_runtime"),
    )
    return str(claim_row.get("claim_id"))


def _record_entity_for_material(*, record: dict[str, Any], asset_kind: str, receipt_id: str) -> str | None:
    """REQ-DSR-011 / D-09 — entity assertion on symbol/asset for material writes."""
    from blackdark.data_governance.entity_assertions import record_entity_assertion

    entity_id = str(record.get("symbol") or record.get("asset") or "").upper()
    if not entity_id:
        return None
    assertion = record_entity_assertion(
        entity_type="market_asset",
        entity_id=entity_id,
        assertion=f"{asset_kind}_write_for_{entity_id}",
        source=str(record.get("source") or asset_kind),
        confidence=float(record.get("confidence") or record.get("score") or 0.75),
        evidence_ref=str(receipt_id),
        conflict_state="CONFIRMED",
    )
    return str(assertion.get("assertion_id"))


def _enforce_promotion_gate(*, evidence_class: str, target: str, record: dict[str, Any]) -> None:
    """REQ-DSR-018 / D-15 — promotion gate before evidence class upgrade."""
    from blackdark.data_governance.promotion_gate import evaluate_promotion_gate

    has_evidence = bool(record.get("promotion_evidence") or record.get("production_verified"))
    gate = evaluate_promotion_gate(
        champion_id=str(evidence_class),
        challenger_id=str(target),
        hypothesis=f"promote_{evidence_class}_to_{target}",
        baseline_metric=0.0,
        challenger_metric=1.0 if has_evidence else 0.0,
        non_regression_pass=has_evidence,
        sample_coverage=str(record.get("sample_coverage") or ("adequate" if has_evidence else "insufficient")),
        approver=str(record.get("approver") or "runtime_gate"),
        rollback_trigger="evidence_class_regression",
    )
    if not gate.get("promoted"):
        raise GovernanceViolationError("promotion_gate_denied", f"{evidence_class}->{target}")


def enforce_data_state_for_decision(*, dataset: str, count: int, latest_record_at: str | None = None) -> dict[str, Any]:
    """DSR-017 — stale/missing must degrade, never silent live."""
    state, reason = resolve_data_state(count=count, dataset=dataset, latest_record_at=latest_record_at)
    meta = {"data_state": state, "data_state_reason": reason}
    if state != DATA_STATE_LIVE:
        meta["degraded"] = True
        meta["availability"] = "degraded" if state == "STALE" else "blocked"
    return meta


def enforce_material_write(
    *,
    asset_kind: str,
    record: dict[str, Any],
    surface: str,
    parent: dict[str, Any] | None = None,
    schema_id: str | None = None,
    claim_text: str | None = None,
) -> dict[str, Any]:
    """
    Central runtime gate for signal/decision/exposure/failure/market_event writes.
    Returns enriched record (receipt, lineage, retention, contract stamp).
    """
    if _disabled():
        return record

    contract_id = ASSET_CONTRACT_MAP.get(asset_kind, "")
    if not contract_id:
        raise GovernanceViolationError("unmapped_asset_kind", asset_kind)

    assert_governance_subsystem_ready(surface=surface)
    enforce_rights_for_contract(contract_id, "storage")
    pit = enforce_replay_framing(
        source=str(record.get("source") or ""),
        claim_text=claim_text,
        record=record,
    )
    if pit:
        record["pit_contract_id"] = pit["pit_id"]

    contract = get_contract(contract_id)
    if not contract:
        raise GovernanceViolationError("contract_not_found", contract_id)
    ok, missing = validate_contract(contract)
    if not ok:
        raise GovernanceViolationError("contract_invalid", f"{contract_id}:{','.join(missing)}")

    sid = schema_id or SCHEMA_MAP.get(asset_kind)
    if sid:
        schema_ok, schema_missing = validate_record_against_schema(sid, record)
        if not schema_ok:
            raise GovernanceViolationError("schema_violation", ",".join(schema_missing))

    evidence_class = record.get("evidence_class") or infer_evidence_class(source=str(record.get("source") or surface))
    if parent:
        enriched = propagate_lineage(parent, record, transform=f"{surface}:{asset_kind}")
        if enriched.get("promotion_blocked"):
            raise GovernanceViolationError("evidence_promotion_denied", str(enriched["promotion_blocked"]))
        record = enriched
    else:
        origin = inherit_evidence_origin(parent_class=evidence_class, source=str(record.get("source") or surface))
        record.setdefault("evidence_origin", origin["evidence_origin"])
        record.setdefault("lineage", origin)

    target = record.get("evidence_class")
    if target and evidence_class and target != evidence_class:
        _enforce_promotion_gate(evidence_class=str(evidence_class), target=str(target), record=record)
        try:
            assert_promotion_allowed(evidence_class, target)  # type: ignore[arg-type]
        except ValueError as exc:
            raise GovernanceViolationError("evidence_promotion_denied", str(exc)) from exc

    retention_id = contract.get("retention_class")
    retention = get_retention_class(str(retention_id)) if retention_id else None
    if retention:
        record["retention_class"] = retention.get("class_id")
        record["storage_tier"] = retention.get("tier")

    artifact_id = (
        record.get("decision_id")
        or record.get("signal_id")
        or record.get("exposure_id")
        or record.get("failure_id")
        or record.get("event_id")
        or record.get("prediction_id")
        or "unknown"
    )
    receipt = issue_intelligence_receipt(
        artifact_type=asset_kind,
        artifact_id=str(artifact_id),
        source_snapshot_hash=record.get("features_hash") or record.get("certificate_hash"),
        evidence_class=str(evidence_class),
        source=str(record.get("source") or surface),
        output=record,
    )
    record["governance"] = {
        "contract_id": contract_id,
        "receipt_id": receipt.get("receipt_id"),
        "enforced_at": datetime.now(UTC).isoformat(),
        "surface": surface,
        "policy": "v4_v2_runtime",
    }
    if pit:
        record["governance"]["pit_contract_id"] = pit["pit_id"]
    prov = _stamp_provenance(asset_kind=asset_kind, record=record, artifact_id=str(artifact_id))
    record["governance"].update(prov)
    claim_id = _register_material_claim(
        asset_kind=asset_kind,
        artifact_id=str(artifact_id),
        receipt_id=str(receipt.get("receipt_id")),
        record=record,
    )
    record["governance"]["claim_id"] = claim_id
    assertion_id = _record_entity_for_material(record=record, asset_kind=asset_kind, receipt_id=str(receipt.get("receipt_id")))
    if assertion_id:
        record["governance"]["entity_assertion_id"] = assertion_id
    from blackdark.data_governance.outcome_registry import ensure_outcome_registry
    from blackdark.data_governance.opportunity_universe import ensure_opportunity_universes
    from blackdark.data_governance.derived_assets import ensure_derived_classifications
    from blackdark.data_governance.collection_policy import ensure_collection_policies

    outcome_reg = ensure_outcome_registry()
    opp_reg = ensure_opportunity_universes()
    derived = ensure_derived_classifications()
    policies = ensure_collection_policies()
    record["governance"]["outcome_evaluator"] = outcome_reg.get("evaluators", {}).get("decision_outcome_v1", {}).get("version")
    record["governance"]["opportunity_universe"] = list(opp_reg.get("universes", {}).keys())[:1]
    record["governance"]["derived_assets_registered"] = len(derived.get("assets", {}))
    record["governance"]["collection_policies"] = len(policies.get("policies", {}))
    from blackdark.data_governance.asset_value_ledger import record_asset_value

    record_asset_value(asset_id=contract_id, usage_count=1, review_action="keep")
    record.setdefault("evidence_class", evidence_class)
    return record


async def enforce_capability_execute(
    capability_id: int,
    *,
    user: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> None:
    """Gate cap646 execute — subsystem ready + collection policy exists."""
    if _disabled():
        return
    assert_governance_subsystem_ready(surface=f"cap646:{capability_id}")
    policies = ensure_collection_policies().get("policies", {})
    if not policies:
        raise GovernanceViolationError("collection_policy_missing", str(capability_id))
    from blackdark.data_governance.data_room_index import build_data_room_index

    build_data_room_index(root=ROOT)


def enforce_oracle_chain_record(record: dict[str, Any], *, surface: str = "oracle") -> dict[str, Any]:
    """DSR-016 — chain append preceded by contract/rights/receipt enforcement."""
    if _disabled():
        return record
    assert_governance_subsystem_ready(surface=surface)
    enforce_rights_for_contract("dac_oracle_audit_chain", "storage")
    enriched = dict(record)
    enriched.setdefault("source", record.get("source") or "oracle")
    enriched.setdefault("evidence_class", infer_evidence_class(source=str(enriched.get("source"))))
    pit = enforce_replay_framing(source=str(enriched.get("source")), record=enriched)
    if pit:
        enriched["pit_contract_id"] = pit["pit_id"]
    artifact_id = str(enriched.get("prediction_id") or enriched.get("event") or "oracle")
    receipt = issue_intelligence_receipt(
        artifact_type="oracle_chain",
        artifact_id=artifact_id,
        evidence_class=str(enriched.get("evidence_class")),
        source=str(enriched.get("source")),
        output=enriched,
    )
    enriched["governance"] = {
        "contract_id": "dac_oracle_audit_chain",
        "receipt_id": receipt.get("receipt_id"),
        "enforced_at": datetime.now(UTC).isoformat(),
        "surface": surface,
    }
    if pit:
        enriched["governance"]["pit_contract_id"] = pit["pit_id"]
    prov = _stamp_provenance(asset_kind="oracle_chain", record=enriched, artifact_id=artifact_id)
    enriched["governance"].update(prov)
    claim_id = _register_material_claim(
        asset_kind="oracle_chain",
        artifact_id=artifact_id,
        receipt_id=str(receipt.get("receipt_id")),
        record=enriched,
    )
    enriched["governance"]["claim_id"] = claim_id
    from blackdark.data_governance.outcome_registry import ensure_outcome_registry

    outcome_reg = ensure_outcome_registry()
    enriched["governance"]["outcome_evaluator"] = outcome_reg.get("evaluators", {}).get(
        "oracle_outcome_v1", {}
    ).get("version")
    return enriched


def enforce_ledger_link_update(
    *,
    decision_id: str,
    prior_row: dict[str, Any],
    updates: dict[str, Any],
    reason: str,
) -> None:
    """DSR-007 — append-only corrections when linking exposure/outcome."""
    if _disabled():
        return
    import hashlib

    from blackdark.data_governance.corrections import record_correction

    assert_governance_subsystem_ready(surface="decision_ledger_link")
    prior_ref = hashlib.sha256(
        json.dumps(prior_row, sort_keys=True, default=str).encode()
    ).hexdigest()[:24]
    record_correction(
        target_asset="dac_decision_ledger",
        target_record_id=decision_id,
        observed_at=str(prior_row.get("created_at") or datetime.now(UTC).isoformat()),
        effective_at=datetime.now(UTC).isoformat(),
        reason=reason,
        prior_snapshot_ref=prior_ref,
        new_value_summary=updates,
    )


def enforce_oracle_outcome_resolution(
    *,
    prediction_id: int,
    outcome: str,
    accuracy_score: float,
) -> dict[str, Any]:
    """REQ-0815 / DSR-009 — outcome evaluator active before oracle resolve."""
    if _disabled():
        return {}
    assert_governance_subsystem_ready(surface="oracle_resolve")
    from blackdark.data_governance.outcome_registry import ensure_outcome_registry

    reg = ensure_outcome_registry()
    ev = reg.get("evaluators", {}).get("oracle_outcome_v1")
    if not ev or not ev.get("active"):
        raise GovernanceViolationError("outcome_evaluator_inactive", "oracle_outcome_v1")
    claim_id = _register_material_claim(
        asset_kind="oracle_outcome",
        artifact_id=str(prediction_id),
        receipt_id=f"oracle:{prediction_id}:{outcome}",
        record={"model_version": ev.get("version"), "source": "oracle_resolve"},
    )
    return {
        "evaluator_id": "oracle_outcome_v1",
        "evaluator_version": ev.get("version"),
        "claim_id": claim_id,
        "outcome": outcome,
        "accuracy_score": accuracy_score,
    }
