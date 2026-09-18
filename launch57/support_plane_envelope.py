"""
Launch-57 Support Plane — cross-path material composition envelope.

Applies §23 router, §28 progressive disclosure L1–L5, §31 accessibility, and §32
measurement hooks to canonical launch57/* consumer responses.
"""

from __future__ import annotations

import time
from typing import Any

from launch57.accessibility_common import attach_launch57_accessibility
from launch57.router_selection_contract import run_router_selection_contract
from launch57.trust_adaptive_common import (
    build_level2_why_disclosure,
    build_level3_drivers_disclosure,
    build_level4_evidence_disclosure,
    build_level5_expert_disclosure,
)

BUILDER_STATUS = "PASS_ENGINEERING"
METHODOLOGY_VERSION = "launch57-support-plane-envelope-1.0"

# Data-spine capabilities — router/composition not required per support-plane scope.
_DATA_SPINE_LAUNCH_IDS: frozenset[int] = frozenset({21, 22, 23, 24, 39, 40, 41, 42})


def material_composition_applies(launch_item_id: int | None, surface: str | None) -> bool:
    if not launch_item_id or not surface:
        return False
    if int(launch_item_id) in _DATA_SPINE_LAUNCH_IDS:
        return False
    return True


def attach_router_if_material(
    body: dict[str, Any],
    *,
    launch_item_id: int,
    surface: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """§23.5 on all material composition consumer paths."""
    if not material_composition_applies(launch_item_id, surface):
        return body
    if body.get("router_selection_contract"):
        return body
    p = dict(params or {})
    symbol = str(body.get("symbol") or p.get("symbol") or "BTC").upper()
    spine = body.get("data_spine") or body.get("spine")
    if isinstance(spine, dict):
        spine = {
            "symbol": symbol,
            "freshness_state": body.get("freshness_state") or spine.get("freshness_state"),
            "live_eligible": spine.get("live_eligible", body.get("live_eligible", True)),
        }
    else:
        spine = {
            "symbol": symbol,
            "freshness_state": body.get("freshness_state"),
            "live_eligible": body.get("live_eligible", True),
        }
    oracle = body.get("single_sentence_oracle") or body.get("oracle")
    if isinstance(oracle, dict) and "decision_action" not in oracle:
        oracle = oracle.get("single_sentence_oracle") or oracle
    started = time.perf_counter()
    router = run_router_selection_contract(
        goal=surface,
        symbol=symbol,
        params=p,
        spine=spine,
        oracle=oracle if isinstance(oracle, dict) else None,
    )
    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 3)
    block = dict(router.get("router_selection_contract") or {})
    trace = block.get("composition_trace") or {}
    trace["measured_router_latency_ms"] = elapsed_ms
    block["composition_trace"] = trace
    block["cross_path_router"] = True
    out = dict(body)
    out["router_selection_contract"] = block
    return out


def finalize_launch57_consumer_response(
    body: dict[str, Any],
    disclosure: dict[str, Any],
    *,
    extra: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Full support-plane envelope: router (if material) → L1–L5 → accessibility.
    """
    launch_item_id = int(disclosure.get("launch_item_id") or body.get("launch_item_id") or 0)
    surface = str(disclosure.get("surface") or body.get("surface") or "")
    answer_state = disclosure.get("answer_state") or body.get("answer_state")
    wrapped = attach_router_if_material(
        dict(body),
        launch_item_id=launch_item_id,
        surface=surface,
        params=params,
    )
    level1 = dict(disclosure)
    progressive = {
        "level_1": level1,
        "level_2": build_level2_why_disclosure(wrapped, level1),
        "level_3": build_level3_drivers_disclosure(wrapped, level1),
        "level_4": build_level4_evidence_disclosure(wrapped, level1),
        "level_5": build_level5_expert_disclosure(wrapped, level1),
        "safety_floor_visible": True,
        "methodology_version": "launch57-trust-adaptive-common-1.1",
    }
    out = dict(wrapped)
    block = dict(extra or {})
    block.update(progressive)
    out["adaptive_disclosure"] = block
    out["safety_floor_visible"] = True
    out["support_plane_envelope"] = {
        "methodology_version": METHODOLOGY_VERSION,
        "builder_status": BUILDER_STATUS,
        "router_attached": bool(out.get("router_selection_contract")),
        "progressive_layers": ["level_1", "level_2", "level_3", "level_4", "level_5"],
    }
    return attach_launch57_accessibility(
        out,
        surface=surface or "launch57_consumer",
        lang=str((params or {}).get("lang") or body.get("lang") or "en"),
    )
