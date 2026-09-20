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


@router.get("/api/launch57/ohlcv")
async def launch57_ohlcv(
    symbol: str = Query("BTC"),
    interval: str = Query("1h"),
    limit: int = Query(100, ge=1, le=500),
):
    """Launch #23 — OHLCV bars for dashboard chart."""
    from launch57.data_batch1 import ohlcv

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await ohlcv(symbol=asset, params={"symbol": asset, "interval": interval, "limit": limit})


@router.get("/api/launch57/quote")
async def launch57_quote(symbol: str = Query("BTC")):
    """Launch #24 — quote + symbol metadata (distinct contracts)."""
    from launch57.data_batch1 import quote_data, symbol_metadata

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    quote = await quote_data(symbol=asset, params={"symbol": asset})
    metadata = await symbol_metadata(symbol=asset, params={"symbol": asset})
    return {
        "launch_item_id": 24,
        "surface": "quote_and_metadata",
        "symbol": asset,
        "success": bool(quote.get("success")) and bool(metadata.get("success")),
        "quote": quote,
        "metadata": metadata,
        "backend_module": "launch57.data_batch1",
        "backend_entrypoint": "quote_data+symbol_metadata",
    }


@router.get("/api/launch57/point-in-time-metrics")
async def launch57_point_in_time_metrics(
    symbol: str = Query("BTC"),
    price: float | None = Query(None),
):
    """Launch #39 — immutable point-in-time metrics snapshot."""
    from launch57.data_batch2 import point_in_time_immutable_metrics

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    metrics: dict[str, Any] = {"symbol": asset}
    if price is not None:
        metrics["price"] = price
    return await point_in_time_immutable_metrics(
        symbol=asset,
        params={"symbol": asset, "metrics": metrics, "source_authority": "launch57:consumer_path"},
    )


@router.get("/api/launch57/data-provenance")
async def launch57_data_provenance(symbol: str = Query("BTC")):
    """Launch #40 — user-visible data quality & provenance."""
    from launch57.data_batch2 import data_quality_provenance_layer
    from launch57.temporal_common import to_rfc3339, utc_now

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await data_quality_provenance_layer(
        symbol=asset,
        params={
            "symbol": asset,
            "source_authority": "launch57:consumer_path",
            "source_time": to_rfc3339(utc_now()),
            "quality_state": "decision_grade",
        },
    )


@router.get("/api/launch57/freshness")
async def launch57_freshness(
    symbol: str = Query("BTC"),
    quote_age_ms: float | None = Query(None),
    quote_fresh: bool | None = Query(None),
):
    """Launch #41 — freshness assurance (fail-closed; STALE never presented as LIVE)."""
    from launch57.data_batch2 import freshness_update_assurance

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    params: dict[str, Any] = {"symbol": asset}
    if quote_age_ms is not None:
        params["quote_age_ms"] = quote_age_ms
    if quote_fresh is not None:
        params["quote_fresh"] = quote_fresh
    return await freshness_update_assurance(symbol=asset, params=params)


@router.get("/api/launch57/unified-exchange")
async def launch57_unified_exchange(symbol: str = Query("BTC")):
    """Launch #42 — unified exchange connector routing."""
    from launch57.data_batch1 import unified_exchange_connector

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await unified_exchange_connector(symbol=asset, params={"symbol": asset})


@router.get("/api/launch57/market-regime")
async def launch57_market_regime(request: Request, symbol: str = Query("BTC")):
    """Launch #7 — Market Regime / Compass."""
    _require_launch57_auth(request, 7)
    from launch57.decision_batch1 import market_regime_compass

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await market_regime_compass(symbol=asset, params={"symbol": asset})


