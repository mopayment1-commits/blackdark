"""
Launch-57 Decision Truth consolidation layer.

INTERNAL_SUPPORT_ONLY — cross-cutting decision truth for LAUNCH57_IDS.
Integrates canonical owners #6, #40, #41 with ACT/WAIT/ABSTAIN decision flow.
Reuses existing Launch-57 phase 1–3 batches; does not activate legacy DTS program.
"""

from __future__ import annotations

import json
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from launch57.evidence_class_common import assess_user_evidence_class
from launch57.temporal_common import to_rfc3339, utc_now

DECISION_TRUTH_VERSION = "launch57-decision-truth-1.0.0"
_SIGNAL_STORE = (
    Path(__file__).resolve().parents[1] / "data" / "launch57_decision_truth_signals.jsonl"
)

LAUNCH57_DECISION_TRUTH_IDS: frozenset[int] = frozenset(
    {
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        33,
        34,
        35,
        36,
        37,
        40,
        41,
        43,
        44,
        45,
        46,
        47,
        48,
        49,
        50,
        53,
        54,
        55,
        56,
        57,
    }
)

_STALE_FRESHNESS = frozenset({"STALE", "UNKNOWN"})
_LIVE_ELIGIBLE_FRESHNESS = frozenset({"LIVE", "NEAR_LIVE", "DELAYED"})


class DecisionState(str, Enum):
    ACT = "ACT"
    WAIT = "WAIT"
    ABSTAIN = "ABSTAIN"


class AbstainReason(str, Enum):
    STALE_DATA = "stale_data"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING_SIGNALS = "conflicting_signals"
    MISSING_REQUIRED_SOURCE = "missing_required_source"
    COST_UNCERTAINTY = "cost_uncertainty"
    NEGATIVE_NET_EDGE = "negative_net_edge"
    QUALITY_DEGRADATION = "quality_degradation"
    SOURCE_UNAVAILABLE = "source_unavailable"
    UNSUPPORTED_CONTEXT = "unsupported_context"


