"""
Launch-57 Phase 7 — Edge + UI Batch 1.

Build order: #43 CAP-0230/0635 → #38 CAP-0040 → #49 → #50 → #52
"""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer
from launch57.decision_common import require_net_edge_if_cost_claim, stamp_decision_batch
from launch57.b6_net_edge_bridge import apply_b6_trust_envelope, enrich_arbitrage_opportunities_block
from launch57.edge_ui_common import (
    attach_edge_ui_envelope,
    free_tier_history_limit,
    gated_edge_ui,
    launch57_library_entries,
    mvrv_source_blocker_note,
    read_decision_history_rows,
)
from launch57.trust_adaptive_common import (
    apply_capability_library_guard,
    apply_discipline_mirror_guard,
    apply_mvrv_provenance_guard,
    apply_personal_history_guard,
    apply_spot_perp_net_edge_semantics,
    attach_adaptive_disclosure,
    build_capability_library_disclosure,
    build_discipline_mirror_disclosure,
    build_level1_decision_disclosure,
    build_mvrv_provenance_disclosure,
    build_personal_history_disclosure,
    build_spot_perp_net_edge_disclosure,
)

LAUNCH57_EDGE_UI_BATCH1_CAP_IDS: frozenset[int] = frozenset({230, 635, 40})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    230: 43,
    635: 43,
    40: 38,
}

_BINDING = "launch57_phase7_edge_ui_batch1"
_MODULE = "launch57.edge_ui_batch1"

_SPOT_PERP_KINDS = frozenset({"spot_futures", "funding", "basis"})


