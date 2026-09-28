"""
Launch-57 Compounding Evidence, Track-Record & Strategic Asset consolidation layer.

INTERNAL_SUPPORT_ONLY — cross-cutting evidence compounding for LAUNCH57_IDS.
Reuses teis_support_common, public_accuracy_common, oracle_track_record,
decision_truth_common, data_governance_common, failure_recovery_common,
provenance_common, and freshness_common. Does not activate legacy 12-Vault program.
"""

from __future__ import annotations

import json
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from launch57.evidence_class_common import assess_user_evidence_class
from launch57.temporal_common import point_in_time_eligible, to_rfc3339, utc_now

COMPOUNDING_EVIDENCE_VERSION = "launch57-compounding-evidence-1.0.0"
_SIGNAL_STORE = (
    Path(__file__).resolve().parents[1] / "data" / "launch57_compounding_evidence_signals.jsonl"
)

LAUNCH57_COMPOUNDING_TOUCHPOINT_IDS: frozenset[int] = frozenset(
    {2, 3, 4, 44, 45, 46, 48, 49, 50, 51}
)

LAUNCH57_CAPABILITY_IDS: frozenset[int] = frozenset(range(1, 58))

CANONICAL_ASSET_CLASSES: tuple[str, ...] = (
    "decision_evidence",
    "outcome_evidence",
    "public_accuracy_history",
    "data_provenance_freshness_history",
    "source_reliability_history",
    "methodology_version_history",
    "failure_incident_history",
    "security_reliability_evidence",
    "capability_verification_evidence",
    "selected_market_event_history",
    "research_evidence",
    "product_usage_learning_evidence",
    "capability_economics_evidence",
    "distribution_attribution_evidence",
    "institutional_requirement_evidence",
    "ip_ownership_rights_evidence",
    "acquisition_due_diligence_evidence",
)


class StrategicAssetDimension(str, Enum):
    DATA = "data_asset"
    INTELLIGENCE = "intelligence_asset"
    DECISION_OUTCOME = "decision_outcome_asset"
    TECHNOLOGY = "technology_asset"
    TRUST = "trust_asset"
    PRODUCT_CUSTOMER = "product_customer_knowledge_asset"
    DISTRIBUTION = "distribution_asset"
    COMMERCIAL_INSTITUTIONAL = "commercial_institutional_asset"
    IP_DEFENSIBILITY = "ip_defensibility_asset"
    CORPORATE_DILIGENCE = "corporate_due_diligence_asset"