@router.get("/api/launch57/beginner-mode")
async def launch57_beginner_mode(
    request: Request,
    symbol: str = Query("BTC"),
    verdict: str = Query("Neutral"),
    risk_score: float = Query(5.0),
):
    """Launch #8 — Beginner Decision Mode."""
    _require_launch57_auth(request, 8)
    from launch57.decision_batch1 import beginner_decision_mode

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await beginner_decision_mode(
        symbol=asset,
        params={"symbol": asset, "verdict": verdict, "risk_score": risk_score},
    )


@router.get("/api/launch57/cross-signal-confirmation")
async def launch57_cross_signal_confirmation(request: Request, symbol: str = Query("BTC")):
    """Launch #9 — Cross-Signal Confirmation."""
    _require_launch57_auth(request, 9)
    from launch57.decision_batch1 import cross_signal_confirmation

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await cross_signal_confirmation(symbol=asset, params={"symbol": asset})


@router.get("/api/launch57/contradiction-detection")
async def launch57_contradiction_detection(request: Request, symbol: str = Query("BTC")):
    """Launch #10 — Contradiction Detection."""
    _require_launch57_auth(request, 10)
    from launch57.decision_batch1 import contradiction_detection

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await contradiction_detection(symbol=asset, params={"symbol": asset})


@router.get("/api/launch57/actionability-score")
async def launch57_actionability_score(request: Request, symbol: str = Query("BTC")):
    """Launch #11 — Smart Money Actionability Score."""
    _require_launch57_auth(request, 11)
    from launch57.decision_batch1 import smart_money_actionability_score

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await smart_money_actionability_score(symbol=asset, params={"symbol": asset})


@router.get("/api/launch57/conviction-engine")
async def launch57_conviction_engine(
    request: Request,
    symbol: str = Query("BTC"),
    opportunity_level: float = Query(7.5),
):
    """Launch #12 — Smart Money Conviction Engine."""
    _require_launch57_auth(request, 12)
    from launch57.decision_batch2 import smart_money_conviction_engine

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await smart_money_conviction_engine(
        symbol=asset,
        params={"symbol": asset, "opportunity_level": opportunity_level},
    )


@router.get("/api/launch57/risk-disclosure")
async def launch57_risk_disclosure(
    request: Request,
    symbol: str = Query("BTC"),
    decision_action: str = Query("WAIT"),
    decision_truth_state: str = Query("UNAVAILABLE"),
):
    """Launch #47 — one-click risk disclosure on visible decision."""
    _require_launch57_auth(request, 47)
    from launch57.trust_batch2 import one_click_risk_disclosure

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    action = str(decision_action or "WAIT").upper()
    return await one_click_risk_disclosure(
        symbol=asset,
        params={
            "symbol": asset,
            "decision_action": action,
            "decision_truth_state": decision_truth_state,
        },
    )


@router.get("/api/launch57/abstain-reasons")
async def launch57_abstain_reasons(
    request: Request,
    symbol: str = Query("BTC"),
    decision_action: str = Query("WAIT"),
    decision_truth_state: str = Query("ABSTAINED"),
):
    """Launch #48 — abstain/reject reasons visible (WAIT/ABSTAIN — no judgment without reason)."""
    _require_launch57_auth(request, 48)
    from launch57.trust_batch2 import abstain_reject_reasons_visible

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    action = str(decision_action or "WAIT").upper()
    return await abstain_reject_reasons_visible(
        symbol=asset,
        params={
            "symbol": asset,
            "decision_action": action,
            "decision_truth_state": decision_truth_state,
        },
    )


@router.get("/api/launch57/accumulation-distribution")
async def launch57_accumulation_distribution(
    request: Request,
    symbol: str = Query("BTC"),
    limit: int = Query(10, ge=1, le=50),
):
    """Launch #13 — Accumulation / Distribution Detection."""
    _require_launch57_auth(request, 13)
    from launch57.smart_money_batch1 import accumulation_distribution_detection

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await accumulation_distribution_detection(
        symbol=asset,
        params={"symbol": asset, "limit": limit},
    )