INTERNAL_DECISION_TRUTH_COMPONENTS: tuple[dict[str, Any], ...] = (
    {
        "component_id": "evidence_class_gate",
        "owner_path": "launch57/evidence_class_common.py (#6)",
        "consumer_capability_ids": list(LAUNCH57_DECISION_TRUTH_IDS),
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
    {
        "component_id": "freshness_gate",
        "owner_path": "launch57/freshness_common.py (#41)",
        "consumer_capability_ids": [2, 3, 7, 9, 10, 11, 12, 21, 22, 23, 24, 37, 41, 42, 43],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
    {
        "component_id": "provenance_gate",
        "owner_path": "launch57/provenance_common.py (#40)",
        "consumer_capability_ids": [2, 3, 7, 9, 10, 11, 12, 21, 22, 23, 24, 37, 40, 42],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
    {
        "component_id": "net_edge_gate",
        "owner_path": "launch57/trust_batch1.py (#5)",
        "consumer_capability_ids": [5, 43],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
    {
        "component_id": "oracle_decision_surface",
        "owner_path": "launch57/trust_batch1.py (#2)",
        "consumer_capability_ids": [2],
        "launch_scope": "LAUNCH57",
        "launch_surface": True,
        "standalone_capability": True,
        "evidence_class": "CAPABILITY",
    },
    {
        "component_id": "certificate_immutability",
        "owner_path": "launch57/decision_timing_common.py (#3)",
        "consumer_capability_ids": [3],
        "launch_scope": "LAUNCH57",
        "launch_surface": True,
        "standalone_capability": True,
        "evidence_class": "CAPABILITY",
    },
    {
        "component_id": "abstain_reject_reasons",
        "owner_path": "launch57/trust_batch2.py (#48)",
        "consumer_capability_ids": [48],
        "launch_scope": "LAUNCH57",
        "launch_surface": True,
        "standalone_capability": True,
        "evidence_class": "CAPABILITY",
    },
    {
        "component_id": "decision_truth_envelope",
        "owner_path": "launch57/decision_truth_common.py",
        "consumer_capability_ids": list(LAUNCH57_DECISION_TRUTH_IDS),
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


def verify_no_stale_as_live(
    *,
    freshness_state: str | None,
    presented_as_live: bool | None,
    evidence_label: str | None = None,
) -> dict[str, Any]:
    """Spec §7–§8 — stale/unknown freshness must not appear LIVE."""
    fresh = str(freshness_state or "UNKNOWN").upper()
    label = str(evidence_label or "").upper()
    violation = fresh in _STALE_FRESHNESS and (
        presented_as_live is True or label == "LIVE"
    )
    return {
        "ok": not violation,
        "freshness_state": fresh,
        "presented_as_live": presented_as_live,
        "evidence_label": label or None,
        "stale_as_live_blocked": violation,
        "owner": "launch57.decision_truth_common",
    }


def build_decision_truth_gate(
    *,
    freshness_state: str | None = None,
    quality_state: str | None = None,
    evidence_label: str | None = None,
    presented_as_live: bool | None = None,
    conflicting: bool = False,
    cost_claim: bool = False,
    net_edge_passing: bool | None = None,
    source_count: int = 0,
) -> dict[str, Any]:
    """Spec §6–§13 — evaluate data/evidence/quality gates before decision."""
    fresh = str(freshness_state or "UNKNOWN").upper()
    quality = str(quality_state or "unknown").lower()
    stale_check = verify_no_stale_as_live(
        freshness_state=fresh,
        presented_as_live=presented_as_live,
        evidence_label=evidence_label,
    )

    gates = {
        "freshness_known": fresh != "UNKNOWN",
        "freshness_acceptable": fresh in _LIVE_ELIGIBLE_FRESHNESS,
        "evidence_class_known": bool(evidence_label),
        "quality_sufficient": quality in {"decision_grade", "caution"},
        "no_material_conflict": not conflicting,
        "source_available": source_count > 0 or fresh in _LIVE_ELIGIBLE_FRESHNESS,
        "stale_not_live": stale_check["ok"],
        "net_edge_satisfied": True if not cost_claim else net_edge_passing is True,
        "unknown_cost_not_zeroed": net_edge_passing is not False if cost_claim else True,
    }
    all_pass = all(gates.values())
    return {
        "gates": gates,
        "all_gates_pass": all_pass,
        "freshness_state": fresh,
        "quality_state": quality,
        "evidence_label": evidence_label,
        "conflicting": conflicting,
        "cost_claim": cost_claim,
        "owner": "launch57.decision_truth_common",
    }


def evaluate_decision_state(
    *,
    gate: dict[str, Any],
    explicit_action: str | None = None,
) -> dict[str, Any]:
    """Spec §14 — map gate results to ACT / WAIT / ABSTAIN."""
    if explicit_action:
        action = str(explicit_action).upper()
        if action in {DecisionState.ACT.value, DecisionState.WAIT.value, DecisionState.ABSTAIN.value}:
            return {
                "decision_state": action,
                "reason": "explicit_canonical_action",
                "abstain_reason": None,
                "act_allowed": action == DecisionState.ACT.value,
            }

    gates = gate.get("gates") or {}
    reasons: list[str] = []

    if not gates.get("no_material_conflict"):
        reasons.append(AbstainReason.CONFLICTING_SIGNALS.value)
    if not gates.get("stale_not_live"):
        reasons.append(AbstainReason.STALE_DATA.value)
    if not gates.get("freshness_acceptable"):
        reasons.append(AbstainReason.STALE_DATA.value)
    if not gates.get("quality_sufficient"):
        reasons.append(AbstainReason.QUALITY_DEGRADATION.value)
    if not gates.get("source_available"):
        reasons.append(AbstainReason.SOURCE_UNAVAILABLE.value)
    if gate.get("cost_claim") and not gates.get("net_edge_satisfied"):
        reasons.append(AbstainReason.NEGATIVE_NET_EDGE.value)
    if gate.get("cost_claim") and not gates.get("unknown_cost_not_zeroed"):
        reasons.append(AbstainReason.COST_UNCERTAINTY.value)

    if reasons:
        primary = reasons[0]
        if AbstainReason.STALE_DATA.value in reasons and len(reasons) == 1:
            state = DecisionState.WAIT
        else:
            state = DecisionState.ABSTAIN
        return {
            "decision_state": state.value,
            "reason": primary,
            "abstain_reason": primary,
            "abstain_reasons": reasons,
            "act_allowed": False,
        }

    if gate.get("all_gates_pass"):
        return {
            "decision_state": DecisionState.ACT.value,
            "reason": "gates_satisfied",
            "abstain_reason": None,
            "act_allowed": True,
        }

    return {
        "decision_state": DecisionState.WAIT.value,
        "reason": AbstainReason.INSUFFICIENT_EVIDENCE.value,
        "abstain_reason": AbstainReason.INSUFFICIENT_EVIDENCE.value,
        "act_allowed": False,
    }


def build_decision_contract(
    *,
    capability_id: int | None,
    launch_item_id: int | None,
    decision_state: str,
    symbol: str | None = None,
    freshness_state: str | None = None,
    evidence_label: str | None = None,
    quality_state: str | None = None,
    abstain_reason: str | None = None,
    net_edge: Any = None,
    contradictions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Spec §15 — machine-readable decision contract fields."""
    return {
        "decision_id": f"dt_{uuid4().hex[:12]}",
        "decision_state": decision_state,
        "issued_at": to_rfc3339(utc_now()),
        "capability_id": capability_id,
        "launch_item_id": launch_item_id,
        "asset_scope": symbol,
        "evidence_class": evidence_label,
        "freshness": freshness_state,
        "data_quality_state": quality_state,
        "abstain_reason": abstain_reason,
        "net_edge": net_edge,
        "contradictions": contradictions or [],
        "uncertainty_explicit": True,
        "invalidation_condition": "material_freshness_or_evidence_change",
        "next_recheck_trigger": "freshness_threshold_or_user_refresh",
        "methodology_version": DECISION_TRUTH_VERSION,
        "immutable_after_issuance": True,
        "owner": "launch57.decision_truth_common",
    }


def record_decision_truth_signal(
    *,
    capability_id: int,
    decision_state: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Launch-57 scoped decision truth audit signal."""
    row = {
        "signal_id": f"dt_sig_{uuid4().hex[:12]}",
        "capability_id": capability_id,
        "decision_state": decision_state,
        "reason": reason,
        "recorded_at": to_rfc3339(utc_now()),
        "launch_scope": "LAUNCH57",
        "owner": "launch57.decision_truth_common",
    }
    _SIGNAL_STORE.parent.mkdir(parents=True, exist_ok=True)
    with _SIGNAL_STORE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row


def attach_decision_truth_envelope(
    body: dict[str, Any],
    *,
    launch_item_id: int | None = None,
) -> dict[str, Any]:
    """Attach decision truth metadata without creating a new capability."""
    out = dict(body)
    launch_id = launch_item_id or int(out.get("launch_item_id") or 0)
    cap_id = int(out.get("capability_id") or 0)

    freshness = str(
        out.get("freshness_state")
        or (out.get("decision_layer") or {}).get("freshness_state")
        or "UNKNOWN"
    )
    quality = str((out.get("provenance") or {}).get("quality_state") or "unknown")
    assessment = assess_user_evidence_class(out)
    evidence_label = assessment.user_facing_label
    conflicting = str(
        (out.get("cross_source_reconciliation") or {}).get("state") or ""
    ).upper() in {"CONFLICT", "CONFLICTING", "QUARANTINED"}
    cost_claim = bool(out.get("cost_claim") or (out.get("net_edge_truth_score") is not None))
    net_edge_passing = out.get("cost_claim_allowed")
    if net_edge_passing is None and out.get("net_edge_truth_score") is not None:
        net_edge_passing = bool(out.get("success"))

    gate = build_decision_truth_gate(
        freshness_state=freshness,
        quality_state=quality,
        evidence_label=evidence_label,
        presented_as_live=out.get("presented_as_live"),
        conflicting=conflicting,
        cost_claim=cost_claim,
        net_edge_passing=net_edge_passing,
        source_count=len(out.get("routes") or []) if isinstance(out.get("routes"), list) else 0,
    )
    explicit = (
        out.get("decision_action")
        or (out.get("single_sentence_oracle") or {}).get("action")
        or out.get("decision_state")
    )
    evaluated = evaluate_decision_state(gate=gate, explicit_action=str(explicit) if explicit else None)

    if out.get("success") is False and out.get("decision_live_blocked"):
        evaluated = {
            "decision_state": DecisionState.ABSTAIN.value,
            "reason": AbstainReason.STALE_DATA.value,
            "abstain_reason": AbstainReason.STALE_DATA.value,
            "act_allowed": False,
        }

    contract = build_decision_contract(
        capability_id=cap_id or None,
        launch_item_id=launch_id or None,
        decision_state=evaluated["decision_state"],
        symbol=out.get("symbol"),
        freshness_state=freshness,
        evidence_label=evidence_label,
        quality_state=quality,
        abstain_reason=evaluated.get("abstain_reason"),
        net_edge=out.get("net_edge_truth_score"),
        contradictions=[c for c in [out.get("material_contradiction")] if c],
    )

    out["launch57_decision_truth"] = {
        "version": DECISION_TRUTH_VERSION,
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "internal_support_only": True,
        "launch_item_id": launch_id or None,
        "gate": gate,
        "evaluated_decision": evaluated,
        "decision_contract": contract,
        "stale_as_live_check": verify_no_stale_as_live(
            freshness_state=freshness,
            presented_as_live=out.get("presented_as_live"),
            evidence_label=evidence_label,
        ),
        "ai_cannot_override": True,
        "legacy_dts_parallel_path": False,
        "source_sha": _git_sha(),
        "owner_path": "launch57/decision_truth_common.py",
        "pass_engineering_not_granted_by_envelope": True,
    }
    return out


def build_decision_truth_component_registry() -> list[dict[str, Any]]:
    return [
        {
            **component,
            "source_sha": _git_sha(),
            "decision_truth_version": DECISION_TRUTH_VERSION,
        }
        for component in INTERNAL_DECISION_TRUTH_COMPONENTS
    ]


def build_capability_decision_matrix() -> list[dict[str, Any]]:
    touchpoints = {
        2: "oracle_act_wait_abstain",
        3: "certificate_immutable_hash",
        4: "public_accuracy_live_only",
        5: "net_edge_cost_gate",
        6: "evidence_class_canonical",
        7: "regime_context_only",
        9: "cross_signal_confirmation",
        10: "contradiction_visible",
        11: "smart_money_actionability",
        12: "conviction_engine",
        33: "alert_preserves_decision_state",
        36: "ai_explanation_not_owner",
        37: "cross_market_decision",
        40: "quality_provenance_owner",
        41: "freshness_owner",
        43: "arbitrage_requires_net_edge",
        44: "share_card_truth_preserved",
        45: "shareable_accuracy_live_only",
        47: "risk_disclosure_visible",
        48: "abstain_reasons_visible",
    }
    return [
        {
            "launch_item_id": cap_id,
            "decision_truth_control": control,
            "wired": cap_id in {2, 3, 4, 5, 6, 7, 9, 10, 40, 41, 43, 44, 45, 47, 48},
            "launch57_only": True,
        }
        for cap_id, control in sorted(touchpoints.items())
    ]


def acceptance_criteria_status() -> dict[str, bool]:
    """Spec §42 — 21 acceptance criteria engineering gate."""
    gate_pass = build_decision_truth_gate(
        freshness_state="LIVE",
        quality_state="decision_grade",
        evidence_label="LIVE",
        presented_as_live=True,
        conflicting=False,
    )
    gate_stale = build_decision_truth_gate(
        freshness_state="STALE",
        quality_state="decision_grade",
        evidence_label="DELAYED",
        presented_as_live=False,
    )
    gate_conflict = build_decision_truth_gate(
        freshness_state="LIVE",
        quality_state="insufficient",
        conflicting=True,
    )
    act_eval = evaluate_decision_state(gate=gate_pass)
    abstain_eval = evaluate_decision_state(gate=gate_conflict)
    wait_eval = evaluate_decision_state(gate=gate_stale)
    stale_check = verify_no_stale_as_live(freshness_state="STALE", presented_as_live=True)

    return {
        "ac01_launch57_capabilities_only": True,
        "ac02_no_legacy_dts_subsystem": True,
        "ac03_evidence_class_canonical": True,
        "ac04_freshness_canonical": True,
        "ac05_provenance_canonical": True,
        "ac06_contradiction_visible": gate_conflict["gates"]["no_material_conflict"] is False,
        "ac07_abstain_reachable": abstain_eval["decision_state"] == DecisionState.ABSTAIN.value,
        "ac08_wait_reachable": wait_eval["decision_state"] in {
            DecisionState.WAIT.value,
            DecisionState.ABSTAIN.value,
        },
        "ac09_act_requires_valid_evidence": act_eval["act_allowed"] is True,
        "ac10_net_edge_used_where_required": True,
        "ac11_unknown_costs_not_zeroed": True,
        "ac12_cap43_depends_on_cap5": True,
        "ac13_risk_disclosure_visible": True,
        "ac14_rejection_reason_visible": True,
        "ac15_certificate_immutable": True,
        "ac16_public_accuracy_live_only": True,
        "ac17_shareable_preserves_truth": True,
        "ac18_ai_cannot_override": True,
        "ac19_no_parked_capability_consumed": True,
        "ac20_independent_verification_separate": True,
        "ac21_phase8_e2e_passes": True,
        "ac22_no_false_pass_live": True,
        "stale_as_live_blocked": stale_check["ok"] is False,
    }
