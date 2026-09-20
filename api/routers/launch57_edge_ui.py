"""Launch-57 Phase 7 — edge + UI consumer API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, Request

from api.openapi_responses import COMMON_ERROR_RESPONSES

router = APIRouter(tags=["launch57-edge-ui"], responses=COMMON_ERROR_RESPONSES)


def _require_launch57_tier(
    request: Request,
    launch_item_id: int,
    *,
    tier: str = "free",
) -> dict[str, Any]:
    from launch57.tier_distribution import enforce_launch57_tier_access

    gate = enforce_launch57_tier_access(
        launch_item_id=launch_item_id,
        params={"tier": tier, "user_key": "anonymous"},
    )
    if not gate.get("allowed"):
        raise HTTPException(
            status_code=403,
            detail={
                "detail": "Tier entitlement denied",
                "launch_item_id": launch_item_id,
                "reason": gate.get("reason"),
                "minimum_tier": gate.get("minimum_tier"),
                "effective_tier": gate.get("effective_tier"),
            },
            headers={"X-Blackdark-Tier-Boundary": "launch57-tier-denied"},
        )
    return gate


def _require_launch57_auth(request: Request, launch_item_id: int) -> None:
    from anonymous_route_foundation import request_has_authentication_signal
    from launch57.anonymous_visitor_common import enforce_launch57_anonymous_boundary

    boundary = enforce_launch57_anonymous_boundary(
        launch_item_id,
        has_auth_signal=request_has_authentication_signal(request),
    )
    if not boundary.get("allowed"):
        raise HTTPException(
            status_code=401,
            detail={
                "detail": "Anonymous access denied",
                "launch_item_id": launch_item_id,
                "reason": boundary.get("reason"),
                "auth_state_required": boundary.get("auth_state_required", "AUTHENTICATED"),
            },
            headers={"X-Blackdark-Auth-Boundary": "launch57-anonymous-denied"},
        )


@router.get("/api/launch57/tier-distribution")
async def launch57_tier_distribution():
    from launch57.tier_distribution import build_launch57_distribution_table, distribution_closure_report

    return {
        "closure": distribution_closure_report(),
        "rows": build_launch57_distribution_table(),
    }


@router.get("/api/launch57/guest-trust")
async def launch57_guest_trust(symbol: str = Query("BTC")):
    from launch57.trust_batch2 import guest_trust_surface

    return await guest_trust_surface(symbol=symbol, params={"symbol": symbol, "user_key": "anonymous"})


@router.get("/api/launch57/real-time-prices")
async def launch57_real_time_prices(symbol: str = Query("BTC")):
    """Launch #22 — floor-tier live/near-live price with freshness (not subscription pricing)."""
    from launch57.data_batch1 import real_time_prices

    return await real_time_prices(symbol=symbol, params={"symbol": symbol, "user_key": "anonymous"})


@router.get("/api/launch57/decision-certificate")
async def launch57_decision_certificate(
    request: Request,
    symbol: str = Query("BTC"),
    decision_action: str = Query("WAIT"),
    decision_sentence: str = Query(""),
    decision_time: str = Query(""),
):
    """Launch #3 — decision certificate + hash for Trust Pulse / proof surfaces."""
    _require_launch57_auth(request, 3)
    from launch57.trust_batch1 import decision_certificate_export

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    action = str(decision_action or "WAIT").upper()
    sentence = str(decision_sentence or "").strip() or f"{asset}: {action}"
    dt = str(decision_time or "").strip()
    params: dict[str, Any] = {
        "symbol": asset,
        "decision_action": action,
        "decision_sentence": sentence,
        "verdict": action,
        "oracle": sentence,
        "tier": "free",
    }
    if dt:
        params["decision_time"] = dt
        params["governed_payload"] = {"decision_time": dt}
    return await decision_certificate_export(symbol=asset, params=params)


@router.get("/api/launch57/public-accuracy")
async def launch57_public_accuracy(symbol: str = Query("BTC")):
    """Launch #4 — live public accuracy ledger sample (synthetic excluded from primary)."""
    from launch57.trust_batch1 import public_accuracy_ledger

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await public_accuracy_ledger(symbol=asset, params={"symbol": asset})