@router.get("/api/launch57/token-screener")
async def launch57_token_screener(
    request: Request,
    symbol: str = Query("BTC"),
    limit: int = Query(25, ge=1, le=100),
):
    """Launch #14 — Smart Money Token Screener."""
    _require_launch57_auth(request, 14)
    from launch57.smart_money_batch1 import smart_money_token_screener

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await smart_money_token_screener(
        symbol=asset,
        params={"symbol": asset, "limit": limit},
    )


@router.get("/api/launch57/entity-wallet")
async def launch57_entity_wallet(
    request: Request,
    symbol: str = Query("BTC"),
    address: str = Query("0x0000000000000000000000000000000000000000"),
    chain: str = Query("ethereum"),
):
    """Launch #15 — Entity-Aware Wallet Intelligence."""
    _require_launch57_auth(request, 15)
    from launch57.smart_money_batch2 import entity_aware_wallet_intelligence

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await entity_aware_wallet_intelligence(
        symbol=asset,
        params={"symbol": asset, "address": address, "chain": chain},
    )


@router.get("/api/launch57/exchange-flow")
async def launch57_exchange_flow(request: Request, symbol: str = Query("BTC")):
    """Launch #16 — Exchange Flow Intelligence (in/out/net)."""
    _require_launch57_auth(request, 16)
    from launch57.smart_money_batch1 import exchange_flow_intelligence

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await exchange_flow_intelligence(symbol=asset, params={"symbol": asset})


@router.get("/api/launch57/whale-ratio-filter")
async def launch57_whale_ratio_filter(request: Request, symbol: str = Query("BTC")):
    """Launch #17 — Exchange Whale Ratio + internal-flow filter."""
    _require_launch57_auth(request, 17)
    from launch57.smart_money_batch1 import exchange_whale_ratio, internal_flow_filter

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    ratio = await exchange_whale_ratio(symbol=asset, params={"symbol": asset})
    flow_filter = await internal_flow_filter(symbol=asset, params={"symbol": asset})
    return {
        "launch_item_id": 17,
        "symbol": asset,
        "success": bool(ratio.get("success")) or bool(flow_filter.get("success")),
        "exchange_whale_ratio": ratio,
        "internal_flow_filter": flow_filter,
        "backend_module": "launch57.smart_money_batch1",
        "backend_entrypoint": "exchange_whale_ratio+internal_flow_filter",
    }


@router.get("/api/launch57/whale-alerts")
async def launch57_whale_alerts(
    request: Request,
    symbol: str = Query("BTC"),
    limit: int = Query(20, ge=1, le=50),
):
    """Launch #18 — Whale Accumulation / Movement Alerts."""
    _require_launch57_auth(request, 18)
    from launch57.smart_money_batch2 import whale_accumulation_distribution_intelligence

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await whale_accumulation_distribution_intelligence(
        symbol=asset,
        params={"symbol": asset, "limit": limit},
    )


@router.get("/api/launch57/inter-entity-flow")
async def launch57_inter_entity_flow(request: Request, symbol: str = Query("BTC")):
    """Launch #19 — Inter-Entity Flow (limited launch)."""
    _require_launch57_auth(request, 19)
    from launch57.smart_money_batch2 import inter_entity_flow_intelligence

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await inter_entity_flow_intelligence(symbol=asset, params={"symbol": asset})


@router.get("/api/launch57/address-labels")
async def launch57_address_labels(
    request: Request,
    symbol: str = Query("BTC"),
    address: str = Query("0x0000000000000000000000000000000000000000"),
):
    """Launch #20 — Address Labels & Cohorts (limited nucleus)."""
    _require_launch57_auth(request, 20)
    from launch57.smart_money_batch1 import address_labels_cohorts

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await address_labels_cohorts(
        symbol=asset,
        params={"symbol": asset, "address": address},
    )


@router.get("/api/launch57/futures-oi")
async def launch57_futures_oi(request: Request, symbol: str = Query("BTC")):
    """Launch #25 — Futures OI intelligence."""
    _require_launch57_auth(request, 25)
    from launch57.derivatives_batch1 import futures_open_interest_intelligence

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await futures_open_interest_intelligence(symbol=asset, params={"symbol": asset})


