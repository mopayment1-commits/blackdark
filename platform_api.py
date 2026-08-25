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


@router.get("/canonical/resolve")
async def canonical_resolve(input: str = Query(..., min_length=1, max_length=128)):
    """Infrastructure — resolve any symbol/alias/pair to canonical asset ID."""
    from blackdark.canonical.resolver import resolve_asset

    return resolve_asset(input).to_dict()


@router.get("/canonical/assets")
async def canonical_assets(limit: int = Query(105, ge=1, le=200)):
    """Infrastructure — canonical asset reference list (stable mapping)."""
    from blackdark.canonical.registry import all_canonical_assets, registry_stats

    assets = all_canonical_assets()[:limit]
    return {
        "ok": True,
        "count": len(assets),
        "assets": [a.to_dict() for a in assets],
        "stats": registry_stats(),
    }


@router.get("/canonical/layer/status")
async def canonical_layer_status():
    """Infrastructure — Canonical Data Layer health + bootstrap stats."""
    from blackdark.canonical.layer import get_canonical_layer

    layer = get_canonical_layer()
    stats = await layer.bootstrap(persist=True)
    return {**layer.status(), "bootstrap": stats}


@router.post("/canonical/ingest")
async def canonical_ingest(
    source: str = Query(...),
    dataset: str = Query(...),
    payload: dict[str, Any] = Body(...),
    asset_hint: str | None = Query(None),
):
    """Infrastructure — normalize + persist a vendor payload under canonical ID."""
    from blackdark.canonical.layer import get_canonical_layer

    layer = get_canonical_layer()
    return await layer.ingest(
        source=source,
        dataset=dataset,
        raw=payload,
        asset_hint=asset_hint,
    )


@router.get("/ingestion/coingecko/status")
async def ingestion_coingecko_status():
    """Infrastructure — CoinGecko primary ingestion connector health."""
    from blackdark.ingestion.coingecko_connector import coingecko_connector_status

    return coingecko_connector_status()


@router.get("/ingestion/coingecko/price")
async def ingestion_coingecko_price(asset: str = Query("BTC")):
    """Infrastructure — normalized CoinGecko price with canonical ID + fallback."""
    from blackdark.ingestion.coingecko_connector import fetch_coingecko_price

    return await fetch_coingecko_price(asset)


@router.get("/ingestion/coingecko/markets")
async def ingestion_coingecko_markets(per_page: int = Query(50, ge=10, le=250)):
    from blackdark.ingestion.coingecko_connector import fetch_coingecko_markets

    return await fetch_coingecko_markets(per_page=per_page)


@router.post("/ingestion/coingecko/sync")
async def ingestion_coingecko_sync():
    """Trigger primary CoinGecko ingestion pass into data lake."""
    from blackdark.ingestion.coingecko_connector import run_coingecko_primary_ingest

    return await run_coingecko_primary_ingest()


@router.get("/alpha/signal")
async def alpha_engine_signal(asset: str = Query("BTC")):
    """Alpha Engine (#13) — unified signal from all input sources."""
    from bd_platform.alpha_engine import compute_alpha_signal

    return await compute_alpha_signal(asset)


@router.get("/alpha/ranking")
async def alpha_engine_ranking(limit: int = Query(25, ge=5, le=50)):
    """Alpha Engine (#13) — ranked universe using multi-source inputs."""
    from bd_platform.alpha_engine import rank_alpha_universe

    return await rank_alpha_universe(limit=limit)


@router.get("/defi/il/pools")
async def il_pools(query: str = Query("ETH USDC"), limit: int = Query(15, ge=1, le=30)):
    from lp_il_simulator import fetch_live_pools

    return await fetch_live_pools(query, limit=limit)


@router.get("/defi/il/live")
async def il_live_simulator(
    token_a: str = Query("ETH"),
    token_b: str = Query("USDC"),
    amount_usd: float = Query(10_000, gt=0, le=10_000_000),
    price_change_pct: float | None = Query(None),
    horizon_days: float = Query(30, gt=0, le=365),
    pair_address: str | None = None,
    persist: bool = Query(False),
):
    from lp_il_simulator import persist_simulation, simulate_lp_live

    result = await simulate_lp_live(
        token_a=token_a,
        token_b=token_b,
        amount_usd=amount_usd,
        price_change_pct=price_change_pct,
        horizon_days=horizon_days,
        pair_address=pair_address,
    )
    if persist and result.get("ok"):
        log_id = await persist_simulation(result)
        result["simulation_log_id"] = log_id
    return result


@router.post("/defi/il/simulate")
async def il_simulate_post(body: dict = Body(...)):
    from lp_il_simulator import persist_simulation, simulate_lp_live, simulate_lp_position

    if body.get("live", True):
        result = await simulate_lp_live(
            token_a=str(body.get("token_a", "ETH")),
            token_b=str(body.get("token_b", "USDC")),
            amount_usd=float(body.get("amount_usd", 10_000)),
            price_change_pct=body.get("price_change_pct"),
            horizon_days=float(body.get("horizon_days", 30)),
            pair_address=body.get("pair_address"),
        )
    else:
        result = simulate_lp_position(
            amount_usd=float(body.get("amount_usd", 10_000)),
            entry_price=float(body["entry_price"]),
            exit_price=float(body["exit_price"]),
            fee_apy_pct=float(body.get("fee_apy_pct", 0)),
            horizon_days=float(body.get("horizon_days", 30)),
        )
    if body.get("persist") and result.get("ok"):
        log_id = await persist_simulation(result if "simulation" in result else {"simulation": result})
        result["simulation_log_id"] = log_id
    return result


@router.get("/defi/il/vulnerability-score")
async def il_vulnerability(
    symbol: str = Query("ETH-USDC"),
    volatility_30d_pct: float | None = None,
    liquidity_usd: float | None = None,
    fee_apy_pct: float | None = None,
):
    from lp_il_simulator import il_vulnerability_score

    return il_vulnerability_score(
        symbol=symbol,
        volatility_30d_pct=volatility_30d_pct,
        liquidity_usd=liquidity_usd,
        fee_apy_pct=fee_apy_pct,
    )


@router.get("/defi/il/history")
async def il_simulation_history(limit: int = Query(20, ge=1, le=100)):
    from database import fetch_simulation_logs

    rows = await fetch_simulation_logs(limit=limit)
    return {"kind": "lp_il", "simulations": [r for r in rows if r.get("kind") == "lp_il"]}


@router.get("/onchain/mvrv-realignment")
async def mvrv_realignment(asset: str = Query("BTC")):
    from bd_platform.mvrv_realignment import compute_mvrv_realignment

    return await compute_mvrv_realignment(asset)


@router.get("/alpha/factor-ranking")
async def alpha_factor_ranking(limit: int = Query(25, ge=5, le=50)):
    from bd_platform.alpha_factor_ranking import rank_assets_by_alpha_factors

    return await rank_assets_by_alpha_factors(limit=limit)


@router.get("/squeeze/triggers")
async def squeeze_triggers(asset: str = Query("BTC")):
    from bd_platform.squeeze_trigger_engine import squeeze_trigger_coordinates

    return await squeeze_trigger_coordinates(asset)


@router.get("/intelligence-ledger/execution")
async def intelligence_ledger_execution(
    asset: str = Query("ETH"),
    amount_usd: float = Query(10_000.0, ge=100.0, le=10_000_000.0),
    chain: str = Query("ethereum"),
    side: str = Query("buy"),
    user_tolerance_bps: int | None = Query(None, ge=10, le=300),
):
    """Sprint 2 — best execution path from 1inch + AMM + CEX + slippage optimizer."""
    from bd_platform.intelligence_ledger import build_execution_intelligence

    return await build_execution_intelligence(
        asset=asset,
        amount_usd=amount_usd,
        chain=chain,
        side=side,
        user_tolerance_bps=user_tolerance_bps,
    )


@router.get("/intelligence-ledger/slippage-optimize")
async def intelligence_ledger_slippage(
    asset: str = Query("ETH"),
    amount_usd: float = Query(10_000.0, ge=100.0, le=10_000_000.0),
    chain: str = Query("ethereum"),
    user_tolerance_bps: int | None = Query(None, ge=10, le=300),
):
    """Slippage Intelligence Module (#5 + #17) — self-optimization + asymmetric cost."""
    from bd_platform.slippage_tolerance_optimizer import optimize_slippage_tolerance

    return await optimize_slippage_tolerance(
        asset,
        amount_usd=amount_usd,
        chain=chain,
        user_tolerance_bps=user_tolerance_bps,
    )


@router.get("/address-intelligence/search")
async def address_intelligence_search(
    address: str = Query(..., min_length=10),
    chain: str = Query("ethereum"),
):
    """On-Chain Address Intelligence (#10) — unified address search."""
    from bd_platform.address_intelligence import search_address

    return await search_address(address, chain=chain)


@router.get("/address-intelligence/history")
async def address_intelligence_history(
    address: str = Query(..., min_length=10),
    chain: str = Query("ethereum"),
    days: int = Query(30, ge=1, le=90),
):
    """On-Chain Address Intelligence (#19) — balance history chart data."""
    from bd_platform.address_intelligence import balance_history

    return await balance_history(address, chain=chain, days=days)


@router.get("/address-intelligence/updates")
async def address_intelligence_updates(
    address: str = Query(..., min_length=10),
    chain: str = Query("ethereum"),
    limit: int = Query(20, ge=1, le=50),
):
    """On-Chain Address Intelligence (#20) — balance update feed (state diffs)."""
    from bd_platform.address_intelligence import balance_updates

    return await balance_updates(address, chain=chain, limit=limit)


