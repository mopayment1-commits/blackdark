"""Platform API router — all 40 roadmap endpoints."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request

from security_auth import require_admin, require_authenticated

from api.openapi_responses import COMMON_ERROR_RESPONSES

router = APIRouter(prefix="/api/platform", tags=["platform"], responses=COMMON_ERROR_RESPONSES)


def _local_or_admin(request: Request, x_admin_key: str | None = None) -> None:
    """Fail-closed key save — admin API key only (never trust proxy peer/loopback)."""
    from security_auth import verify_admin_key

    _ = request
    if verify_admin_key(x_admin_key):
        return
    raise HTTPException(status_code=403, detail="Admin authentication required to save API keys")


def _force_safe_dry_run(requested: Any) -> bool:
    """Live execute via HTTP only when explicitly allowed for admins."""
    if requested is None:
        return True
    want_live = not bool(requested)
    if not want_live:
        return True
    allow = os.getenv("LIVE_EXECUTION_ALLOW_API", "false").lower() in {"1", "true", "yes"}
    if not allow:
        raise HTTPException(
            status_code=403,
            detail="Live execution via API disabled. Set LIVE_EXECUTION_ALLOW_API=true for admin live orders.",
        )
    return False


@router.get("/keys/status")
async def platform_keys_status(_admin: dict = Depends(require_admin)):
    from bd_platform.key_manager import keys_status

    return keys_status()


@router.get("/keys/verify")
async def platform_keys_verify(_admin: dict = Depends(require_admin)):
    from bd_platform.key_manager import verify_all_keys

    return await verify_all_keys()


@router.post("/keys/save", responses=COMMON_ERROR_RESPONSES)
async def platform_keys_save(
    request: Request,
    body: dict[str, str] = Body(...),
    x_admin_key: str | None = Header(None, alias="X-Admin-Key"),
):
    from bd_platform.key_manager import save_platform_keys

    _local_or_admin(request, x_admin_key)
    verify = str(body.pop("verify", "true")).lower() not in {"0", "false", "no"}
    return await save_platform_keys(body, verify=verify)


@router.get("/features")
async def platform_features():
    from bd_platform.completion import completion_summary

    return completion_summary()


@router.get("/completion")
async def platform_completion():
    from bd_platform.completion import completion_summary

    return completion_summary()


@router.get("/ml/explain")
async def ml_explain(asset: str = Query("BTC")):
    from bd_platform.trulens_eval import explain_prediction

    return await explain_prediction(asset)


@router.get("/coverage")
async def platform_coverage():
    from bd_platform.coverage_report import coverage_report

    return coverage_report()


@router.get("/derivatives/overview")
async def derivatives_overview(asset: str = Query("BTC")):
    from bd_platform.derivatives_hub import derivatives_overview as _fn

    return await _fn(asset)


@router.get("/derivatives/cex-dex-compare")
async def cex_dex_deriv_compare(asset: str = Query("BTC")):
    from bd_platform.derivatives_hub import cex_dex_derivatives_compare

    return await cex_dex_derivatives_compare(asset)


@router.get("/arb/cex-dex")
async def cex_dex_arb(quote_usd: float = Query(1000)):
    from bd_platform.cex_dex_arbitrage import scan_cex_dex_opportunities

    return await scan_cex_dex_opportunities(quote_usd=quote_usd)


@router.get("/arb/cex-dex/status")
async def cex_dex_status_route():
    from bd_platform.cex_dex_executor import cex_dex_status

    return cex_dex_status()


@router.post("/arb/cex-dex/execute", responses=COMMON_ERROR_RESPONSES)
async def cex_dex_execute(
    body: dict[str, Any] = Body(default_factory=dict),
    _admin: dict = Depends(require_admin),
):
    from bd_platform.cex_dex_arbitrage import scan_cex_dex_opportunities
    from bd_platform.cex_dex_executor import execute_cex_dex_opportunity, run_cex_dex_cycle

    dry_run = _force_safe_dry_run(body.get("dry_run"))

    if body.get("cycle"):
        return await run_cex_dex_cycle(
            quote_usd=float(body.get("quote_usd") or 1000),
            dry_run=dry_run,
        )

    opp = body.get("opportunity")
    if not opp:
        scan = await scan_cex_dex_opportunities(quote_usd=float(body.get("quote_usd") or 1000))
        opps = [o for o in scan.get("opportunities") or [] if o.get("profitable")]
        if not opps:
            return {"success": False, "reason": "no_profitable_opportunity", "scan": scan}
        opp = opps[0]

    return await execute_cex_dex_opportunity(opp, dry_run=dry_run)


@router.get("/liquidations/radar")
async def liq_radar(asset: str = Query("BTC")):
    from bd_platform.liquidation_radar import liquidation_radar

    return await liquidation_radar(asset)


@router.get("/agent/telegram")
async def telegram_agent(text: str = Query("What is BTC oracle accuracy?")):
    from bd_platform.telegram_agent import handle_agent_message

    return await handle_agent_message(text)


@router.get("/proof/public")
async def public_proof(tx_id: str | None = Query(None), seq: int | None = Query(None)):
    from bd_platform.public_proof import build_public_proof

    return build_public_proof(tx_id=tx_id, seq=seq)


@router.get("/proof/inclusion")
async def proof_inclusion(seq: int = Query(..., ge=1)):
    from bd_platform.public_proof import merkle_inclusion_proof

    return merkle_inclusion_proof(seq)


@router.post("/proof/verify-inclusion")
async def proof_verify_inclusion(body: dict[str, Any] = Body(...)):
    from bd_platform.public_proof import verify_merkle_inclusion

    return verify_merkle_inclusion(body)


@router.post("/proof/commit")
async def proof_commit(body: dict[str, Any] = Body(...)):
    from bd_platform.public_proof import commit_record

    record = body.get("record") or body
    salt = body.get("salt")
    return commit_record(record if isinstance(record, dict) else {"data": record}, salt=salt)


@router.post("/proof/verify-commitment")
async def proof_verify_commitment(body: dict[str, Any] = Body(...)):
    from bd_platform.public_proof import verify_commitment

    return verify_commitment(body.get("record") or {}, str(body.get("salt") or ""), str(body.get("commitment") or ""))


@router.get("/market/rankings")
async def market_rankings(limit: int = Query(100, le=250)):
    from bd_platform.market_rankings import market_rankings as _fn

    return await _fn(limit=limit)


@router.get("/market/coin/{coin_id}")
async def market_coin_detail(coin_id: str):
    from bd_platform.market_rankings import coin_detail

    return await coin_detail(coin_id)


@router.get("/onchain/pairs")
async def onchain_pairs(q: str = Query("BTC")):
    from bd_platform.onchain_hub import dexscreener_pairs

    return await dexscreener_pairs(q)


@router.get("/unlocks/calendar")
async def unlocks_calendar(limit: int = Query(30)):
    from bd_platform.token_unlocks import unlock_calendar

    return await unlock_calendar(limit=limit)


@router.get("/social/lunarcrush")
async def lunarcrush(symbol: str = Query("BTC")):
    from bd_platform.onchain_hub import lunarcrush_metrics

    return await lunarcrush_metrics(symbol)


@router.get("/events/calendar")
async def events_calendar():
    from bd_platform.onchain_hub import coinmarketcal_events

    return await coinmarketcal_events()


@router.get("/wallet/debank")
async def wallet_debank(address: str = Query(..., min_length=10)):
    from bd_platform.onchain_hub import debank_wallet

    return await debank_wallet(address)


@router.get("/wallet/clusters")
async def wallet_clusters(address: str = Query(..., min_length=10)):
    from bd_platform.onchain_hub import wallet_clusters as _fn

    return await _fn(address)


@router.get("/defi/geckoterminal")
async def gecko_terminal(network: str = Query("eth")):
    from bd_platform.onchain_hub import geckoterminal_pairs

    return await geckoterminal_pairs(network=network)


@router.get("/charts/config")
async def charts_config(symbol: str = Query("BTCUSDT")):
    from bd_platform.tradingview_bridge import chart_config

    return chart_config(symbol)


@router.get("/analytics/footprint")
async def footprint(asset: str = Query("BTC")):
    from bd_platform.footprint_analytics import footprint_snapshot

    return await footprint_snapshot(asset)


@router.get("/wallet/scopescan")
async def scopescan(address: str = Query(..., min_length=10)):
    from bd_platform.onchain_hub import scopescan_labels

    return await scopescan_labels(address)


@router.get("/whale/narrative")
async def whale_narrative(limit: int = Query(5)):
    from bd_platform.whale_story import whale_narrative as _fn

    return await _fn(limit)


@router.get("/news/coindesk")
async def news_coindesk(limit: int = Query(10)):
    from bd_platform.news_classifier import coindesk_feed

    return await coindesk_feed(limit)


@router.get("/defi/raises")
async def defi_raises():
    from bd_platform.onchain_hub import defillama_raises

    return await defillama_raises()


@router.get("/macro/bitcoin")
async def macro_btc():
    from bd_platform.onchain_hub import lookintobitcoin_macro

    return await lookintobitcoin_macro()


@router.get("/news/classify")
async def news_classify(limit: int = Query(20)):
    from bd_platform.news_classifier import classify_headlines

    return await classify_headlines(limit)


@router.get("/l2/security")
async def l2_security():
    from bd_platform.onchain_hub import l2beat_security

    return await l2beat_security()


@router.get("/flows/cross-chain")
async def cross_chain_flows():
    from bd_platform.onchain_hub import blockpour_flows

    return await blockpour_flows()


@router.get("/analytics/intotheblock")
async def itb_metrics(asset: str = Query("BTC")):
    from bd_platform.onchain_hub import intotheblock_metrics

    return await intotheblock_metrics(asset)


@router.get("/bots/grid")
async def grid_list():
    from bd_platform.grid_bot import list_grids

    return list_grids()


@router.post("/bots/grid")
async def grid_create(
    body: dict[str, Any] = Body(...),
    _user: dict = Depends(require_authenticated),
):
    from bd_platform.grid_bot import create_grid

    if body.get("lower_price") is None or body.get("upper_price") is None:
        raise HTTPException(
            status_code=422,
            detail="lower_price and upper_price are required for paper grid bots",
        )
    try:
        lower = float(body["lower_price"])
        upper = float(body["upper_price"])
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="lower_price/upper_price must be numeric") from exc
    if lower <= 0 or upper <= lower:
        raise HTTPException(status_code=422, detail="require 0 < lower_price < upper_price")

    return create_grid(
        asset=str(body.get("asset") or "BTC"),
        lower_price=lower,
        upper_price=upper,
        grids=int(body.get("grids") or body.get("grid_count") or 10),
        quote_usd=float(body.get("quote_usd") or 1000),
    )


@router.get("/marketplace/strategies")
async def marketplace_list():
    from bd_platform.strategy_marketplace import list_strategies

    return list_strategies()


@router.post("/marketplace/strategies")
async def marketplace_publish(
    body: dict[str, Any] = Body(...),
    _user: dict = Depends(require_authenticated),
):
    from bd_platform.strategy_marketplace import publish_strategy

    return publish_strategy(
        str(body.get("name") or "Untitled"),
        str(body.get("kind") or "custom"),
        tier=str(body.get("tier") or "community"),
    )


@router.post("/scripts/run")
async def run_script(
    body: dict[str, Any] = Body(...),
    _user: dict = Depends(require_authenticated),
):
    from bd_platform.script_sandbox import run_script as _run

    return _run(str(body.get("expression") or "price > 0"), variables=body.get("variables"))


@router.get("/rules")
async def rules_list():
    from bd_platform.ifttt_rules import list_rules

    return list_rules()


@router.post("/rules")
async def rules_create(
    body: dict[str, Any] = Body(...),
    _user: dict = Depends(require_authenticated),
):
    from bd_platform.ifttt_rules import create_rule

    return create_rule(if_condition=str(body["if"]), then_action=str(body["then"]))


@router.post("/rules/evaluate")
async def rules_evaluate(_user: dict = Depends(require_authenticated)):
    from bd_platform.ifttt_rules import evaluate_rules

    return await evaluate_rules()


@router.post("/portfolio/rebalance")
async def portfolio_rebalance(
    body: dict[str, Any] = Body(...),
    _user: dict = Depends(require_authenticated),
):
    from bd_platform.portfolio_rebalancer import suggest_rebalance

    return suggest_rebalance(
        body.get("holdings") or {},
        target_weights=body.get("target_weights"),
    )


@router.get("/tradingview/config")
async def tv_config(symbol: str = Query("BTCUSDT")):
    from bd_platform.tradingview_bridge import chart_config

    return chart_config(symbol)


@router.post("/tradingview/webhook", responses=COMMON_ERROR_RESPONSES)
async def tv_webhook(request: Request, payload: dict[str, Any] = Body(...)):
    import hmac

    from bd_platform.tradingview_bridge import handle_webhook
    from security_auth import is_production_env

    expected = os.getenv("TRADINGVIEW_WEBHOOK_SECRET", "").strip()
    sig = (request.headers.get("X-TradingView-Signature") or "").strip()
    if not expected:
        if is_production_env():
            raise HTTPException(
                status_code=503,
                detail="TRADINGVIEW_WEBHOOK_SECRET required in production",
            )
    elif not (sig and hmac.compare_digest(sig, expected)):
        raise HTTPException(status_code=401, detail="Invalid TradingView webhook signature")
    # Always dry-run unless admin live flag is on — bridge itself defaults dry-run.
    return await handle_webhook(payload, signature=sig or None)


@router.get("/risk/drawdown")
async def drawdown_status():
    from bd_platform.drawdown_guard import drawdown_status as _fn

    return _fn()


@router.post("/risk/drawdown")
async def drawdown_update(body: dict[str, Any] = Body(...), _admin: dict = Depends(require_admin)):
    from bd_platform.drawdown_guard import update_equity

    return update_equity(float(body.get("equity_usd") or 0))


@router.get("/nlp/finbert")
async def finbert_analyze(q: str = Query(..., min_length=3)):
    from bd_platform.finbert_sentiment import analyze_text

    return analyze_text(q)


@router.get("/stream/sse")
async def platform_sse(request: Request):
    from fastapi.responses import StreamingResponse

    from bd_platform.sse_stream import sse_event_generator

    interval = float(request.query_params.get("interval", "5"))
    return StreamingResponse(
        sse_event_generator(interval_sec=max(2.0, interval)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/bus/status")
async def bus_status():
    from bd_platform.kafka_bridge import bus_status as _fn

    return _fn()


@router.get("/vault/status")
async def vault_status():
    from bd_platform.vault_client import vault_status as _fn

    return _fn()


@router.post("/vault/store", responses=COMMON_ERROR_RESPONSES)
async def vault_store(body: dict[str, Any] = Body(...), _admin: dict = Depends(require_admin)):
    from bd_platform.vault_client import store_secret

    key = str(body.get("key") or "")
    value = str(body.get("value") or "")
    if not key or not value:
        raise HTTPException(status_code=400, detail="key and value required")
    return store_secret(key, value)


@router.get("/vault/read")
async def vault_read(key: str = Query(...), _admin: dict = Depends(require_admin)):
    from bd_platform.vault_client import read_secret

    return read_secret(key)


@router.get("/arb/pairs")
async def pairs_trading_scan():
    from bd_platform.pairs_trading import scan_pairs

    return await scan_pairs()


@router.get("/onchain/advanced")
async def onchain_advanced(asset: str = Query("BTC")):
    from bd_platform.onchain_advanced import compute_advanced_metrics

    return await compute_advanced_metrics(asset)


@router.get("/ml/rl", responses=COMMON_ERROR_RESPONSES)
async def rl_policy(features: str = Query(""), train: bool = Query(False)):
    from ml.rl_policy import policy_status, predict_action

    if train:
        raise HTTPException(
            status_code=403,
            detail="Use POST /api/platform/ml/rl/train with admin auth to train RL policy",
        )

    feats: dict[str, float] = {}
    if features:
        for part in features.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                try:
                    feats[k.strip()] = float(v.strip())
                except ValueError:
                    pass
    return {"status": policy_status(), "prediction": predict_action(feats or None)}


@router.post("/ml/rl/train")
async def rl_policy_train(_admin: dict = Depends(require_admin)):
    import random

    from ml.rl_policy import policy_status, train_ppo_policy

    samples = [
        (
            {
                "ret_24h": random.uniform(-0.05, 0.05),
                "volatility": random.uniform(0.02, 0.1),
                "obi_score": random.uniform(-1, 1),
                "sentiment_score": random.uniform(-1, 1),
            },
            random.uniform(-1, 1),
        )
        for _ in range(100)
    ]
    trained = train_ppo_policy(samples, epochs=30)
    return {"status": policy_status(), "trained": trained}


@router.get("/intelligence-ledger/pattern-recognition/status")
async def pattern_recognition_status_route():
    """#281 Order Book Pattern Recognition Engine — renamed, no financial claims."""
    from bd_platform.order_book_pattern_recognition import pattern_recognition_status

    return pattern_recognition_status()