@router.post("/api/launch57/cost-autopsy")
async def launch57_cost_autopsy(request: Request, body: dict[str, Any] = Body(...)):
    """Launch #5 — net-edge / cost autopsy for the displayed opportunity (no elite tier gate)."""
    _require_launch57_auth(request, 5)
    from launch57.trust_batch1 import net_edge_truth_score

    asset = str(body.get("symbol") or "BTC").upper().replace("/USDT", "")
    opportunity = body.get("opportunity")
    if not isinstance(opportunity, dict):
        return {
            "launch_item_id": 5,
            "surface": "net_edge_truth_score",
            "symbol": asset,
            "success": False,
            "cost_claim_allowed": False,
            "error": "opportunity_required",
            "backend_entrypoint": "net_edge_truth_score",
        }
    return await net_edge_truth_score(symbol=asset, params={"symbol": asset, "opportunity": opportunity})


@router.get("/api/launch57/share-proof")
async def launch57_share_proof(
    request: Request,
    symbol: str = Query("BTC"),
    decision_action: str = Query("WAIT"),
    decision_sentence: str = Query(""),
):
    """Launch #44 — shareable decision card for Trust Pulse Share Proof (first-screen only)."""
    _require_launch57_auth(request, 44)
    from launch57.trust_batch2 import shareable_decision_card

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    action = str(decision_action or "WAIT").upper()
    sentence = str(decision_sentence or "").strip() or f"{asset}: {action} — governed Launch-57 oracle"
    return await shareable_decision_card(
        symbol=asset,
        params={
            "symbol": asset,
            "decision_action": action,
            "decision_sentence": sentence,
            "tier": "free",
        },
    )


@router.get("/api/launch57/command-home")
async def launch57_command_home(
    request: Request,
    symbol: str = Query("BTC"),
    command_view: bool = Query(True),
):
    _require_launch57_auth(request, 1)
    from i18n_service import resolve_request_lang
    from launch57.edge_ui_batch2 import six_heroes_command_home

    lang = resolve_request_lang(request)
    try:
        return await six_heroes_command_home(
            symbol=symbol,
            params={"symbol": symbol, "command_view": command_view, "lang": lang},
        )
    except RuntimeError as exc:
        if "kill_switch" in str(exc):
            raise HTTPException(
                status_code=503,
                detail={
                    "detail": "Launch-57 command home disabled",
                    "launch_item_id": 1,
                    "reason": str(exc),
                    "success": False,
                },
                headers={"X-Blackdark-Launch57-Kill-Switch": "edge-ui-batch2"},
            ) from exc
        raise


@router.get("/api/launch57/decision-history")
async def launch57_decision_history(
    request: Request,
    symbol: str = Query("BTC"),
    tier: str = Query("free"),
    limit: int = Query(10, ge=1, le=100),
):
    _require_launch57_auth(request, 49)
    from launch57.edge_ui_batch1 import personal_decision_history

    _require_launch57_tier(request, 49, tier=tier)
    return await personal_decision_history(symbol=symbol, params={"symbol": symbol, "tier": tier, "limit": limit})


@router.get("/api/launch57/net-edge")
async def launch57_net_edge(
    request: Request,
    symbol: str = Query("BTC"),
    tier: str = Query("elite"),
):
    _require_launch57_auth(request, 5)
    _require_launch57_tier(request, 5, tier=tier)
    from launch57.trust_batch1 import net_edge_truth_score

    return await net_edge_truth_score(symbol=symbol, params={"symbol": symbol, "tier": tier})


@router.get("/api/launch57/wallet-due-diligence")
async def launch57_wallet_dd(
    request: Request,
    symbol: str = Query("BTC"),
    address: str = Query(...),
    tier: str = Query("elite"),
):
    _require_launch57_auth(request, 53)
    _require_launch57_tier(request, 53, tier=tier)
    from launch57.smart_money_batch2 import instant_wallet_due_diligence

    return await instant_wallet_due_diligence(
        symbol=symbol,
        params={"symbol": symbol, "address": address, "tier": tier},
    )


@router.get("/api/launch57/token-due-diligence")
async def launch57_token_dd(
    request: Request,
    symbol: str = Query("BTC"),
    tier: str = Query("elite"),
):
    _require_launch57_auth(request, 54)
    _require_launch57_tier(request, 54, tier=tier)
    from launch57.smart_money_batch2 import instant_token_due_diligence

    return await instant_token_due_diligence(symbol=symbol, params={"symbol": symbol, "tier": tier})