@router.get("/address-intelligence/overview")
async def address_intelligence_overview_route(
    address: str = Query(..., min_length=10),
    chain: str = Query("ethereum"),
    history_days: int = Query(30, ge=1, le=90),
):
    """Unified On-Chain Address Intelligence — search + history + updates."""
    from bd_platform.address_intelligence import address_intelligence_overview

    return await address_intelligence_overview(address, chain=chain, history_days=history_days)


@router.get("/decision-intelligence/signal")
async def decision_intelligence_signal(
    asset: str = Query("BTC"),
    include_backtest: bool = Query(True),
):
    """Decision Intelligence Engine (#48) — actionable signal with reasoning."""
    from bd_platform.decision_intelligence_engine import generate_decision_signal

    return await generate_decision_signal(asset, include_backtest=include_backtest)


@router.get("/decision-intelligence/ranking")
async def decision_intelligence_ranking_route(limit: int = Query(10, ge=3, le=20)):
    """Decision Intelligence — ranked universe by confidence."""
    from bd_platform.decision_intelligence_engine import decision_intelligence_ranking

    return await decision_intelligence_ranking(limit=limit)


@router.get("/decision-intelligence/features")
async def decision_intelligence_features(asset: str = Query("BTC")):
    """Decision Intelligence — 100+ feature extraction."""
    from ml.decision_features import extract_decision_features

    return await extract_decision_features(asset)


@router.get("/decision-intelligence/backtest")
async def decision_intelligence_backtest(asset: str = Query("BTC")):
    """Decision Intelligence — walk-forward backtest + risk metrics."""
    from ml.walk_forward import run_walk_forward_backtest

    return await run_walk_forward_backtest(asset)


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


# ── Feature #155 — Market Radar Infrastructure ───────────────────────────────


@router.get("/market-radar/dashboard")
async def market_radar_dashboard_route(
    asset: str = Query("BTC"),
    assets: str = Query("BTC,ETH,SOL", description="Comma-separated assets for price matrix"),
):
    """Unified Market Radar dashboard — #155 + #140 + #186 + #142 + #139."""
    from bd_platform.market_radar_dashboard import build_market_radar_dashboard

    asset_list = [a.strip() for a in assets.split(",") if a.strip()]
    return await build_market_radar_dashboard(asset, focus_assets=asset_list)


@router.get("/market-radar/dashboard/status")
async def market_radar_dashboard_status_route():
    from bd_platform.market_radar_dashboard import market_radar_dashboard_status

    return market_radar_dashboard_status()


@router.get("/market-radar/order-book")
async def global_order_book_route(
    asset: str = Query("BTC"),
    tier: str = Query("pro"),
):
    """Global Order Book tab — #249 merged into Market Radar."""
    from bd_platform.global_order_book import build_global_order_book_panel

    result = build_global_order_book_panel(asset, tier=tier)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/market-radar/order-book/status")
async def global_order_book_status_route():
    from bd_platform.global_order_book import global_order_book_status

    return global_order_book_status()


# ── Order Book Feed — #256 + #257 + #258 merged (Sprint 0) ─────────────────────


@router.get("/order-book-feed/status")
async def order_book_feed_status_route():
    from bd_platform.order_book_feed import order_book_feed_status

    return order_book_feed_status()


@router.get("/order-book-feed")
async def order_book_feed_route(
    asset: str = Query("BTC"),
    level: str = Query("L1", description="L1 | L2 | L3"),
    venue: str = Query("binance"),
    tier: str = Query("pro"),
):
    from bd_platform.order_book_feed import get_order_book_feed

    if level.upper() not in ("L1", "L2", "L3"):
        raise HTTPException(status_code=400, detail="level must be L1, L2, or L3")
    result = get_order_book_feed(asset, level=level.upper(), venue=venue, tier=tier)  # type: ignore[arg-type]
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/market-radar/infrastructure/status")
async def market_radar_infrastructure_status_route():
    """Multi-exchange price monitoring infrastructure (#155)."""
    from bd_platform.market_radar_infrastructure import market_radar_infrastructure_status

    return market_radar_infrastructure_status()


@router.get("/market-radar/prices/matrix")
async def market_radar_price_matrix_route(
    assets: str = Query("BTC,ETH,SOL", description="Comma-separated assets"),
    max_assets: int = Query(20, ge=1, le=50),
):
    """Cross-exchange price matrix — infrastructure behind Market Radar (#155)."""
    from bd_platform.market_radar_infrastructure import monitor_multi_asset_prices

    asset_list = [a.strip() for a in assets.split(",") if a.strip()]
    return await monitor_multi_asset_prices(asset_list or None, max_assets=max_assets)


# ── Feature #140 — Macro Events Calendar ─────────────────────────────────────


@router.get("/market-radar/macro-events")
async def macro_events_calendar_route(limit: int = Query(15, ge=1, le=50)):
    """Macro Events Calendar with impact forecasting (#140)."""
    from bd_platform.macro_events_engine import build_macro_events_calendar

    return await build_macro_events_calendar(limit=limit)


@router.get("/market-radar/macro-events/status")
async def macro_events_status_route():
    from bd_platform.macro_events_engine import macro_events_status

    return macro_events_status()


# ── Feature #186 — Industry Event Monitor ────────────────────────────────────


@router.get("/market-radar/events/stream")
async def industry_event_stream_route(
    limit: int = Query(50, ge=1, le=200),
    category: str | None = Query(None),
):
    """Real-time industry event stream (#186)."""
    from bd_platform.industry_event_monitor import get_event_feed

    return get_event_feed(limit=limit, category=category)


@router.post("/market-radar/events/scan", responses=COMMON_ERROR_RESPONSES)
async def industry_event_scan_route(_admin: dict = Depends(require_admin)):
    """Trigger event source scan (#186)."""
    from bd_platform.industry_event_monitor import scan_event_sources

    return await scan_event_sources()


@router.get("/market-radar/events/status")
async def industry_event_status_route():
    from bd_platform.industry_event_monitor import industry_event_monitor_status

    return industry_event_monitor_status()


# ── Feature #142 — Liquidity Health Check ────────────────────────────────────


@router.get("/market-radar/liquidity-health")
async def liquidity_health_route(
    asset: str = Query("ETH"),
    chain: str = Query("ethereum"),
):
    """Liquidity Health Check — required before token purchase (#142)."""
    from bd_platform.liquidity_health_check import analyze_liquidity_health

    return await analyze_liquidity_health(asset, chain=chain)


@router.get("/market-radar/liquidity-health/status")
async def liquidity_health_status_route():
    from bd_platform.liquidity_health_check import liquidity_health_status

    return liquidity_health_status()


# ── Feature #139 — Sentiment Intelligence ────────────────────────────────────


@router.get("/market-radar/sentiment")
async def sentiment_intelligence_route(asset: str = Query("BTC")):
    """Weighted multi-source sentiment (#139)."""
    from bd_platform.sentiment_intelligence import analyze_asset_sentiment

    return await analyze_asset_sentiment(asset)


@router.get("/market-radar/sentiment/overview")
async def sentiment_intelligence_overview_route(
    assets: str = Query("BTC,ETH,SOL,BNB,XRP"),
):
    """Multi-asset sentiment overview (#139)."""
    from bd_platform.sentiment_intelligence import sentiment_intelligence_overview

    asset_list = [a.strip() for a in assets.split(",") if a.strip()]
    return await sentiment_intelligence_overview(assets=asset_list or None)


@router.get("/market-radar/sentiment/status")
async def sentiment_intelligence_status_route():
    from bd_platform.sentiment_intelligence import sentiment_intelligence_status

    return sentiment_intelligence_status()


# ── Feature #156 — Exit Strategy Assistant ───────────────────────────────────


@router.get("/oracle/exit-zone")
async def exit_zone_route(
    asset: str = Query("BTC"),
    entry_price: float | None = Query(None),
    zone_low: float | None = Query(None),
    zone_high: float | None = Query(None),
):
    """Recommended Exit Zone — suggestion only, NOT mandatory sell (#156)."""
    from bd_platform.exit_strategy_assistant import compute_recommended_exit_zone

    return await compute_recommended_exit_zone(
        asset,
        entry_price=entry_price,
        custom_zone_low=zone_low,
        custom_zone_high=zone_high,
    )


@router.post("/oracle/exit-zone/save", responses=COMMON_ERROR_RESPONSES)
async def exit_zone_save_route(
    body: dict[str, Any] = Body(...),
    user: dict = Depends(require_authenticated),
):
    """Save user-edited exit zone (#156)."""
    from bd_platform.exit_strategy_assistant import save_user_exit_zone

    asset = str(body.get("asset") or "BTC")
    zone_low = float(body.get("zone_low") or 0)
    zone_high = float(body.get("zone_high") or 0)
    user_id = str(user.get("id") or user.get("email") or "user")
    return save_user_exit_zone(asset, zone_low=zone_low, zone_high=zone_high, user_id=user_id)


@router.get("/oracle/exit-zone/status")
async def exit_zone_status_route():
    from bd_platform.exit_strategy_assistant import exit_strategy_status

    return exit_strategy_status()


# ── Feature #160 — DeFi Safety Layer ─────────────────────────────────────────