@router.get("/api/launch57/funding-rate")
async def launch57_funding_rate(request: Request, symbol: str = Query("BTC")):
    """Launch #26 — Funding rate intelligence."""
    _require_launch57_auth(request, 26)
    from launch57.derivatives_batch1 import funding_rate_intelligence

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await funding_rate_intelligence(symbol=asset, params={"symbol": asset})


@router.get("/api/launch57/liquidation-intelligence")
async def launch57_liquidation_intelligence(request: Request, symbol: str = Query("BTC")):
    """Launch #27 — Liquidation intelligence / light heatmap."""
    _require_launch57_auth(request, 27)
    from launch57.derivatives_batch1 import liquidation_intelligence_light

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await liquidation_intelligence_light(symbol=asset, params={"symbol": asset})


@router.get("/api/launch57/taker-leverage")
async def launch57_taker_leverage(request: Request, symbol: str = Query("BTC")):
    """Launch #28 — Taker buy/sell + leverage ratio."""
    _require_launch57_auth(request, 28)
    from launch57.derivatives_batch1 import estimated_leverage_ratio, taker_buy_sell_pressure

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    taker = await taker_buy_sell_pressure(symbol=asset, params={"symbol": asset})
    leverage = await estimated_leverage_ratio(symbol=asset, params={"symbol": asset})
    return {
        "launch_item_id": 28,
        "symbol": asset,
        "success": bool(taker.get("success")) or bool(leverage.get("success")),
        "taker_buy_sell_pressure": taker,
        "estimated_leverage_ratio": leverage,
        "backend_module": "launch57.derivatives_batch1",
        "backend_entrypoint": "taker_buy_sell_pressure+estimated_leverage_ratio",
    }


@router.get("/api/launch57/derivatives-sentiment")
async def launch57_derivatives_sentiment(request: Request, symbol: str = Query("BTC")):
    """Launch #29 — Derivatives sentiment composite."""
    _require_launch57_auth(request, 29)
    from launch57.derivatives_batch1 import derivatives_sentiment_composite

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await derivatives_sentiment_composite(symbol=asset, params={"symbol": asset})


@router.get("/api/launch57/order-book")
async def launch57_order_book(request: Request, symbol: str = Query("BTC")):
    """Launch #30 — Order book intelligence (L1 minimum)."""
    _require_launch57_auth(request, 30)
    from launch57.derivatives_batch2 import order_book_intelligence

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await order_book_intelligence(symbol=asset, params={"symbol": asset})


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

    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    return await spot_perp_arbitrage_scanner(symbol=asset, params={"symbol": asset, "tier": tier})


@router.post("/api/launch57/spot-perp-arbitrage")
async def launch57_spot_perp_arbitrage_post(request: Request, body: dict[str, Any] = Body(...)):
    """Launch #43 — spot–perp arbitrage with mandatory Net-Edge (#5) for dashboard consumer."""
    _require_launch57_auth(request, 43)
    tier = str(body.get("tier") or "quant")
    _require_launch57_tier(request, 43, tier=tier)
    from launch57.edge_ui_batch1 import spot_perp_arbitrage_scanner

    asset = str(body.get("symbol") or "BTC").upper().replace("/USDT", "")
    params: dict[str, Any] = {"symbol": asset, "tier": tier}
    if body.get("cost_claim") is not None:
        params["cost_claim"] = bool(body.get("cost_claim"))
    opportunity = body.get("opportunity")
    if isinstance(opportunity, dict):
        params["opportunity"] = opportunity
    if body.get("quote_amount") is not None:
        params["quote_amount"] = body.get("quote_amount")
    if body.get("limit") is not None:
        params["limit"] = body.get("limit")
    return await spot_perp_arbitrage_scanner(symbol=asset, params=params)


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
