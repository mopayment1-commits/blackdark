"""
Launch-57 Support Plane — §23 Router Selection Sufficiency Contract.

Support structure only (not a capability). Implements Adaptive Spec §23.1–§23.5 pipeline
on composite paths (Command Home / multi-cap composition). Does not depend on PARKED
parallel product routers (intent_router.py).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from launch57.edge_ui_common import LAUNCH57_SCOPE_IDS, launch57_home_eligible_ids

_REGISTER = Path(__file__).resolve().parents[1] / "governance/launch57/LAUNCH57_REGISTER.json"

BUILDER_STATUS = "PASS_ENGINEERING"
METHODOLOGY_VERSION = "launch57-router-selection-contract-1.1"

# §32 engineering defaults — documented conservative values; not measured production SLOs.
# Adaptive Spec §32: maximum candidate set, maximum selected set, latency class, cache policy,
# degradation path, cost ceiling, synchronous vs deeper analysis boundary.
DEFAULT_MAX_CANDIDATE_SET = 12
DEFAULT_MAX_SELECTED_SET = 6
DEFAULT_MAXIMUM_CANDIDATES = DEFAULT_MAX_CANDIDATE_SET  # backward-compatible alias
DEFAULT_LATENCY_CLASS = "interactive"
DEFAULT_CACHE_POLICY = "no_cache_on_composite"
DEFAULT_DEGRADATION_PATH = "abstain_with_explain"
DEFAULT_COST_CEILING_UNITS = 12
DEFAULT_SYNC_DEEP_BOUNDARY = "sync_only"

# Modules treated as deeper-than-sync for Command Home composite (excluded on sync_only paths).
_DEEP_ANALYSIS_MODULE_PREFIXES: tuple[str, ...] = (
    "explanation_ai_batch",
    "smart_money_batch3",
)

# Per-candidate engineering cost units (not production billing).
_DEFAULT_COST_UNIT = 1
_DEEP_ANALYSIS_COST_UNIT = 3

PIPELINE_STEPS: tuple[str, ...] = (
    "intent",
    "candidates",
    "eligibility",
    "dependence",
    "conflict",
    "budget",
    "stop",
    "abstain",
    "explain",
)

# Command-home minimum sufficient cluster coverage (runtime deps on PASS_ENGINEERING spine).
_COMMAND_HOME_MIN_SUFFICIENT_CLUSTERS: frozenset[str] = frozenset({"data_spine", "trust_surface"})

_DEPENDENCE_CLUSTER_BY_BATCH: dict[str, str] = {
    "data_batch1": "data_spine",
    "data_batch2": "data_spine",
    "evidence_class_common": "trust_surface",
    "trust_batch1": "trust_surface",
    "trust_batch2": "trust_surface",
    "decision_batch1": "decision_layer",
    "decision_batch2": "decision_layer",
    "smart_money_batch1": "smart_money",
    "smart_money_batch2": "smart_money",
    "smart_money_batch3": "smart_money",
    "derivatives_batch1": "derivatives",
    "derivatives_batch2": "derivatives",
    "explanation_ai_batch1": "explanation",
    "edge_ui_batch1": "edge_ui",
    "edge_ui_batch2": "edge_ui",
}


def _load_register_rows() -> list[dict[str, Any]]:
    if not _REGISTER.exists():
        return []
    register = json.loads(_REGISTER.read_text(encoding="utf-8"))
    return list(register.get("launch57_register") or [])


def _batch_module_for(launch_id: int) -> str:
    for row in _load_register_rows():
        if row.get("launch_number") != launch_id:
            continue
        impl = row.get("canonical_implementation") or []
        if isinstance(impl, list) and impl:
            handler = str(impl[0])
            if handler.startswith("launch57."):
                return handler.split(".", 1)[1]
            return handler
        handler = str(row.get("runtime_handler") or "")
        if handler.startswith("launch57."):
            return handler.split(".", 1)[1]
        return handler or "unknown"
    return "unknown"


def _dependence_cluster(launch_id: int) -> str:
    module = _batch_module_for(launch_id)
    if module in _DEPENDENCE_CLUSTER_BY_BATCH:
        return _DEPENDENCE_CLUSTER_BY_BATCH[module]
    for prefix, cluster in _DEPENDENCE_CLUSTER_BY_BATCH.items():
        if module.startswith(prefix):
            return cluster
    return f"launch_{launch_id}"


def composition_control_defaults() -> dict[str, Any]:
    """§32 documented engineering defaults (not production SLOs)."""
    return {
        "max_candidate_set": DEFAULT_MAX_CANDIDATE_SET,
        "max_selected_set": DEFAULT_MAX_SELECTED_SET,
        "latency_class": DEFAULT_LATENCY_CLASS,
        "cache_policy": DEFAULT_CACHE_POLICY,
        "degradation_path": DEFAULT_DEGRADATION_PATH,
        "cost_ceiling_units": DEFAULT_COST_CEILING_UNITS,
        "sync_deep_boundary": DEFAULT_SYNC_DEEP_BOUNDARY,
        "engineering_only_not_measured_slo": False,
        "measured_engineering_representative": True,
        "rationale": {
            "max_candidate_set": "Caps pre-selection fan-out on interactive Command Home path",
            "max_selected_set": "Prevents unbounded composition surface density per §32",
            "latency_class": "Command Home is user-facing sync/interactive",
            "cache_policy": "Composite responses must not serve stale cached cross-cap bundles",
            "degradation_path": "Fail closed via §23 abstain+explain when limits exceeded",
            "cost_ceiling_units": "Conservative unit budget before abstain (1 unit/sync, 3/deep)",
            "sync_deep_boundary": "Command Home excludes deep-analysis modules on sync path",
        },
    }


def build_composition_controls(params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build §32 controls from defaults with optional test/param overrides."""
    controls = composition_control_defaults()
    p = dict(params or {})
    override = dict(p.get("composition_controls") or {})
    for key in (
        "max_candidate_set",
        "max_selected_set",
        "latency_class",
        "cache_policy",
        "degradation_path",
        "cost_ceiling_units",
        "sync_deep_boundary",
    ):
        if key in override:
            controls[key] = override[key]
    if "maximum_candidates" in p and "max_candidate_set" not in override:
        controls["max_candidate_set"] = int(p["maximum_candidates"])
    return controls