@router.get("/defi/contract-safety")
async def defi_contract_safety_route(
    address: str = Query(..., min_length=42, max_length=42),
    chain: str = Query("ethereum"),
    protocol: str | None = Query(None),
):
    """Passive smart contract risk scan — flags only, no 100% guarantee (#160)."""
    from bd_platform.defi_safety_layer import scan_contract_risk

    return await scan_contract_risk(address, chain=chain, protocol_name=protocol or "")


@router.get("/defi/contract-safety/status")
async def defi_contract_safety_status_route():
    from bd_platform.defi_safety_layer import defi_safety_status

    return defi_safety_status()


# ── Features #177 + #182 — Public Content Hub ────────────────────────────────


@router.post("/share/content", responses=COMMON_ERROR_RESPONSES)
async def create_content_route(
    body: dict[str, Any] = Body(...),
    user: dict = Depends(require_authenticated),
):
    """Create chart, idea, or dashboard share draft (#177 + #182)."""
    from bd_platform.public_content_hub import create_content

    owner = str(user.get("id") or user.get("email") or "0")
    return create_content(
        owner_id=owner,
        title=str(body.get("title") or "Untitled"),
        content_type=str(body.get("content_type") or "chart"),  # type: ignore[arg-type]
        content_data=body.get("content_data") if isinstance(body.get("content_data"), dict) else {},
        dashboard_metadata=body.get("dashboard_metadata")
        if isinstance(body.get("dashboard_metadata"), dict)
        else {},
        notes=str(body.get("notes") or ""),
        privacy=str(body.get("privacy") or "private"),  # type: ignore[arg-type]
    )


@router.post("/share/content/capture-dashboard", responses=COMMON_ERROR_RESPONSES)
async def capture_dashboard_route(
    body: dict[str, Any] = Body(default_factory=dict),
    user: dict = Depends(require_authenticated),
):
    """Capture Market Radar dashboard snapshot draft (#182)."""
    from bd_platform.public_content_hub import capture_dashboard_snapshot

    owner = str(user.get("id") or user.get("email") or "0")
    return await capture_dashboard_snapshot(
        owner_id=owner,
        title=str(body.get("title") or ""),
        asset=str(body.get("asset") or "BTC"),
        privacy=str(body.get("privacy") or "private"),  # type: ignore[arg-type]
    )


@router.post("/share/content/{item_id}/publish", responses=COMMON_ERROR_RESPONSES)
async def publish_content_route(
    item_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    user: dict = Depends(require_authenticated),
):
    """Publish immutable versioned snapshot (#177 + #182)."""
    from bd_platform.public_content_hub import publish_content

    return publish_content(
        item_id=item_id,
        owner_id=str(user.get("id") or user.get("email") or "0"),
        privacy=str(body.get("privacy") or "unlisted"),  # type: ignore[arg-type]
    )


@router.put("/share/content/{item_id}", responses=COMMON_ERROR_RESPONSES)
async def update_content_route(
    item_id: str,
    body: dict[str, Any] = Body(...),
    user: dict = Depends(require_authenticated),
):
    """Update owner draft — published snapshot unchanged (#177 + #182)."""
    from bd_platform.public_content_hub import update_content_draft

    return update_content_draft(
        item_id=item_id,
        owner_id=str(user.get("id") or user.get("email") or "0"),
        title=body.get("title"),
        content_data=body.get("content_data") if isinstance(body.get("content_data"), dict) else None,
        dashboard_metadata=body.get("dashboard_metadata")
        if isinstance(body.get("dashboard_metadata"), dict)
        else None,
        notes=body.get("notes"),
        privacy=body.get("privacy"),  # type: ignore[arg-type]
    )


@router.post("/share/content/{item_id}/clone", responses=COMMON_ERROR_RESPONSES)
async def clone_content_route(
    item_id: str,
    user: dict = Depends(require_authenticated),
):
    """Clone published snapshot to a new private draft — view + clone only (#182)."""
    from bd_platform.public_content_hub import clone_content

    return clone_content(
        item_id=item_id,
        owner_id=str(user.get("id") or user.get("email") or "0"),
    )


@router.get("/share/content")
async def list_content_route(user: dict = Depends(require_authenticated)):
    """List user's shared content (#177 + #182)."""
    from bd_platform.public_content_hub import list_user_content

    return list_user_content(str(user.get("id") or user.get("email") or "0"))


@router.get("/share/view/{slug}")
async def public_content_view_route(slug: str):
    """Public/unlisted immutable snapshot view (#177 + #182)."""
    from bd_platform.public_content_hub import get_public_view

    result = get_public_view(slug)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/share/status")
async def public_content_hub_status_route():
    from bd_platform.public_content_hub import public_content_hub_status

    return public_content_hub_status()


# ── Feature #177 — Chart / Idea Sharing (compatibility aliases) ───────────────


@router.post("/share/charts", responses=COMMON_ERROR_RESPONSES)
async def create_chart_share_route(
    body: dict[str, Any] = Body(...),
    user: dict = Depends(require_authenticated),
):
    from bd_platform.chart_sharing_service import create_chart_share

    return create_chart_share(
        owner_id=str(user.get("id") or user.get("email") or "0"),
        title=str(body.get("title") or "Untitled"),
        chart_type=str(body.get("chart_type") or "idea"),
        chart_data=body.get("chart_data") if isinstance(body.get("chart_data"), dict) else {},
        notes=str(body.get("notes") or ""),
        privacy=str(body.get("privacy") or "private"),
    )


@router.post("/share/charts/{share_id}/publish", responses=COMMON_ERROR_RESPONSES)
async def publish_chart_share_route(
    share_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    user: dict = Depends(require_authenticated),
):
    from bd_platform.chart_sharing_service import publish_chart_share

    return publish_chart_share(
        share_id=share_id,
        owner_id=str(user.get("id") or user.get("email") or "0"),
        privacy=str(body.get("privacy") or "unlisted"),
    )


@router.put("/share/charts/{share_id}", responses=COMMON_ERROR_RESPONSES)
async def update_chart_share_route(
    share_id: str,
    body: dict[str, Any] = Body(...),
    user: dict = Depends(require_authenticated),
):
    from bd_platform.chart_sharing_service import update_chart_share

    return update_chart_share(
        share_id=share_id,
        owner_id=str(user.get("id") or user.get("email") or "0"),
        title=body.get("title"),
        chart_data=body.get("chart_data") if isinstance(body.get("chart_data"), dict) else None,
        notes=body.get("notes"),
        privacy=body.get("privacy"),
    )


@router.get("/share/charts")
async def list_chart_shares_route(user: dict = Depends(require_authenticated)):
    from bd_platform.chart_sharing_service import list_user_chart_shares

    return list_user_chart_shares(str(user.get("id") or user.get("email") or "0"))


@router.get("/share/chart/{slug}")
async def public_chart_view_route(slug: str):
    from bd_platform.chart_sharing_service import get_public_chart_view

    result = get_public_chart_view(slug)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


# ── Feature #187 — BLACKDARK Research Portal ─────────────────────────────────


@router.get("/research/status")
async def research_portal_status_route():
    from bd_platform.research_portal import research_portal_status

    return research_portal_status()