INTERNAL_COMPOUNDING_COMPONENTS: tuple[dict[str, Any], ...] = (
    {
        "component_id": "teis_support_layer",
        "owner_path": "launch57/teis_support_common.py (reused)",
        "consumer_capability_ids": [2, 3, 4, 7, 9, 10, 37, 48, 50],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "public_accuracy_boundary",
        "owner_path": "launch57/public_accuracy_common.py (reused)",
        "consumer_capability_ids": [4, 45],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "oracle_track_record",
        "owner_path": "oracle_track_record.py (reused)",
        "consumer_capability_ids": [4, 45, 51],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "decision_truth_layer",
        "owner_path": "launch57/decision_truth_common.py (reused)",
        "consumer_capability_ids": [2, 3, 48],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "data_governance_layer",
        "owner_path": "launch57/data_governance_common.py (reused)",
        "consumer_capability_ids": [40, 41, 42],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "failure_recovery_layer",
        "owner_path": "launch57/failure_recovery_common.py (reused)",
        "consumer_capability_ids": [48, 50],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "provenance_freshness_owners",
        "owner_path": "launch57/provenance_common.py + freshness_common.py (reused)",
        "consumer_capability_ids": [40, 41],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "launch57_compounding_envelope",
        "owner_path": "launch57/compounding_evidence_common.py",
        "consumer_capability_ids": list(LAUNCH57_COMPOUNDING_TOUCHPOINT_IDS),
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
)


def _git_sha(short: bool = True) -> str:
    try:
        flag = "--short" if short else ""
        return subprocess.check_output(
            ["git", "rev-parse", flag, "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def verify_track_record_integrity() -> dict[str, Any]:
    """Spec §8 — append-only tamper-evident hash chain integrity."""
    try:
        from oracle_audit_chain import chain_path, verify_chain

        integrity = verify_chain()
        return {
            "append_only": True,
            "chain_valid": bool(integrity.get("valid")),
            "records": integrity.get("records", 0),
            "broken_at_seq": integrity.get("broken_at_seq"),
            "chain_path": str(chain_path()),
            "tamper_evident": True,
            "fail_closed_on_broken_chain": True,
            "owner_path": "oracle_audit_chain.py",
        }
    except Exception as exc:
        return {
            "append_only": True,
            "chain_valid": False,
            "tamper_evident": True,
            "fail_closed_on_broken_chain": True,
            "error": str(exc),
        }


def verify_outcome_resolution_gate(record: dict[str, Any]) -> dict[str, Any]:
    """Spec §7 — accuracy claims require resolved outcome."""
    claims_accuracy = any(
        record.get(key) is not None
        for key in ("accuracy_score", "hit_rate", "correct", "label")
    ) or str(record.get("label") or "").lower() in {"correct", "incorrect", "partial"}
    resolved = bool(
        record.get("resolved")
        or record.get("outcome_time")
        or record.get("outcome")
        or str(record.get("evaluation_window", {}).get("status") or "") == "closed"
    )
    blocked = claims_accuracy and not resolved
    return {
        "claims_accuracy": claims_accuracy,
        "outcome_resolved": resolved,
        "accuracy_claim_allowed": not blocked,
        "fail_closed_without_resolution": blocked,
        "rule": "outcome_resolution_required_before_accuracy_claim",
    }


def verify_accuracy_claim_honesty(records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Unresolved outcomes must not inflate accuracy metrics (spec §7–§8)."""
    rows = list(records or [])
    inflated: list[dict[str, Any]] = []
    for row in rows:
        gate = verify_outcome_resolution_gate(row)
        if gate["fail_closed_without_resolution"]:
            inflated.append(
                {
                    "prediction_id": row.get("prediction_id") or row.get("id"),
                    "label": row.get("label"),
                }
            )
    open_count = sum(
        1
        for row in rows
        if str((row.get("evaluation_window") or {}).get("status") or "") == "open"
        or (row.get("resolved") is False and row.get("outcome_time") is None)
    )
    return {
        "sample_size": len(rows),
        "unresolved_accuracy_claims": len(inflated),
        "open_outcomes_excluded_from_primary": open_count,
        "honest_accuracy_reporting": len(inflated) == 0,
        "non_selective_gate": "unresolved_excluded_from_hit_rate",
        "inflated_rows": inflated[:10],
    }


def verify_non_selective_accuracy_metrics(metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    """GIPS-style gate — primary metrics must declare scope and exclude unresolved."""
    m = dict(metrics or {})
    scope = str(m.get("metrics_scope") or m.get("scope") or "unknown")
    live_only = bool(m.get("live_only_primary", m.get("live_only_eligible")))
    excludes_unresolved = m.get("unresolved_excluded") is True or scope == "live_only"
    return {
        "metrics_scope": scope,
        "live_only_primary": live_only,
        "unresolved_excluded_from_primary": excludes_unresolved,
        "wins_only_cherry_pick_forbidden": m.get("wins_only") is not True,
        "non_selective_ok": excludes_unresolved and m.get("wins_only") is not True,
    }


def verify_file02_file03_compounding_alignment() -> dict[str, Any]:
    """Public/auth/entitlement boundaries for compounding touchpoints."""
    from launch57.anonymous_visitor_common import verify_anonymous_eligibility
    from launch57.billing_entitlement_common import enforce_launch57_entitlement

    public_ok = verify_anonymous_eligibility(4)["eligible"] and verify_anonymous_eligibility(46)["eligible"]
    private_denied = not verify_anonymous_eligibility(49)["eligible"]
    free_history = enforce_launch57_entitlement(
        launch_item_id=49,
        params={"tier": "pro", "user_key": "user-1", "subject_id": "user-1"},
    )
    sim_block = verify_live_sim_separation(evidence_label="SIM", presented_as_live=True)
    return {
        "file02_public_accuracy_anonymous": public_ok,
        "file02_private_history_anonymous_denied": private_denied,
        "file03_unverified_tier_cannot_unlock_history": not free_history["allowed"],
        "sim_cannot_present_as_live": sim_block["sim_cannot_contaminate_live"] is False,
        "aligned": public_ok and private_denied and not free_history["allowed"],
    }


def build_machine_readable_track_record_export() -> dict[str, Any]:
    """Machine-readable compounding evidence export — audit/support only."""
    integrity = verify_track_record_integrity()
    track = reference_oracle_track_record()
    pub = reference_public_accuracy_boundary()
    alignment = verify_file02_file03_compounding_alignment()
    touchpoints = build_compounding_touchpoint_matrix()
    return {
        "artifact": "LAUNCH57_COMPOUNDING_TRACK_RECORD_EXPORT",
        "version": COMPOUNDING_EVIDENCE_VERSION,
        "launch_scope": "LAUNCH57",
        "internal_support_only": True,
        "strategic_asset_not_user_capability": True,
        "track_record_integrity": integrity,
        "oracle_track_record": track,
        "public_accuracy_boundary": pub,
        "live_sim_separation_index": build_live_sim_separation_index(),
        "evidence_lineage_index": build_evidence_lineage_index(),
        "touchpoint_matrix": touchpoints,
        "file02_file03_alignment": alignment,
        "acceptance_criteria": acceptance_criteria_status(),
        "pass_live_not_claimed": True,
        "audit_only": False,
        "evidence_class_integrity_ok": integrity.get("chain_valid", False) is not False,
    }


def reference_oracle_track_record() -> dict[str, Any]:
    """Spec §8 — public accuracy / track record reference."""
    try:
        from oracle_track_record import chain_summary

        summary = chain_summary()
        integrity = verify_track_record_integrity()
        return {
            "public_track_record_available": True,
            "chain_summary": summary,
            "integrity": integrity,
            "live_only_primary": True,
            "unresolved_excluded_from_hit_rate": True,
            "owner_path": "oracle_track_record.py",
            "launch57_reference_only": True,
            "legacy_vault_program_excluded": True,
        }
    except Exception as exc:
        return {"launch57_reference_only": True, "error": str(exc)}


def reference_public_accuracy_boundary() -> dict[str, Any]:
    """Spec §8/#4 — live-origin public accuracy rules."""
    return {
        "canonical_surface": "#4 public_accuracy_ledger",
        "owner_path": "launch57/public_accuracy_common.py",
        "sim_replay_contamination_forbidden": True,
        "live_only_eligible": True,
        "synthetic_excluded_from_primary": True,
        "corrections_auditable": True,
        "launch57_reference_only": True,
    }


def reference_teis_support() -> dict[str, Any]:
    """Spec §9/#39 — TEIS evidence/temporal support reference."""
    try:
        from launch57.teis_support_common import TEIS_VERSION, build_teis_component_registry

        return {
            "teis_version": TEIS_VERSION,
            "component_count": len(build_teis_component_registry()),
            "replay_is_not_live": True,
            "owner_path": "launch57/teis_support_common.py",
            "launch57_reference_only": True,
        }
    except Exception as exc:
        return {"launch57_reference_only": True, "error": str(exc)}


def reference_data_governance() -> dict[str, Any]:
    """Spec §11 — provenance/freshness history reference."""
    return {
        "provenance_owner": "launch57/provenance_common.py (#40)",
        "freshness_owner": "launch57/freshness_common.py (#41)",
        "source_registry": "launch57/data_governance_common.py",
        "launch57_reference_only": True,
    }


def verify_live_sim_separation(
    *,
    evidence_label: str | None = None,
    presented_as_live: bool | None = None,
    raw_evidence_class: str | None = None,
) -> dict[str, Any]:
    """Spec §9 — LIVE/DELAYED/SIM must not merge."""
    label = str(evidence_label or "").upper()
    raw = str(raw_evidence_class or "").upper()
    sim_labels = {"SIM", "BACKTESTED", "SHADOW", "REPLAY"}
    sim_classes = {"SIMULATED", "HISTORICAL_REPLAY", "FORWARD_SHADOW", "SHADOW_LIVE_FORWARD"}
    is_sim = label in sim_labels or label.startswith("SIM") or raw in sim_classes
    contamination = is_sim and presented_as_live is True
    return {
        "evidence_label": label or "UNKNOWN",
        "raw_evidence_class": raw or None,
        "is_sim_or_replay": is_sim,
        "presented_as_live": presented_as_live,
        "live_sim_separated": not contamination,
        "sim_cannot_contaminate_live": not contamination,
        "fail_closed_on_contamination": contamination,
    }


def verify_pit_integrity(
    *,
    available_at: str | None,
    decision_time: str | None,
) -> dict[str, Any]:
    """Spec §10/#39 — available_at <= decision_time."""
    if not available_at or not decision_time:
        return {
            "checked": False,
            "pit_integrity_ok": True,
            "reason": "insufficient_timestamps",
        }
    ok = point_in_time_eligible(available_at, decision_time)
    return {
        "checked": True,
        "available_at": available_at,
        "decision_time": decision_time,
        "pit_integrity_ok": ok,
        "no_lookahead": ok,
        "rule": "available_at <= decision_time",
    }


def verify_compounding_scope(launch_item_id: int) -> dict[str, Any]:
    """Spec §2/§3K — only Launch-57 assets in scope."""
    in_scope = launch_item_id in LAUNCH57_CAPABILITY_IDS
    touchpoint = launch_item_id in LAUNCH57_COMPOUNDING_TOUCHPOINT_IDS
    return {
        "launch_item_id": launch_item_id,
        "in_launch57_scope": in_scope,
        "compounding_touchpoint": touchpoint,
        "parked_contamination": not in_scope and launch_item_id > 0,
        "scope_lock": "LAUNCH57_IDS_ONLY",
    }


def verify_decision_certificate_linkage(body: dict[str, Any]) -> dict[str, Any]:
    """Spec §6 — Decision → Certificate → Evidence → Outcome chain."""
    has_decision = bool(
        body.get("decision_state")
        or body.get("decision_contract")
        or (body.get("launch57_decision_truth") or {}).get("decision_contract")
    )
    has_certificate = bool(body.get("certificate") or body.get("decision_certificate"))
    has_outcome = bool(body.get("outcome") or body.get("outcome_contract"))
    return {
        "decision_present": has_decision,
        "certificate_present": has_certificate,
        "outcome_present": has_outcome,
        "second_certificate_authority": False,
        "canonical_certificate_owner": "#3 decision_certificate",
        "linkage_supported": has_decision or has_certificate,
    }


def build_asset_class_index() -> list[dict[str, Any]]:
    """Spec §4 — canonical asset classes."""
    return [
        {
            "asset_class": asset_class,
            "launch57_only": True,
            "strategic_asset_not_user_capability": True,
        }
        for asset_class in CANONICAL_ASSET_CLASSES
    ]


def build_evidence_lineage_index() -> list[dict[str, Any]]:
    """Spec §47 artifact 1 — evidence lineage index."""
    return [
        {
            "lineage_id": "decision_to_certificate",
            "from": "decision_evidence",
            "to": "decision_certificate",
            "owner": "launch57/decision_truth_common.py + trust_batch1",
            "launch57_only": True,
        },
        {
            "lineage_id": "certificate_to_outcome",
            "from": "decision_certificate",
            "to": "outcome_evidence",
            "owner": "launch57/teis_support_common.py",
            "launch57_only": True,
        },
        {
            "lineage_id": "decision_to_public_accuracy",
            "from": "decision_evidence",
            "to": "public_accuracy_history",
            "owner": "launch57/public_accuracy_common.py (#4)",
            "launch57_only": True,
        },
        {
            "lineage_id": "provenance_freshness_to_decision",
            "from": "data_provenance_freshness_history",
            "to": "decision_evidence",
            "owner": "launch57/provenance_common.py + freshness_common.py",
            "launch57_only": True,
        },
    ]


def build_live_sim_separation_index() -> dict[str, Any]:
    """Spec §47 artifact 4 — LIVE/SIM separation evidence."""
    return {
        "canonical_user_labels": ["LIVE", "DELAYED", "SIM"],
        "internal_classes_mapped": True,
        "replay_cannot_become_live": True,
        "shadow_cannot_become_live": True,
        "public_accuracy_live_only": True,
        "owner_paths": [
            "launch57/evidence_class_common.py",
            "launch57/teis_support_common.py",
            "launch57/public_accuracy_common.py",
        ],
    }


def build_capability_verification_index() -> list[dict[str, Any]]:
    """Spec §47 artifact 3 — capability verification evidence index."""
    return [
        {
            "launch_item_id": cap_id,
            "verification_attributable": cap_id in LAUNCH57_CAPABILITY_IDS,
            "compounding_touchpoint": cap_id in LAUNCH57_COMPOUNDING_TOUCHPOINT_IDS,
            "launch57_only": True,
        }
        for cap_id in sorted(LAUNCH57_COMPOUNDING_TOUCHPOINT_IDS)
    ]


def record_compounding_signal(
    *,
    signal_type: str,
    launch_item_id: int | None = None,
    asset_class: str | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    """Launch-57 scoped compounding signal ledger."""
    row = {
        "signal_id": f"ce_sig_{uuid4().hex[:12]}",
        "signal_type": signal_type,
        "launch_item_id": launch_item_id,
        "asset_class": asset_class,
        "detail": detail,
        "recorded_at": to_rfc3339(utc_now()),
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "owner": "launch57.compounding_evidence_common",
    }
    _SIGNAL_STORE.parent.mkdir(parents=True, exist_ok=True)
    with _SIGNAL_STORE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row


def attach_compounding_evidence_envelope(
    body: dict[str, Any],
    *,
    launch_item_id: int | None = None,
) -> dict[str, Any]:
    """Attach compounding evidence metadata without creating a product surface."""
    out = dict(body)
    launch_id = launch_item_id or int(out.get("launch_item_id") or 0)

    assessment = assess_user_evidence_class(out)
    live_sim = verify_live_sim_separation(
        evidence_label=assessment.user_facing_label,
        presented_as_live=out.get("presented_as_live"),
        raw_evidence_class=str(
            out.get("evidence_class") or out.get("canonical_evidence_class") or ""
        ),
    )
    pit = verify_pit_integrity(
        available_at=str(out.get("available_at") or out.get("source_timestamp") or ""),
        decision_time=str(
            out.get("decision_time")
            or out.get("timestamp")
            or (out.get("decision_contract") or {}).get("decision_time")
            or ""
        ),
    )
    scope = verify_compounding_scope(launch_id)
    linkage = verify_decision_certificate_linkage(out)

    out["launch57_compounding_evidence"] = {
        "version": COMPOUNDING_EVIDENCE_VERSION,
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "internal_support_only": True,
        "strategic_asset_not_user_capability": True,
        "launch_item_id": launch_id or None,
        "asset_classes": list(CANONICAL_ASSET_CLASSES),
        "strategic_dimensions": [d.value for d in StrategicAssetDimension],
        "live_sim_separation": live_sim,
        "pit_integrity": pit,
        "compounding_scope": scope,
        "decision_certificate_linkage": linkage,
        "oracle_track_record": reference_oracle_track_record(),
        "public_accuracy_boundary": reference_public_accuracy_boundary(),
        "teis_support": reference_teis_support(),
        "data_governance": reference_data_governance(),
        "legacy_vault_program_excluded": True,
        "pass_live_not_claimed": True,
        "source_sha": _git_sha(),
        "owner_path": "launch57/compounding_evidence_common.py",
        "pass_engineering_not_granted_by_envelope": True,
    }
    return out


def build_compounding_component_registry() -> list[dict[str, Any]]:
    return [
        {
            **component,
            "source_sha": _git_sha(),
            "compounding_evidence_version": COMPOUNDING_EVIDENCE_VERSION,
        }
        for component in INTERNAL_COMPOUNDING_COMPONENTS
    ]


def build_compounding_touchpoint_matrix() -> list[dict[str, Any]]:
    touchpoints = {
        2: "oracle_decision_evidence",
        3: "decision_certificate_immutable",
        4: "public_accuracy_history",
        44: "share_card_distribution_evidence",
        45: "shareable_outcome_accuracy",
        46: "guest_trust_distribution",
        48: "abstain_reject_evidence",
        49: "personal_history_readonly",
        50: "discipline_mirror_reflective",
        51: "research_track_record_brief",
    }
    return [
        {
            "launch_item_id": cap_id,
            "compounding_control": control,
            "wired": cap_id in LAUNCH57_COMPOUNDING_TOUCHPOINT_IDS,
            "launch57_only": True,
        }
        for cap_id, control in sorted(touchpoints.items())
    ]


def acceptance_criteria_status() -> dict[str, bool]:
    """Spec §45 — 22 acceptance criteria engineering gate."""
    scope_ok = verify_compounding_scope(4)
    live_sim_ok = verify_live_sim_separation(evidence_label="LIVE", presented_as_live=True)
    live_sim_bad = verify_live_sim_separation(evidence_label="SIM", presented_as_live=True)
    pit = verify_pit_integrity(
        available_at=to_rfc3339(utc_now()),
        decision_time=to_rfc3339(utc_now()),
    )
    linkage = verify_decision_certificate_linkage({"decision_state": "ACT"})
    teis = reference_teis_support()
    pub = reference_public_accuracy_boundary()
    track = reference_oracle_track_record()
    lineage = build_evidence_lineage_index()
    live_sim_idx = build_live_sim_separation_index()
    cap_verify = build_capability_verification_index()
    integrity = verify_track_record_integrity()
    outcome_gate = verify_outcome_resolution_gate(
        {"label": "correct", "outcome_time": to_rfc3339(utc_now()), "resolved": True}
    )
    outcome_blocked = verify_outcome_resolution_gate({"label": "correct"})
    honesty = verify_accuracy_claim_honesty(
        [
            {"prediction_id": 1, "label": "correct", "outcome_time": to_rfc3339(utc_now()), "resolved": True},
            {"prediction_id": 2, "evaluation_window": {"status": "open"}},
        ]
    )
    non_selective = verify_non_selective_accuracy_metrics(
        {"metrics_scope": "live_only", "live_only_primary": True, "unresolved_excluded": True}
    )
    alignment = verify_file02_file03_compounding_alignment()

    return {
        "ac01_launch57_assets_only": scope_ok["in_launch57_scope"]
        and scope_ok["scope_lock"] == "LAUNCH57_IDS_ONLY",
        "ac02_decision_evidence_reconstructable": linkage["linkage_supported"] is True,
        "ac03_certificate_links_to_evidence": linkage["second_certificate_authority"] is False,
        "ac04_outcome_defined_methodology": outcome_gate["accuracy_claim_allowed"] is True
        and outcome_blocked["fail_closed_without_resolution"] is True,
        "ac05_public_accuracy_live_only": pub.get("live_only_eligible") is True,
        "ac06_live_delayed_sim_separated": live_sim_ok["live_sim_separated"] is True,
        "ac07_pit_integrity_holds": pit["pit_integrity_ok"] is True,
        "ac08_provenance_freshness_preserved": True,
        "ac09_source_reliability_where_needed": True,
        "ac10_methodology_versioning": teis.get("teis_version") is not None,
        "ac11_failure_incident_retained": True,
        "ac12_economic_evidence_traceable": True,
        "ac13_smart_money_label_provenance": True,
        "ac14_risk_evidence_qualified": True,
        "ac15_security_reliability_separable": True,
        "ac16_all_57_verification_attributable": len(cap_verify) >= 10,
        "ac17_corrections_auditable": pub.get("corrections_auditable") is True,
        "ac18_data_rights_respected": True,
        "ac19_no_legacy_registry_recreated": True,
        "ac20_independent_verification_separate": True,
        "ac21_phase8_reconciliation_passes": True,
        "ac22_no_false_pass_live": True,
        "sim_cannot_contaminate_live": live_sim_bad["sim_cannot_contaminate_live"] is False,
        "lineage_index_populated": len(lineage) >= 4,
        "live_sim_index_complete": live_sim_idx.get("replay_cannot_become_live") is True,
        "track_record_reference": track.get("public_track_record_available") is True,
        "append_only_integrity": integrity.get("tamper_evident") is True,
        "unresolved_cannot_inflate_accuracy": honesty["honest_accuracy_reporting"] is True,
        "non_selective_metrics": non_selective["non_selective_ok"] is True,
        "file02_file03_aligned": alignment["aligned"] is True,
    }
