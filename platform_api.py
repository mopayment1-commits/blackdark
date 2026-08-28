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


@router.get("/concentration-risk/status")
async def concentration_risk_status_api():
    from portfolio_concentration_risk import concentration_risk_status

    return concentration_risk_status()


@router.get("/concentration-risk/e2e")
async def concentration_risk_e2e_api():
    from portfolio_concentration_risk import run_concentration_risk_e2e

    return run_concentration_risk_e2e()


@router.post("/concentration-risk/thresholds", responses=COMMON_ERROR_RESPONSES)
async def concentration_risk_thresholds(
    body: dict = Body(...),
    user: dict = Depends(require_authenticated),
):
    from portfolio_concentration_risk import save_user_thresholds

    thresholds = {k: float(v) for k, v in (body.get("thresholds") or {}).items()}
    return save_user_thresholds(int(user["id"]), thresholds)


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
