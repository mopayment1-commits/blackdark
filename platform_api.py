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
