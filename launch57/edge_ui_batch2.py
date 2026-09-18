"""
Launch-57 Phase 7 — Edge + UI Batch 2 (build last).

Launch #1 — Six Heroes Command Home — «ماذا أفعل الآن؟»
"""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer
from decision_truth.product.command_view import build_command_view
from decision_truth.product.six_heroes import build_six_heroes
from launch57.decision_common import load_decision_spine, stale_gate_body, stamp_decision_batch
from launch57.edge_ui_common import LAUNCH57_SCOPE_IDS, attach_edge_ui_envelope
from launch57.router_selection_contract import run_router_selection_contract
from launch57.accessibility_common import attach_launch57_accessibility
from launch57.trust_adaptive_common import (
    apply_command_home_guard,
    attach_adaptive_disclosure,
    build_command_home_disclosure,
    build_progressive_disclosure_stack,
)
from launch57.trust_batch1 import single_sentence_oracle

_BINDING = "launch57_phase7_edge_ui_batch2"
_MODULE = "launch57.edge_ui_batch2"


def _governed_params(p: dict[str, Any], semantics: dict[str, Any], spine: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(p)
    governed = dict(out.get("governed_payload") or {})
    contract = semantics.get("contract") or {}
    if contract.get("material_limitation"):
        governed["critical_limitation"] = contract["material_limitation"]
    if semantics.get("scope_rejected"):
        governed["unsupported_readiness_scope"] = True
    out["governed_payload"] = governed
    if spine:
        out["freshness_state"] = spine.get("freshness_state")
    return out


def _attach_edge_adaptive(
    wrapped: dict[str, Any],
    *,
    p: dict[str, Any],
    spine: dict[str, Any] | None,
    launch_item_id: int,
    surface: str,
    semantics: dict[str, Any],
    disclosure_key: str,
    disclosure: dict[str, Any],
) -> dict[str, Any]:
    contract = semantics.get("contract") or {}
    if contract:
        wrapped["edge_ui_contract"] = contract
        wrapped["evidence_class_visible"] = contract.get("evidence_class")
    wrapped["evidence_display"] = {
        "canonical_evidence_class": contract.get("evidence_class"),
        "freshness_state": (spine or {}).get("freshness_state"),
    }
    governed_p = _governed_params(p, semantics, spine)
    uncertainty = (
        "qualified"
        if semantics.get("scope_rejected") or str(semantics.get("answer_state", "")).startswith("BLOCKED")
        else "standard"
    )
    progressive = build_progressive_disclosure_stack(
        {**wrapped, **governed_p},
        launch_item_id=launch_item_id,
        surface=surface,
        answer_state=semantics.get("answer_state"),
        evidence_display=wrapped.get("evidence_display"),
        uncertainty=uncertainty,
    )
    out = attach_adaptive_disclosure(
        wrapped,
        progressive["level_1"],
        extra={disclosure_key: disclosure},
        progressive_stack=progressive,
        apply_full_support_plane=False,
    )
    if not out.get("router_selection_contract"):
        home = out.get("six_heroes_command_home") or {}
        router_block = (home.get("router_selection_contract") or {})
        if router_block:
            out["router_selection_contract"] = router_block
    return attach_launch57_accessibility(out, surface=surface, lang=str(p.get("lang") or "en"))


async def six_heroes_command_home(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #1 — command home from governed oracle/decision/trust only; LAUNCH57 PASS items."""
    p = dict(params or {})
    asset = str(p.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    spine = await load_decision_spine(asset, p)

    if not spine["live_eligible"]:
        body = stamp_decision_batch(
            stale_gate_body(
                capability_id=0,
                launch_item_id=1,
                surface="six_heroes_command_home",
                symbol=spine["symbol"],
                spine=spine,
                entrypoint="six_heroes_command_home",
            ),
            capability_id=0,
            launch_item_id=1,
            entrypoint="six_heroes_command_home",
            batch_module=_MODULE,
            binding_source=_BINDING,
        )
        return attach_edge_ui_envelope(ai_compliance_footer(body), spine=spine)

    oracle = await single_sentence_oracle(symbol=spine["symbol"], params=p)
    router = run_router_selection_contract(
        goal="six_heroes_command_home",
        symbol=spine["symbol"],
        params=p,
        spine=spine,
        oracle=oracle,
    )
    router_block = router.get("router_selection_contract") or {}
    if router_block.get("abstain"):
        body = stamp_decision_batch(
            {
                "surface": "six_heroes_command_home",
                "symbol": spine["symbol"],
                "success": False,
                "answer_state": router_block.get("answer_state") or "ABSTAIN",
                "six_heroes_command_home": {
                    "question": "ماذا أفعل الآن؟",
                    "router_selection_contract": router_block,
                    "abstain": True,
                    "abstain_reason": router_block.get("abstain_reason"),
                    "abstain_explanation": router_block.get("abstain_explanation"),
                    "eligible_launch57_ids": [],
                    "launch57_scope_only": True,
                    "excludes_parked": True,
                    "consumer_path": "api/routers/launch57_edge_ui.py",
                },
                "freshness_state": spine["freshness_state"],
                "presented_as_live": spine["presented_as_live"],
            },
            capability_id=0,
            launch_item_id=1,
            entrypoint="six_heroes_command_home",
            batch_module=_MODULE,
            binding_source=_BINDING,
        )
        wrapped = attach_edge_ui_envelope(ai_compliance_footer(body), spine=spine)
        abstain_body = {**wrapped, "six_heroes_command_home": body.get("six_heroes_command_home") or {}}
        progressive = build_progressive_disclosure_stack(
            abstain_body,
            launch_item_id=1,
            surface="six_heroes_command_home",
            answer_state="ABSTAIN",
            evidence_display={"freshness_state": spine.get("freshness_state")},
            uncertainty="insufficient_evidence",
        )
        out = attach_adaptive_disclosure(
            wrapped,
            progressive["level_1"],
            extra={"command_home_disclosure": {"abstain": True, "router": router_block.get("explain")}},
            progressive_stack=progressive,
            apply_full_support_plane=False,
        )
        out["router_selection_contract"] = router_block
        return attach_launch57_accessibility(out, surface="six_heroes_command_home", lang=str(p.get("lang") or "en"))

    oracle_block = oracle.get("single_sentence_oracle") or {}
    contract = {
        "decision_state": oracle.get("decision_action") or oracle_block.get("action"),
        "grade": oracle_block.get("grade"),
        "evidence_class": oracle.get("evidence_class"),
        "freshness": spine.get("freshness_state"),
        "net_edge": oracle.get("net_edge_truth_score"),
    }
    payload: dict[str, Any] = {
        "symbol": spine["symbol"],
        "decision_truth_state": contract.get("decision_state") or "UNAVAILABLE",
        "decision_truth": {"contract": contract, "evidence_lifecycle": oracle.get("evidence_display")},
        "single_sentence_oracle": oracle.get("single_sentence_oracle"),
        "freshness_state": spine["freshness_state"],
        "price": spine.get("price"),
        "change_24h": spine.get("change_24h"),
    }

    heroes = build_six_heroes(payload)
    command_view = build_command_view(payload, enabled=bool(p.get("command_view", True)))
    guarded = apply_command_home_guard(
        heroes=heroes,
        command_view=command_view,
        oracle=oracle,
        spine=spine,
        params=p,
    )
    guard_eligible = list(guarded.get("eligible_launch57_ids") or [])
    if guarded.get("scope_rejected"):
        eligible: list[int] = []
    else:
        router_selected = set(router_block.get("selected_launch_ids") or [])
        eligible = sorted(set(guard_eligible) & router_selected) if router_selected else guard_eligible

    body = stamp_decision_batch(
        {
            "surface": "six_heroes_command_home",
            "symbol": spine["symbol"],
            "success": guarded.get("answer_state") == "COMMAND_HOME_GROUNDED",
            "six_heroes_command_home": {
                "question": "ماذا أفعل الآن؟",
                "heroes": guarded.get("heroes"),
                "oracle": oracle,
                "command_view": guarded.get("command_view"),
                "eligible_launch57_ids": eligible,
                "launch57_scope_only": True,
                "excludes_parked": True,
                "excludes_non_launch57_ids": True,
                "no_duplicate_capability_directory": True,
                "six_heroes_primary": True,
                "oracle_path": "launch57.trust_batch1:single_sentence_oracle",
                "router_selection_contract": router_block,
                "home_guard": guarded,
            },
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
            "consumer_path": "api/routers/launch57_edge_ui.py",
        },
        capability_id=0,
        launch_item_id=1,
        entrypoint="six_heroes_command_home",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_edge_ui_envelope(ai_compliance_footer(body), spine=spine)
    wrapped["launch57_scope_guard"] = {
        "max_launch_id": max(LAUNCH57_SCOPE_IDS),
        "all_eligible_within_scope": all(i in LAUNCH57_SCOPE_IDS for i in eligible),
    }
    disclosure = build_command_home_disclosure(guarded)
    return _attach_edge_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=1,
        surface="six_heroes_command_home",
        semantics=guarded,
        disclosure_key="command_home_disclosure",
        disclosure=disclosure,
    )


async def execute_launch57_edge_ui_batch2(
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sym = str((params or {}).get("symbol") or "BTC")
    return await six_heroes_command_home(symbol=sym, params=dict(params or {}))