@router.get("/intelligence-ledger/pattern-recognition")
async def pattern_recognition_panel_route(asset: str = Query("BTC")):
    """#281 historical pattern match — NOT trading signals."""
    from bd_platform.order_book_pattern_recognition import build_pattern_recognition_panel

    return build_pattern_recognition_panel(asset)


@router.get("/intelligence-ledger/flow-anomaly/status")
async def flow_anomaly_detection_status_route():
    """#282 Flow Anomaly Detection — rule-based, Intelligence Ledger."""
    from bd_platform.flow_anomaly_detection import flow_anomaly_detection_status

    return flow_anomaly_detection_status()


@router.get("/intelligence-ledger/flow-anomaly")
async def flow_anomaly_panel_route(asset: str = Query("BTC")):
    """#282 orderflow anomaly panel with baseline controls."""
    from bd_platform.flow_anomaly_detection import build_flow_anomaly_panel

    return build_flow_anomaly_panel(asset)


@router.get("/intelligence-ledger/flow-anomaly/alerts")
async def flow_anomaly_alerts_route(
    asset: str | None = Query(None),
    venue: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """#282 anomaly alerts with evidence schema."""
    from bd_platform.flow_anomaly_detection import list_anomaly_alerts

    return list_anomaly_alerts(asset=asset, venue=venue, limit=limit)


@router.get("/price-feed/status")
async def price_feed_layer_status_route():
    """#283 Price Feed Layer — Sprint 0 infrastructure, not standalone."""
    from bd_platform.price_feed_layer import price_feed_layer_status

    return price_feed_layer_status()


@router.get("/price-feed/live")
async def price_feed_live_route(asset: str = Query("BTC")):
    """#283 live prices with latency/freshness on every quote."""
    from bd_platform.price_feed_layer import get_live_prices

    return get_live_prices(asset)


@router.get("/price-feed/tiered-streaming/status")
async def tiered_price_streaming_status_route():
    """#128 Tiered Price Streaming — sub-second enterprise tier only."""
    from bd_platform.tiered_price_streaming import tiered_price_streaming_status

    return tiered_price_streaming_status()


@router.get("/price-feed/tiered-streaming")
async def tiered_price_streaming_panel_route(
    tier: str = Query("free"),
    asset: str = Query("BTC"),
    requested_interval_ms: int | None = Query(None),
):
    from bd_platform.tiered_price_streaming import build_tiered_streaming_panel

    result = build_tiered_streaming_panel(
        tier=tier,
        asset=asset,
        requested_interval_ms=requested_interval_ms,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=403, detail=result.get("access") or result.get("error"))
    return result


@router.get("/price-feed/tiered-streaming/sla-tests")
async def tiered_price_streaming_sla_tests_route():
    from bd_platform.tiered_price_streaming import run_tier_sla_tests

    return run_tier_sla_tests()


@router.get("/intelligence-ledger/evidence-confidence/status")
async def evidence_confidence_status_route():
    """#284 Evidence Confidence Framework — cross-cutting, Sprint 2."""
    from bd_platform.evidence_confidence import evidence_confidence_status

    return evidence_confidence_status()


@router.get("/intelligence-ledger/evidence-confidence")
async def evidence_confidence_assessment_route(assessment_id: str = Query(...)):
    """#284 confidence score + evidence breakdown — not profit probability."""
    from bd_platform.evidence_confidence import build_confidence_assessment

    result = build_confidence_assessment(assessment_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/epistemic-output/status")
async def epistemic_output_framework_status_route():
    """#316 Epistemic Output Framework — cross-cutting design principle, Sprint 2."""
    from bd_platform.epistemic_output_framework import epistemic_output_framework_status

    return epistemic_output_framework_status()


@router.get("/intelligence-ledger/epistemic-output")
async def epistemic_output_panel_route(panel_id: str = Query("btc_macro_synthesis")):
    """#316 cross-domain analysis — Fact/Inference/Hypothesis separated, fully traceable."""
    from bd_platform.epistemic_output_framework import build_cross_domain_panel

    result = build_cross_domain_panel(panel_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.post("/intelligence-ledger/epistemic-output/wrap")
async def epistemic_output_wrap_route(
    analysis_summary: str = Body(...),
    epistemic_items: list[dict[str, Any]] = Body(...),
    domains: list[str] = Body(default_factory=list),
    title: str | None = Body(None),
):
    """#316 wrap any intelligence output in epistemic envelope — no Decision language."""
    from bd_platform.epistemic_output_framework import wrap_intelligence_output

    return wrap_intelligence_output(
        analysis_summary=analysis_summary,
        epistemic_items=epistemic_items,
        domains=domains,
        title=title,
    )


@router.get("/intelligence-ledger/sector-rotation/status")
async def sector_rotation_status_route():
    """#286 Sector Rotation & Flow Module — versioned universe, survivorship controlled."""
    from bd_platform.sector_rotation import sector_rotation_status

    return sector_rotation_status()


@router.get("/intelligence-ledger/sector-rotation")
async def sector_rotation_panel_route():
    """#286 rotation matrix + leaderboard."""
    from bd_platform.sector_rotation import build_sector_rotation_panel

    return build_sector_rotation_panel()


@router.get("/intelligence-ledger/community-pulse/status")
async def community_pulse_status_route():
    """#272+#287+#290+#292 Community Pulse — purchased feed, no NLP team."""
    from bd_platform.community_pulse import community_pulse_status

    return community_pulse_status()


@router.get("/intelligence-ledger/community-pulse")
async def community_pulse_panel_route(asset: str = Query("BTC")):
    """#287 NLP sentiment merged into #272 cluster — not standalone."""
    from bd_platform.community_pulse import build_community_pulse_panel

    result = build_community_pulse_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/alert-engine/status")
async def alert_engine_status_route():
    """#289 Alert Engine — renamed from Smart Alerts, rule-based first."""
    from bd_platform.alert_engine import alert_engine_status

    return alert_engine_status()


@router.get("/intelligence-ledger/alert-engine")
async def alert_engine_panel_route():
    """#289 rule evaluation + delivery panel."""
    from bd_platform.alert_engine import build_alert_engine_panel

    return build_alert_engine_panel()


@router.get("/intelligence-ledger/alert-engine/rules")
async def alert_engine_rules_route(
    alert_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    from bd_platform.alert_engine import list_alert_rules

    return list_alert_rules(alert_type=alert_type, limit=limit)


@router.get("/intelligence-ledger/alert-engine/delivery-logs")
async def alert_engine_delivery_logs_route(limit: int = Query(50, ge=1, le=200)):
    from bd_platform.alert_engine import list_delivery_logs

    return list_delivery_logs(limit=limit)


@router.get("/intelligence-ledger/alert-engine/derivatives-rules")
async def alert_engine_derivatives_rules_route(
    asset: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """#323 Derivatives Alert Rules — merged into #289 Alert Engine."""
    from bd_platform.alert_engine import list_derivatives_alert_rules

    return list_derivatives_alert_rules(asset=asset, limit=limit)


@router.get("/intelligence-ledger/derivatives-market-state/status")
async def derivatives_market_state_status_route():
    """#327 Derivatives Market State Module — absorbs #328 + #329."""
    from bd_platform.derivatives_market_state import derivatives_market_state_status

    return derivatives_market_state_status()


@router.get("/intelligence-ledger/derivatives-market-state")
async def derivatives_market_state_panel_route(asset: str = Query("BTC")):
    from bd_platform.derivatives_market_state import build_derivatives_market_state_panel

    result = build_derivatives_market_state_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/derivatives-cross-signal/status")
async def derivatives_cross_signal_synthesis_status_route():
    """#315 Derivatives Cross-Signal Synthesis — layer above #327."""
    from bd_platform.derivatives_cross_signal_synthesis import derivatives_cross_signal_synthesis_status

    return derivatives_cross_signal_synthesis_status()


@router.get("/intelligence-ledger/derivatives-cross-signal")
async def derivatives_cross_signal_synthesis_panel_route(
    asset: str = Query("BTC"),
    timeframe: str = Query("4h"),
):
    from bd_platform.derivatives_cross_signal_synthesis import build_cross_signal_synthesis_panel

    if timeframe not in ("1h", "4h", "1d"):
        raise HTTPException(status_code=400, detail="timeframe must be 1h, 4h, or 1d")
    result = build_cross_signal_synthesis_panel(asset, timeframe=timeframe)  # type: ignore[arg-type]
    if not result.get("ok"):
        if result.get("error") == "insufficient_signals":
            return result
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/liquidation-clusters/status")
async def liquidation_cluster_analytics_status_route():
    """#307 Liquidation Cluster Analytics — data display only, no prediction."""
    from bd_platform.liquidation_cluster_analytics import liquidation_cluster_analytics_status

    return liquidation_cluster_analytics_status()


@router.get("/intelligence-ledger/liquidation-clusters")
async def liquidation_cluster_analytics_panel_route(asset: str = Query("BTC")):
    from bd_platform.liquidation_cluster_analytics import build_liquidation_cluster_panel

    result = build_liquidation_cluster_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/private-market-vc/status")
async def private_market_vc_flow_status_route():
    """#314 Private Market & VC Flow Intelligence — Wave 2 Pro."""
    from bd_platform.private_market_vc_flow import private_market_vc_flow_status

    return private_market_vc_flow_status()


@router.get("/intelligence-ledger/private-market-vc")
async def private_market_vc_flow_dashboard_route(sector: str | None = Query(None)):
    from bd_platform.private_market_vc_flow import build_vc_flow_dashboard

    return build_vc_flow_dashboard(sector=sector)


@router.get("/intelligence-ledger/cross-exchange-funding/status")
async def cross_exchange_funding_rate_analytics_status_route():
    """#317 Cross-Exchange Funding Rate Analytics — data display only, no arbitrage language."""
    from bd_platform.cross_exchange_funding_rate_analytics import cross_exchange_funding_rate_analytics_status

    return cross_exchange_funding_rate_analytics_status()


@router.get("/intelligence-ledger/cross-exchange-funding")
async def cross_exchange_funding_rate_analytics_panel_route(asset: str = Query("BTC")):
    from bd_platform.cross_exchange_funding_rate_analytics import build_cross_exchange_funding_panel

    return build_cross_exchange_funding_panel(asset=asset)


@router.get("/intelligence-ledger/taker-pressure/status")
async def taker_pressure_status_route():
    """#296 Taker Pressure Module — CEX spot + perp, orderflow sub-feature."""
    from bd_platform.taker_pressure import taker_pressure_status

    return taker_pressure_status()


@router.get("/intelligence-ledger/taker-pressure")
async def taker_pressure_panel_route(asset: str = Query("BTC")):
    """#296 taker buy/sell pressure panel with rolling imbalance."""
    from bd_platform.taker_pressure import build_taker_pressure_panel

    result = build_taker_pressure_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/taker-pressure/classification-tests")
async def taker_pressure_classification_tests_route(limit: int = Query(50, ge=1, le=200)):
    """#296 CVD classification accuracy tests — min 95%."""
    from bd_platform.taker_pressure import list_classification_tests

    return list_classification_tests(limit=limit)


@router.get("/intelligence-ledger/token-incentives/status")
async def token_incentives_status_route():
    """#298 Token Incentives & Emissions — DeFi only, Wave 2."""
    from bd_platform.token_incentives_emissions import token_incentives_status

    return token_incentives_status()


@router.get("/intelligence-ledger/token-incentives")
async def token_incentives_panel_route(protocol: str = Query("aave")):
    """#298 incentives chart — USD at emission timestamp."""
    from bd_platform.token_incentives_emissions import build_token_incentives_panel

    result = build_token_incentives_panel(protocol)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/token-incentives/emissions")
async def token_incentives_emissions_route(
    protocol: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    from bd_platform.token_incentives_emissions import list_emissions

    return list_emissions(protocol=protocol, limit=limit)


@router.get("/intelligence-ledger/trend-metrics/status")
async def trend_metric_collector_status_route():
    """#299 Trend Metric Collector — point-in-time infrastructure layer."""
    from bd_platform.trend_metric_collector import trend_metric_collector_status

    return trend_metric_collector_status()


@router.get("/intelligence-ledger/trend-metrics")
async def trend_metric_panel_route(asset: str = Query("BTC")):
    """#299 trend score + acceleration + timeframe breakdown."""
    from bd_platform.trend_metric_collector import build_trend_metric_panel

    result = build_trend_metric_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/trend-metrics/rankings")
async def trend_metric_rankings_route(limit: int = Query(50, ge=1, le=200)):
    from bd_platform.trend_metric_collector import list_universe_rankings

    return list_universe_rankings(limit=limit)


@router.get("/intelligence-ledger/trending-assets/status")
async def trending_assets_status_route():
    """#300 Trending Assets — depends on #272 Community Pulse stable."""
    from bd_platform.trending_assets import trending_assets_status

    return trending_assets_status()


@router.get("/intelligence-ledger/trending-assets")
async def trending_assets_leaderboard_route(limit: int = Query(20, ge=1, le=100)):
    """#300 trending coins leaderboard — deterministic rank."""
    from bd_platform.trending_assets import build_trending_leaderboard

    result = build_trending_leaderboard(limit=limit)
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=result.get("error") or "dependency_blocked")
    return result


@router.get("/intelligence-ledger/token-unlock/status")
async def token_unlock_intelligence_status_route():
    """#707 Token Unlock Intelligence Engine — absorbs #703+#704+#708."""
    from bd_platform.token_unlock_intelligence_engine import token_unlock_intelligence_status

    return token_unlock_intelligence_status()


@router.get("/intelligence-ledger/token-unlock/dashboard")
async def token_unlock_dashboard_route(limit: int = Query(30, ge=1, le=100)):
    """#708 dashboard — Calendar + List + Magnitude + Impact + Actionability."""
    from bd_platform.token_unlock_intelligence_engine import build_unlock_dashboard

    return build_unlock_dashboard(limit=limit)


@router.get("/intelligence-ledger/token-unlock/calendar")
async def token_unlock_calendar_route(limit: int = Query(30, ge=1, le=100)):
    """#704 calendar absorbed into #708 — primary sources + revisions tracked."""
    from bd_platform.token_unlock_intelligence_engine import build_unlock_calendar

    return build_unlock_calendar(limit=limit)


@router.get("/intelligence-ledger/token-unlock/impact")
async def token_unlock_impact_route(asset: str = Query("ARB")):
    """#707 impact score + comparable historical events — no guaranteed direction."""
    from bd_platform.token_unlock_intelligence_engine import build_impact_panel

    result = build_impact_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/token-unlock/actionability")
async def token_unlock_actionability_route(asset: str = Query("ARB")):
    """#703 actionability absorbed — 0–100 score with reasons + conflicting factors."""
    from bd_platform.token_unlock_intelligence_engine import build_actionability_panel

    result = build_actionability_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/strategy-lab/status")
async def strategy_lab_status_route():
    """#716 Strategy Lab + #712 internal QA gate — Pro/Institution."""
    from bd_platform.strategy_lab import strategy_lab_status

    return strategy_lab_status()


@router.get("/intelligence-ledger/strategy-lab")
async def strategy_lab_panel_route(strategy_id: str = Query("liquidity_inflow_alert")):
    """#716 historical backtest panel — simulation not prediction."""
    from bd_platform.strategy_lab import build_strategy_lab_panel

    result = build_strategy_lab_panel(strategy_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/strategy-lab/strategies")
async def strategy_lab_strategies_route(limit: int = Query(20, ge=1, le=50)):
    from bd_platform.strategy_lab import list_strategies

    return list_strategies(limit=limit)


@router.get("/intelligence-ledger/strategy-lab/verified-badge")
async def strategy_lab_verified_badge_route():
    """#712 — user-visible badge only. Internal QA details hidden."""
    from bd_platform.strategy_lab import build_model_verified_badge

    return build_model_verified_badge()


@router.get("/intelligence-ledger/portfolio-health/status")
async def portfolio_health_status_route():
    """#717 Diversification Score + #109 risk + #199 PnL drift."""
    from bd_platform.portfolio_diversification import portfolio_diversification_status

    return portfolio_diversification_status()


@router.get("/intelligence-ledger/portfolio-health")
async def portfolio_health_panel_route(portfolio_id: str = Query("default")):
    """#717 portfolio health — Diversification Score (not 'Entropy')."""
    from bd_platform.portfolio_diversification import build_portfolio_health_panel

    result = build_portfolio_health_panel(portfolio_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-ai/position-risk/status")
async def portfolio_position_risk_status_route():
    """#366 + #373 Portfolio AI position risk — educational, no risk score."""
    from bd_platform.portfolio_position_risk import portfolio_position_risk_status

    return portfolio_position_risk_status()


@router.get("/intelligence-ledger/portfolio-ai/position-stress-scenario")
async def portfolio_position_stress_scenario_route(position_id: str = Query("pos_001")):
    """#366 Position Stress Scenario — absorbed from Liquidation Risk."""
    from bd_platform.portfolio_position_risk import build_position_stress_scenario

    result = build_position_stress_scenario(position_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-ai/position-risk-context")
async def portfolio_position_risk_context_route(position_id: str = Query("pos_001")):
    """#373 Position Risk Context — component breakdown, no risk score."""
    from bd_platform.portfolio_position_risk import build_position_risk_context

    result = build_position_risk_context(position_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-ai/multi-model-liquidation/status")
async def multi_model_liquidation_blocked_status_route():
    """#377 HOLD & BLOCK — pending multiple liquidation models."""
    from bd_platform.portfolio_position_risk import build_multi_model_liquidation_blocked_status

    return build_multi_model_liquidation_blocked_status()


@router.get("/intelligence-ledger/smart-anomaly-alerts/status")
async def smart_anomaly_alerts_status_route():
    """#719 Smart Anomaly Alert Engine — absorbs #131+#121."""
    from bd_platform.smart_anomaly_alert_engine import smart_anomaly_alert_engine_status

    return smart_anomaly_alert_engine_status()


@router.get("/intelligence-ledger/smart-anomaly-alerts")
async def smart_anomaly_alerts_panel_route(asset: str = Query("BTC")):
    from bd_platform.smart_anomaly_alert_engine import build_smart_anomaly_panel

    return build_smart_anomaly_panel(asset)


@router.get("/intelligence-ledger/smart-anomaly-alerts/alerts")
async def smart_anomaly_alerts_list_route(
    asset: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    from bd_platform.smart_anomaly_alert_engine import list_anomaly_alerts

    return list_anomaly_alerts(asset=asset, limit=limit)


@router.get("/intelligence-ledger/market-intelligence/status")
async def market_intelligence_status_route():
    """#721 Market Intelligence Engine — bot activity layer."""
    from bd_platform.market_intelligence_engine import market_intelligence_engine_status

    return market_intelligence_engine_status()


@router.get("/intelligence-ledger/market-intelligence/bot-activity")
async def market_intelligence_bot_activity_route(asset: str = Query("BTC")):
    from bd_platform.market_intelligence_engine import build_market_intelligence_panel

    result = build_market_intelligence_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-risk/status")
async def portfolio_risk_status_route():
    """#723 Portfolio Risk Analytics — correlation widget."""
    from bd_platform.portfolio_risk_analytics import portfolio_risk_analytics_status

    return portfolio_risk_analytics_status()


@router.get("/intelligence-ledger/portfolio-risk/correlation")
async def portfolio_risk_correlation_route(
    universe_id: str = Query("default"),
    window_days: int = Query(30, ge=7, le=180),
):
    from bd_platform.portfolio_risk_analytics import build_correlation_panel

    result = build_correlation_panel(universe_id, window_days=window_days)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/market-breadth/status")
async def market_breadth_status_route():
    """#724 Market Breadth Module — Market Radar widget."""
    from bd_platform.market_breadth import market_breadth_status

    return market_breadth_status()


@router.get("/intelligence-ledger/market-breadth")
async def market_breadth_panel_route():
    from bd_platform.market_breadth import build_market_breadth_panel

    return build_market_breadth_panel()


@router.get("/charting/status")
async def interactive_charting_status_route():
    """#726 Interactive Charting Engine — renamed from CryptoQuant, absorbs #732."""
    from bd_platform.interactive_charting_engine import interactive_charting_status

    return interactive_charting_status()


@router.get("/charting")
async def interactive_charting_panel_route(symbol: str = Query("BTC/USDT")):
    from bd_platform.interactive_charting_engine import build_charting_panel

    return build_charting_panel(symbol)


@router.get("/dashboard-builder/status")
async def dashboard_builder_status_route():
    """#728 Dashboard Builder — depends on #726+#742."""
    from bd_platform.dashboard_builder import dashboard_builder_status

    return dashboard_builder_status()


@router.get("/dashboard-builder")
async def dashboard_builder_panel_route(dashboard_id: str = Query("default")):
    from bd_platform.dashboard_builder import build_dashboard_panel

    result = build_dashboard_panel(dashboard_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/datashare/status")
async def datashare_enterprise_status_route():
    """#730 Datashare Enterprise — Wave 3 DEFERRED, schema contracts documented."""
    from bd_platform.datashare_enterprise import datashare_enterprise_status

    return datashare_enterprise_status()


@router.get("/intelligence-ledger/defi-economics/status")
async def defi_economics_status_route():
    """#733 DeFi Economics Module — earnings proxy, not GAAP."""
    from bd_platform.defi_economics import defi_economics_status

    return defi_economics_status()


@router.get("/intelligence-ledger/defi-economics")
async def defi_economics_panel_route(protocol: str = Query("aave")):
    from bd_platform.defi_economics import build_defi_economics_panel

    result = build_defi_economics_panel(protocol)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/market-radar/exchange-activity/status")
async def market_radar_exchange_activity_status_route():
    """#734 Exchange Activity — Market Radar indicator."""
    from bd_platform.market_radar_indicators import market_radar_indicators_status

    return market_radar_indicators_status()


@router.get("/intelligence-ledger/market-radar/exchange-activity")
async def market_radar_exchange_activity_route(exchange: str = Query("binance")):
    from bd_platform.market_radar_indicators import build_exchange_activity_indicator

    result = build_exchange_activity_indicator(exchange)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/market-radar/derivatives-venue-feed/status")
async def market_radar_derivatives_venue_feed_status_route():
    """#331 Derivatives Venue Feed — absorbed into #274 Market Data Engine. Raw display only."""
    from bd_platform.market_data_engine import market_data_engine_status

    return market_data_engine_status()


@router.get("/intelligence-ledger/market-radar/derivatives-venue-feed")
async def market_radar_derivatives_venue_feed_route(asset: str = Query("BTC")):
    from bd_platform.market_data_engine import build_derivatives_venue_feed

    result = build_derivatives_venue_feed(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/market-radar/funding-rate-context/status")
async def market_radar_funding_rate_context_status_route():
    """#333 Funding Rate Context Panel — NOT Intelligence. Market data display only."""
    from bd_platform.market_data_engine import market_data_engine_status

    return market_data_engine_status()


@router.get("/intelligence-ledger/market-radar/funding-rate-context")
async def market_radar_funding_rate_context_route(asset: str = Query("BTC")):
    from bd_platform.market_data_engine import build_funding_rate_context_panel

    result = build_funding_rate_context_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/market-radar/basis-curve")
async def market_radar_basis_curve_route(asset: str = Query("BTC")):
    """#343 Basis Curve — absorbed into Market Radar / Derivatives Panel."""
    from bd_platform.market_data_engine import build_basis_curve_component

    result = build_basis_curve_component(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/market-radar/market-data-normalization")
async def market_data_normalization_layer_route(asset: str = Query("BTC")):
    """#395 Market Data Normalization Layer — absorbed into #274."""
    from bd_platform.market_data_engine import build_market_data_normalization_layer

    result = build_market_data_normalization_layer(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/data-layer/volatility-regime/status")
async def cross_asset_volatility_regime_status_route():
    """#501 Cross-Asset Volatility Regime Analyzer — no scoring terminology."""
    from bd_platform.cross_asset_volatility_regime import cross_asset_volatility_regime_status

    return cross_asset_volatility_regime_status()


@router.get("/intelligence-ledger/data-layer/volatility-regime")
async def cross_asset_volatility_regime_panel_route(asset: str = Query("BTC")):
    from bd_platform.cross_asset_volatility_regime import build_cross_asset_volatility_panel

    result = build_cross_asset_volatility_panel(asset)
    if not result.get("ok"):
        raise HTTPException(
            status_code=403 if result.get("error") == "legal_review_pending" else 404,
            detail=result.get("error") or "not_found",
        )
    return result


@router.get("/intelligence-ledger/data-layer/tail-risk-metrics/status")
async def historical_tail_risk_metrics_status_route():
    """#503+#504 Historical Tail Risk Estimates (VaR/CVaR) — merged, no advisory language."""
    from bd_platform.historical_tail_risk_metrics import historical_tail_risk_metrics_status

    return historical_tail_risk_metrics_status()


@router.get("/intelligence-ledger/data-layer/tail-risk-metrics")
async def historical_tail_risk_metrics_panel_route(
    asset: str = Query("BTC"),
    portfolio_id: str | None = Query(None),
    confidence: float = Query(0.95, ge=0.5, le=0.99),
    notional_usd: float = Query(10_000, gt=0),
):
    """#503+#504 Historical Tail Risk Estimates — asset or portfolio scope."""
    from bd_platform.historical_tail_risk_metrics import build_historical_tail_risk_panel

    result = build_historical_tail_risk_panel(
        asset=asset,
        portfolio_id=portfolio_id,
        confidence=confidence,
        notional_usd=notional_usd,
    )
    if not result.get("ok"):
        raise HTTPException(
            status_code=403 if result.get("error") == "legal_review_pending" else 404,
            detail=result.get("error") or "not_found",
        )
    return result


@router.get("/intelligence-ledger/onchain-layer/bridge-flow/status")
async def cross_chain_bridge_flow_monitor_status_route():
    """#506+#521 Cross-Chain Bridge Flow Monitor — data monitoring, no AI/signals."""
    from bd_platform.cross_chain_bridge_flow_monitor import cross_chain_bridge_flow_monitor_status

    return cross_chain_bridge_flow_monitor_status()


@router.get("/intelligence-ledger/onchain-layer/bridge-flow")
async def cross_chain_bridge_flow_monitor_panel_route(
    bridge_id: str | None = Query(None),
    source_chain: str | None = Query(None),
    dest_chain: str | None = Query(None),
):
    from bd_platform.cross_chain_bridge_flow_monitor import build_bridge_flow_panel

    return build_bridge_flow_panel(
        bridge_id=bridge_id,
        source_chain=source_chain,
        dest_chain=dest_chain,
    )


@router.get("/intelligence-ledger/security-layer/dusting-detection/status")
async def dusting_attack_detection_alert_status_route():
    """#507 Dusting Attack Detection Alert — detection only, not neutralizer."""
    from bd_platform.dusting_attack_detection_alert import dusting_attack_detection_alert_status

    return dusting_attack_detection_alert_status()


@router.get("/intelligence-ledger/security-layer/dusting-detection")
async def dusting_attack_detection_alert_panel_route(
    address: str | None = Query(None),
    wallet_id: str | None = Query(None),
):
    from bd_platform.dusting_attack_detection_alert import build_dusting_detection_panel

    result = build_dusting_detection_panel(address=address, wallet_id=wallet_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/exchange-flow-velocity/status")
async def exchange_flow_velocity_monitor_status_route():
    """#508 Exchange Flow Velocity Monitor — integrated feed, not standalone."""
    from bd_platform.exchange_flow_velocity_monitor import exchange_flow_velocity_monitor_status

    return exchange_flow_velocity_monitor_status()


@router.get("/intelligence-ledger/onchain-layer/exchange-flow-velocity")
async def exchange_flow_velocity_monitor_panel_route(
    exchange_id: str | None = Query(None),
    asset: str | None = Query(None),
):
    from bd_platform.exchange_flow_velocity_monitor import build_exchange_flow_velocity_panel

    result = build_exchange_flow_velocity_panel(exchange_id=exchange_id, asset=asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/bucketed-cvd/status")
async def bucketed_cvd_status_route():
    """#518 Bucketed CVD — on-chain metrics layer, versioned bucket definitions."""
    from bd_platform.bucketed_cvd import bucketed_cvd_status

    return bucketed_cvd_status()


@router.get("/intelligence-ledger/onchain-layer/bucketed-cvd")
async def bucketed_cvd_panel_route(asset: str = Query("BTC")):
    from bd_platform.bucketed_cvd import build_bucketed_cvd_panel

    result = build_bucketed_cvd_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/cost-basis/status")
async def cost_basis_distribution_status_route():
    """#520 Cost Basis Distribution — on-chain analytics, no future leakage."""
    from bd_platform.cost_basis_distribution import cost_basis_distribution_status

    return cost_basis_distribution_status()


@router.get("/intelligence-ledger/onchain-layer/cost-basis")
async def cost_basis_distribution_panel_route(asset: str = Query("BTC")):
    from bd_platform.cost_basis_distribution import build_cost_basis_panel

    result = build_cost_basis_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/cross-chain-liquidity/status")
async def cross_chain_liquidity_flow_status_route():
    """#522 Cross-Chain Liquidity Flow — bridge verified, double-count prevented."""
    from bd_platform.cross_chain_liquidity_flow import cross_chain_liquidity_flow_status

    return cross_chain_liquidity_flow_status()


@router.get("/intelligence-ledger/onchain-layer/cross-chain-liquidity")
async def cross_chain_liquidity_flow_panel_route(
    asset: str | None = Query(None),
    chain: str | None = Query(None),
):
    from bd_platform.cross_chain_liquidity_flow import build_cross_chain_liquidity_panel

    return build_cross_chain_liquidity_panel(asset=asset, chain=chain)


@router.get("/intelligence-ledger/onchain-layer/cross-chain-liquidity/reconciliation-tests")
async def cross_chain_liquidity_reconciliation_tests_route():
    from bd_platform.cross_chain_liquidity_flow import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/onchain-layer/exchange-intelligence/status")
async def exchange_intelligence_layer_status_route():
    """#544 Exchange Intelligence Layer — epic #544 #546-550 merged."""
    from bd_platform.exchange_intelligence_layer import exchange_intelligence_layer_status

    return exchange_intelligence_layer_status()


@router.get("/intelligence-ledger/onchain-layer/exchange-intelligence")
async def exchange_intelligence_layer_panel_route(
    exchange_id: str = Query("binance"),
    asset: str | None = Query(None),
    adjusted: bool = Query(True),
):
    from bd_platform.exchange_intelligence_layer import build_exchange_intelligence_panel

    return build_exchange_intelligence_panel(
        exchange_id=exchange_id,
        asset=asset,
        adjusted=adjusted,
    )


@router.get("/intelligence-ledger/onchain-layer/exchange-intelligence/reconciliation-tests")
async def exchange_intelligence_reconciliation_tests_route():
    from bd_platform.exchange_intelligence_layer import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/onchain-layer/holder-analytics/status")
async def holder_analytics_layer_status_route():
    """#559 #560 Holder Analytics Layer — STH/LTH cohorts + distribution."""
    from bd_platform.holder_analytics_layer import holder_analytics_layer_status

    return holder_analytics_layer_status()


@router.get("/intelligence-ledger/onchain-layer/holder-analytics")
async def holder_analytics_panel_route(
    asset: str = Query("BTC"),
    as_of: str | None = Query(None),
):
    from bd_platform.holder_analytics_layer import build_holder_analytics_panel

    result = build_holder_analytics_panel(asset=asset, as_of=as_of)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/holder-analytics/reconciliation-tests")
async def holder_analytics_reconciliation_tests_route():
    from bd_platform.holder_analytics_layer import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/onchain-layer/miner-intelligence/status")
async def miner_intelligence_layer_status_route():
    """#566 #567 #568 Miner Intelligence Layer — flow tracking + MPI."""
    from bd_platform.miner_intelligence_layer import miner_intelligence_layer_status

    return miner_intelligence_layer_status()


@router.get("/intelligence-ledger/onchain-layer/miner-intelligence")
async def miner_intelligence_panel_route(
    miner_id: str = Query("miner_foundry_usa"),
    adjusted: bool = Query(True),
):
    from bd_platform.miner_intelligence_layer import build_miner_intelligence_panel

    result = build_miner_intelligence_panel(miner_id=miner_id, adjusted=adjusted)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/miner-intelligence/mpi")
async def miners_position_index_route(
    miner_id: str = Query("miner_foundry_usa"),
):
    from bd_platform.miner_intelligence_layer import build_miners_position_index

    result = build_miners_position_index(miner_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/miner-intelligence/reconciliation-tests")
async def miner_intelligence_reconciliation_tests_route():
    from bd_platform.miner_intelligence_layer import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/onchain-layer/dex-intelligence/status")
async def dex_intelligence_layer_status_route():
    """#535 DEX Intelligence Layer — pool liquidity with scam/spam filters."""
    from bd_platform.dex_intelligence_layer import dex_intelligence_layer_status

    return dex_intelligence_layer_status()


@router.get("/intelligence-ledger/onchain-layer/dex-intelligence")
async def dex_intelligence_panel_route(
    token_symbol: str | None = Query(None),
    chain: str | None = Query(None),
):
    from bd_platform.dex_intelligence_layer import build_dex_intelligence_panel

    return build_dex_intelligence_panel(token_symbol=token_symbol, chain=chain)


@router.get("/intelligence-ledger/onchain-layer/dex-intelligence/reconciliation-tests")
async def dex_intelligence_reconciliation_tests_route():
    from bd_platform.dex_intelligence_layer import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/intelligence-layer/market-data-screener/status")
async def custom_market_data_screener_status_route():
    """#533 Custom Market Data Screener — user-controlled multi-domain filtering."""
    from bd_platform.custom_market_data_screener import custom_market_data_screener_status

    return custom_market_data_screener_status()


@router.get("/intelligence-ledger/intelligence-layer/market-data-screener")
async def custom_market_data_screener_run_route(
    saved_screener_id: str | None = Query(None),
    whale_activity_min: float | None = Query(None),
    risk_score_max: float | None = Query(None),
    onchain_signal_min: float | None = Query(None),
    user_id: str = Query("default"),
):
    from bd_platform.custom_market_data_screener import run_screener

    filters: dict[str, Any] = {}
    if whale_activity_min is not None:
        filters["whale_activity_min"] = {"min": whale_activity_min}
    if risk_score_max is not None:
        filters["risk_score_max"] = {"max": risk_score_max}
    if onchain_signal_min is not None:
        filters["onchain_signal_min"] = {"min": onchain_signal_min}

    return run_screener(filters or None, saved_screener_id=saved_screener_id, user_id=user_id)


@router.get("/intelligence-ledger/intelligence-layer/market-data-screener/saved")
async def custom_market_data_screener_saved_route():
    from bd_platform.custom_market_data_screener import list_saved_screeners

    return list_saved_screeners()


@router.get("/intelligence-ledger/intelligence-layer/dev-market-divergence/status")
async def dev_market_divergence_status_route():
    """#537 Development-to-Market Divergence Detector — descriptive only."""
    from bd_platform.dev_market_divergence_detector import dev_market_divergence_detector_status

    return dev_market_divergence_detector_status()


@router.get("/intelligence-ledger/intelligence-layer/dev-market-divergence")
async def dev_market_divergence_panel_route(project_id: str = Query("uniswap")):
    from bd_platform.dev_market_divergence_detector import build_divergence_panel

    result = build_divergence_panel(project_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/dev-market-divergence/qa-tests")
async def dev_market_divergence_qa_route():
    from bd_platform.dev_market_divergence_detector import run_divergence_qa_tests

    return run_divergence_qa_tests()


@router.get("/intelligence-ledger/foundation/entity-resolution/status")
async def entity_resolution_engine_status_route():
    """#541 Entity Resolution Engine — Sprint 0 critical foundation."""
    from bd_platform.entity_resolution_engine import entity_resolution_engine_status

    return entity_resolution_engine_status()


@router.get("/intelligence-ledger/foundation/entity-resolution")
async def entity_resolution_engine_panel_route(
    entity_id: str | None = Query(None),
    address: str | None = Query(None),
):
    from bd_platform.entity_resolution_engine import build_entity_resolution_panel

    result = build_entity_resolution_panel(entity_id=entity_id, address=address)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/entity-intelligence/status")
async def entity_intelligence_layer_status_route():
    """#539 #540 Entity Intelligence Layer — PnL tracker + entity profiles."""
    from bd_platform.entity_intelligence_layer import entity_intelligence_layer_status

    return entity_intelligence_layer_status()


@router.get("/intelligence-ledger/entity-intelligence")
async def entity_intelligence_panel_route(
    entity_id: str = Query("entity_whale_alpha"),
):
    from bd_platform.entity_intelligence_layer import build_entity_intelligence_panel

    result = build_entity_intelligence_panel(entity_id=entity_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/entity-intelligence/pnl")
async def entity_pnl_tracker_route(
    entity_id: str = Query("entity_whale_alpha"),
):
    from bd_platform.entity_intelligence_layer import build_entity_pnl_tracker

    result = build_entity_pnl_tracker(entity_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/entity-intelligence/reconciliation-tests")
async def entity_intelligence_reconciliation_tests_route():
    from bd_platform.entity_intelligence_layer import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/entity-layer/investor-intelligence/status")
async def investor_intelligence_layer_status_route():
    """#562 #563 Investor Intelligence Layer — activity + profiles."""
    from bd_platform.investor_intelligence_layer import investor_intelligence_layer_status

    return investor_intelligence_layer_status()


@router.get("/intelligence-ledger/entity-layer/investor-intelligence")
async def investor_intelligence_panel_route(
    investor_id: str = Query("investor_paradigm"),
):
    from bd_platform.investor_intelligence_layer import build_investor_intelligence_panel

    result = build_investor_intelligence_panel(investor_id=investor_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/entity-layer/investor-intelligence/reconciliation-tests")
async def investor_intelligence_reconciliation_tests_route():
    from bd_platform.investor_intelligence_layer import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/data-layer/infrastructure/status")
async def data_infrastructure_layer_status_route():
    """#564 Data Infrastructure Layer — Market + Network Join (Sprint 0)."""
    from bd_platform.data_infrastructure_layer import data_infrastructure_layer_status

    return data_infrastructure_layer_status()


@router.get("/intelligence-ledger/data-layer/infrastructure/market-network-join")
async def market_network_join_route(
    as_of: str | None = Query(None),
    asset: str | None = Query(None),
):
    from bd_platform.data_infrastructure_layer import build_data_infrastructure_panel

    result = build_data_infrastructure_panel(as_of=as_of, asset=asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/data-layer/infrastructure/reconciliation-tests")
async def data_infrastructure_reconciliation_tests_route():
    from bd_platform.data_infrastructure_layer import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/infrastructure/custom-alerts/status")
async def custom_alerts_status_route():
    """#532 Custom Alerts — backend enforced, rate limits, tx evidence."""
    from bd_platform.custom_alerts import custom_alerts_status

    return custom_alerts_status()


@router.get("/intelligence-ledger/infrastructure/custom-alerts")
async def custom_alerts_panel_route(user_id: str = Query("default")):
    from bd_platform.custom_alerts import build_custom_alerts_panel

    return build_custom_alerts_panel(user_id=user_id)


@router.get("/intelligence-ledger/intelligence-layer/price-move-correlator/status")
async def price_move_event_correlator_status_route():
    """#519 Price-Move Event Correlator — temporal correlation, not causation."""
    from bd_platform.price_move_event_correlator import price_move_event_correlator_status

    return price_move_event_correlator_status()


@router.get("/intelligence-ledger/intelligence-layer/price-move-correlator")
async def price_move_event_correlator_panel_route(
    candle_id: str = Query("btc_2026_08_26_14h"),
    asset: str | None = Query(None),
):
    from bd_platform.price_move_event_correlator import build_price_move_event_correlator_panel

    result = build_price_move_event_correlator_panel(candle_id=candle_id, asset=asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/flow-to-price-correlator/status")
async def flow_to_price_event_correlator_status_route():
    """#556 Flow-to-Price Event Correlator — competing hypotheses, not causation."""
    from bd_platform.flow_to_price_event_correlator import flow_to_price_event_correlator_status

    return flow_to_price_event_correlator_status()


@router.get("/intelligence-ledger/intelligence-layer/flow-to-price-correlator")
async def flow_to_price_event_correlator_panel_route(
    event_id: str = Query("btc_move_2026_08_26"),
    asset: str | None = Query(None),
):
    from bd_platform.flow_to_price_event_correlator import build_flow_to_price_event_correlator_panel

    result = build_flow_to_price_event_correlator_panel(event_id=event_id, asset=asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/market-context/status")
async def cross_domain_market_context_status_route():
    """#524 Cross-Domain Market Context Layer — epic, absorbs #523-530."""
    from bd_platform.cross_domain_market_context_layer import cross_domain_market_context_status

    return cross_domain_market_context_status()


@router.get("/intelligence-ledger/intelligence-layer/market-context")
async def cross_domain_market_context_panel_route(
    context_id: str = Query("btc_cross_domain"),
    asset: str = Query("BTC"),
):
    """#524 Market context feed — Fact/Inference/Hypothesis separated, no recommendation."""
    from bd_platform.cross_domain_market_context_layer import build_market_context_panel

    result = build_market_context_panel(context_id=context_id, asset=asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/market-context/sub-module/{sub_module_id}")
async def cross_domain_market_context_sub_module_route(
    sub_module_id: str,
    asset: str = Query("BTC"),
):
    """#524 sub-module feed — task not ticket (#523-530)."""
    from bd_platform.cross_domain_market_context_layer import build_sub_module_feed

    result = build_sub_module_feed(sub_module_id, asset=asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/whale-flow-destination/status")
async def whale_flow_destination_tracker_status_route():
    """#510 Whale Flow Destination Tracker — integrated, rule-based heuristics."""
    from bd_platform.whale_flow_destination_tracker import whale_flow_destination_tracker_status

    return whale_flow_destination_tracker_status()


@router.get("/intelligence-ledger/onchain-layer/whale-flow-destination")
async def whale_flow_destination_tracker_panel_route(
    asset: str | None = Query(None),
    whale_address: str | None = Query(None),
):
    from bd_platform.whale_flow_destination_tracker import build_whale_flow_destination_panel

    return build_whale_flow_destination_panel(asset=asset, whale_address=whale_address)


@router.get("/intelligence-ledger/intelligence-layer/ai-content/status")
async def ai_content_engine_status_route():
    """#511+#512+#513 AI Content Engine — evidence feed, digest, screener."""
    from bd_platform.ai_content_engine import ai_content_engine_status

    return ai_content_engine_status()


@router.get("/intelligence-ledger/intelligence-layer/ai-content")
async def ai_content_engine_panel_route(
    asset: str = Query("BTC"),
    digest_id: str = Query("daily"),
    sort_by: str = Query("factor_alignment"),
):
    from bd_platform.ai_content_engine import build_ai_content_engine_panel

    return build_ai_content_engine_panel(asset=asset, digest_id=digest_id, sort_by=sort_by)


@router.get("/intelligence-ledger/intelligence-layer/ai-content/evidence")
async def market_evidence_feed_route(asset: str = Query("BTC")):
    """#511 Market Evidence Feed."""
    from bd_platform.ai_content_engine import build_market_evidence_feed

    return build_market_evidence_feed(asset=asset)


@router.get("/intelligence-ledger/intelligence-layer/ai-content/digest")
async def market_digest_route(digest_id: str = Query("daily")):
    """#512 Market Digest Generator."""
    from bd_platform.ai_content_engine import build_market_digest

    result = build_market_digest(digest_id=digest_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/ai-content/screener")
async def multi_factor_screener_route(sort_by: str = Query("factor_alignment")):
    """#513 Multi-Factor Opportunity Screener — user-controlled, not rating."""
    from bd_platform.ai_content_engine import build_multi_factor_screener

    result = build_multi_factor_screener(sort_by=sort_by)
    if not result.get("ok"):
        raise HTTPException(
            status_code=403 if result.get("error") == "legal_review_pending" else 404,
            detail=result.get("error") or "not_found",
        )
    return result


@router.get("/intelligence-ledger/intelligence-layer/ai-content/news")
async def news_integration_route(asset: str = Query("BTC"), limit: int = Query(10, ge=1, le=50)):
    """#575 News Integration — merged into AI Content Engine, source links preserved."""
    from bd_platform.ai_content_engine import build_news_panel_async

    return await build_news_panel_async(asset=asset, limit=limit)


@router.get("/intelligence-ledger/ux-layer/natural-language/status")
async def natural_language_interpreter_status_route():
    """#573 Natural Language Interpreter — rule-based intent routing, no advisory."""
    from bd_platform.natural_language_interpreter import natural_language_interpreter_status

    return natural_language_interpreter_status()


@router.get("/intelligence-ledger/ux-layer/natural-language/schemas")
async def natural_language_tool_schemas_route():
    """#573 Deterministic tool schemas."""
    from bd_platform.natural_language_interpreter import build_tool_schemas

    return build_tool_schemas()


@router.get("/intelligence-ledger/ux-layer/natural-language")
async def natural_language_interpreter_route(
    query: str = Query("What is Bitcoin's exchange flow?"),
    user_tier: str = Query("guest"),
):
    from bd_platform.natural_language_interpreter import build_nli_panel

    return build_nli_panel(query=query, user_tier=user_tier)


@router.get("/intelligence-ledger/ux-layer/natural-language/reconciliation-tests")
async def natural_language_reconciliation_tests_route():
    from bd_platform.natural_language_interpreter import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/onchain-layer/metrics-library/status")
async def onchain_metrics_library_status_route():
    """#577 On-Chain Metrics Library epic — #574 API delivery sub-task."""
    from bd_platform.onchain_metrics_library import onchain_metrics_library_status

    return onchain_metrics_library_status()


@router.get("/intelligence-ledger/onchain-layer/metrics-library")
async def onchain_metrics_library_panel_route(asset: str = Query("BTC")):
    from bd_platform.onchain_metrics_library import build_onchain_metrics_library_panel

    return build_onchain_metrics_library_panel(asset)


@router.get("/intelligence-ledger/onchain-layer/metrics-library/network-api")
async def network_data_pro_metrics_route(asset: str = Query("BTC")):
    """#574 Network Data Pro Metrics — institutional API (sub-task of #577)."""
    from bd_platform.onchain_metrics_library import build_network_data_pro_api

    return build_network_data_pro_api(asset)


@router.get("/intelligence-ledger/onchain-layer/metrics-library/historical-qa")
async def onchain_metrics_historical_qa_route():
    from bd_platform.onchain_metrics_library import run_historical_qa_tests

    return run_historical_qa_tests()


@router.get("/intelligence-ledger/intelligence-layer/historical-narratives/status")
async def historical_narrative_explorer_status_route():
    """#250 Historical Narrative Explorer — Sprint 2 sentiment research archive."""
    from bd_platform.historical_narrative_explorer import historical_narrative_explorer_status

    return historical_narrative_explorer_status()


@router.get("/intelligence-ledger/intelligence-layer/historical-narratives")
async def historical_narrative_explorer_panel_route(
    narrative_id: str = Query("defi_summer"),
    asset: str | None = Query(None),
    time_range: str | None = Query(None),
):
    from bd_platform.historical_narrative_explorer import build_historical_narrative_panel

    result = build_historical_narrative_panel(
        narrative_id=narrative_id,
        asset=asset,
        time_range=time_range,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/historical-narratives/historical-qa")
async def historical_narrative_explorer_qa_route():
    from bd_platform.historical_narrative_explorer import run_historical_qa_tests

    return run_historical_qa_tests()


@router.get("/intelligence-ledger/data-layer/protocol-metrics/status")
async def protocol_metrics_layer_status_route():
    """#514 Protocol Metrics Layer — Active Users with bot filtering."""
    from bd_platform.protocol_metrics_layer import protocol_metrics_layer_status

    return protocol_metrics_layer_status()


@router.get("/intelligence-ledger/data-layer/protocol-metrics")
async def protocol_metrics_panel_route(protocol_id: str = Query("uniswap")):
    from bd_platform.protocol_metrics_layer import build_protocol_metrics_panel

    result = build_protocol_metrics_panel(protocol_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/data-layer/protocol-economics/status")
async def protocol_economics_layer_status_route():
    """#554 #555 Protocol Economics Layer — fees & revenue with explicit definitions."""
    from bd_platform.protocol_economics_layer import protocol_economics_layer_status

    return protocol_economics_layer_status()


@router.get("/intelligence-ledger/data-layer/protocol-economics")
async def protocol_economics_panel_route(protocol_id: str = Query("uniswap")):
    from bd_platform.protocol_economics_layer import build_protocol_economics_panel

    result = build_protocol_economics_panel(protocol_id=protocol_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/data-layer/protocol-economics/historical-qa")
async def protocol_economics_historical_qa_route():
    from bd_platform.protocol_economics_layer import run_historical_qa_tests

    return run_historical_qa_tests()


@router.get("/intelligence-ledger/portfolio-layer/snapshots/status")
async def portfolio_intelligence_layer_status_route():
    """#515 #557 #558 Portfolio Intelligence Layer — tracker + wallet balance."""
    from bd_platform.portfolio_intelligence_layer import portfolio_intelligence_layer_status

    return portfolio_intelligence_layer_status()


@router.get("/intelligence-ledger/portfolio-layer/snapshots")
async def portfolio_intelligence_panel_route(
    portfolio_id: str = Query("demo_portfolio"),
    snapshot_timestamp: str | None = Query(None),
    wallet_address: str | None = Query(None),
    wallet_chain: str | None = Query(None),
    wallet_timestamp: str | None = Query(None),
):
    from bd_platform.portfolio_intelligence_layer import build_portfolio_intelligence_panel

    result = build_portfolio_intelligence_panel(
        portfolio_id,
        snapshot_timestamp=snapshot_timestamp,
        wallet_address=wallet_address,
        wallet_chain=wallet_chain,
        wallet_timestamp=wallet_timestamp,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-layer/wallet-balance")
async def historical_wallet_balance_route(
    address: str = Query("0xabc1234567890def1234567890abc1234567890ab"),
    chain: str = Query("ethereum"),
    timestamp: str = Query("2026-08-01T00:00:00Z"),
):
    """#558 Historical Wallet Balance Tool — point-in-time lookup."""
    from bd_platform.portfolio_intelligence_layer import build_historical_wallet_balance

    result = build_historical_wallet_balance(address, chain=chain, timestamp=timestamp)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-layer/reconciliation-tests")
async def portfolio_intelligence_reconciliation_tests_route():
    from bd_platform.portfolio_intelligence_layer import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/portfolio-layer/multi-chain-tracker")
async def multi_chain_portfolio_tracker_route(
    portfolio_id: str = Query("demo_portfolio"),
):
    """#569 Multi-Chain Portfolio Tracker — cross-chain dedupe + exposure metrics."""
    from bd_platform.portfolio_intelligence_layer import build_multi_chain_portfolio_tracker

    result = build_multi_chain_portfolio_tracker(portfolio_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/market-conditions/status")
async def market_conditions_context_monitor_status_route():
    """#565 Market Conditions Context Monitor — factor alignment indicators."""
    from bd_platform.market_conditions_context_monitor import market_conditions_context_monitor_status

    return market_conditions_context_monitor_status()


@router.get("/intelligence-ledger/intelligence-layer/market-conditions")
async def market_conditions_context_monitor_panel_route(
    market_id: str = Query("crypto_aggregate"),
):
    from bd_platform.market_conditions_context_monitor import build_market_conditions_panel

    result = build_market_conditions_panel(market_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/market-conditions/reconciliation-tests")
async def market_conditions_reconciliation_tests_route():
    from bd_platform.market_conditions_context_monitor import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/data-layer/protocol-valuation/status")
async def protocol_valuation_layer_status_route():
    """#570 #571 Protocol Valuation Layer — NVT ratio & historical context."""
    from bd_platform.protocol_valuation_layer import protocol_valuation_layer_status

    return protocol_valuation_layer_status()


@router.get("/intelligence-ledger/data-layer/protocol-valuation")
async def protocol_valuation_panel_route(
    asset_id: str = Query("bitcoin"),
    entity_adjusted: bool = Query(True),
):
    from bd_platform.protocol_valuation_layer import build_protocol_valuation_panel

    result = build_protocol_valuation_panel(asset_id, entity_adjusted=entity_adjusted)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/data-layer/protocol-valuation/reconciliation-tests")
async def protocol_valuation_reconciliation_tests_route():
    from bd_platform.protocol_valuation_layer import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/data-layer/asset-profiles/status")
async def asset_intelligence_profiles_status_route():
    """#516 Asset Intelligence Profiles — Sprint 0 foundation."""
    from bd_platform.asset_intelligence_profiles import asset_intelligence_profiles_status

    return asset_intelligence_profiles_status()


@router.get("/intelligence-ledger/data-layer/asset-profiles")
async def asset_intelligence_profiles_panel_route(entity_id: str = Query("asset_btc")):
    from bd_platform.asset_intelligence_profiles import build_asset_intelligence_panel

    result = build_asset_intelligence_panel(entity_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/market-radar/fundraising-velocity")
async def market_radar_fundraising_velocity_route(
    project_id: str | None = Query(None),
    sector: str | None = Query(None),
):
    """#341 Fundraising Velocity Indicator — Project Intelligence, no score."""
    from bd_platform.private_market_vc_flow import build_fundraising_velocity_indicator

    result = build_fundraising_velocity_indicator(project_id=project_id, sector=sector)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/funding-arbitrage-simulator/status")
async def funding_arbitrage_simulator_status_route():
    """#338 Funding Arbitrage Simulator — Wave 3 Pro/Institution, paper-only."""
    from bd_platform.funding_arbitrage_simulator import funding_arbitrage_simulator_status

    return funding_arbitrage_simulator_status()


@router.get("/intelligence-ledger/funding-arbitrage-simulator")
async def funding_arbitrage_simulator_panel_route(asset: str | None = Query(None)):
    from bd_platform.funding_arbitrage_simulator import build_simulation_panel

    result = build_simulation_panel(asset=asset)
    if not result.get("ok"):
        raise HTTPException(status_code=403 if result.get("error") == "legal_review_pending" else 404,
                          detail=result.get("error") or "not_found")
    return result


@router.get("/internal/strategy-validation/status")
async def strategy_validation_engine_status_route():
    """#350 Strategy Validation Engine — INTERNAL ONLY, not user-facing."""
    from bd_platform.strategy_validation_engine import strategy_validation_engine_status

    return strategy_validation_engine_status()


@router.get("/internal/strategy-validation")
async def strategy_validation_engine_run_route(strategy_id: str | None = Query(None)):
    from bd_platform.strategy_validation_engine import run_strategy_validation

    result = run_strategy_validation(strategy_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/internal/reference-data-registry/status")
async def reference_data_registry_status_route():
    """#394 Reference Data Registry — Wave 0 internal infrastructure."""
    from bd_platform.reference_data_registry import reference_data_registry_status

    return reference_data_registry_status()


@router.get("/internal/reference-data-registry")
async def reference_data_registry_snapshot_route():
    from bd_platform.reference_data_registry import build_registry_snapshot

    return build_registry_snapshot()


@router.get("/internal/reference-data-registry/lookup")
async def reference_data_registry_lookup_route(
    source: str = Query(...),
    source_id: str = Query(...),
    entity_type: str = Query("asset"),
):
    from bd_platform.reference_data_registry import lookup_canonical_id

    result = lookup_canonical_id(source=source, source_id=source_id, entity_type=entity_type)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/entity-profiler/status")
async def entity_profiler_status_route():
    """#736 Entity Profiler — exchange usage intelligence layer."""
    from bd_platform.entity_profiler import entity_profiler_status

    return entity_profiler_status()


@router.get("/intelligence-ledger/entity-profiler")
async def entity_profiler_panel_route(entity_id: str = Query("whale_001")):
    from bd_platform.entity_profiler import build_entity_profiler_panel

    result = build_entity_profiler_panel(entity_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-metrics/status")
async def onchain_metrics_suite_status_route():
    """#737 On-Chain Metrics Suite — HODL waves absorbed."""
    from bd_platform.onchain_metrics_suite import onchain_metrics_suite_status

    return onchain_metrics_suite_status()


@router.get("/intelligence-ledger/onchain-metrics")
async def onchain_metrics_panel_route(asset: str = Query("BTC")):
    from bd_platform.onchain_metrics_suite import build_onchain_metrics_panel

    result = build_onchain_metrics_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/market-data/indices/status")
async def market_data_indices_status_route():
    """#739 Index Data — merged into Market Data API."""
    from bd_platform.market_data_indices import market_data_indices_status

    return market_data_indices_status()


@router.get("/intelligence-ledger/market-data/indices")
async def market_data_indices_feed_route(index_id: str = Query("crypto_top100")):
    from bd_platform.market_data_indices import build_index_feed

    result = build_index_feed(index_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/ma-intelligence/status")
async def ma_intelligence_status_route():
    """#740 M&A Intelligence Module."""
    from bd_platform.ma_intelligence import ma_intelligence_status

    return ma_intelligence_status()


@router.get("/intelligence-ledger/ma-intelligence/deals")
async def ma_intelligence_deal_route(deal_id: str = Query("deal_001")):
    from bd_platform.ma_intelligence import build_ma_deal_panel

    result = build_ma_deal_panel(deal_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/ma-intelligence/trends")
async def ma_intelligence_trends_route():
    from bd_platform.ma_intelligence import build_ma_trends_dashboard

    return build_ma_trends_dashboard()


@router.get("/intelligence-ledger/market-radar/screener/status")
async def market_screener_status_route():
    """#742 Smart Screener — Market Radar."""
    from bd_platform.market_screener import market_screener_status

    return market_screener_status()


@router.get("/intelligence-ledger/market-radar/screener")
async def market_screener_run_route(
    tier: str = Query("free"),
    saved_filter_id: str | None = Query(None),
):
    from bd_platform.market_screener import run_screener

    return run_screener(tier=tier, saved_filter_id=saved_filter_id)


@router.get("/intelligence-ledger/market-radar/screener/saved-filters")
async def market_screener_saved_filters_route():
    from bd_platform.market_screener import list_saved_filters

    return list_saved_filters()


@router.get("/intelligence-ledger/asset-screener/status")
async def asset_screener_status_route():
    """#1008 Asset Screener & Filter Engine — Sprint 2."""
    from bd_platform.asset_screener import asset_screener_status

    return asset_screener_status()


@router.get("/intelligence-ledger/asset-screener/presets")
async def asset_screener_presets_route():
    from bd_platform.asset_screener import list_presets

    return list_presets()


@router.get("/intelligence-ledger/asset-screener")
async def asset_screener_run_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = Query("market_cap_usd"),
    sort_dir: str = Query("desc"),
    include_missing: bool = Query(False),
    preset_id: str | None = Query(None),
):
    from bd_platform.asset_screener import run_asset_screener

    return run_asset_screener(
        sort_by=sort_by,
        sort_dir=sort_dir,  # type: ignore[arg-type]
        page=page,
        page_size=page_size,
        include_missing=include_missing,
        preset_id=preset_id,
    )


@router.post("/intelligence-ledger/asset-screener")
async def asset_screener_run_post_route(
    filters: dict[str, Any] = Body(default_factory=dict),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = Query("market_cap_usd"),
    sort_dir: str = Query("desc"),
    include_missing: bool = Query(False),
    preset_id: str | None = Query(None),
):
    """#1008 server-side filter body — all filters enforced backend."""
    from bd_platform.asset_screener import run_asset_screener

    return run_asset_screener(
        filters=filters,
        sort_by=sort_by,
        sort_dir=sort_dir,  # type: ignore[arg-type]
        page=page,
        page_size=page_size,
        include_missing=include_missing,
        preset_id=preset_id,
    )


@router.get("/intelligence-ledger/asset-screener/export")
async def asset_screener_export_route(
    export_format: str = Query("json", alias="format"),
    sort_by: str = Query("market_cap_usd"),
    sort_dir: str = Query("desc"),
    include_missing: bool = Query(False),
    preset_id: str | None = Query(None),
):
    from bd_platform.asset_screener import export_screener_results

    if export_format not in ("csv", "json"):
        raise HTTPException(status_code=400, detail="format must be csv or json")
    return export_screener_results(
        sort_by=sort_by,
        sort_dir=sort_dir,  # type: ignore[arg-type]
        export_format=export_format,  # type: ignore[arg-type]
        include_missing=include_missing,
        preset_id=preset_id,
    )


@router.get("/intelligence-ledger/surveillance/status")
async def surveillance_engine_status_route():
    """#743 Surveillance Engine — absorbs #721."""
    from bd_platform.surveillance_engine import surveillance_engine_status

    return surveillance_engine_status()


@router.get("/intelligence-ledger/surveillance")
async def surveillance_engine_panel_route(
    tier: str = Query("free"),
    case_id: str | None = Query(None),
):
    from bd_platform.surveillance_engine import build_surveillance_panel

    return build_surveillance_panel(tier=tier, case_id=case_id)


@router.get("/intelligence-ledger/options-context/status")
async def options_context_status_route():
    """#744 Options Context Module — BTC/ETH max pain/gamma."""
    from bd_platform.options_context import options_context_status

    return options_context_status()


@router.get("/intelligence-ledger/options-context")
async def options_context_panel_route(asset: str = Query("BTC")):
    from bd_platform.options_context import build_options_context_panel

    result = build_options_context_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result