@router.get("/research/search")
async def research_search_route(
    q: str = Query("", description="Search query — supports Arabic semantic search"),
    mode: str = Query("fulltext", description="fulltext or semantic"),
    sector: str | None = Query(None),
    asset: str | None = Query(None),
    author: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    from bd_platform.research_portal import search_reports

    return search_reports(
        q,
        mode="semantic" if mode == "semantic" else "fulltext",  # type: ignore[arg-type]
        sector=sector,
        asset=asset,
        author=author,
        limit=limit,
    )


@router.get("/research/filters")
async def research_filters_route():
    from bd_platform.research_portal import list_filters

    return list_filters()


@router.get("/research/reports/{report_id}")
async def research_report_route(
    report_id: str,
    version: int | None = Query(None),
):
    from bd_platform.research_portal import get_report

    result = get_report(report_id, version=version)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.put("/research/reports/{report_id}", responses=COMMON_ERROR_RESPONSES)
async def research_update_route(
    report_id: str,
    body: dict[str, Any] = Body(...),
    user: dict = Depends(require_authenticated),
):
    """Update report — archives previous version (#187)."""
    from bd_platform.research_portal import update_report

    return update_report(
        report_id,
        editor_id=str(user.get("id") or user.get("email") or "editor"),
        title=body.get("title"),
        summary=body.get("summary"),
        body=body.get("body"),
        tags=body.get("tags") if isinstance(body.get("tags"), list) else None,
    )


@router.post("/research/saved/{report_id}", responses=COMMON_ERROR_RESPONSES)
async def research_save_route(report_id: str, user: dict = Depends(require_authenticated)):
    from bd_platform.research_portal import save_report_for_user

    return save_report_for_user(str(user.get("id") or user.get("email") or "0"), report_id)


@router.delete("/research/saved/{report_id}", responses=COMMON_ERROR_RESPONSES)
async def research_unsave_route(report_id: str, user: dict = Depends(require_authenticated)):
    from bd_platform.research_portal import unsave_report_for_user

    return unsave_report_for_user(str(user.get("id") or user.get("email") or "0"), report_id)


@router.get("/research/saved")
async def research_saved_list_route(user: dict = Depends(require_authenticated)):
    from bd_platform.research_portal import list_saved_reports

    return list_saved_reports(str(user.get("id") or user.get("email") or "0"))


# ── Features #194 + #200 — Connector Coverage Map ────────────────────────────


@router.get("/connectors/coverage")
async def connector_coverage_map_route():
    """Coverage map with live parity — part of Unified Connector (#194/#200)."""
    from bd_platform.connector_coverage_map import build_coverage_map

    return await build_coverage_map()


@router.get("/connectors/coverage/status")
async def connector_coverage_status_route():
    from bd_platform.connector_coverage_map import connector_coverage_status

    return connector_coverage_status()


# ── Feature #197 — Weighted Social Sentiment (Sentiment Quality Engine) ──────


@router.get("/sentiment/quality")
async def sentiment_quality_route(asset: str = Query("BTC")):
    """Weighted social sentiment with explain contributors (#197)."""
    from bd_platform.weighted_social_sentiment import analyze_weighted_social_sentiment

    return await analyze_weighted_social_sentiment(asset)


@router.get("/sentiment/quality/status")
async def sentiment_quality_status_route():
    from bd_platform.weighted_social_sentiment import weighted_social_sentiment_status

    return weighted_social_sentiment_status()


@router.post("/sentiment/quality/manipulation-test")
async def sentiment_manipulation_test_route(
    body: dict[str, Any] = Body(default_factory=dict),
):
    """Run manipulation resistance test (#197)."""
    from bd_platform.weighted_social_sentiment import (
        run_manipulation_resistance_test,
        _default_contributors,
    )

    asset = str(body.get("asset") or "BTC")
    bots = int(body.get("bot_count") or 100)
    contributors = _default_contributors(asset, 0.3)
    return run_manipulation_resistance_test(contributors, bot_count=bots)


# ── Feature #203 — Incentive Tracker Module ──────────────────────────────────


@router.get("/incentives/status")
async def incentive_tracker_status_route():
    from bd_platform.incentive_tracker import incentive_tracker_status

    return incentive_tracker_status()


@router.get("/incentives")
async def incentive_programs_list_route(
    status: str | None = Query(None),
    protocol: str | None = Query(None),
    chain: str | None = Query(None),
    limit: int = Query(100, ge=1, le=200),
):
    from bd_platform.incentive_tracker import list_incentive_programs

    return list_incentive_programs(
        status=status,  # type: ignore[arg-type]
        protocol=protocol,
        chain=chain,
        limit=limit,
    )


@router.get("/incentives/{program_id}")
async def incentive_program_detail_route(program_id: str):
    from bd_platform.incentive_tracker import get_incentive_program

    result = get_incentive_program(program_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


# ── Feature #206 — Analyst Notes Feed (lightweight, not consensus engine) ─────


@router.get("/analyst-notes/status")
async def analyst_notes_status_route():
    from bd_platform.analyst_notes_feed import analyst_notes_status

    return analyst_notes_status()


@router.get("/analyst-notes")
async def analyst_notes_list_route(
    asset: str | None = Query(None),
    firm: str | None = Query(None),
    view: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    from bd_platform.analyst_notes_feed import list_analyst_notes

    return list_analyst_notes(asset=asset, firm=firm, view=view, limit=limit)  # type: ignore[arg-type]


@router.get("/analyst-notes/summary/{asset}")
async def analyst_notes_summary_route(asset: str):
    from bd_platform.analyst_notes_feed import get_asset_analyst_summary

    return get_asset_analyst_summary(asset)


@router.get("/analyst-notes/{note_id}")
async def analyst_note_detail_route(note_id: str):
    from bd_platform.analyst_notes_feed import get_analyst_note

    result = get_analyst_note(note_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


# ── Feature #208 — Source Registry & Provenance Layer (#118 merged) ──────────


@router.get("/provenance/status")
async def source_registry_status_route():
    from bd_platform.source_registry_provenance import source_registry_status

    return source_registry_status()


@router.get("/provenance/registry")
async def source_registry_route():
    from bd_platform.source_registry_provenance import build_source_registry

    return build_source_registry()


@router.get("/provenance/lineage/{metric}")
async def provenance_lineage_route(metric: str, asset: str = Query("BTC")):
    from bd_platform.source_registry_provenance import trace_metric_lineage

    return trace_metric_lineage(metric, asset)


@router.post("/provenance/reconcile")
async def provenance_reconcile_route(body: dict[str, Any] = Body(...)):
    from bd_platform.source_registry_provenance import reconcile_sources

    readings = body.get("readings") if isinstance(body.get("readings"), list) else []
    return reconcile_sources(readings)


@router.post("/provenance/provider-test")
async def provider_degradation_test_route():
    from bd_platform.source_registry_provenance import run_provider_degradation_test

    return await run_provider_degradation_test()


# ── Feature #211 — Economic Calendar (widget import + asset relevance) ───────


@router.get("/economic-calendar/status")
async def economic_calendar_status_route():
    from bd_platform.economic_calendar import economic_calendar_status

    return economic_calendar_status()


@router.get("/economic-calendar/widget")
async def economic_calendar_widget_route(
    theme: str = Query("dark"),
    locale: str = Query("en"),
):
    from bd_platform.economic_calendar import tradingview_widget_config

    return tradingview_widget_config(theme=theme, locale=locale)


@router.get("/economic-calendar")
async def economic_calendar_list_route(
    asset: str | None = Query(None),
    country: str | None = Query(None),
    category: str | None = Query(None),
    impact: str | None = Query(None),
    upcoming_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
):
    from bd_platform.economic_calendar import list_economic_events

    return list_economic_events(
        asset=asset,
        country=country,
        category=category,
        impact=impact,  # type: ignore[arg-type]
        upcoming_only=upcoming_only,
        limit=limit,
    )


@router.get("/economic-calendar/relevance/{asset}")
async def economic_calendar_relevance_route(asset: str):
    from bd_platform.economic_calendar import get_asset_calendar_relevance

    return get_asset_calendar_relevance(asset)


@router.get("/economic-calendar/{event_id}")
async def economic_calendar_detail_route(event_id: str):
    from bd_platform.economic_calendar import get_economic_event

    result = get_economic_event(event_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


# ── Feature #212 — Block-Level Ingestion Layer ───────────────────────────────


@router.get("/block-ingestion/status")
async def block_ingestion_status_route():
    from bd_platform.block_level_ingestion import block_level_ingestion_status

    return block_level_ingestion_status()


@router.get("/block-ingestion/latency-slo")
async def block_ingestion_latency_slo_route(chain: str | None = Query(None)):
    from bd_platform.block_level_ingestion import measure_latency_slo

    return measure_latency_slo(chain=chain)


@router.get("/block-ingestion/gaps")
async def block_ingestion_gaps_route(chain: str | None = Query(None)):
    from bd_platform.block_level_ingestion import get_gap_alerts

    return get_gap_alerts(chain=chain)


@router.get("/block-ingestion/feeds")
async def block_ingestion_feeds_route(
    chain: str | None = Query(None),
    tier: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    from bd_platform.block_level_ingestion import list_block_feeds

    return list_block_feeds(chain=chain, tier=tier, limit=limit)  # type: ignore[arg-type]


@router.get("/block-ingestion/bars/{chain_id}")
async def block_ingestion_bars_route(chain_id: str, limit: int = Query(10, ge=1, le=100)):
    from bd_platform.block_level_ingestion import aggregate_minute_bars

    result = aggregate_minute_bars(chain_id, limit=limit)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/block-ingestion/blocks/{block_id}")
async def block_ingestion_block_detail_route(block_id: str):
    from bd_platform.block_level_ingestion import get_block

    result = get_block(block_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.post("/block-ingestion/reorg")
async def block_ingestion_reorg_route(body: dict[str, Any] = Body(...)):
    from bd_platform.block_level_ingestion import handle_reorg

    return handle_reorg(
        str(body.get("chain_id") or ""),
        int(body.get("block_height") or 0),
        str(body.get("old_hash") or ""),
        str(body.get("new_hash") or ""),
    )


# ── Feature #209+#213 — Drift Monitoring Engine (merged) ─────────────────────


@router.get("/drift-monitoring/status")
async def drift_monitoring_status_route():
    from bd_platform.drift_monitoring_engine import drift_monitoring_status

    return drift_monitoring_status()


@router.get("/drift-monitoring/baselines")
async def drift_baselines_list_route():
    from bd_platform.drift_monitoring_engine import list_baselines

    return list_baselines()


@router.get("/drift-monitoring/baselines/{version}")
async def drift_baseline_detail_route(version: str):
    from bd_platform.drift_monitoring_engine import get_baseline

    result = get_baseline(version)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/drift-monitoring/dashboard")
async def drift_dashboard_route(model_id: str = Query("oracle_signal_v3")):
    from bd_platform.drift_monitoring_engine import get_drift_dashboard

    return get_drift_dashboard(model_id=model_id)


@router.post("/drift-monitoring/detect")
async def drift_detect_route(body: dict[str, Any] = Body(...)):
    from bd_platform.drift_monitoring_engine import detect_drift

    values = body.get("values") if isinstance(body.get("values"), dict) else {}
    return detect_drift(
        values,
        baseline_version=body.get("baseline_version"),
        model_id=str(body.get("model_id") or "oracle_signal_v3"),
    )


@router.post("/drift-monitoring/review")
async def drift_review_route(body: dict[str, Any] = Body(...)):
    from bd_platform.drift_monitoring_engine import review_drift_alert

    return review_drift_alert(
        str(body.get("alert_id") or ""),
        decision=str(body.get("decision") or "pending"),  # type: ignore[arg-type]
        reviewer=str(body.get("reviewer") or "unknown"),
        notes=str(body.get("notes") or ""),
    )


@router.post("/drift-monitoring/reproducible-test")
async def drift_reproducible_test_route():
    from bd_platform.drift_monitoring_engine import run_reproducible_drift_test

    return run_reproducible_drift_test()


# ── Feature #214 merged — Data Catalog (Metric Availability Registry) ────────


@router.get("/data-catalog/status")
async def data_catalog_status_route():
    from bd_platform.data_catalog import data_catalog_status

    return data_catalog_status()


@router.get("/data-catalog/registry")
async def data_catalog_registry_route():
    from bd_platform.data_catalog import build_metric_registry_from_production

    return build_metric_registry_from_production()


@router.get("/data-catalog/search")
async def data_catalog_search_route(
    asset: str | None = Query(None),
    category: str | None = Query(None),
    metric: str | None = Query(None),
    access: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    from bd_platform.data_catalog import search_metric_availability

    return search_metric_availability(
        asset=asset, category=category, metric=metric, access=access, limit=limit
    )


@router.get("/data-catalog/metrics/{metric_id}")
async def data_catalog_metric_detail_route(metric_id: str):
    from bd_platform.data_catalog import get_metric_detail

    result = get_metric_detail(metric_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.post("/data-catalog/parity-test")
async def data_catalog_parity_test_route():
    from bd_platform.data_catalog import run_parity_tests

    return run_parity_tests()


# ── Feature #215 merged — Data Storage Infrastructure ──────────────────────────


@router.get("/data-storage/status")
async def data_storage_status_route():
    from bd_platform.data_storage_infrastructure import data_storage_infrastructure_status

    return data_storage_infrastructure_status()


@router.get("/data-storage/tiers")
async def data_storage_tiers_route():
    from bd_platform.data_storage_infrastructure import get_storage_tier_status

    return await get_storage_tier_status()


@router.get("/data-storage/retention-policy")
async def data_storage_retention_policy_route():
    from bd_platform.data_storage_infrastructure import get_retention_policy

    return get_retention_policy()


@router.post("/data-storage/restore-test")
async def data_storage_restore_test_route(tier: str = Query("tier1_hot")):
    from bd_platform.data_storage_infrastructure import run_restore_test

    return await run_restore_test(tier=tier)


@router.post("/data-storage/migration-safety")
async def data_storage_migration_safety_route():
    from bd_platform.data_storage_infrastructure import run_migration_safety_check

    return await run_migration_safety_check()


# ── Feature #217 — OHLCV Core Feed ───────────────────────────────────────────


@router.get("/ohlcv/status")
async def ohlcv_core_status_route():
    from bd_platform.ohlcv_core_feed import ohlcv_core_feed_status

    return ohlcv_core_feed_status()


@router.get("/ohlcv/candles")
async def ohlcv_candles_list_route(
    asset: str | None = Query(None),
    interval: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    from bd_platform.ohlcv_core_feed import list_ohlcv_candles

    return list_ohlcv_candles(asset=asset, interval=interval, limit=limit)


@router.get("/ohlcv/candles/{candle_id}")
async def ohlcv_candle_detail_route(candle_id: str):
    from bd_platform.ohlcv_core_feed import get_ohlcv_candle

    result = get_ohlcv_candle(candle_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


# ── Feature #216 — News Context Panel ────────────────────────────────────────


@router.get("/news-context/status")
async def news_context_status_route():
    from bd_platform.news_context_panel import news_context_status

    return news_context_status()


@router.get("/news-context")
async def news_context_list_route(
    asset: str | None = Query(None),
    relevance: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    from bd_platform.news_context_panel import list_news_context

    return list_news_context(asset=asset, relevance=relevance, limit=limit)  # type: ignore[arg-type]


@router.get("/news-context/{card_id}")
async def news_context_card_route(card_id: str):
    from bd_platform.news_context_panel import get_news_card

    result = get_news_card(card_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.post("/news-context/refresh")
async def news_context_refresh_route(limit: int = Query(15, ge=1, le=50)):
    from bd_platform.news_context_panel import refresh_news_from_feeds

    return await refresh_news_from_feeds(limit=limit)


# ── Feature #702 — DeFi TVL Engine (Market Radar DeFi layer) ───────────────────


@router.get("/market-radar/defi/tvl/status")
async def defi_tvl_status_route():
    from bd_platform.defi_tvl_engine import defi_tvl_engine_status

    return defi_tvl_engine_status()


@router.get("/market-radar/defi/tvl/methodology")
async def defi_tvl_methodology_route():
    from bd_platform.defi_tvl_engine import get_methodology

    return get_methodology()


@router.get("/market-radar/defi/tvl")
async def defi_tvl_dashboard_route(
    chain: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    from bd_platform.defi_tvl_engine import build_tvl_dashboard

    return build_tvl_dashboard(chain=chain, category=category, limit=limit)


@router.get("/market-radar/defi/tvl/{protocol_id}")
async def defi_tvl_protocol_route(protocol_id: str):
    from bd_platform.defi_tvl_engine import get_protocol_tvl

    result = get_protocol_tvl(protocol_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


# ── Feature #705 merged — Canonical Asset Registry (#194 Unified Connector) ────


@router.get("/connectors/assets/status")
async def canonical_assets_status_route():
    from bd_platform.canonical_asset_registry import canonical_asset_registry_status

    return canonical_asset_registry_status()


@router.get("/connectors/assets")
async def canonical_assets_list_route(
    lifecycle: str | None = Query(None),
    chain: str | None = Query(None),
    canonical_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
):
    from bd_platform.canonical_asset_registry import list_canonical_assets

    return list_canonical_assets(
        lifecycle=lifecycle,  # type: ignore[arg-type]
        chain=chain,
        canonical_only=canonical_only,
        limit=limit,
    )


@router.get("/connectors/assets/resolve/{symbol}")
async def canonical_asset_resolve_route(symbol: str):
    from bd_platform.canonical_asset_registry import resolve_asset

    result = resolve_asset(symbol)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/connectors/assets/{symbol}/dev-health")
async def dev_health_asset_route(symbol: str):
    from bd_platform.dev_health_score import get_dev_health_for_asset

    result = get_dev_health_for_asset(symbol)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="dev_health_unavailable: ownership not verified or asset not tracked",
        )
    return result


@router.get("/dev-health/status")
async def dev_health_status_route():
    from bd_platform.dev_health_score import dev_health_status

    return dev_health_status()


@router.get("/connectors/assets/{symbol}/dex-volume")
async def dex_volume_asset_route(symbol: str):
    from bd_platform.dex_volume_feed import get_dex_volume_for_asset

    result = get_dex_volume_for_asset(symbol)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="dex_volume_unavailable: asset not tracked in DEX volume feed",
        )
    return result


@router.get("/dex-volume/status")
async def dex_volume_status_route():
    from bd_platform.dex_volume_feed import dex_volume_feed_status

    return dex_volume_feed_status()


@router.get("/connectors/assets/{symbol}/futures-volume")
async def futures_volume_asset_route(symbol: str):
    from bd_platform.futures_volume_intelligence import get_futures_volume_for_asset

    result = get_futures_volume_for_asset(symbol)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="futures_volume_unavailable: asset not tracked in futures volume feed",
        )
    return result


@router.get("/futures-volume/status")
async def futures_volume_status_route():
    from bd_platform.futures_volume_intelligence import futures_volume_intelligence_status

    return futures_volume_intelligence_status()


@router.get("/futures-volume/dashboard")
async def futures_volume_dashboard_route():
    from bd_platform.futures_volume_intelligence import get_futures_volume_dashboard

    return get_futures_volume_dashboard()


# ── Feature #247 — Gas Cost Engine (Core Infrastructure for Fee DB #130) ───────


@router.get("/gas-cost/status")
async def gas_cost_engine_status_route():
    from bd_platform.gas_cost_engine import gas_cost_engine_status

    return gas_cost_engine_status()


@router.get("/gas-cost/predict")
async def gas_cost_predict_route(
    chain: str = Query("ethereum"),
    tx_type: str = Query("swap"),
    tier: str = Query("free"),
):
    from bd_platform.gas_cost_engine import predict_gas_cost

    return predict_gas_cost(chain, tx_type=tx_type, tier=tier)  # type: ignore[arg-type]


@router.get("/gas-cost/monitoring")
async def gas_cost_monitoring_route():
    from bd_platform.gas_cost_engine import get_calibration_monitoring

    return get_calibration_monitoring()


@router.get("/connectors/unified")
async def unified_connector_view_route(probe_live: bool = Query(True)):
    from bd_platform.connector_coverage_map import build_unified_connector_view

    return await build_unified_connector_view(probe_live=probe_live)


# ── Feature #709 merged — Yield Sustainability Score (#198) ────────────────────


@router.get("/defi/yield-sustainability/status")
async def yield_sustainability_status_route():
    from bd_platform.yield_sustainability_score import yield_sustainability_status

    return yield_sustainability_status()


@router.get("/defi/yield-sustainability")
async def yield_sustainability_list_route(
    protocol: str | None = Query(None),
    chain: str | None = Query(None),
    sustainability: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    from bd_platform.yield_sustainability_score import list_yield_pools

    return list_yield_pools(
        protocol=protocol,
        chain=chain,
        sustainability=sustainability,  # type: ignore[arg-type]
        limit=limit,
    )


@router.get("/defi/yield-sustainability/{pool_id}")
async def yield_sustainability_pool_route(pool_id: str):
    from bd_platform.yield_sustainability_score import get_yield_pool

    result = get_yield_pool(pool_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


# ── DeFi Yield Center — #709 + #710 + #711 + #198 merged (Sprint 2) ───────────


@router.get("/defi/yield-center/status")
async def defi_yield_center_status_route():
    from bd_platform.defi_yield_center import defi_yield_center_status

    return defi_yield_center_status()


@router.get("/defi/yield-center/dashboard")
async def defi_yield_center_dashboard_route():
    from bd_platform.defi_yield_center import get_yield_center_dashboard

    return await get_yield_center_dashboard()


@router.get("/defi/yield-center/screener")
async def defi_yield_center_screener_route(
    chain: str | None = Query(None),
    min_tvl_usd: float | None = Query(None),
    max_risk: str | None = Query(None),
    exclude_stale: bool = Query(True),
    limit: int = Query(50, ge=1, le=200),
):
    from bd_platform.defi_yield_center import screen_yield_pools

    return screen_yield_pools(
        chain=chain,
        min_tvl_usd=min_tvl_usd,
        max_risk=max_risk,  # type: ignore[arg-type]
        exclude_stale=exclude_stale,
        limit=limit,
    )


@router.get("/defi/yield-center/arbitrage")
async def defi_yield_center_arbitrage_list_route(
    tier: str | None = Query(None),
    min_net_yield_pct: float | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    from bd_platform.defi_yield_center import list_yield_arbitrage

    return list_yield_arbitrage(
        tier=tier,  # type: ignore[arg-type]
        min_net_yield_pct=min_net_yield_pct,
        limit=limit,
    )


@router.get("/defi/yield-center/arbitrage/{opp_id}")
async def defi_yield_center_arbitrage_detail_route(opp_id: str):
    from bd_platform.defi_yield_center import get_arbitrage_opportunity

    result = get_arbitrage_opportunity(opp_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.post("/defi/yield-center/arbitrage/{opp_id}/simulate")
async def defi_yield_center_arbitrage_simulate_route(opp_id: str):
    from bd_platform.defi_yield_center import run_arbitrage_simulation

    result = run_arbitrage_simulation(opp_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/defi/yield-center/optimize")
async def defi_yield_center_optimize_route(
    capital_usd: float = Query(100_000, ge=1000),
    max_risk: str = Query("medium"),
):
    from bd_platform.defi_yield_center import optimize_yield_allocation

    return optimize_yield_allocation(capital_usd=capital_usd, max_risk=max_risk)  # type: ignore[arg-type]


# ── DeFi Slippage Mapper — #228 (Sprint 2, Intelligence) ───────────────────────


@router.get("/market-radar/defi/slippage-mapper/status")
async def defi_slippage_mapper_status_route():
    from bd_platform.defi_slippage_mapper import defi_slippage_mapper_status

    return defi_slippage_mapper_status()


@router.get("/market-radar/defi/slippage-mapper/dashboard")
async def defi_slippage_mapper_dashboard_route(asset: str = Query("ETH")):
    from bd_platform.defi_slippage_mapper import build_defi_slippage_dashboard

    return build_defi_slippage_dashboard(asset)


@router.get("/market-radar/defi/slippage-mapper/protocol/{protocol_id}")
async def defi_slippage_mapper_protocol_route(protocol_id: str):
    from bd_platform.defi_slippage_mapper import get_protocol_slippage

    result = get_protocol_slippage(protocol_id)
    if not result:
        raise HTTPException(status_code=404, detail="protocol_not_found")
    return result


# ── Feature #750 merged — On-Chain Metrics Suite (Realized Cap Model) ──────────


@router.get("/onchain/metrics-suite/status")
async def onchain_metrics_suite_status_route():
    from bd_platform.onchain_metrics_suite import onchain_metrics_suite_status

    return onchain_metrics_suite_status()


@router.get("/onchain/metrics-suite/methodology")
async def onchain_metrics_methodology_route():
    from bd_platform.onchain_metrics_suite import get_methodology

    return get_methodology()


@router.get("/onchain/metrics-suite")
async def onchain_metrics_suite_route(asset: str = Query("BTC")):
    from bd_platform.onchain_metrics_suite import get_onchain_metrics_suite

    return await get_onchain_metrics_suite(asset)


@router.get("/onchain/metrics-suite/realized-cap")
async def onchain_realized_cap_route(asset: str = Query("BTC")):
    from bd_platform.onchain_metrics_suite import compute_realized_cap

    return await compute_realized_cap(asset)


@router.get("/onchain/metrics-suite/mdia")
async def onchain_mdia_route(asset: str = Query("BTC")):
    from bd_platform.onchain_metrics_suite import compute_mdia

    return await compute_mdia(asset)


# ── Portfolio Risk Analytics Suite — #723 + #724 + #746 merged ────────────────


@router.get("/portfolio/risk-analytics/status")
async def portfolio_risk_analytics_status_route():
    from bd_platform.portfolio_risk_analytics import portfolio_risk_analytics_status

    return portfolio_risk_analytics_status()


@router.get("/portfolio/risk-analytics/correlation")
async def portfolio_correlation_matrix_route(
    symbols: str | None = Query(None, description="Comma-separated symbols"),
):
    from bd_platform.portfolio_risk_analytics import build_correlation_matrix

    syms = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    return build_correlation_matrix(syms)


@router.get("/portfolio/risk-analytics/breadth")
async def portfolio_return_breadth_route(
    symbols: str | None = Query(None, description="Comma-separated symbols"),
):
    from bd_platform.portfolio_risk_analytics import compute_return_breadth

    syms = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    return compute_return_breadth(syms)


@router.post("/portfolio/risk-analytics/simulate")
async def portfolio_risk_simulate_route(
    holdings: list[dict[str, Any]] = Body(...),
    horizon_days: int = Query(30, ge=7, le=90),
    iterations: int = Query(10_000, ge=1000, le=10_000),
    user: dict = Depends(require_authenticated),
):
    from auth_service import feature_allowed
    from bd_platform.portfolio_risk_analytics import run_risk_scenario_simulation

    if not feature_allowed(user, "risk_scenario_simulator"):
        raise HTTPException(status_code=403, detail="risk_scenario_simulator_requires_pro")
    return run_risk_scenario_simulation(
        holdings, horizon_days=horizon_days, iterations=iterations,
    )


@router.post("/portfolio/risk-analytics")
async def portfolio_risk_analytics_route(
    holdings: list[dict[str, Any]] = Body(...),
    horizon_days: int = Query(30, ge=7, le=90),
    user: dict = Depends(require_authenticated),
):
    from auth_service import feature_allowed
    from bd_platform.portfolio_risk_analytics import get_portfolio_risk_analytics

    if not feature_allowed(user, "risk_scenario_simulator"):
        raise HTTPException(status_code=403, detail="risk_scenario_simulator_requires_pro")
    return get_portfolio_risk_analytics(holdings, horizon_days=horizon_days)


# ── Signal Validation Engine — #747 MTF convergence (validation layer) ─────────


@router.get("/signal-engine/validation/status")
async def signal_validation_status_route():
    from bd_platform.signal_validation_engine import signal_validation_status

    return signal_validation_status()


@router.get("/signal-engine/validation/mtf")
async def signal_mtf_validation_route(asset: str = Query("BTC")):
    from bd_platform.signal_validation_engine import validate_mtf_convergence

    return await validate_mtf_convergence(asset)


@router.get("/signal-engine/validation")
async def signal_validation_route(
    asset: str = Query("BTC"),
    opportunity_score: float | None = Query(None),
):
    from bd_platform.signal_validation_engine import run_signal_validation

    return await run_signal_validation(asset, opportunity_score=opportunity_score)


# ── Scenario Engine — #751 probabilistic scenarios (Enterprise tier) ────────────


@router.get("/scenario-engine/status")
async def scenario_engine_status_route():
    from bd_platform.scenario_engine import scenario_engine_status

    return scenario_engine_status()


@router.get("/scenario-engine/calibration")
async def scenario_engine_calibration_route():
    from bd_platform.scenario_engine import get_calibration

    return get_calibration()


@router.get("/scenario-engine")
async def scenario_engine_generate_route(
    asset: str = Query("BTC"),
    regime: str | None = Query(None),
    user: dict = Depends(require_authenticated),
):
    from auth_service import feature_allowed
    from bd_platform.scenario_engine import generate_scenarios

    if not feature_allowed(user, "scenario_engine"):
        raise HTTPException(status_code=403, detail="scenario_engine_requires_enterprise")
    return await generate_scenarios(asset, regime=regime)


@router.get("/scenario-engine/sensitivity")
async def scenario_engine_sensitivity_route(
    asset: str = Query("BTC"),
    shock: str = Query(..., description="Sensitivity shock e.g. 'Fed cuts 25bps'"),
    user: dict = Depends(require_authenticated),
):
    from auth_service import feature_allowed
    from bd_platform.scenario_engine import run_sensitivity_analysis

    if not feature_allowed(user, "scenario_engine"):
        raise HTTPException(status_code=403, detail="scenario_engine_requires_enterprise")
    result = run_sensitivity_analysis(asset, shock)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


# ── Sprint 0 — Streaming Infrastructure (#218 + #222) ─────────────────────────


@router.get("/streaming/status")
async def streaming_infrastructure_status_route():
    from bd_platform.streaming_infrastructure import streaming_infrastructure_status

    return streaming_infrastructure_status()


@router.get("/streaming/slos")
async def streaming_slos_route():
    from bd_platform.streaming_infrastructure import get_stream_slos

    return get_stream_slos()


@router.get("/streaming/multiplex")
async def streaming_multiplex_route(assets: str | None = Query(None)):
    from bd_platform.streaming_infrastructure import get_multiplex_feed_config

    asset_list = [a.strip().upper() for a in assets.split(",")] if assets else None
    return get_multiplex_feed_config(asset_list)


@router.get("/streaming/health")
async def streaming_health_route(_admin: dict = Depends(require_admin)):
    from bd_platform.streaming_infrastructure import get_connection_health

    return get_connection_health()


@router.post("/streaming/backfill")
async def streaming_backfill_route(
    feed_id: str = Query(...),
    gap_start: int | None = Query(None),
    gap_end: int | None = Query(None),
):
    from bd_platform.streaming_infrastructure import backfill_on_reconnect

    return backfill_on_reconnect(feed_id, gap_start=gap_start, gap_end=gap_end)


# ── Sprint 0 — Freshness Assurance Layer (#219) ───────────────────────────────


@router.get("/freshness/status")
async def freshness_assurance_status_route():
    from bd_platform.freshness_assurance import freshness_assurance_status

    return freshness_assurance_status()


@router.get("/freshness/clock-sync")
async def freshness_clock_sync_route():
    from bd_platform.freshness_assurance import get_clock_sync_status

    return get_clock_sync_status()


@router.get("/freshness/dashboard")
async def freshness_dashboard_route():
    from bd_platform.freshness_assurance import get_freshness_dashboard

    return get_freshness_dashboard()


@router.get("/freshness/feeds/{feed_id}")
async def freshness_feed_route(feed_id: str, asset: str = Query("BTC")):
    from bd_platform.freshness_assurance import get_feed_freshness

    return get_feed_freshness(feed_id, asset)


@router.get("/freshness/feeds/{feed_id}/percentiles")
async def freshness_percentiles_route(feed_id: str, asset: str = Query("BTC")):
    from bd_platform.freshness_assurance import get_percentile_latency

    return get_percentile_latency(feed_id, asset)


@router.get("/freshness/feeds/{feed_id}/history")
async def freshness_history_route(feed_id: str, limit: int = Query(50, ge=1, le=200)):
    from bd_platform.freshness_assurance import get_freshness_history

    return get_freshness_history(feed_id, limit=limit)


@router.get("/freshness/health-check")
async def freshness_health_check_route():
    from bd_platform.freshness_assurance import run_freshness_health_check

    return run_freshness_health_check()


# ── #231 B2B Query Latency SLA — merged into #219 Freshness Assurance ─────────


@router.get("/freshness/b2b-sla/status")
async def b2b_sla_status_route():
    from bd_platform.b2b_sla_monitoring import b2b_sla_status

    return b2b_sla_status()


@router.get("/freshness/b2b-sla/dashboard")
async def b2b_sla_dashboard_route(
    tier: str = Query("institutional"),
    internal: bool = Query(False),
):
    from bd_platform.b2b_sla_monitoring import get_b2b_sla_dashboard

    return get_b2b_sla_dashboard(tier=tier, internal=internal)


@router.get("/freshness/b2b-sla/endpoints/{endpoint_path:path}")
async def b2b_sla_endpoint_latency_route(endpoint_path: str):
    from bd_platform.b2b_sla_monitoring import get_endpoint_latency, get_endpoint_uptime

    ep = f"/{endpoint_path}" if not endpoint_path.startswith("/") else endpoint_path
    if not ep.startswith("/api"):
        ep = f"/api/v1/platform/{endpoint_path.lstrip('/')}"
    return {
        "latency": get_endpoint_latency(ep),
        "uptime": get_endpoint_uptime(ep),
    }


@router.get("/freshness/b2b-sla/rate-limit")
async def b2b_sla_rate_limit_route(
    client_key: str = Query("default"),
    tier: str = Query("institutional"),
):
    from bd_platform.b2b_sla_monitoring import get_rate_limit_status

    return get_rate_limit_status(client_key, tier)


@router.get("/freshness/b2b-sla/fallback")
async def b2b_sla_fallback_route():
    from bd_platform.b2b_sla_monitoring import get_fallback_status

    return get_fallback_status()


@router.get("/freshness/b2b-sla/cache-policy")
async def b2b_sla_cache_policy_route(tier: str = Query("free")):
    from bd_platform.b2b_sla_monitoring import get_cache_policy

    return get_cache_policy(tier)


# ── Positioning Intelligence — #221 merged into Sentiment Panel (Sprint 2) ─────


@router.get("/market-radar/sentiment/positioning/status")
async def positioning_intelligence_status_route():
    from bd_platform.positioning_intelligence import positioning_intelligence_status

    return positioning_intelligence_status()


@router.get("/market-radar/sentiment/positioning")
async def positioning_intelligence_route(asset: str = Query("BTC")):
    from bd_platform.positioning_intelligence import get_top_trader_positioning

    return get_top_trader_positioning(asset)


@router.get("/market-radar/sentiment/positioning/divergence")
async def positioning_divergence_route(asset: str = Query("BTC")):
    from bd_platform.positioning_intelligence import get_positioning_divergence

    return get_positioning_divergence(asset)


# ── Data Engineering Stack — #223 dbt Connector merged (Sprint 0) ─────────────


@router.get("/data-engineering/status")
async def data_engineering_stack_status_route():
    from bd_platform.data_engineering_stack import data_engineering_stack_status

    return await data_engineering_stack_status()


@router.get("/data-engineering/lineage")
async def data_engineering_lineage_route():
    from bd_platform.data_engineering_stack import get_model_lineage

    return get_model_lineage()


@router.get("/data-engineering/model-tests")
async def data_engineering_model_tests_route():
    from bd_platform.data_engineering_stack import get_model_tests

    return get_model_tests()


@router.post("/data-engineering/pipeline/run")
async def data_engineering_pipeline_run_route(
    _admin: dict = Depends(require_admin),
):
    from bd_platform.data_engineering_stack import run_data_pipeline

    try:
        return await run_data_pipeline(operator=str(_admin.get("email") or "admin"))
    except RuntimeError as exc:
        if "dbt_not_configured" in str(exc):
            raise HTTPException(status_code=503, detail="dbt_not_configured") from exc
        raise


# ── Verifiable AI Engine — #230 Core AI Layer (Sprint 1) ─────────────────────


@router.get("/verifiable-ai/status")
async def verifiable_ai_status_route():
    from bd_platform.verifiable_ai_engine import verifiable_ai_status

    return verifiable_ai_status()


@router.post("/verifiable-ai/ground")
async def verifiable_ai_ground_route(
    query: str = Body(..., embed=True),
    asset: str | None = Body(None, embed=True),
):
    from bd_platform.verifiable_ai_engine import ground_ai_response

    return await ground_ai_response(query, asset=asset)


@router.get("/verifiable-ai/audit")
async def verifiable_ai_audit_route(
    limit: int = Query(50, ge=1, le=200),
    since_days: int | None = Query(None, ge=1, le=90),
):
    from bd_platform.verifiable_ai_engine import get_audit_trail

    return get_audit_trail(limit=limit, since_days=since_days)


@router.get("/verifiable-ai/middleware/status")
async def ai_grounding_middleware_status_route():
    from bd_platform.ai_grounding_middleware import grounding_middleware_status

    return grounding_middleware_status()


@router.get("/verifiable-ai/red-team")
async def verifiable_ai_red_team_route(limit: int = Query(100, ge=1, le=200)):
    from bd_platform.verifiable_ai_engine import run_red_team_suite

    return await run_red_team_suite(limit=limit)


# ── Premium Intelligence Module — #255 Korea + #233 Coinbase (Sprint 2) ───────


@router.get("/market-radar/premiums/status")
async def premium_intelligence_status_route():
    from bd_platform.premium_intelligence import premium_intelligence_status

    return premium_intelligence_status()


@router.get("/market-radar/premiums/dashboard")
async def regional_premiums_dashboard_route(asset: str = Query("BTC")):
    from bd_platform.premium_intelligence import get_regional_premiums_dashboard

    return get_regional_premiums_dashboard(asset)


@router.get("/market-radar/premiums/korea")
async def korea_premium_route(asset: str = Query("BTC")):
    from bd_platform.premium_intelligence import get_korea_premium

    return get_korea_premium(asset)


@router.get("/market-radar/premiums/coinbase")
async def coinbase_premium_route(asset: str = Query("BTC")):
    from bd_platform.premium_intelligence import get_coinbase_premium

    return get_coinbase_premium(asset)


# ── Technical Ratings + Momentum Intelligence — #755 + #273 (Sprint 2) ──────────


@router.get("/market-radar/technical-ratings/status")
async def technical_ratings_status_route():
    from bd_platform.technical_ratings import technical_ratings_status

    return technical_ratings_status()


@router.get("/market-radar/technical-ratings")
async def technical_ratings_route(asset: str = Query("BTC")):
    from bd_platform.technical_ratings import get_technical_composite

    return get_technical_composite(asset)


@router.get("/market-radar/momentum/status")
async def momentum_intelligence_status_route():
    from bd_platform.momentum_intelligence import momentum_intelligence_status

    return momentum_intelligence_status()


@router.get("/market-radar/momentum")
async def momentum_intelligence_route(asset: str = Query("BTC")):
    from bd_platform.momentum_intelligence import get_momentum_analysis

    return get_momentum_analysis(asset)


# ── Social Hype Analyzer — #293 replaces #758 (Sprint 2) ─────────────────────


@router.get("/market-radar/sentiment/hype/status")
async def social_hype_analyzer_status_route():
    from bd_platform.social_hype_analyzer import social_hype_analyzer_status

    return social_hype_analyzer_status()


@router.get("/market-radar/sentiment/hype")
async def social_hype_analyzer_route(asset: str = Query("BTC")):
    from bd_platform.social_hype_analyzer import analyze_asset_hype

    return analyze_asset_hype(asset)


@router.get("/market-radar/sentiment/hype/scan")
async def social_hype_market_scan_route(limit: int = Query(10, ge=1, le=50)):
    from bd_platform.social_hype_analyzer import scan_market_hype

    return scan_market_hype(limit=limit)


# ── Macro Intelligence Hub — #263 (Sprint 2, Pro/Institution) ──────────────────


@router.get("/market-radar/macro-hub/status")
async def macro_intelligence_hub_status_route():
    from bd_platform.macro_intelligence_hub import macro_intelligence_hub_status

    return macro_intelligence_hub_status()


@router.get("/market-radar/macro-hub/dashboard")
async def macro_intelligence_hub_dashboard_route(
    asset: str = Query("BTC"),
    tier: str = Query("pro"),
    window: str = Query("30D"),
):
    from bd_platform.macro_intelligence_hub import build_macro_intelligence_hub

    return build_macro_intelligence_hub(asset, tier=tier, window=window)  # type: ignore[arg-type]


@router.get("/market-radar/macro-hub/coupling")
async def macro_intelligence_hub_coupling_route(asset: str = Query("BTC")):
    from bd_platform.macro_intelligence_hub import build_macro_coupling

    return build_macro_coupling(asset)


@router.get("/market-radar/macro-hub/treasury-companies")
async def macro_hub_treasury_companies_route(asset: str = Query("BTC")):
    from bd_platform.treasury_intelligence import build_treasury_dashboard

    return build_treasury_dashboard(asset)


@router.get("/market-radar/macro-hub/treasury-companies/{ticker}")
async def macro_hub_treasury_company_route(ticker: str):
    from bd_platform.treasury_intelligence import get_treasury_company

    result = get_treasury_company(ticker)
    if not result:
        raise HTTPException(status_code=404, detail="treasury_company_not_found")
    return result


@router.get("/market-radar/treasury-intelligence/status")
async def treasury_intelligence_status_route():
    from bd_platform.treasury_intelligence import treasury_intelligence_status

    return treasury_intelligence_status()


# ── Exchange Intelligence Hub — #734-736 + #242 Outflow (Sprint 2) ─────────────


@router.get("/market-radar/exchange-hub/status")
async def exchange_intelligence_hub_status_route():
    from bd_platform.exchange_intelligence_hub import exchange_intelligence_hub_status

    return exchange_intelligence_hub_status()


@router.get("/market-radar/exchange-hub/dashboard")
async def exchange_intelligence_hub_dashboard_route(asset: str = Query("BTC")):
    from bd_platform.exchange_intelligence_hub import build_exchange_intelligence_hub

    result = build_exchange_intelligence_hub(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "asset_not_tracked")
    return result


@router.get("/market-radar/exchange-hub/outflow")
async def exchange_outflow_route(asset: str = Query("BTC")):
    from bd_platform.exchange_outflow_intelligence import build_outflow_dashboard

    result = build_outflow_dashboard(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "asset_not_tracked")
    return result


@router.get("/market-radar/exchange-hub/inflow")
async def exchange_inflow_route(asset: str = Query("BTC")):
    from bd_platform.exchange_inflow_intelligence import build_inflow_dashboard

    result = build_inflow_dashboard(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "asset_not_tracked")
    return result


@router.get("/market-radar/exchange-hub/netflow")
async def exchange_netflow_route(asset: str = Query("BTC")):
    from bd_platform.exchange_netflow_intelligence import build_netflow_dashboard

    result = build_netflow_dashboard(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "asset_not_tracked")
    return result


# ── Global Liquidity Intelligence — #248 (Sprint 2, Pro/Institution) ───────────


@router.get("/market-radar/global-liquidity/status")
async def global_liquidity_status_route():
    from bd_platform.global_liquidity_intelligence import global_liquidity_status

    return global_liquidity_status()


@router.get("/market-radar/global-liquidity/dashboard")
async def global_liquidity_dashboard_route(asset: str = Query("BTC")):
    from bd_platform.global_liquidity_intelligence import build_global_liquidity_dashboard

    return build_global_liquidity_dashboard(asset)


@router.get("/market-radar/global-liquidity/regime")
async def global_liquidity_regime_route(asset: str = Query("BTC")):
    from bd_platform.global_liquidity_intelligence import build_liquidity_regime

    return build_liquidity_regime(asset)


@router.get("/market-radar/global-liquidity/index")
async def global_liquidity_index_route():
    from bd_platform.global_liquidity_intelligence import build_liquidity_index

    return build_liquidity_index()


# ── CVD Intelligence — #232 (Sprint 2, Pro) ───────────────────────────────────


@router.get("/market-radar/cvd/status")
async def cvd_intelligence_status_route():
    from bd_platform.cvd_intelligence import cvd_intelligence_status

    return cvd_intelligence_status()


@router.get("/market-radar/cvd/analysis")
async def cvd_intelligence_analysis_route(
    asset: str = Query("BTC"),
    window: str = Query("1H"),
):
    from bd_platform.cvd_intelligence import build_cvd_analysis

    return build_cvd_analysis(asset, window=window)


@router.get("/market-radar/cvd/chart")
async def cvd_intelligence_chart_route(
    asset: str = Query("BTC"),
    window: str = Query("1H"),
):
    from bd_platform.cvd_intelligence import build_cvd_chart

    return build_cvd_chart(asset, window=window)


# ── ETF Intelligence Module — #210 + #240 (Sprint 2, Pro) ───────────────────


@router.get("/market-radar/etf-intelligence/status")
async def etf_intelligence_status_route():
    from bd_platform.etf_intelligence import etf_intelligence_status

    return etf_intelligence_status()


@router.get("/market-radar/etf-intelligence/dashboard")
async def etf_intelligence_dashboard_route(asset: str = Query("BTC")):
    from bd_platform.etf_intelligence import build_etf_intelligence_dashboard

    return build_etf_intelligence_dashboard(asset)


@router.get("/market-radar/etf-intelligence/flows")
async def etf_intelligence_flows_route(asset: str = Query("BTC")):
    from bd_platform.etf_intelligence import build_etf_flow_series

    return build_etf_flow_series(asset)


@router.get("/market-radar/etf-intelligence/market-context")
async def etf_intelligence_market_context_route(asset: str = Query("BTC")):
    from bd_platform.etf_intelligence import build_etf_market_context

    return build_etf_market_context(asset)


@router.get("/market-radar/etf-intelligence/etp-data")
async def etf_intelligence_etp_data_route(asset: str = Query("BTC")):
    from bd_platform.etf_intelligence import build_etp_data

    result = build_etp_data(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "asset_not_configured")
    return result


# ── Signal Context Layer — #330-REV (Sprint 2, Pro) ───────────────────────────


@router.get("/market-radar/signal-context/status")
async def signal_context_layer_status_route():
    from bd_platform.signal_context_layer import signal_context_layer_status

    return signal_context_layer_status()


@router.get("/market-radar/signal-context")
async def signal_context_panel_route(asset: str = Query("BTC")):
    from bd_platform.signal_context_layer import build_context_panel

    return await build_context_panel(asset, surface="market_radar")


@router.get("/portfolio/signal-context")
async def portfolio_signal_context_route(asset: str = Query("BTC")):
    from bd_platform.signal_context_layer import build_portfolio_context_panel

    return await build_portfolio_context_panel(asset)


# ── MCP for AI — #262 AI Agent Server (Sprint 2) ─────────────────────────────


@router.get("/mcp/status")
async def mcp_ai_server_status_route():
    from bd_platform.mcp_ai_server import mcp_ai_server_status

    return mcp_ai_server_status()


@router.get("/mcp/tools/schema")
async def mcp_tool_schema_route():
    from bd_platform.mcp_ai_server import get_tool_schemas

    return get_tool_schemas()


@router.post("/mcp/tools/call")
async def mcp_tool_call_route(
    tool_name: str = Body(..., embed=True),
    parameters: dict[str, Any] = Body(default_factory=dict, embed=True),
    x_api_key: str = Header(..., alias="X-API-Key"),
    x_agent_fingerprint: str = Header(..., alias="X-Agent-Fingerprint"),
):
    from bd_platform.mcp_ai_server import call_mcp_tool

    return await call_mcp_tool(
        tool_name,
        parameters,
        api_key=x_api_key,
        agent_fingerprint=x_agent_fingerprint,
    )


@router.get("/mcp/trace")
async def mcp_tool_trace_route(
    limit: int = Query(50, ge=1, le=200),
    agent_id: str | None = Query(None),
    x_api_key: str = Header(..., alias="X-API-Key"),
    x_agent_fingerprint: str = Header(..., alias="X-Agent-Fingerprint"),
):
    from bd_platform.mcp_ai_server import _resolve_agent, get_tool_trace

    auth = _resolve_agent(x_api_key, x_agent_fingerprint)
    if not auth.get("ok"):
        raise HTTPException(status_code=401, detail=auth.get("message", "authentication_required"))
    return get_tool_trace(limit=limit, agent_id=agent_id or auth.get("agent_id"))

