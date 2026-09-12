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


def assert_governance_subsystem_ready(*, surface: str) -> None:
    """DSR-001/015/024 — contracts + restore evidence must exist before live execute."""
    if _disabled():
        return
    ensure_contracts_materialized()
    ensure_collection_policies()
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


def enforce_replay_framing(*, source: str | None, claim_text: str | None = None) -> None:
    """§8 / DSR-003 — replay sources must not be framed as live predictions."""
    if _disabled():
        return
    src = (source or "").lower()
    is_replay = any(h in src for h in ("replay", "backtest", "historical_seed", "market_replay"))
    if not is_replay:
        return
    text = claim_text or ""
    ok, reason = validate_pit_framing(is_replay=True, claim_text=text or "point-in-time replay")
    if not ok:
        raise GovernanceViolationError("pit_framing_violation", reason)


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
    enforce_replay_framing(source=str(record.get("source") or ""), claim_text=claim_text)

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
    enforce_replay_framing(source=str(enriched.get("source")))
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
    return enriched