def _governed_params(p: dict[str, Any], semantics: dict[str, Any], spine: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(p)
    governed = dict(out.get("governed_payload") or {})
    contract = semantics.get("contract") or {}
    if contract.get("material_limitation"):
        governed["critical_limitation"] = contract["material_limitation"]
    if semantics.get("behavioral_learning_rejected"):
        governed["unsupported_learning_scope"] = True
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
    uncertainty = "qualified" if semantics.get("behavioral_learning_rejected") or semantics.get("answer_state", "").startswith("BLOCKED") else "standard"
    level1 = build_level1_decision_disclosure(
        governed_p,
        launch_item_id=launch_item_id,
        surface=surface,
        answer_state=semantics.get("answer_state"),
        evidence_display=wrapped.get("evidence_display"),
        uncertainty=uncertainty,
    )
    return attach_adaptive_disclosure(wrapped, level1, extra={disclosure_key: disclosure})


async def spot_perp_arbitrage_scanner(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #43 / CAP-0230 — spot–perp arbitrage with mandatory Net-Edge."""
    from arbitrage_service import scan_arbitrage_opportunities

    p = dict(params or {})
    blocked, spine = await gated_edge_ui(
        capability_id=230,
        launch_item_id=43,
        surface="spot_perp_arbitrage_scanner",
        entrypoint="spot_perp_arbitrage_scanner",
        symbol=symbol,
        params=p,
        module=_MODULE,
        binding=_BINDING,
    )
    if blocked:
        return blocked

    opportunity = p.get("opportunity")
    cost_claim = bool(opportunity) or bool(p.get("cost_claim"))
    net_edge_result = None
    if cost_claim:
        edge_block = await require_net_edge_if_cost_claim(symbol=spine["symbol"], params=p, cost_claim=True)
        if edge_block and edge_block.get("blocked"):
            body = stamp_decision_batch(
                {
                    "surface": "spot_perp_arbitrage_scanner",
                    "symbol": spine["symbol"],
                    "success": False,
                    "error": edge_block.get("reason"),
                    "net_edge_required": True,
                    "net_edge_path": edge_block.get("net_edge_path"),
                    "cost_claim_blocked": True,
                    "opportunity_required": opportunity is None,
                    "freshness_state": spine["freshness_state"],
                    "presented_as_live": False,
                },
                capability_id=230,
                launch_item_id=43,
                entrypoint="spot_perp_arbitrage_scanner",
                batch_module=_MODULE,
                binding_source=_BINDING,
            )
            return attach_edge_ui_envelope(ai_compliance_footer(body), spine=spine)
        net_edge_result = edge_block

    scan = await scan_arbitrage_opportunities(
        quote_amount=float(p.get("quote_amount") or 1000.0),
        prefer_live=spine.get("presented_as_live"),
    )
    opps = [
        row
        for row in (scan.get("opportunities") or [])
        if str(row.get("kind") or "") in _SPOT_PERP_KINDS
    ]

    spot_block = enrich_arbitrage_opportunities_block(
        {
            "opportunities": opps[: int(p.get("limit") or 10)],
            "scan_meta": {
                "data_source": scan.get("data_source"),
                "data_age_sec": scan.get("data_age_sec"),
                "executable_count": scan.get("executable_count"),
                "timestamp": scan.get("timestamp"),
            },
            "net_edge_evaluated": net_edge_result is not None,
            "net_edge": (net_edge_result or {}).get("net_edge"),
            "net_edge_path": "launch57.trust_batch1:net_edge_truth_score",
        },
        payload=p,
        scan_meta=scan,
        display_timezone=p.get("display_timezone"),
    )
    semantics = apply_spot_perp_net_edge_semantics(
        spot_block.get("opportunities"),
        net_edge_result=net_edge_result,
        params=p,
        spine=spine,
    )
    spot_block["opportunities"] = semantics.get("qualified_opportunities")
    spot_block["net_edge_semantics"] = semantics
    spot_block["executable_count"] = semantics.get("executable_count")
    body = stamp_decision_batch(
        {
            "surface": "spot_perp_arbitrage_scanner",
            "symbol": spine["symbol"],
            "success": bool(spot_block.get("opportunities")) and semantics.get("executable_count", 0) > 0,
            "spot_perp_arbitrage": spot_block,
            "cost_claim_allowed": bool(net_edge_result and not net_edge_result.get("blocked")),
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
            "presented_as_current": bool(semantics.get("executable_count")),
        },
        capability_id=230,
        launch_item_id=43,
        entrypoint="spot_perp_arbitrage_scanner",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    body = apply_b6_trust_envelope(body, display_timezone=p.get("display_timezone"))
    wrapped = attach_edge_ui_envelope(ai_compliance_footer(body), spine=spine)
    disclosure = build_spot_perp_net_edge_disclosure(semantics)
    return _attach_edge_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=43,
        surface="spot_perp_arbitrage_scanner",
        semantics=semantics,
        disclosure_key="spot_perp_net_edge_disclosure",
        disclosure=disclosure,
    )


async def unified_arbitrage_opportunity_engine(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #43 / CAP-0635 — unified arbitrage engine companion (Net-Edge gated)."""
    out = await spot_perp_arbitrage_scanner(symbol=symbol, params=params)
    out["surface"] = "unified_arbitrage_opportunity_engine"
    out["capability_id"] = 635
    out["launch_item_id"] = 43
    out["backend_entrypoint"] = "unified_arbitrage_opportunity_engine"
    if "spot_perp_arbitrage" in out:
        out["unified_arbitrage_opportunity_engine"] = out.pop("spot_perp_arbitrage")
    return out


async def mvrv_mvrv_z_score_suite(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #38 / CAP-0040 — MVRV/Z BTC/ETH core with explicit source blocker."""
    from bd_platform.mvrv_realignment import compute_mvrv_realignment
    from bd_platform.onchain_hub import lookintobitcoin_macro

    p = dict(params or {})
    blocked, spine = await gated_edge_ui(
        capability_id=40,
        launch_item_id=38,
        surface="mvrv_mvrv_z_score_suite",
        entrypoint="mvrv_mvrv_z_score_suite",
        symbol=symbol,
        params=p,
        module=_MODULE,
        binding=_BINDING,
    )
    if blocked:
        return blocked

    asset = spine["symbol"]
    cores: dict[str, Any] = {}
    source_status: dict[str, Any] = {}

    macro_ref = await lookintobitcoin_macro()
    targets = [asset] if asset in {"BTC", "ETH"} else ["BTC", "ETH"]
    for target in targets:
        mvrv = await compute_mvrv_realignment(target)
        cores[target] = mvrv
        has_z = mvrv.get("z_score") is not None and mvrv.get("ok")
        source_status[target] = {
            "licensed_mvrv_feed": False,
            "local_proxy_compute": bool(has_z),
            "reference_only_urls": [
                ind.get("url")
                for ind in (macro_ref.get("indicators") or [])
                if ind.get("id") == "mvrv"
            ],
            "blocker": None if has_z else "BLOCKED_EXTERNAL",
            "blocker_reason": None if has_z else "licensed_onchain_mvrv_source_not_configured",
            "presented_as_live": bool(has_z and spine["presented_as_live"]),
            "disclaimer": mvrv_source_blocker_note(),
        }

    guarded = apply_mvrv_provenance_guard(
        cores,
        source_status,
        asset=asset,
        spine=spine,
        params=p,
    )
    any_live = any(s.get("presented_as_live") for s in guarded.get("source_status", {}).values())
    body = stamp_decision_batch(
        {
            "surface": "mvrv_mvrv_z_score_suite",
            "symbol": asset,
            "success": bool(guarded.get("cores")),
            "mvrv_z_score_suite": {
                "cores": guarded.get("cores"),
                "source_status": guarded.get("source_status"),
                "macro_reference": macro_ref if macro_ref.get("indicators") else None,
                "licensed_source_configured": guarded.get("licensed_source_configured"),
                "no_phantom_live_values": guarded.get("no_phantom_live_values"),
                "mvrv_guard": guarded,
            },
            "freshness_state": spine["freshness_state"],
            "presented_as_live": any_live,
        },
        capability_id=40,
        launch_item_id=38,
        entrypoint="mvrv_mvrv_z_score_suite",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_edge_ui_envelope(ai_compliance_footer(body), spine=spine)
    disclosure = build_mvrv_provenance_disclosure(guarded)
    return _attach_edge_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=38,
        surface="mvrv_mvrv_z_score_suite",
        semantics=guarded,
        disclosure_key="mvrv_provenance_disclosure",
        disclosure=disclosure,
    )


async def personal_decision_history(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #49 — personal decision history (limited Free tier)."""
    p = dict(params or {})
    tier = str(p.get("tier") or "free").lower()
    limit = int(p.get("limit") or free_tier_history_limit())
    rows = read_decision_history_rows(limit=limit, tier=tier)
    guarded = apply_personal_history_guard(rows, params=p, tier=tier)

    body = stamp_decision_batch(
        {
            "surface": "personal_decision_history",
            "symbol": str(p.get("symbol") or symbol or "BTC"),
            "success": guarded.get("answer_state") == "HISTORY_OBSERVABLE",
            "personal_decision_history": {
                "decisions": guarded.get("decisions"),
                "count": guarded.get("count"),
                "tier": tier,
                "free_limit": free_tier_history_limit(),
                "limited_free": tier == "free",
                "source": "decision_ledger.jsonl",
                "history_guard": guarded,
                "history_only": True,
            },
            "consumer_path": "api/routers/launch57_edge_ui.py",
        },
        capability_id=0,
        launch_item_id=49,
        entrypoint="personal_decision_history",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_edge_ui_envelope(ai_compliance_footer(body), params=p)
    disclosure = build_personal_history_disclosure(guarded)
    from launch57.identity_auth_common import attach_identity_auth_envelope

    adapted = _attach_edge_adaptive(
        wrapped,
        p=p,
        spine=None,
        launch_item_id=49,
        surface="personal_decision_history",
        semantics=guarded,
        disclosure_key="personal_history_disclosure",
        disclosure=disclosure,
    )
    from launch57.billing_entitlement_common import attach_billing_entitlement_envelope

    adapted = attach_identity_auth_envelope(
        adapted,
        launch_item_id=49,
        surface_type="private",
        params=p,
    )
    return attach_billing_entitlement_envelope(adapted, launch_item_id=49, params=p)


async def discipline_mirror_light(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #50 — light discipline / missed-movement mirror."""
    from discipline_mirror import personal_mirror

    p = dict(params or {})
    user_key = str(p.get("user_key") or "anonymous")
    mirror = personal_mirror(user_key, limit=int(p.get("limit") or 20))
    guarded = apply_discipline_mirror_guard(mirror, params=p)
    reflective = dict(guarded.get("discipline_mirror") or {})
    body = stamp_decision_batch(
        {
            "surface": "discipline_mirror_light",
            "symbol": str(p.get("symbol") or symbol or "BTC"),
            "success": guarded.get("answer_state") == "MIRROR_OBSERVABLE",
            "discipline_mirror": {
                **reflective,
                "lightweight": True,
                "missed_movement_mirror": True,
                "mirror_guard": guarded,
            },
            "consumer_path": "api/routers/launch57_edge_ui.py",
        },
        capability_id=0,
        launch_item_id=50,
        entrypoint="discipline_mirror_light",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_edge_ui_envelope(ai_compliance_footer(body), params=p)
    disclosure = build_discipline_mirror_disclosure(guarded)
    from launch57.identity_auth_common import attach_identity_auth_envelope

    adapted = _attach_edge_adaptive(
        wrapped,
        p=p,
        spine=None,
        launch_item_id=50,
        surface="discipline_mirror_light",
        semantics=guarded,
        disclosure_key="discipline_mirror_disclosure",
        disclosure=disclosure,
    )
    from launch57.billing_entitlement_common import attach_billing_entitlement_envelope

    adapted = attach_identity_auth_envelope(
        adapted,
        launch_item_id=50,
        surface_type="private",
        params=p,
    )
    return attach_billing_entitlement_envelope(adapted, launch_item_id=50, params=p)


async def capability_library_search(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #52 — secondary capability library (search), not primary home."""
    p = dict(params or {})
    query = str(p.get("query") or p.get("q") or "")
    entries = launch57_library_entries(query=query or None)
    guarded = apply_capability_library_guard(entries, params=p)
    body = stamp_decision_batch(
        {
            "surface": "capability_library_search",
            "symbol": str(p.get("symbol") or symbol or "BTC"),
            "success": guarded.get("answer_state") == "LIBRARY_GROUNDED",
            "capability_library": {
                "results": guarded.get("results"),
                "count": guarded.get("count"),
                "secondary_layer": True,
                "not_primary_home": True,
                "launch57_scope_only": True,
                "query": query or None,
                "library_guard": guarded,
                "ssot_source": guarded.get("ssot_source"),
                "no_second_registry": True,
            },
            "consumer_path": "api/routers/launch57_edge_ui.py",
        },
        capability_id=0,
        launch_item_id=52,
        entrypoint="capability_library_search",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_edge_ui_envelope(ai_compliance_footer(body))
    disclosure = build_capability_library_disclosure(guarded)
    return _attach_edge_adaptive(
        wrapped,
        p=p,
        spine=None,
        launch_item_id=52,
        surface="capability_library_search",
        semantics=guarded,
        disclosure_key="capability_library_disclosure",
        disclosure=disclosure,
    )


_DISPATCH: dict[int, str] = {
    230: "spot_perp_arbitrage_scanner",
    635: "unified_arbitrage_opportunity_engine",
    40: "mvrv_mvrv_z_score_suite",
}

_PRODUCT_DISPATCH: dict[int, str] = {
    49: "personal_decision_history",
    50: "discipline_mirror_light",
    52: "capability_library_search",
}


async def execute_launch57_edge_ui_batch1(
    capability_id: int,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if capability_id not in LAUNCH57_EDGE_UI_BATCH1_CAP_IDS:
        raise ValueError(f"capability {capability_id} not in Launch-57 edge+UI batch 1")
    fn = globals()[_DISPATCH[capability_id]]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))


async def execute_launch57_edge_ui_product(
    launch_item_id: int,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if launch_item_id not in _PRODUCT_DISPATCH:
        raise ValueError(f"launch item {launch_item_id} not in Launch-57 edge+UI batch 1 product surfaces")
    fn = globals()[_PRODUCT_DISPATCH[launch_item_id]]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
