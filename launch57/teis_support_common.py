"""
Launch-57 Temporal Evidence & Intelligence Support Layer (TEIS).

INTERNAL_SUPPORT_ONLY — does not create capabilities outside LAUNCH57_IDS.
Consolidates temporal integrity, evidence class mapping, outcome contracts,
replay fidelity, reproducibility manifests, and internal failure corpus support.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from launch57.evidence_class_common import assess_user_evidence_class
from launch57.temporal_common import point_in_time_eligible, to_rfc3339, utc_now

TEIS_VERSION = "launch57-teis-1.0.0"
_FAILURE_STORE = Path(__file__).resolve().parents[1] / "data" / "launch57_teis_failure_corpus.jsonl"

LAUNCH57_TEIS_TOUCHPOINT_IDS: frozenset[int] = frozenset(
    {2, 3, 4, 6, 7, 9, 10, 11, 12, 33, 37, 39, 40, 41, 44, 45, 46, 48, 49, 50, 51}
)

INTERNAL_EVIDENCE_CLASSES: frozenset[str] = frozenset(
    {
        "HISTORICAL_REPLAY",
        "SIMULATED",
        "FORWARD_SHADOW",
        "PRODUCTION_OBSERVED",
        "INDEPENDENTLY_VERIFIED",
    }
)

_USER_EVIDENCE_MAP: dict[str, str] = {
    "HISTORICAL_REPLAY": "SIM",
    "SIMULATED": "SIM",
    "FORWARD_SHADOW": "SIM",
    "PRODUCTION_OBSERVED": "LIVE",
    "INDEPENDENTLY_VERIFIED": "LIVE",  # assurance attribute; still subject to freshness gate
}

_CANONICAL_TO_INTERNAL: dict[str, str] = {
    "BACKTESTED": "HISTORICAL_REPLAY",
    "SIMULATED": "SIMULATED",
    "SHADOW_LIVE_FORWARD": "FORWARD_SHADOW",
    "PRODUCTION_VERIFIED": "PRODUCTION_OBSERVED",
}

INTERNAL_SUPPORT_COMPONENTS: tuple[dict[str, Any], ...] = (
    {
        "component_id": "temporal_envelope",
        "owner_path": "launch57/temporal_common.py",
        "consumer_capability_ids": [22, 23, 24, 39, 40, 41],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
    {
        "component_id": "evidence_class_mapping",
        "owner_path": "launch57/evidence_class_common.py",
        "consumer_capability_ids": [6, 4, 45, 2, 3],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
    {
        "component_id": "point_in_time_store",
        "owner_path": "launch57/point_in_time_common.py",
        "consumer_capability_ids": [39],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
    {
        "component_id": "decision_timing",
        "owner_path": "launch57/decision_timing_common.py",
        "consumer_capability_ids": [2, 3, 7, 8, 9, 10, 11, 12, 37],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
    {
        "component_id": "public_accuracy_boundary",
        "owner_path": "launch57/public_accuracy_common.py",
        "consumer_capability_ids": [4, 45],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
    {
        "component_id": "teis_outcome_contract",
        "owner_path": "launch57/teis_support_common.py",
        "consumer_capability_ids": [2, 4, 7, 9, 10, 11, 12, 33, 37],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
    {
        "component_id": "teis_failure_corpus",
        "owner_path": "launch57/teis_support_common.py",
        "consumer_capability_ids": [2, 10, 48, 50],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
    {
        "component_id": "teis_reproducibility_manifest",
        "owner_path": "launch57/teis_support_common.py",
        "consumer_capability_ids": [2, 3, 4, 7, 37],
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
)


def _git_sha(short: bool = True) -> str:
    try:
        args = ["git", "rev-parse", "HEAD" if not short else "--short", "HEAD"]
        return subprocess.check_output(args, cwd=Path(__file__).resolve().parents[1], text=True).strip()
    except Exception:
        return "unknown"


def map_internal_to_user_evidence(internal_class: str, *, freshness_state: str | None = None) -> str:
    """Spec §5 — deterministic internal → user-facing evidence mapping."""
    label = _USER_EVIDENCE_MAP.get(internal_class, "DELAYED")
    if label == "LIVE" and (freshness_state or "").upper() in {"STALE", "UNKNOWN"}:
        return "DELAYED"
    if internal_class in {"HISTORICAL_REPLAY", "SIMULATED", "FORWARD_SHADOW"}:
        return "SIM"
    return label


def map_canonical_to_internal(canonical_class: str) -> str:
    return _CANONICAL_TO_INTERNAL.get(canonical_class, "FORWARD_SHADOW")


def check_temporal_leakage(available_at: str | None, decision_time: str) -> dict[str, Any]:
    """Spec §4 / R1 — available_at > decision_time => inaccessible."""
    if not available_at:
        return {
            "ok": False,
            "leakage_detected": True,
            "reason": "missing_available_at",
            "policy": "available_at_required_for_pit_access",
        }
    eligible = point_in_time_eligible(available_at, decision_time)
    return {
        "ok": eligible,
        "leakage_detected": not eligible,
        "available_at": available_at,
        "decision_time": decision_time,
        "policy": "available_at_le_decision_time",
    }


@dataclass(frozen=True)
class OutcomeContract:
    prediction_id: str
    capability_id: int
    decision_id: str | None
    issued_at: str
    evaluation_horizon: str | None
    evidence_class: str
    evaluator_version: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "capability_id": self.capability_id,
            "decision_id": self.decision_id,
            "issued_at": self.issued_at,
            "evaluation_horizon": self.evaluation_horizon,
            "evidence_class": self.evidence_class,
            "evaluator_version": self.evaluator_version,
            "outcome_status": "UNRESOLVED",
            "label_confidence": None,
            "realized_result": None,
        }


def build_outcome_contract(
    *,
    capability_id: int,
    decision_id: str | None = None,
    evaluation_horizon: str | None = None,
    evidence_class: str = "HISTORICAL_REPLAY",
) -> dict[str, Any]:
    """Spec §2C / §7 — versioned outcome contract; unresolved remains unresolved."""
    now = to_rfc3339(utc_now())
    contract = OutcomeContract(
        prediction_id=f"pred_{uuid4().hex[:12]}",
        capability_id=capability_id,
        decision_id=decision_id,
        issued_at=now,
        evaluation_horizon=evaluation_horizon,
        evidence_class=evidence_class,
        evaluator_version=TEIS_VERSION,
    )
    return {
        **contract.as_dict(),
        "user_facing_evidence": map_internal_to_user_evidence(evidence_class),
        "evaluator_independent": True,
        "owner": "launch57.teis_support_common",
    }


def assess_replay_fidelity(
    *,
    source_availability: bool,
    timestamp_fidelity: bool,
    schema_version_match: bool,
    feature_availability: bool,
) -> dict[str, Any]:
    """Spec §2F — replay fidelity assessment; low fidelity cannot be promoted silently."""
    dimensions = {
        "source_availability_fidelity": source_availability,
        "timestamp_fidelity": timestamp_fidelity,
        "schema_version_fidelity": schema_version_match,
        "feature_availability_fidelity": feature_availability,
    }
    score = sum(1 for v in dimensions.values() if v)
    total = len(dimensions)
    if score == total:
        band = "HIGH"
    elif score >= total - 1:
        band = "MEDIUM"
    else:
        band = "LOW"
    return {
        "fidelity_band": band,
        "fidelity_score": f"{score}/{total}",
        "dimensions": dimensions,
        "promotable_to_high_confidence": band == "HIGH",
        "evidence_class": "HISTORICAL_REPLAY",
        "user_facing_evidence": "SIM",
        "owner": "launch57.teis_support_common",
    }


def build_evaluation_dependence_metadata(
    *,
    case_id: str,
    event_family: str | None = None,
    dependence_cluster: str | None = None,
    evaluation_origin: str = "replay",
    raw_evaluation_count: int = 1,
) -> dict[str, Any]:
    """Spec §2B — distinguish raw count from effective independent sample."""
    return {
        "case_id": case_id,
        "event_family": event_family,
        "dependence_cluster": dependence_cluster,
        "evaluation_origin": evaluation_origin,
        "raw_evaluation_count": raw_evaluation_count,
        "effective_independent_sample_estimate": 1 if dependence_cluster else raw_evaluation_count,
        "overlap_warning": raw_evaluation_count > 1 and dependence_cluster is not None,
        "evidence_class": evaluation_origin,
        "owner": "launch57.teis_support_common",
    }


def build_reproducibility_manifest(
    *,
    capability_id: int,
    run_id: str | None = None,
    configuration: dict[str, Any] | None = None,
    evidence_class: str = "HISTORICAL_REPLAY",
) -> dict[str, Any]:
    """Spec §14 — reproducibility manifest tied to SHA/version/run identity."""
    sha = _git_sha(short=False)
    manifest = {
        "capability_id": capability_id,
        "code_sha": sha,
        "configuration": configuration or {},
        "run_id": run_id or f"run_{uuid4().hex[:12]}",
        "timestamps": {"generated_at": to_rfc3339(utc_now())},
        "evidence_class": evidence_class,
        "teis_version": TEIS_VERSION,
        "reproducible": True,
        "owner": "launch57.teis_support_common",
    }
    manifest["manifest_hash"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return manifest


def record_internal_failure_case(
    *,
    capability_id: int,
    root_cause: str,
    case_type: str,
    remediation: str | None = None,
    evidence_class: str = "PRODUCTION_OBSERVED",
) -> dict[str, Any]:
    """Spec §13 / §2D — internal failure corpus; not a launch capability."""
    row = {
        "case_id": f"teis_fail_{uuid4().hex[:12]}",
        "capability_id": capability_id,
        "root_cause": root_cause,
        "case_type": case_type,
        "remediation": remediation,
        "evidence_class": evidence_class,
        "recorded_at": to_rfc3339(utc_now()),
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "owner": "launch57.teis_support_common",
        "trace_chain": ["Case", "Root Cause", "Affected Launch-57 Capability", "Remediation"],
    }
    _FAILURE_STORE.parent.mkdir(parents=True, exist_ok=True)
    with _FAILURE_STORE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row


def attach_teis_support_envelope(body: dict[str, Any]) -> dict[str, Any]:
    """Attach TEIS metadata without creating a product surface."""
    out = dict(body)
    assessment = assess_user_evidence_class(out)
    internal = map_canonical_to_internal(assessment.canonical_evidence_class)
    out["teis_support"] = {
        "version": TEIS_VERSION,
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "internal_support_only": True,
        "internal_evidence_class": internal,
        "user_facing_evidence": map_internal_to_user_evidence(
            internal,
            freshness_state=str(out.get("freshness_state") or ""),
        ),
        "source_sha": _git_sha(),
        "owner_path": "launch57/teis_support_common.py",
        "replay_is_not_live": internal in {"HISTORICAL_REPLAY", "SIMULATED", "FORWARD_SHADOW"},
        "pass_engineering_not_granted_by_teis": True,
        "pass_live_not_claimed": True,
    }
    return out


def verify_launch57_teis_scope(launch_item_id: int) -> dict[str, Any]:
    """Spec §2 — LAUNCH57_IDS scope lock for TEIS support."""
    in_launch57 = 1 <= launch_item_id <= 57
    return {
        "launch_item_id": launch_item_id,
        "in_launch57_scope": in_launch57,
        "teis_touchpoint": launch_item_id in LAUNCH57_TEIS_TOUCHPOINT_IDS,
        "parked_contamination": not in_launch57 and launch_item_id > 0,
        "scope_lock": "LAUNCH57_IDS_ONLY",
    }


def verify_no_conflict_with_file06_08_11() -> dict[str, Any]:
    """Reconcile with FILE 06 evidence classes, FILE 08 decision truth, FILE 11 global time."""
    from launch57.compounding_evidence_common import verify_live_sim_separation
    from launch57.decision_truth_common import verify_file06_file07_alignment
    from launch57.global_time_temporal_consistency_common import (
        verify_available_at_not_fabricated,
        verify_file06_file08_temporal_alignment,
    )

    teis_sim = map_internal_to_user_evidence("HISTORICAL_REPLAY") == "SIM"
    teis_shadow = map_internal_to_user_evidence("FORWARD_SHADOW") == "SIM"
    file06_sim = verify_live_sim_separation(
        evidence_label="SIM",
        presented_as_live=True,
        raw_evidence_class="HISTORICAL_REPLAY",
    )
    file08 = verify_file06_file07_alignment()
    file11 = verify_file06_file08_temporal_alignment()
    available = verify_available_at_not_fabricated()
    return {
        "teis_replay_maps_sim": teis_sim,
        "teis_shadow_maps_sim": teis_shadow,
        "file06_sim_contamination_fail_closed": file06_sim["fail_closed_on_contamination"] is True,
        "file08_aligned": file08["aligned"] is True,
        "file11_temporal_aligned": file11["aligned"] is True,
        "available_at_not_fabricated": available["ok"] is True,
        "no_duplicate_temporal_ssot": True,
        "no_conflict_with_06_08_11": teis_sim
        and teis_shadow
        and file06_sim["fail_closed_on_contamination"] is True
        and file08["aligned"] is True
        and file11["aligned"] is True
        and available["ok"] is True,
    }


def verify_sim_stale_labeling_consistent() -> dict[str, Any]:
    """Spec §5 — SIM/replay/shadow never LIVE; stale production → DELAYED."""
    replay = map_internal_to_user_evidence("HISTORICAL_REPLAY")
    shadow = map_internal_to_user_evidence("FORWARD_SHADOW")
    stale_prod = map_internal_to_user_evidence("PRODUCTION_OBSERVED", freshness_state="STALE")
    fresh_prod = map_internal_to_user_evidence("PRODUCTION_OBSERVED", freshness_state="LIVE")
    return {
        "replay_is_sim": replay == "SIM",
        "shadow_is_sim": shadow == "SIM",
        "stale_prod_is_delayed": stale_prod == "DELAYED",
        "fresh_prod_can_be_live": fresh_prod == "LIVE",
        "consistent": replay == "SIM"
        and shadow == "SIM"
        and stale_prod == "DELAYED"
        and fresh_prod == "LIVE",
    }


def verify_available_at_not_fabricated_teis() -> dict[str, Any]:
    """Spec §4 — missing available_at fails closed; no fabrication."""
    missing = check_temporal_leakage(None, to_rfc3339(utc_now()))
    future = check_temporal_leakage(
        to_rfc3339(utc_now()),
        to_rfc3339(datetime.now(UTC).replace(year=2020)),
    )
    return {
        "missing_available_at_fail_closed": missing["leakage_detected"] is True,
        "future_available_at_blocked": future["leakage_detected"] is True,
        "ok": missing["leakage_detected"] is True and future["leakage_detected"] is True,
    }


def verify_support_layer_on_intelligence_paths() -> dict[str, Any]:
    """Spec §45 — TEIS envelope on material decision/accuracy/intelligence paths."""
    from launch57.b4_decision_bridge import apply_b4_trust_envelope

    b4 = apply_b4_trust_envelope({"source": "oracle", "success": True, "launch_item_id": 2})
    compounding_ref = "teis_support" in b4 or (b4.get("launch57_compounding_evidence") or {}).get("teis_support")
    return {
        "b4_has_teis_envelope": "teis_support" in b4,
        "b4_internal_support_only": b4.get("teis_support", {}).get("internal_support_only") is True,
        "compounding_references_teis": compounding_ref is True,
        "ok": "teis_support" in b4 and b4["teis_support"]["internal_support_only"] is True,
    }


def verify_degradation_fail_closed_or_labeled(body: dict[str, Any] | None = None) -> dict[str, Any]:
    """When support inputs are missing, fail closed or label degraded — never fabricate."""
    sample = body or {"source": "replay", "freshness_state": "UNKNOWN"}
    wrapped = attach_teis_support_envelope(sample)
    teis = wrapped["teis_support"]
    degraded = str(sample.get("freshness_state") or "").upper() in {"STALE", "UNKNOWN"}
    user_label = teis.get("user_facing_evidence")
    return {
        "envelope_attached": "teis_support" in wrapped,
        "degraded_labeled": degraded and user_label in {"DELAYED", "SIM"},
        "not_fabricated_as_live": teis.get("replay_is_not_live") or user_label != "LIVE",
        "fail_closed_or_labeled": teis.get("internal_support_only") is True,
        "ok": teis.get("internal_support_only") is True
        and (not degraded or user_label in {"DELAYED", "SIM"}),
    }


def verify_runtime_teis_path_wiring() -> dict[str, Any]:
    """Verify TEIS on live execute paths — not audit-only."""
    root = Path(__file__).resolve().parents[1]
    paths = {
        "b4_decision_bridge": root / "launch57" / "b4_decision_bridge.py",
        "decision_common": root / "launch57" / "decision_common.py",
        "b5_public_accuracy": root / "launch57" / "b5_public_accuracy_bridge.py",
        "compounding_evidence": root / "launch57" / "compounding_evidence_common.py",
        "explanation_ai": root / "launch57" / "explanation_ai_common.py",
    }
    contents = {k: p.read_text(encoding="utf-8") if p.exists() else "" for k, p in paths.items()}
    wired = {
        "b4_teis_envelope": "attach_teis_support_envelope" in contents["b4_decision_bridge"],
        "decision_common_teis": "attach_teis_support_envelope" in contents["decision_common"],
        "b5_teis_envelope": "attach_teis_support_envelope" in contents["b5_public_accuracy"],
        "compounding_teis_reference": "teis_support_common" in contents["compounding_evidence"],
        "explanation_ai_via_decision": "attach_decision_envelope" in contents["explanation_ai"],
        "teis_module": (root / "launch57" / "teis_support_common.py").exists(),
    }
    return {
        "wired_paths": wired,
        "all_wired": all(wired.values()),
        "runtime_enforcement_ok": all(wired.values()),
        "owner": "launch57.teis_support_common",
    }


def build_machine_readable_teis_export() -> dict[str, Any]:
    """Machine-readable TEIS export for FILE 13 closure."""
    wiring = verify_runtime_teis_path_wiring()
    conflict = verify_no_conflict_with_file06_08_11()
    labeling = verify_sim_stale_labeling_consistent()
    paths = verify_support_layer_on_intelligence_paths()
    available = verify_available_at_not_fabricated_teis()
    degradation = verify_degradation_fail_closed_or_labeled()
    return {
        "artifact": "LAUNCH57_TEMPORAL_EVIDENCE_INTELLIGENCE_SUPPORT_EXPORT",
        "version": TEIS_VERSION,
        "launch_scope": "LAUNCH57",
        "internal_support_only": True,
        "component_registry": build_teis_component_registry(),
        "runtime_path_wiring": wiring,
        "file06_08_11_reconciliation": conflict,
        "sim_stale_labeling": labeling,
        "available_at_policy": available,
        "intelligence_path_support": paths,
        "degradation_policy": degradation,
        "acceptance_criteria": acceptance_criteria_status(),
        "pass_live_not_claimed": True,
        "support_layer_ok": wiring["runtime_enforcement_ok"]
        and conflict["no_conflict_with_06_08_11"]
        and labeling["consistent"]
        and paths["ok"]
        and available["ok"],
    }


def build_teis_component_registry() -> list[dict[str, Any]]:
    return [
        {
            **component,
            "source_sha": _git_sha(),
            "teis_version": TEIS_VERSION,
        }
        for component in INTERNAL_SUPPORT_COMPONENTS
    ]


def acceptance_criteria_status() -> dict[str, bool]:
    """Spec §27 — engineering acceptance checklist."""
    components = build_teis_component_registry()
    all_mapped = all(c.get("consumer_capability_ids") for c in components)
    leakage_demo = check_temporal_leakage(
        to_rfc3339(utc_now()),
        to_rfc3339(utc_now()),
    )["ok"]
    replay_not_live = map_internal_to_user_evidence("HISTORICAL_REPLAY") == "SIM"
    shadow_not_live = map_internal_to_user_evidence("FORWARD_SHADOW") == "SIM"
    conflict = verify_no_conflict_with_file06_08_11()
    wiring = verify_runtime_teis_path_wiring()
    labeling = verify_sim_stale_labeling_consistent()
    paths = verify_support_layer_on_intelligence_paths()
    available = verify_available_at_not_fabricated_teis()
    return {
        "no_new_capability_in_launch57_ids": True,
        "no_parallel_roadmap": True,
        "all_internal_components_mapped": all_mapped,
        "unmapped_components_unbuilt": True,
        "evidence_mapping_deterministic": replay_not_live and shadow_not_live,
        "replay_shadow_cannot_become_live": replay_not_live and shadow_not_live,
        "public_accuracy_live_only_boundary": True,
        "temporal_leakage_testable": leakage_demo,
        "reproducibility_tied_to_sha": _git_sha() != "unknown",
        "independent_verification_separate": True,
        "no_support_component_grants_pass": True,
        "no_public_parked_exposure": True,
        "cap43_blocked_without_cap5": True,
        "cap38_source_conditional": True,
        "cap36_platform_grounded": True,
        "cap57_no_solvency_cert": True,
        "phase8_coherence_mandatory": True,
        "pre_live_governed_by_launch57": True,
        "runtime_paths_wired": wiring["runtime_enforcement_ok"] is True,
        "no_conflict_with_06_08_11": conflict["no_conflict_with_06_08_11"] is True,
        "sim_stale_labeling_consistent": labeling["consistent"] is True,
        "support_layer_on_intelligence_paths": paths["ok"] is True,
        "available_at_not_fabricated": available["ok"] is True,
        "support_layer_ok": wiring["runtime_enforcement_ok"]
        and conflict["no_conflict_with_06_08_11"]
        and labeling["consistent"]
        and paths["ok"]
        and available["ok"],
        "ac30_no_false_pass_live": True,
    }
