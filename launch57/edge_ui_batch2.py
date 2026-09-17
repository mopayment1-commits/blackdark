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
from launch57.edge_ui_common import LAUNCH57_SCOPE_IDS, attach_edge_ui_envelope, launch57_home_eligible_ids
from launch57.trust_batch1 import single_sentence_oracle

_BINDING = "launch57_phase7_edge_ui_batch2"
_MODULE = "launch57.edge_ui_batch2"


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
    eligible = launch57_home_eligible_ids()

    body = stamp_decision_batch(
        {
            "surface": "six_heroes_command_home",
            "symbol": spine["symbol"],
            "success": True,
            "six_heroes_command_home": {
                "question": "ماذا أفعل الآن؟",
                "heroes": heroes,
                "command_view": command_view,
                "eligible_launch57_ids": sorted(eligible),
                "launch57_scope_only": True,
                "excludes_parked": True,
                "excludes_non_launch57_ids": True,
                "oracle_path": "launch57.trust_batch1:single_sentence_oracle",
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
    out = attach_edge_ui_envelope(ai_compliance_footer(body), spine=spine)
    out["launch57_scope_guard"] = {
        "max_launch_id": max(LAUNCH57_SCOPE_IDS),
        "all_eligible_within_scope": all(i in LAUNCH57_SCOPE_IDS for i in eligible),
    }
    return out


async def execute_launch57_edge_ui_batch2(
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sym = str((params or {}).get("symbol") or "BTC")
    return await six_heroes_command_home(symbol=sym, params=dict(params or {}))