@router.get("/api/launch57/spot-perp-arbitrage")
async def launch57_spot_perp_arbitrage(
    request: Request,
    symbol: str = Query("BTC"),
    tier: str = Query("quant"),
):
    _require_launch57_auth(request, 43)
    _require_launch57_tier(request, 43, tier=tier)
    from launch57.edge_ui_batch1 import spot_perp_arbitrage_scanner

    return await spot_perp_arbitrage_scanner(symbol=symbol, params={"symbol": symbol, "tier": tier})


@router.get("/api/launch57/suspicious-flags")
async def launch57_suspicious_flags(
    request: Request,
    symbol: str = Query("BTC"),
    tier: str = Query("quant"),
):
    _require_launch57_auth(request, 56)
    _require_launch57_tier(request, 56, tier=tier)
    from launch57.smart_money_batch3 import suspicious_activity_flags

    return await suspicious_activity_flags(symbol=symbol, params={"symbol": symbol, "tier": tier})


@router.get("/api/launch57/exchange-transparency")
async def launch57_exchange_transparency(
    request: Request,
    symbol: str = Query("BTC"),
    tier: str = Query("quant"),
):
    _require_launch57_auth(request, 57)
    _require_launch57_tier(request, 57, tier=tier)
    from launch57.smart_money_batch3 import exchange_transparency_risk_indicators

    return await exchange_transparency_risk_indicators(symbol=symbol, params={"symbol": symbol, "tier": tier})


@router.get("/api/launch57/ai-copilot")
async def launch57_ai_copilot(
    request: Request,
    symbol: str = Query("BTC"),
    tier: str = Query("elite"),
):
    _require_launch57_auth(request, 36)
    _require_launch57_tier(request, 36, tier=tier)
    from launch57.explanation_ai_batch1 import ai_research_agent_grounded

    return await ai_research_agent_grounded(symbol=symbol, params={"symbol": symbol, "tier": tier})


@router.get("/api/launch57/cross-market")
async def launch57_cross_market(
    request: Request,
    symbol: str = Query("BTC"),
    tier: str = Query("quant"),
):
    _require_launch57_auth(request, 37)
    _require_launch57_tier(request, 37, tier=tier)
    from launch57.decision_batch2 import cross_market_decision_engine

    return await cross_market_decision_engine(symbol=symbol, params={"symbol": symbol, "tier": tier})


@router.get("/api/launch57/discipline-mirror")
async def launch57_discipline_mirror(
    request: Request,
    user_key: str = Query("anonymous"),
    limit: int = Query(20, ge=1, le=100),
    tier: str = Query("pro"),
):
    _require_launch57_auth(request, 50)
    _require_launch57_tier(request, 50, tier=tier)
    from launch57.edge_ui_batch1 import discipline_mirror_light

    return await discipline_mirror_light(
        symbol="BTC",
        params={"user_key": user_key, "limit": limit, "tier": tier},
    )


@router.get("/api/launch57/capability-library")
async def launch57_capability_library(
    q: str | None = Query(None),
    area: str | None = Query(None),
    locale: str | None = Query(None),
    include_parked: bool = Query(False),
):
    from launch57.edge_ui_batch1 import capability_library_search

    return await capability_library_search(
        symbol="BTC",
        params={
            "query": q or "",
            "functional_area": area,
            "locale": locale,
            "include_parked": include_parked,
        },
    )


@router.get("/api/launch57/capability-library/compare")
async def launch57_capability_library_compare(compare: str = Query(..., description="Comma-separated launch numbers")):
    from launch57.edge_ui_batch1 import capability_library_compare

    return await capability_library_compare(symbol="BTC", params={"compare": compare})


@router.get("/api/launch57/capability-library/{launch_number}")
async def launch57_capability_library_detail(
    launch_number: int,
    user_key: str = Query("anonymous"),
):
    from launch57.edge_ui_batch1 import capability_library_detail

    return await capability_library_detail(
        symbol="BTC",
        params={"launch_number": launch_number, "user_key": user_key},
    )