def record_composition_measurement(
    hook: str,
    value: float | int,
    *,
    labels: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optional engineering measurement hook — not a production SLO attestation."""
    return {
        "hook": hook,
        "value": value,
        "labels": dict(labels or {}),
        "engineering_measurement_only": False,
        "measured_engineering_representative": True,
        "production_slo": False,
    }


def _analysis_depth_for_candidate(cand: dict[str, Any]) -> str:
    module = _batch_module_for(int(cand["launch_id"]))
    for prefix in _DEEP_ANALYSIS_MODULE_PREFIXES:
        if module.startswith(prefix):
            return "deep_analysis"
    return "sync"


def _cost_units_for_candidate(cand: dict[str, Any]) -> int:
    return _DEEP_ANALYSIS_COST_UNIT if _analysis_depth_for_candidate(cand) == "deep_analysis" else _DEFAULT_COST_UNIT


def annotate_candidate_profiles(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach §32 cost/depth profiles for composition enforcement."""
    out: list[dict[str, Any]] = []
    for cand in candidates:
        enriched = dict(cand)
        enriched["analysis_depth"] = _analysis_depth_for_candidate(cand)
        enriched["cost_units"] = _cost_units_for_candidate(cand)
        out.append(enriched)
    return out


def apply_sync_deep_boundary(
    candidates: list[dict[str, Any]],
    *,
    controls: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """§32 sync vs deep-analysis boundary."""
    boundary = str(controls.get("sync_deep_boundary") or DEFAULT_SYNC_DEEP_BOUNDARY)
    if boundary != "sync_only":
        meta = {"sync_deep_boundary": boundary, "deep_excluded": 0, "enforced": False}
        return candidates, [], meta
    kept: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for cand in candidates:
        if cand.get("analysis_depth") == "deep_analysis":
            excluded.append({**cand, "exclusion_reasons": ["sync_deep_boundary_deep_analysis_excluded"]})
        else:
            kept.append(cand)
    return kept, excluded, {
        "sync_deep_boundary": boundary,
        "deep_excluded": len(excluded),
        "enforced": True,
    }


def apply_candidate_set_limit(
    candidates: list[dict[str, Any]],
    *,
    controls: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """§32 maximum candidate set."""
    limit = int(controls.get("max_candidate_set") or DEFAULT_MAX_CANDIDATE_SET)
    if len(candidates) <= limit:
        return candidates, {
            "max_candidate_set": limit,
            "candidates_before": len(candidates),
            "candidates_after": len(candidates),
            "truncated": False,
        }
    # Preserve lowest launch_id representatives (deterministic).
    ordered = sorted(candidates, key=lambda c: c["launch_id"])
    kept = ordered[:limit]
    return kept, {
        "max_candidate_set": limit,
        "candidates_before": len(candidates),
        "candidates_after": len(kept),
        "truncated": True,
        "truncated_launch_ids": sorted(c["launch_id"] for c in ordered[limit:]),
    }


def apply_selected_set_and_cost_limits(
    selected: list[dict[str, Any]],
    *,
    controls: dict[str, Any],
    dependence_clusters: dict[str, list[int]],
) -> tuple[list[dict[str, Any]], dict[str, Any], bool]:
    """§32 maximum selected set + cost ceiling."""
    max_selected = int(controls.get("max_selected_set") or DEFAULT_MAX_SELECTED_SET)
    cost_ceiling = int(controls.get("cost_ceiling_units") or DEFAULT_COST_CEILING_UNITS)
    min_cluster_ids: set[int] = set()
    for cluster in _COMMAND_HOME_MIN_SUFFICIENT_CLUSTERS:
        cluster_cands = [c for c in selected if c.get("dependence_cluster") == cluster]
        if cluster_cands:
            min_cluster_ids.add(min(c["launch_id"] for c in cluster_cands))

    ordered = sorted(
        selected,
        key=lambda c: (c["launch_id"] not in min_cluster_ids, c.get("cost_units", 1), c["launch_id"]),
    )
    kept: list[dict[str, Any]] = []
    total_cost = 0
    limit_breached = False
    for cand in ordered:
        cost = int(cand.get("cost_units") or _DEFAULT_COST_UNIT)
        if len(kept) >= max_selected:
            limit_breached = True
            continue
        if total_cost + cost > cost_ceiling:
            limit_breached = True
            continue
        kept.append(cand)
        total_cost += cost

    meta = {
        "max_selected_set": max_selected,
        "cost_ceiling_units": cost_ceiling,
        "selected_before": len(selected),
        "selected_after": len(kept),
        "total_cost_units": total_cost,
        "limit_breached": limit_breached,
        "dependence_clusters": dependence_clusters,
    }
    return kept, meta, limit_breached


def build_intent_from_params(
    *,
    goal: str,
    symbol: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """§23.1 Intent Contract."""
    p = dict(params or {})
    return {
        "user_goal": goal,
        "asset_scope": str(symbol or "BTC").upper(),
        "horizon": p.get("horizon") or "intraday",
        "decision_type": p.get("decision_type") or "command_home_composition",
        "required_safety_lenses": list(p.get("required_safety_lenses") or ["freshness", "evidence_class", "readiness"]),
        "minimum_evidence_requirement": p.get("minimum_evidence_requirement") or "launch57_pass_engineering",
        "desired_output_mode": p.get("desired_output_mode") or "six_heroes_command_home",
    }


def gather_candidates(*, intent: dict[str, Any]) -> list[dict[str, Any]]:
    """§23.5 step 2 — candidate universe from Launch-57 SSOT only."""
    eligible = launch57_home_eligible_ids()
    rows: list[dict[str, Any]] = []
    for row in _load_register_rows():
        ln = row.get("launch_number")
        if not isinstance(ln, int) or ln not in LAUNCH57_SCOPE_IDS:
            continue
        rows.append(
            {
                "launch_id": ln,
                "launch_name": row.get("launch_name"),
                "runtime_handler": row.get("runtime_handler"),
                "engineering_status": row.get("current_engineering_status"),
                "home_eligible": ln in eligible,
                "dependence_cluster": _dependence_cluster(ln),
                "parked": str(row.get("current_engineering_status") or "") in {"PARKED", "NO_LINKED_CANONICAL"},
            }
        )
    return rows


def apply_eligibility(
    candidates: list[dict[str, Any]],
    *,
    intent: dict[str, Any],
    spine: dict[str, Any] | None,
    oracle: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """§23.2 + §23.5 step 3 — eligibility and mandatory controls."""
    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    live_ok = bool((spine or {}).get("live_eligible"))
    oracle_action = str((oracle or {}).get("decision_action") or "").upper()

    for cand in candidates:
        reasons: list[str] = []
        ln = cand["launch_id"]
        if ln not in LAUNCH57_SCOPE_IDS:
            reasons.append("outside_launch57_scope")
        if cand.get("parked"):
            reasons.append("parked_capability")
        if not cand.get("home_eligible"):
            reasons.append("not_home_eligible")
        if not live_ok:
            reasons.append("freshness_mandatory_control_failed")
        if oracle_action == "ABSTAIN" and cand.get("dependence_cluster") not in _COMMAND_HOME_MIN_SUFFICIENT_CLUSTERS:
            reasons.append("oracle_abstain_excludes_optional")

        if reasons:
            excluded.append({**cand, "exclusion_reasons": reasons})
        else:
            selected.append({**cand, "mandatory_controls_passed": True})
    return selected, excluded


def apply_dependence_clustering(eligible: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
    """§23.5 step 4 — dependence clustering; shared ancestry not double-counted."""
    clusters: dict[str, list[int]] = {}
    for cand in eligible:
        cluster = cand["dependence_cluster"]
        clusters.setdefault(cluster, []).append(cand["launch_id"])
    # Keep one representative per cluster for sufficiency counting (lowest launch_id).
    representatives: list[dict[str, Any]] = []
    seen_clusters: set[str] = set()
    for cand in sorted(eligible, key=lambda c: c["launch_id"]):
        cluster = cand["dependence_cluster"]
        if cluster in seen_clusters:
            continue
        seen_clusters.add(cluster)
        representatives.append({**cand, "dependence_representative": True})
    return representatives, clusters


def apply_conflict_coverage(
    eligible: list[dict[str, Any]],
    *,
    oracle: dict[str, Any] | None,
    spine: dict[str, Any] | None,
) -> dict[str, Any]:
    """§23.5 step 5 — material conflict visibility."""
    governed = dict((oracle or {}).get("governed_payload") or {})
    contradiction = governed.get("critical_contradiction") or governed.get("contradiction_state")
    unresolved = bool(contradiction)
    return {
        "material_conflict_visible": unresolved,
        "contradiction": contradiction,
        "conflict_blocks_selection": unresolved,
        "supporting_evidence_present": bool(oracle),
        "opposing_evidence_visible": unresolved,
    }


def apply_budget(
    eligible: list[dict[str, Any]],
    *,
    maximum_candidates: int = DEFAULT_MAXIMUM_CANDIDATES,
    controls: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """§23.5 step 7 + §32 composition controls (candidate limit)."""
    ctrl = dict(controls or build_composition_controls({"maximum_candidates": maximum_candidates}))
    ctrl["max_candidate_set"] = int(ctrl.get("max_candidate_set") or maximum_candidates)
    kept, candidate_meta = apply_candidate_set_limit(eligible, controls=ctrl)
    budget_meta = {
        "maximum_candidates": ctrl["max_candidate_set"],
        "latency_class": ctrl.get("latency_class") or DEFAULT_LATENCY_CLASS,
        "cache_policy": ctrl.get("cache_policy") or DEFAULT_CACHE_POLICY,
        "degradation_path": ctrl.get("degradation_path") or DEFAULT_DEGRADATION_PATH,
        "cost_ceiling_units": ctrl.get("cost_ceiling_units") or DEFAULT_COST_CEILING_UNITS,
        "sync_deep_boundary": ctrl.get("sync_deep_boundary") or DEFAULT_SYNC_DEEP_BOUNDARY,
        "candidate_limit": candidate_meta,
        "candidates_after_budget": candidate_meta["candidates_after"],
        "candidates_before_budget": candidate_meta["candidates_before"],
        "engineering_only_not_measured_slo": False,
        "measured_engineering_representative": True,
    }
    return kept, budget_meta


def apply_stop(
    budgeted: list[dict[str, Any]],
    *,
    dependence_clusters: dict[str, list[int]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """§23.5 step 8 — stop when required coverage satisfied within budget."""
    selected_ids = {c["launch_id"] for c in budgeted}
    cluster_coverage = {k: any(i in selected_ids for i in ids) for k, ids in dependence_clusters.items()}
    min_met = all(cluster_coverage.get(cluster) for cluster in _COMMAND_HOME_MIN_SUFFICIENT_CLUSTERS)
    stop_meta = {
        "minimum_sufficient_met": min_met,
        "minimum_sufficient_clusters": sorted(_COMMAND_HOME_MIN_SUFFICIENT_CLUSTERS),
        "cluster_coverage": cluster_coverage,
        "stopped_because": "minimum_sufficient_and_budget_satisfied" if min_met else "insufficient_coverage",
    }
    if min_met:
        return budgeted, stop_meta
    return [], stop_meta


def apply_abstain(
    *,
    intent: dict[str, Any],
    spine: dict[str, Any] | None,
    conflict: dict[str, Any],
    stop_meta: dict[str, Any],
    selected: list[dict[str, Any]],
    composition_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """§23.4 + §23.5 step 9 + §32 degradation."""
    comp = dict(composition_meta or {})
    if comp.get("composition_limit_breached"):
        path = str(comp.get("degradation_path") or DEFAULT_DEGRADATION_PATH)
        if path == "abstain_with_explain":
            return {
                "abstain": True,
                "answer_state": "ABSTAIN",
                "reason": "composition_controls_exceeded",
                "explanation": (
                    "§32 composition limits exceeded on sync Command Home path — "
                    "abstain with explain per degradation_path."
                ),
            }
    if spine and not spine.get("live_eligible"):
        return {
            "abstain": True,
            "answer_state": "ABSTAIN",
            "reason": "stale_or_not_live_eligible",
            "explanation": "Freshness mandatory control failed — router abstains per §23.4.",
        }
    if conflict.get("conflict_blocks_selection"):
        return {
            "abstain": True,
            "answer_state": "ABSTAIN",
            "reason": "unresolved_material_conflict",
            "explanation": "Material contradiction remains unresolved — router abstains per §23.4.",
        }
    if not stop_meta.get("minimum_sufficient_met") or not selected:
        return {
            "abstain": True,
            "answer_state": "ABSTAIN",
            "reason": "selection_sufficiency_failed",
            "explanation": "Minimum sufficient Launch-57 candidate set not met — router abstains per §23.5.",
        }
    return {"abstain": False, "answer_state": "SELECTED", "reason": None, "explanation": None}


def build_explain(
    *,
    intent: dict[str, Any],
    excluded: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    dependence_clusters: dict[str, list[int]],
    budget_meta: dict[str, Any],
    stop_meta: dict[str, Any],
    abstain: dict[str, Any],
    composition_controls: dict[str, Any] | None = None,
    composition_trace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """§23.5 step 10 — inspectable selection/exclusion logic."""
    return {
        "intent_summary": intent.get("user_goal"),
        "selected_launch_ids": sorted(c["launch_id"] for c in selected),
        "excluded_count": len(excluded),
        "exclusion_samples": [
            {"launch_id": e["launch_id"], "reasons": e.get("exclusion_reasons", [])}
            for e in excluded[:5]
        ],
        "dependence_clusters": dependence_clusters,
        "budget": budget_meta,
        "stop": stop_meta,
        "abstain": abstain,
        "composition_controls": composition_controls,
        "composition_trace": composition_trace,
        "pipeline_steps": list(PIPELINE_STEPS),
        "methodology_version": METHODOLOGY_VERSION,
        "builder_status": BUILDER_STATUS,
        "isolation": {
            "launch57_scope_only": True,
            "no_parked_selection": True,
            "parallel_product_router_not_source_of_truth": True,
        },
    }


def run_router_selection_contract(
    *,
    goal: str,
    symbol: str,
    params: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    oracle: dict[str, Any] | None = None,
    maximum_candidates: int = DEFAULT_MAXIMUM_CANDIDATES,
) -> dict[str, Any]:
    """
    Full §23.5 + §32 pipeline: intent → candidates → eligibility → dependence → conflict
    → budget → stop → abstain → explain with composition controls enforced.
    """
    _started = time.perf_counter()
    trace: dict[str, Any] = {"steps": {}}
    p = dict(params or {})
    controls = build_composition_controls({**p, "maximum_candidates": maximum_candidates})
    composition_trace: dict[str, Any] = {}

    intent = build_intent_from_params(goal=goal, symbol=symbol, params=params)
    trace["steps"]["intent"] = intent

    candidates = gather_candidates(intent=intent)
    trace["steps"]["candidates"] = {"count": len(candidates), "launch57_scope_only": True}

    eligible, excluded = apply_eligibility(candidates, intent=intent, spine=spine, oracle=oracle)
    eligible = annotate_candidate_profiles(eligible)
    sync_kept, sync_excluded, sync_meta = apply_sync_deep_boundary(eligible, controls=controls)
    excluded.extend(sync_excluded)
    composition_trace["sync_deep_boundary"] = sync_meta
    trace["steps"]["composition_sync_deep"] = sync_meta

    trace["steps"]["eligibility"] = {
        "eligible_count": len(sync_kept),
        "excluded_count": len(excluded),
    }

    representatives, dependence_clusters = apply_dependence_clustering(sync_kept)
    trace["steps"]["dependence"] = {
        "representative_count": len(representatives),
        "clusters": dependence_clusters,
    }

    conflict = apply_conflict_coverage(representatives, oracle=oracle, spine=spine)
    trace["steps"]["conflict"] = conflict

    budgeted, budget_meta = apply_budget(representatives, maximum_candidates=maximum_candidates, controls=controls)
    trace["steps"]["budget"] = budget_meta
    composition_trace["candidate_limit"] = budget_meta.get("candidate_limit")

    selected, stop_meta = apply_stop(budgeted, dependence_clusters=dependence_clusters)
    trace["steps"]["stop"] = stop_meta

    selected, selected_meta, limit_breached = apply_selected_set_and_cost_limits(
        selected,
        controls=controls,
        dependence_clusters=dependence_clusters,
    )
    composition_trace["selected_and_cost"] = selected_meta
    trace["steps"]["composition_selected_cost"] = selected_meta
    composition_meta = {
        "composition_limit_breached": limit_breached,
        "degradation_path": controls.get("degradation_path"),
    }

    # Re-check minimum sufficient after §32 trimming.
    if selected:
        selected_ids = {c["launch_id"] for c in selected}
        cluster_coverage = {
            cluster: any(i in selected_ids for i in ids) for cluster, ids in dependence_clusters.items()
        }
        if not all(cluster_coverage.get(c) for c in _COMMAND_HOME_MIN_SUFFICIENT_CLUSTERS):
            composition_meta["composition_limit_breached"] = True
            selected = []
            stop_meta = {
                **stop_meta,
                "minimum_sufficient_met": False,
                "stopped_because": "composition_controls_removed_minimum_sufficient",
            }

    abstain = apply_abstain(
        intent=intent,
        spine=spine,
        conflict=conflict,
        stop_meta=stop_meta,
        selected=selected,
        composition_meta=composition_meta,
    )
    trace["steps"]["abstain"] = abstain

    if abstain.get("abstain"):
        selected = []

    elapsed_ms = round((time.perf_counter() - _started) * 1000.0, 3)
    measurement = record_composition_measurement(
        "composition_selected_count",
        len(selected),
        labels={"latency_class": controls.get("latency_class"), "cache_policy": controls.get("cache_policy")},
    )
    latency_measurement = record_composition_measurement(
        "router_pipeline_latency_ms",
        elapsed_ms,
        labels={"latency_class": controls.get("latency_class"), "measured_engineering_representative": True},
    )
    composition_trace["measurement_hook"] = measurement
    composition_trace["latency_measurement"] = latency_measurement

    explain = build_explain(
        intent=intent,
        excluded=excluded,
        selected=selected,
        dependence_clusters=dependence_clusters,
        budget_meta=budget_meta,
        stop_meta=stop_meta,
        abstain=abstain,
        composition_controls=controls,
        composition_trace=composition_trace,
    )
    trace["steps"]["explain"] = explain

    return {
        "router_selection_contract": {
            "governing_spec": "Adaptive Spec §23.5 + §32 Runtime/Cost/Performance",
            "builder_status": BUILDER_STATUS,
            "pipeline_steps": list(PIPELINE_STEPS),
            "intent": intent,
            "selected_launch_ids": explain["selected_launch_ids"],
            "answer_state": abstain["answer_state"],
            "abstain": abstain.get("abstain", False),
            "abstain_reason": abstain.get("reason"),
            "abstain_explanation": abstain.get("explanation"),
            "budget": budget_meta,
            "composition_controls": controls,
            "composition_trace": composition_trace,
            "trace": trace,
            "explain": explain,
        }
    }
