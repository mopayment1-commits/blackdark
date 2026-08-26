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
