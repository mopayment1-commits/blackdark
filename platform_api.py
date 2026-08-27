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


@router.get("/intelligence-ledger/token-unlock/forecaster")
async def token_unlock_forecaster_route(limit: int = Query(30, ge=1, le=100)):
    """#607 Token Unlock Forecaster — severity + provenance, no price prediction."""
    from bd_platform.token_unlock_intelligence_engine import build_unlock_forecaster_panel

    return build_unlock_forecaster_panel(limit=limit)


@router.get("/intelligence-ledger/token-unlock/forecaster/capital-alerts")
async def token_unlock_capital_alerts_route(portfolio_id: str = Query("demo_portfolio")):
    from bd_platform.token_unlock_intelligence_engine import build_capital_protection_unlock_alerts

    return build_capital_protection_unlock_alerts(portfolio_id)


@router.get("/intelligence-ledger/token-unlock/forecaster/alert-tests")
async def token_unlock_alert_tests_route():
    from bd_platform.token_unlock_intelligence_engine import run_unlock_alert_tests

    return run_unlock_alert_tests()


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


@router.get("/intelligence-ledger/portfolio-ai/live-breakeven/status")
async def live_breakeven_tracker_status_route():
    """#404 Live Breakeven Tracker — Position Analytics Layer in Portfolio AI."""
    from bd_platform.live_breakeven_tracker import live_breakeven_tracker_status

    return live_breakeven_tracker_status()


@router.get("/intelligence-ledger/portfolio-ai/live-breakeven")
async def live_breakeven_panel_route(position_id: str = Query("pos_btc_001")):
    """#404 Live Breakeven Tracker — Dynamic Cost Basis with fee transparency."""
    from bd_platform.live_breakeven_tracker import build_live_breakeven_panel

    result = build_live_breakeven_panel(position_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-ai/live-breakeven/simulate")
async def live_breakeven_simulate_route(
    position_id: str = Query("pos_btc_001"),
    hypothetical_dca_qty: float | None = Query(None),
    hypothetical_dca_price: float | None = Query(None),
    hypothetical_exit_qty: float | None = Query(None),
    hypothetical_exit_price: float | None = Query(None),
):
    """#404 Breakeven Scenario Simulator — hypothetical DCA or partial exit."""
    from bd_platform.live_breakeven_tracker import _load_seed, simulate_breakeven_scenario

    seed = _load_seed()
    position = (seed.get("positions") or {}).get(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="position_not_found")
    result = simulate_breakeven_scenario(
        position,
        hypothetical_dca_qty=hypothetical_dca_qty,
        hypothetical_dca_price=hypothetical_dca_price,
        hypothetical_exit_qty=hypothetical_exit_qty,
        hypothetical_exit_price=hypothetical_exit_price,
        fee_defaults=seed.get("fee_defaults"),
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "simulation_failed")
    return result


@router.get("/intelligence-ledger/portfolio-ai/live-breakeven/reconciliation-tests")
async def live_breakeven_reconciliation_tests_route():
    from bd_platform.live_breakeven_tracker import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/portfolio-ai/capital-protection/breakeven-alerts")
async def capital_protection_breakeven_alerts_route(position_id: str = Query("pos_btc_001")):
    """#404 + #410 Capital Awareness — breakeven proximity alerts."""
    from bd_platform.capital_protection_controls import build_breakeven_proximity_alert
    from bd_platform.live_breakeven_tracker import _load_seed, compute_dynamic_breakeven

    seed = _load_seed()
    position = (seed.get("positions") or {}).get(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="position_not_found")
    calc = compute_dynamic_breakeven(position.get("events") or [])
    if not calc.get("ok"):
        raise HTTPException(status_code=400, detail=calc.get("error") or "calc_failed")
    return build_breakeven_proximity_alert(
        position, calc, cp_config=seed.get("capital_protection")
    )


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/status")
async def capital_awareness_controls_status_route():
    """#410 Capital Awareness Controls — Risk Layer (non-executive)."""
    from bd_platform.capital_protection_controls import capital_protection_controls_status

    return capital_protection_controls_status()


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness")
async def capital_awareness_controls_panel_route(portfolio_id: str = Query("demo_portfolio")):
    """#410 Capital Awareness Controls — risk scores, stress tests, risk budget."""
    from bd_platform.capital_protection_controls import build_capital_awareness_panel

    result = build_capital_awareness_panel(portfolio_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/reconciliation-tests")
async def capital_awareness_reconciliation_tests_route():
    from bd_platform.capital_protection_controls import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/real-time-risk-alerts")
async def real_time_risk_alerts_route(portfolio_id: str = Query("demo_portfolio")):
    """#484 Real-Time Risk Alerts — merged into #410."""
    from bd_platform.capital_protection_controls import build_real_time_risk_alerts

    return build_real_time_risk_alerts(portfolio_id)


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/risk-analytics")
async def risk_analytics_route(portfolio_id: str = Query("demo_portfolio")):
    """#485 Risk Analytics — VaR, liquidity, stress — merged into #410."""
    from bd_platform.capital_protection_controls import build_risk_analytics_block

    return build_risk_analytics_block(portfolio_id)


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/opportunity-risk-combined")
async def opportunity_risk_combined_route(portfolio_id: str = Query("demo_portfolio")):
    """#484 + #429 — combined opportunity + risk alerts."""
    from bd_platform.capital_protection_controls import build_opportunity_risk_combined_alerts

    return build_opportunity_risk_combined_alerts(portfolio_id)


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/stress-test")
async def portfolio_stress_test_route(portfolio_id: str = Query("demo_portfolio")):
    """#453 Portfolio Stress Test — merged into #410."""
    from bd_platform.capital_protection_controls import build_portfolio_stress_test_result

    return build_portfolio_stress_test_result(portfolio_id)


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/correlation-matrix")
async def correlation_matrix_route(portfolio_id: str = Query("demo_portfolio")):
    """#463 Correlation matrix — 30-day rolling."""
    from bd_platform.capital_protection_controls import build_correlation_matrix

    return build_correlation_matrix(portfolio_id=portfolio_id)


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/contagion-risk")
async def contagion_risk_route(portfolio_id: str = Query("demo_portfolio")):
    """#463 Contagion risk — sector/chain/stablecoin."""
    from bd_platform.capital_protection_controls import analyze_contagion_risk

    return analyze_contagion_risk(portfolio_id=portfolio_id)


@router.get("/intelligence-ledger/risk-layer/cross-protocol-contagion/status")
async def cross_protocol_contagion_status_route():
    """#652 Cross-Protocol Contagion — Risk Layer Contagion Monitor."""
    from bd_platform.cross_protocol_contagion import cross_protocol_contagion_status

    return cross_protocol_contagion_status()


@router.get("/intelligence-ledger/risk-layer/cross-protocol-contagion")
async def cross_protocol_contagion_monitor_route(trigger_id: str | None = Query(None)):
    from bd_platform.cross_protocol_contagion import build_contagion_monitor

    return build_contagion_monitor(trigger_id)


@router.get("/intelligence-ledger/risk-layer/cross-protocol-contagion/graph")
async def cross_protocol_contagion_graph_route(trigger_id: str | None = Query(None)):
    from bd_platform.cross_protocol_contagion import build_contagion_graph_visualization

    return build_contagion_graph_visualization(trigger_id)


@router.get("/intelligence-ledger/risk-layer/cross-protocol-contagion/portfolio-alert")
async def cross_protocol_contagion_portfolio_alert_route(
    portfolio_id: str = Query("demo_portfolio"),
    trigger_id: str | None = Query(None),
):
    from bd_platform.cross_protocol_contagion import build_portfolio_cluster_alert_410

    return build_portfolio_cluster_alert_410(portfolio_id=portfolio_id, trigger_id=trigger_id)


@router.get("/intelligence-ledger/risk-layer/cross-protocol-contagion/reconciliation-tests")
async def cross_protocol_contagion_reconciliation_route():
    from bd_platform.cross_protocol_contagion import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/onchain-layer/smart-money-flow/status")
async def smart_money_flow_status_route():
    """#408 Smart Money Flow Tracker (absorbs #459 Dormancy)."""
    from bd_platform.smart_money_flow_tracker import smart_money_flow_tracker_status

    return smart_money_flow_tracker_status()


@router.get("/intelligence-ledger/onchain-layer/smart-money-flow")
async def smart_money_flow_panel_route(asset: str | None = Query(None)):
    from bd_platform.smart_money_flow_tracker import build_smart_money_flow_panel

    return build_smart_money_flow_panel(asset)


@router.get("/intelligence-ledger/onchain-layer/smart-money-flow/reconciliation-tests")
async def smart_money_flow_reconciliation_route():
    from bd_platform.smart_money_flow_tracker import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/onchain-layer/smart-money-flow/sopr")
async def sopr_intelligence_route(asset: str = Query("BTC")):
    """#488 SOPR / Profitability Intelligence — merged into #408."""
    from bd_platform.smart_money_flow_tracker import (
        build_market_radar_sopr_context,
        build_sopr_edge_case_tests,
        compute_sopr,
    )

    return {
        "sopr": compute_sopr(asset),
        "market_radar_context": build_market_radar_sopr_context(asset),
        "edge_case_tests": build_sopr_edge_case_tests(),
    }


@router.get("/intelligence-ledger/onchain-layer/smart-money-flow/accumulation-distribution")
async def smart_money_accumulation_distribution_route(asset: str = Query("BTC")):
    """#590 Accumulation/Distribution State + Net-Flow Persistence Indicator."""
    from bd_platform.smart_money_flow_tracker import detect_accumulation_distribution_state

    result = detect_accumulation_distribution_state(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/smart-money-flow/historical-trend")
async def smart_money_historical_trend_route(asset: str = Query("BTC")):
    """#593 Smart Money Historical Trend Analysis — statistical regimes only."""
    from bd_platform.smart_money_flow_tracker import build_historical_trend_analysis

    result = build_historical_trend_analysis(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/smart-money-flow/tracking")
async def smart_money_tracking_feed_route(watchlist_id: str = Query("default")):
    """#598 Smart Money Tracking — classified wallet feed with latency + dedupe."""
    from bd_platform.smart_money_flow_tracker import build_smart_money_tracking_feed

    result = build_smart_money_tracking_feed(watchlist_id=watchlist_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/smart-money-flow/wallet-shadowing")
async def wallet_shadowing_alerts_route(watchlist_id: str = Query("default")):
    """#623 Wallet Shadowing — merged into #408."""
    from bd_platform.smart_money_flow_tracker import build_wallet_shadowing_alerts

    return build_wallet_shadowing_alerts(watchlist_id)


@router.get("/intelligence-ledger/onchain-layer/smart-money-flow/whale-intelligence")
async def whale_accumulation_distribution_route(asset: str = Query("BTC")):
    """#626 Whale Accumulation/Distribution Intelligence — merged into #408."""
    from bd_platform.smart_money_flow_tracker import detect_whale_accumulation_distribution_intelligence

    result = detect_whale_accumulation_distribution_intelligence(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/smart-money-flow/whale-alerts")
async def whale_movement_alerts_route(
    threshold_usd: float = Query(1_000_000),
    direction: str = Query("both"),
    assets: str | None = Query(None),
):
    """#628 Whale Movement Alerts — merged into #408."""
    from bd_platform.smart_money_flow_tracker import build_whale_movement_alerts

    asset_list = [a.strip() for a in assets.split(",")] if assets else None
    return build_whale_movement_alerts(
        threshold_usd=threshold_usd,
        direction=direction,
        assets=asset_list,
    )


@router.get("/intelligence-ledger/onchain-layer/smart-money-flow/whale-radar-overlay")
async def whale_radar_overlay_route(asset: str = Query("BTC")):
    """#626 Market Radar whale flow overlay."""
    from bd_platform.smart_money_flow_tracker import build_market_radar_whale_flow_overlay

    return build_market_radar_whale_flow_overlay(asset)


@router.get("/intelligence-ledger/ui/beginner-decision-mode/status")
async def beginner_decision_mode_status_route():
    """#461 Beginner Decision Mode — merged with #468 Decision-First."""
    from ux_mode import beginner_decision_mode_status

    return beginner_decision_mode_status()


@router.post("/intelligence-ledger/ui/decision-card")
async def decision_card_build_route(body: dict[str, Any] = Body(...)):
    """#461/#468 — build Decision Card for any page context."""
    from ux_mode import apply_ux_mode, build_beginner_decision_card

    payload = dict(body.get("payload") or {})
    mode = str(body.get("ux_mode") or "beginner")
    layer = str(payload.pop("_layer", None) or body.get("layer") or "summary")
    result = apply_ux_mode(payload, mode=mode)
    card = result.get("decision_card") or build_beginner_decision_card(payload, layer=layer)  # type: ignore[arg-type]
    return {"ok": True, "decision_card": card, "ux_mode": mode}


@router.get("/intelligence-ledger/portfolio-ai/risk-score/status")
async def risk_score_surface_status_route():
    from bd_platform.risk_score_surface import risk_score_surface_status

    return risk_score_surface_status()


@router.get("/intelligence-ledger/portfolio-ai/risk-score")
async def risk_score_surface_route(portfolio_id: str = Query("demo_portfolio")):
    from bd_platform.risk_score_surface import build_portfolio_risk_surface

    return build_portfolio_risk_surface(portfolio_id=portfolio_id)


@router.get("/intelligence-ledger/portfolio-ai/risk-score/{asset}")
async def risk_score_asset_route(asset: str, portfolio_id: str = Query("demo_portfolio")):
    from bd_platform.risk_score_surface import score_asset_risk

    return score_asset_risk(asset, portfolio_id=portfolio_id)


@router.get("/intelligence-ledger/alert-center/status")
async def unified_alert_center_status_route():
    from bd_platform.unified_alert_center import unified_alert_center_status

    return unified_alert_center_status()


@router.get("/intelligence-ledger/alert-center/feed")
async def unified_alert_center_feed_route(
    limit: int = Query(50),
    alert_type: str | None = Query(None),
):
    from bd_platform.unified_alert_center import build_unified_alert_feed

    return build_unified_alert_feed(limit=limit, alert_type=alert_type)


@router.get("/intelligence-ledger/portfolio-ai/exchange-health/status")
async def exchange_health_monitor_status_route():
    """#456 Exchange Health Monitor — Sprint-2 Risk Layer."""
    from bd_platform.exchange_health_monitor import exchange_health_monitor_status

    return exchange_health_monitor_status()


@router.get("/intelligence-ledger/portfolio-ai/exchange-health")
async def exchange_health_monitor_panel_route(
    exchange_id: str | None = Query(None),
):
    from bd_platform.exchange_health_monitor import build_exchange_health_panel

    return build_exchange_health_panel(exchange_id)


@router.get("/intelligence-ledger/portfolio-ai/exchange-health/grades")
async def exchange_health_grades_route():
    from bd_platform.exchange_health_monitor import list_exchange_grades

    return {"ok": True, "grades": list_exchange_grades(), "evidence_class": "BACKTESTED"}


@router.get("/intelligence-ledger/portfolio-ai/exchange-health/exposure-alerts")
async def exchange_health_exposure_alerts_route(
    portfolio_id: str = Query("demo_portfolio"),
):
    """#410+#456 — portfolio exposure alerts on low-health exchanges."""
    from bd_platform.exchange_health_monitor import build_portfolio_exchange_exposure_alerts

    return build_portfolio_exchange_exposure_alerts(portfolio_id)


@router.get("/intelligence-ledger/portfolio-ai/exchange-health/arbitrage-filter")
async def exchange_health_arbitrage_filter_route():
    """#403/#429 — arbitrage opportunities filtered by exchange health."""
    from bd_platform.exchange_health_monitor import build_arbitrage_health_panel

    return build_arbitrage_health_panel()


@router.get("/intelligence-ledger/intelligence-layer/exchange-health")
async def intelligence_ledger_exchange_health_route():
    from bd_platform.exchange_health_monitor import build_intelligence_ledger_integration

    return build_intelligence_ledger_integration()


@router.get("/intelligence-ledger/portfolio-ai/exchange-health/reconciliation-tests")
async def exchange_health_reconciliation_tests_route():
    from bd_platform.exchange_health_monitor import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/portfolio-ai/risk-scoring/status")
async def diligence_risk_scoring_status_route():
    """#460 Diligence Risk Scoring — Sprint-2 Risk Layer Core."""
    from bd_platform.diligence_risk_scoring import diligence_risk_scoring_status

    return diligence_risk_scoring_status()


@router.get("/intelligence-ledger/portfolio-ai/risk-scoring")
async def diligence_risk_scoring_panel_route(entity_id: str = Query("BTC")):
    from bd_platform.diligence_risk_scoring import build_risk_scoring_panel

    result = build_risk_scoring_panel(entity_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("entity_risk", {}).get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-ai/risk-scoring/entity/{entity_id}")
async def diligence_risk_entity_route(entity_id: str):
    from bd_platform.diligence_risk_scoring import score_entity_risk

    result = score_entity_risk(entity_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-ai/risk-scoring/token/{token_id}")
async def token_risk_scoring_route(token_id: str):
    """#604 Token Risk Scoring — merged into #460."""
    from bd_platform.diligence_risk_scoring import score_token_risk

    result = score_token_risk(token_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-ai/risk-scoring/collateral/{entity_id}")
async def collateral_risk_route(entity_id: str):
    """#462 Collateral Risk — shared scoring engine."""
    from bd_platform.diligence_risk_scoring import score_collateral_risk

    result = score_collateral_risk(entity_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-ai/risk-scoring/correlation/{entity_id}")
async def correlation_risk_route(entity_id: str):
    """#463 Correlation Risk — shared scoring engine."""
    from bd_platform.diligence_risk_scoring import score_correlation_risk

    result = score_correlation_risk(entity_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-ai/risk-scoring/opportunity-ranking")
async def diligence_opportunity_ranking_route():
    """#417+#460 — Net-Edge truth adjusted by diligence risk."""
    from bd_platform.diligence_risk_scoring import rank_opportunities

    return rank_opportunities()


@router.get("/intelligence-ledger/intelligence-layer/risk-scoring")
async def intelligence_ledger_risk_scoring_route():
    from bd_platform.diligence_risk_scoring import build_intelligence_ledger_integration

    return build_intelligence_ledger_integration()


@router.get("/intelligence-ledger/portfolio-ai/risk-scoring/reconciliation-tests")
async def diligence_risk_scoring_reconciliation_tests_route():
    from bd_platform.diligence_risk_scoring import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/unified-arbitrage/status")
async def unified_arbitrage_engine_status_route():
    """#429 Unified Arbitrage Opportunity Engine — Sprint-2 Core."""
    from bd_platform.unified_arbitrage_engine import unified_arbitrage_engine_status

    return unified_arbitrage_engine_status()


@router.get("/intelligence-ledger/unified-arbitrage")
async def unified_arbitrage_feed_route():
    from bd_platform.unified_arbitrage_engine import build_unified_feed

    return build_unified_feed()


@router.get("/intelligence-ledger/unified-arbitrage/defi")
async def defi_opportunity_scanner_route():
    """#438 DeFi Opportunity Scanner — merged into #429."""
    from bd_platform.defi_opportunity_scanner import build_defi_panel

    return build_defi_panel()


@router.get("/intelligence-ledger/unified-arbitrage/defi/status")
async def defi_opportunity_scanner_status_route():
    from bd_platform.defi_opportunity_scanner import defi_opportunity_scanner_status

    return defi_opportunity_scanner_status()


@router.get("/intelligence-ledger/unified-arbitrage/defi/dex-screener")
async def dex_screener_route():
    """#465 DEX Screener — merged into #438."""
    from bd_platform.defi_opportunity_scanner import screen_dex_pools

    return screen_dex_pools()


@router.get("/intelligence-ledger/unified-arbitrage/defi/lp-position-risk")
async def lp_position_risk_route(position_id: str | None = Query(None)):
    """#470 LP Position Risk Calculator — merged into #438."""
    from bd_platform.defi_opportunity_scanner import build_lp_position_risk_panel

    return build_lp_position_risk_panel(position_id)


@router.get("/intelligence-ledger/unified-arbitrage/defi/liquidity-risk")
async def liquidity_risk_route(protocol: str | None = Query(None)):
    """#473 Liquidity Risk — merged into #438."""
    from bd_platform.defi_opportunity_scanner import (
        analyze_all_liquidity_risks,
        analyze_protocol_liquidity_risk,
    )

    if protocol:
        return analyze_protocol_liquidity_risk(protocol)
    return analyze_all_liquidity_risks()


@router.get("/intelligence-ledger/unified-arbitrage/defi/oracle-risk")
async def oracle_risk_route(protocol: str | None = Query(None)):
    """#482 Oracle Risk — merged into #438 DeFi Opportunity Scanner."""
    from bd_platform.defi_opportunity_scanner import (
        analyze_protocol_oracle_risk,
        build_oracle_risk_view,
    )

    if protocol:
        return analyze_protocol_oracle_risk(protocol)
    return build_oracle_risk_view()


@router.get("/intelligence-ledger/unified-arbitrage/defi/smart-contract-risk")
async def smart_contract_risk_route(protocol: str | None = Query(None)):
    """#491 Smart Contract and Protocol Risk — merged into #438."""
    from bd_platform.defi_opportunity_scanner import (
        analyze_protocol_smart_contract_risk,
        build_smart_contract_risk_view,
    )

    if protocol:
        return analyze_protocol_smart_contract_risk(protocol)
    return build_smart_contract_risk_view()


@router.get("/intelligence-ledger/unified-arbitrage/defi/yield-delta")
async def yield_delta_listener_route():
    """#639 Yield Delta Listener — merged into #438."""
    from bd_platform.defi_opportunity_scanner import build_yield_delta_listener

    return build_yield_delta_listener()


@router.get("/intelligence-ledger/unified-arbitrage/defi/screener")
async def defi_opportunity_screener_route(
    chain: str | None = Query(None),
    protocol: str | None = Query(None),
    risk_grade: str | None = Query(None),
    min_liquidity_usd: float | None = Query(None),
):
    """#658 DeFi Opportunity Screener — merged into #438."""
    from bd_platform.defi_opportunity_scanner import build_defi_opportunity_screener

    return build_defi_opportunity_screener(
        chain=chain,
        protocol=protocol,
        risk_grade=risk_grade,
        min_liquidity_usd=min_liquidity_usd,
    )


@router.get("/intelligence-ledger/unified-arbitrage/defi/reconciliation-tests")
async def defi_opportunity_scanner_reconciliation_route():
    from bd_platform.defi_opportunity_scanner import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/unified-arbitrage/opportunity-alerts")
async def opportunity_alert_engine_route():
    """#434 Opportunity Worth Studying Alert Engine — merged into #429."""
    from bd_platform.unified_arbitrage_engine import build_opportunity_alert_panel

    return build_opportunity_alert_panel()


@router.get("/intelligence-ledger/unified-arbitrage/triangular")
async def triangular_price_divergence_route():
    """#428 Triangular Price Divergence Scanner — merged into #429."""
    from bd_platform.unified_arbitrage_engine import build_triangular_panel

    return build_triangular_panel()


@router.get("/intelligence-ledger/unified-arbitrage/market-radar")
async def unified_arbitrage_market_radar_route():
    from bd_platform.unified_arbitrage_engine import build_market_radar_integration

    return build_market_radar_integration()


@router.get("/intelligence-ledger/intelligence-layer/unified-arbitrage")
async def intelligence_ledger_unified_arbitrage_route():
    from bd_platform.unified_arbitrage_engine import build_intelligence_ledger_integration

    return build_intelligence_ledger_integration()


@router.get("/intelligence-ledger/unified-arbitrage/reconciliation-tests")
async def unified_arbitrage_reconciliation_tests_route():
    from bd_platform.unified_arbitrage_engine import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/unified-arbitrage/probability-signals/status")
async def arbitrage_probability_signal_status_route():
    """#422 Arbitrage Probability Signal — early detection filter for #403."""
    from bd_platform.arbitrage_probability_signal import arbitrage_probability_signal_status

    return arbitrage_probability_signal_status()


@router.get("/intelligence-ledger/unified-arbitrage/probability-signals")
async def arbitrage_probability_signal_panel_route(asset: str | None = Query(None)):
    from bd_platform.arbitrage_probability_signal import build_probability_panel

    return build_probability_panel(asset)


@router.get("/intelligence-ledger/unified-arbitrage/probability-backtest")
async def arbitrage_probability_backtest_route():
    from bd_platform.arbitrage_probability_signal import build_probability_backtest

    return build_probability_backtest()


@router.get("/intelligence-ledger/unified-arbitrage/probability-signals/reconciliation-tests")
async def arbitrage_probability_reconciliation_tests_route():
    from bd_platform.arbitrage_probability_signal import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/unified-arbitrage/economics/status")
async def spread_calculation_engine_status_route():
    """#427 Spread Calculation Engine — Economics Engine for #429."""
    from bd_platform.spread_calculation_engine import spread_calculation_engine_status

    return spread_calculation_engine_status()


@router.get("/intelligence-ledger/unified-arbitrage/economics/regression")
async def spread_calculation_engine_regression_route():
    from bd_platform.spread_calculation_engine import run_regression_fixtures

    return run_regression_fixtures()


@router.get("/intelligence-ledger/unified-arbitrage/economics/reconciliation-tests")
async def spread_calculation_engine_reconciliation_route():
    from bd_platform.spread_calculation_engine import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/unified-arbitrage/basis-funding/status")
async def basis_funding_divergence_status_route():
    """#440 Basis/Funding Divergence Monitor — derivatives category in #429."""
    from bd_platform.basis_funding_divergence_monitor import basis_funding_divergence_status

    return basis_funding_divergence_status()


@router.get("/intelligence-ledger/unified-arbitrage/basis-funding")
async def basis_funding_divergence_panel_route(asset: str | None = Query(None)):
    from bd_platform.basis_funding_divergence_monitor import build_divergence_panel

    return build_divergence_panel(asset)


@router.get("/intelligence-ledger/unified-arbitrage/basis-funding/scan")
async def basis_funding_divergence_scan_route():
    from bd_platform.basis_funding_divergence_monitor import scan_derivatives_divergence

    opps = scan_derivatives_divergence()
    return {"ok": True, "opportunities": opps, "count": len(opps)}


@router.get("/intelligence-ledger/unified-arbitrage/basis-funding/reconciliation-tests")
async def basis_funding_divergence_reconciliation_route():
    from bd_platform.basis_funding_divergence_monitor import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/event-sentiment/status")
async def event_sentiment_monitor_status_route():
    """#443 Event & Sentiment Monitor — Intelligence Ledger Sprint-2."""
    from bd_platform.event_sentiment_monitor import event_sentiment_monitor_status

    return event_sentiment_monitor_status()


@router.get("/intelligence-ledger/event-sentiment")
async def event_sentiment_monitor_panel_route(asset: str | None = Query(None)):
    from bd_platform.event_sentiment_monitor import build_event_sentiment_panel

    return build_event_sentiment_panel(asset)


@router.get("/intelligence-ledger/event-sentiment/calendar")
async def event_sentiment_calendar_route(
    event_type: str | None = Query(None),
    asset: str | None = Query(None),
):
    from bd_platform.event_sentiment_monitor import build_event_calendar

    return build_event_calendar(event_type=event_type, asset=asset)


@router.get("/intelligence-ledger/event-sentiment/alerts")
async def event_sentiment_alerts_route(hours_ahead: int = Query(72)):
    from bd_platform.event_sentiment_monitor import build_alerts

    return build_alerts(hours_ahead=hours_ahead)


@router.get("/intelligence-ledger/event-sentiment/archive")
async def event_sentiment_archive_route():
    from bd_platform.event_sentiment_monitor import build_archive_panel

    return build_archive_panel()


@router.get("/intelligence-ledger/event-sentiment/reconciliation-tests")
async def event_sentiment_reconciliation_route():
    from bd_platform.event_sentiment_monitor import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/stablecoin-health/status")
async def stablecoin_health_monitor_status_route():
    """#467 Stablecoin Health Monitor — Risk Layer (merged into #410)."""
    from bd_platform.stablecoin_health_monitor import stablecoin_health_monitor_status

    return stablecoin_health_monitor_status()


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/stablecoin-health")
async def stablecoin_health_monitor_panel_route(symbol: str | None = Query(None)):
    from bd_platform.stablecoin_health_monitor import analyze_stablecoin, build_stablecoin_health_panel

    if symbol:
        result = analyze_stablecoin(symbol)
        if not result.get("ok"):
            raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
        return result
    return build_stablecoin_health_panel()


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/stablecoin-health/alerts")
async def stablecoin_health_alerts_route(portfolio_id: str = Query("demo_portfolio")):
    from bd_platform.stablecoin_health_monitor import build_portfolio_stablecoin_alerts

    return build_portfolio_stablecoin_alerts(portfolio_id)


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/stablecoin-health/reconciliation-tests")
async def stablecoin_health_reconciliation_route():
    from bd_platform.stablecoin_health_monitor import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/portfolio-ai/capital-awareness/stablecoin-health/exchange-reserve")
async def stablecoin_exchange_reserve_route():
    """#601 Stablecoin Exchange Reserve — merged into #467."""
    from bd_platform.stablecoin_health_monitor import build_stablecoin_exchange_reserve

    return build_stablecoin_exchange_reserve()


@router.get("/intelligence-ledger/investment-thesis/status")
async def investment_thesis_scoring_status_route():
    """#472 Investment Thesis Scoring — Intelligence Ledger (not price probability)."""
    from bd_platform.investment_thesis_scoring import investment_thesis_scoring_status

    return investment_thesis_scoring_status()


@router.get("/intelligence-ledger/investment-thesis")
async def investment_thesis_scoring_panel_route(asset: str | None = Query(None)):
    from bd_platform.investment_thesis_scoring import build_thesis_scoring_panel

    return build_thesis_scoring_panel(asset)


@router.get("/intelligence-ledger/investment-thesis/market-radar-card")
async def investment_thesis_market_radar_card_route(asset: str = Query("BTC")):
    from bd_platform.investment_thesis_scoring import build_market_radar_thesis_card

    result = build_market_radar_thesis_card(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/investment-thesis/reconciliation-tests")
async def investment_thesis_reconciliation_route():
    from bd_platform.investment_thesis_scoring import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/investment-thesis/on-chain-financials/status")
async def on_chain_financials_status_route():
    """#641 On-Chain Financials — merged into #472 Investment Thesis."""
    from bd_platform.on_chain_financials import on_chain_financials_status

    return on_chain_financials_status()


@router.get("/intelligence-ledger/investment-thesis/on-chain-financials")
async def on_chain_financials_panel_route(protocol_id: str = Query("uniswap")):
    """#641 On-Chain Financials panel."""
    from bd_platform.on_chain_financials import build_on_chain_financials

    result = build_on_chain_financials(protocol_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/investment-thesis/on-chain-financials/asset-tab")
async def on_chain_financials_asset_tab_route(asset: str = Query("UNI")):
    """#641 Asset Card financials tab."""
    from bd_platform.on_chain_financials import build_asset_financials_tab

    return build_asset_financials_tab(asset)


@router.get("/intelligence-ledger/investment-thesis/on-chain-financials/market-radar-sector")
async def on_chain_financials_sector_route():
    """#641 Market Radar — DeFi Protocols by Revenue."""
    from bd_platform.on_chain_financials import build_market_radar_revenue_sector

    return build_market_radar_revenue_sector()


@router.get("/intelligence-ledger/investment-thesis/on-chain-financials/export")
async def on_chain_financials_export_route(protocol_id: str = Query("uniswap")):
    from bd_platform.on_chain_financials import export_financials_report

    return export_financials_report(protocol_id)


@router.get("/intelligence-ledger/investment-thesis/on-chain-financials/reconciliation-tests")
async def on_chain_financials_reconciliation_route():
    from bd_platform.on_chain_financials import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/investment-thesis/on-chain-financials/cross-chain-comparison")
async def on_chain_financials_cross_chain_route():
    """#650 Cross-Chain Fundamentals — merged into #641 comparables dashboard."""
    from bd_platform.on_chain_financials import build_cross_chain_comparables_dashboard

    return build_cross_chain_comparables_dashboard()


@router.get("/intelligence-ledger/capital-formation/status")
async def capital_formation_status_route():
    """#648 Capital Formation Radar — Intelligence Ledger dimension."""
    from bd_platform.capital_formation_radar import capital_formation_radar_status

    return capital_formation_radar_status()


@router.get("/intelligence-ledger/capital-formation")
async def capital_formation_radar_route(sector_id: str | None = Query(None)):
    from bd_platform.capital_formation_radar import build_capital_formation_radar

    return build_capital_formation_radar(sector_id)


@router.get("/intelligence-ledger/capital-formation/chart")
async def capital_formation_chart_route():
    from bd_platform.capital_formation_radar import build_capital_formation_chart

    return build_capital_formation_chart()


@router.get("/intelligence-ledger/capital-formation/reconciliation-tests")
async def capital_formation_reconciliation_route():
    from bd_platform.capital_formation_radar import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/defi-decision-intelligence/status")
async def defi_decision_intelligence_status_route():
    """#651 DeFi Decision Engine — Intelligence Ledger dimension."""
    from bd_platform.defi_decision_intelligence import defi_decision_intelligence_status

    return defi_decision_intelligence_status()


@router.get("/intelligence-ledger/defi-decision-intelligence")
async def defi_decision_intelligence_panel_route(protocol_id: str | None = Query(None)):
    from bd_platform.defi_decision_intelligence import build_defi_decision_panel

    return build_defi_decision_panel(protocol_id)


@router.get("/intelligence-ledger/defi-decision-intelligence/score")
async def defi_decision_intelligence_score_route(protocol_id: str = Query("aave_v3")):
    from bd_platform.defi_decision_intelligence import score_decision_relevance

    result = score_decision_relevance(protocol_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/defi-decision-intelligence/reconciliation-tests")
async def defi_decision_intelligence_reconciliation_route():
    from bd_platform.defi_decision_intelligence import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/market-radar/ratio-builder/status")
async def custom_ratio_engine_status_route():
    """#653 Custom Ratio Engine — Market Radar Ratio Builder."""
    from bd_platform.custom_ratio_engine import custom_ratio_engine_status

    return custom_ratio_engine_status()


@router.get("/intelligence-ledger/market-radar/ratio-builder")
async def custom_ratio_builder_panel_route(
    protocol_id: str = Query("uniswap"),
    formula_id: str = Query("ps_ratio"),
):
    from bd_platform.custom_ratio_engine import build_ratio_builder_panel

    return build_ratio_builder_panel(protocol_id, formula_id)


@router.get("/intelligence-ledger/market-radar/ratio-builder/chart")
async def custom_ratio_chart_route(
    protocol_id: str = Query("uniswap"),
    formula_id: str = Query("ps_ratio"),
):
    from bd_platform.custom_ratio_engine import build_ratio_chart

    return build_ratio_chart(protocol_id, formula_id)


@router.get("/intelligence-ledger/market-radar/ratio-builder/peers")
async def custom_ratio_peers_route(
    protocol_id: str = Query("uniswap"),
    formula_id: str = Query("ps_ratio"),
):
    from bd_platform.custom_ratio_engine import build_peer_comparison

    result = build_peer_comparison(protocol_id, formula_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/market-radar/ratio-builder/validate")
async def custom_ratio_validate_route(
    numerator: str = Query("fdv"),
    denominator: str = Query("revenue_30d"),
):
    from bd_platform.custom_ratio_engine import validate_formula

    return validate_formula(numerator, denominator)


@router.get("/intelligence-ledger/market-radar/ratio-builder/thesis-dimension")
async def custom_ratio_thesis_dimension_route(
    asset: str = Query("UNI"),
    formula_id: str = Query("ps_ratio"),
):
    from bd_platform.custom_ratio_engine import score_custom_ratio_thesis_dimension

    result = score_custom_ratio_thesis_dimension(asset, formula_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/market-radar/ratio-builder/reconciliation-tests")
async def custom_ratio_engine_reconciliation_route():
    from bd_platform.custom_ratio_engine import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/market-radar/macro-context/status")
async def dxy_macro_context_status_route():
    """#655 DXY Dollar Index Elasticity — Market Radar Macro Context Panel."""
    from bd_platform.dxy_dollar_elasticity import dxy_dollar_elasticity_status

    return dxy_dollar_elasticity_status()


@router.get("/intelligence-ledger/market-radar/macro-context")
async def dxy_macro_context_panel_route(asset: str = Query("BTC")):
    from bd_platform.dxy_dollar_elasticity import build_macro_context_panel

    return build_macro_context_panel(asset)


@router.get("/intelligence-ledger/market-radar/macro-context/reconciliation-tests")
async def dxy_macro_context_reconciliation_route():
    from bd_platform.dxy_dollar_elasticity import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/daily-market-brief/status")
async def daily_market_brief_status_route():
    """#474 Daily Market Brief — Intelligence Ledger (template-based v1)."""
    from bd_platform.daily_market_brief import daily_market_brief_status

    return daily_market_brief_status()


@router.get("/intelligence-ledger/daily-market-brief")
async def daily_market_brief_panel_route():
    from bd_platform.daily_market_brief import generate_daily_brief

    return generate_daily_brief()


@router.get("/intelligence-ledger/daily-market-brief/market-radar")
async def daily_market_brief_market_radar_route():
    from bd_platform.daily_market_brief import build_market_radar_brief_first

    return build_market_radar_brief_first()


@router.get("/intelligence-ledger/daily-market-brief/reconciliation-tests")
async def daily_market_brief_reconciliation_route():
    from bd_platform.daily_market_brief import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/portfolio-ai/fill-risk-assessment/status")
async def fill_risk_assessment_status_route():
    """#433 Fill Risk Assessment — Intelligence Ledger Risk Layer."""
    from bd_platform.fill_risk_assessment import fill_risk_assessment_status

    return fill_risk_assessment_status()


@router.get("/intelligence-ledger/portfolio-ai/fill-risk-assessment")
async def fill_risk_assessment_panel_route(opportunity_id: str | None = Query(None)):
    from bd_platform.fill_risk_assessment import build_fill_risk_panel

    return build_fill_risk_panel(opportunity_id)


@router.get("/intelligence-ledger/portfolio-ai/fill-risk-assessment/reconciliation-tests")
async def fill_risk_assessment_reconciliation_tests_route():
    from bd_platform.fill_risk_assessment import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/portfolio-ai/portfolio-intelligence/status")
async def portfolio_intelligence_engine_status_route():
    """#449 Portfolio Intelligence Engine — Sprint-1 existing module."""
    from bd_platform.portfolio_intelligence_engine import portfolio_intelligence_engine_status

    return portfolio_intelligence_engine_status()


@router.get("/intelligence-ledger/portfolio-ai/portfolio-intelligence")
async def portfolio_intelligence_engine_panel_route(portfolio_id: str = Query("demo_portfolio")):
    from bd_platform.portfolio_intelligence_engine import build_integrated_panel

    return build_integrated_panel(portfolio_id)


@router.get("/intelligence-ledger/portfolio-ai/portfolio-intelligence/reconciliation-tests")
async def portfolio_intelligence_reconciliation_tests_route():
    from bd_platform.portfolio_intelligence_engine import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/portfolio-ai/portfolio-intelligence/roi-ath")
async def roi_ath_intelligence_route(
    asset: str | None = Query(None),
    portfolio_id: str = Query("demo_portfolio"),
):
    """#483 ROI & ATH Intelligence — merged into Portfolio AI."""
    from bd_platform.portfolio_intelligence_engine import (
        build_roi_ath_asset_card,
        build_roi_ath_panel,
    )

    if asset:
        return build_roi_ath_asset_card(asset)
    return build_roi_ath_panel(portfolio_id)


@router.get("/intelligence-ledger/portfolio-ai/portfolio-intelligence/sharpe")
async def sharpe_intelligence_route(portfolio_id: str = Query("demo_portfolio")):
    """#490 Sharpe Ratio Intelligence — merged into Portfolio AI."""
    from bd_platform.portfolio_intelligence_engine import build_sharpe_intelligence_panel

    return build_sharpe_intelligence_panel(portfolio_id)


@router.get("/intelligence-ledger/portfolio-ai/portfolio-intelligence/entry-exit")
async def entry_exit_timeline_route(wallet_id: str = Query("demo_wallet")):
    """#617 Entry/Exit Timeline — merged into Portfolio AI."""
    from bd_platform.portfolio_intelligence_engine import build_entry_exit_timeline

    return build_entry_exit_timeline(wallet_id)


@router.get("/intelligence-ledger/portfolio-ai/portfolio-intelligence/performance-card")
async def wallet_performance_card_route(wallet_id: str = Query("demo_wallet")):
    """#618 Historical Performance & Win Rate — merged into Portfolio AI."""
    from bd_platform.portfolio_intelligence_engine import build_wallet_historical_performance_card

    return build_wallet_historical_performance_card(wallet_id)


@router.get("/intelligence-ledger/portfolio-ai/portfolio-intelligence/pnl-breakdown")
async def wallet_pnl_breakdown_route(wallet_id: str = Query("demo_wallet")):
    """#619 Wallet PnL Analysis — merged into Portfolio AI."""
    from bd_platform.portfolio_intelligence_engine import build_wallet_pnl_breakdown

    return build_wallet_pnl_breakdown(wallet_id)


@router.get("/intelligence-ledger/portfolio-ai/unified-dashboard")
async def unified_portfolio_dashboard_route(portfolio_id: str = Query("demo_portfolio")):
    """#614 Unified Portfolio Dashboard — Portfolio AI main UI."""
    from bd_platform.portfolio_intelligence_engine import build_unified_portfolio_dashboard

    return build_unified_portfolio_dashboard(portfolio_id)


@router.get("/intelligence-ledger/portfolio-ai/wallet-profiler/status")
async def wallet_profiler_status_route():
    """#620 Wallet Profiler — Sprint-2 Core UI."""
    from bd_platform.wallet_profiler import wallet_profiler_status

    return wallet_profiler_status()


@router.get("/intelligence-ledger/portfolio-ai/wallet-profiler")
async def wallet_profiler_route(address: str = Query(..., min_length=3)):
    """#620 Wallet Profiler — 6-tab comprehensive wallet profile."""
    from bd_platform.wallet_profiler import build_wallet_profile

    return build_wallet_profile(address)


@router.get("/intelligence-ledger/portfolio-ai/wallet-profiler/reconciliation-tests")
async def wallet_profiler_reconciliation_route():
    from bd_platform.wallet_profiler import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/strategy-vetting/status")
async def strategy_vetting_status_route():
    """#492 Strategy Quality Gate — Intelligence Ledger."""
    from bd_platform.strategy_vetting import strategy_vetting_status

    return strategy_vetting_status()


@router.get("/intelligence-ledger/strategy-vetting")
async def strategy_vetting_panel_route():
    from bd_platform.strategy_vetting import build_strategy_quality_gate_panel

    return build_strategy_quality_gate_panel()


@router.get("/intelligence-ledger/strategy-vetting/reconciliation-tests")
async def strategy_vetting_reconciliation_route():
    from bd_platform.strategy_vetting import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/strategy-vetting/{strategy_id}")
async def strategy_vetting_detail_route(strategy_id: str):
    from bd_platform.strategy_vetting import vet_strategy

    result = vet_strategy(strategy_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/capital-awareness/risk-assessment")
async def intelligence_ledger_risk_assessment_route(signal_id: str = Query("sig_btc_momentum")):
    """#410 Intelligence Ledger — mandatory Risk Assessment on every signal."""
    from bd_platform.capital_protection_controls import build_signal_risk_assessment

    result = build_signal_risk_assessment(signal_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-ai/strategy-simulator/status")
async def strategy_simulator_status_route():
    """#411 Strategy Simulator — Paper Portfolio (real money blocked)."""
    from bd_platform.strategy_simulator import strategy_simulator_status

    return strategy_simulator_status()


@router.get("/intelligence-ledger/portfolio-ai/strategy-simulator")
async def strategy_simulator_panel_route():
    """#411 Strategy Simulator — paper portfolio with breakeven + risk budget integration."""
    from bd_platform.strategy_simulator import build_strategy_simulator_panel

    return build_strategy_simulator_panel()


@router.get("/intelligence-ledger/portfolio-ai/strategy-simulator/apply-signal")
async def strategy_simulator_apply_signal_route(signal_id: str = Query("sig_btc_momentum")):
    """#411 Apply Intelligence Ledger signal to paper portfolio — SIMULATION only."""
    from bd_platform.strategy_simulator import apply_signal_to_paper_portfolio

    result = apply_signal_to_paper_portfolio(signal_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/portfolio-ai/strategy-simulator/backtest-30d")
async def strategy_simulator_backtest_route():
    from bd_platform.strategy_simulator import build_paper_backtest_30d

    return build_paper_backtest_30d()


@router.get("/intelligence-ledger/portfolio-ai/strategy-simulator/paper-account")
async def strategy_simulator_paper_account_route():
    """#421 Paper account — balances, positions, PnL. SIMULATION only — no real execution."""
    from bd_platform.strategy_simulator import build_paper_account

    return build_paper_account()


@router.get("/intelligence-ledger/portfolio-ai/strategy-simulator/simulate-order")
async def strategy_simulator_simulate_order_route(
    symbol: str = Query("BTC"),
    side: str = Query("buy"),
    quantity: float = Query(0.01, gt=0),
    price: float = Query(65000, gt=0),
    venue: str = Query("binance"),
    slippage_bps: float | None = Query(None),
):
    """#421 Order simulator with realistic Fee DB fees + slippage options. No real execution."""
    from bd_platform.strategy_simulator import simulate_paper_order

    if side not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="side must be buy or sell")
    result = simulate_paper_order(
        symbol=symbol,
        side=side,  # type: ignore[arg-type]
        quantity=quantity,
        price=price,
        venue=venue,
        slippage_bps=slippage_bps,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "simulation_failed")
    return result


@router.get("/intelligence-ledger/portfolio-ai/strategy-simulator/reconciliation-tests")
async def strategy_simulator_reconciliation_tests_route():
    from bd_platform.strategy_simulator import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/intelligence-layer/live-breakeven/signal-context")
async def intelligence_ledger_breakeven_signal_context_route(
    symbol: str = Query("BTC"),
    signal_id: str | None = Query(None),
):
    """#404 Intelligence Ledger — distance to breakeven on signals when user owns asset."""
    from bd_platform.live_breakeven_tracker import build_intelligence_ledger_signal_context

    return build_intelligence_ledger_signal_context(symbol, signal_id=signal_id)


@router.get("/intelligence-ledger/oracle-vwap/status")
async def oracle_vwap_layer_status_route():
    """#413 Oracle VWAP / Fair Value Index — Oracle API layer (merged with #409)."""
    from bd_platform.oracle_vwap_layer import oracle_vwap_status

    return oracle_vwap_status()


@router.get("/intelligence-ledger/oracle-vwap/market-radar")
async def oracle_vwap_market_radar_route(symbol: str = Query("BTC")):
    """#413 Market Radar — VWAP + per-venue deviation %."""
    from bd_platform.oracle_vwap_layer import build_market_radar_vwap_context

    result = build_market_radar_vwap_context(symbol)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/oracle-vwap/arbitrage-benchmark")
async def oracle_vwap_arbitrage_benchmark_route(symbol: str = Query("BTC")):
    """#413 Arbitrage Scanner (#403) — VWAP benchmark not best bid/ask."""
    from bd_platform.oracle_vwap_layer import build_arbitrage_vwap_benchmark

    result = build_arbitrage_vwap_benchmark(symbol)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/oracle-vwap/breakeven-reference")
async def oracle_vwap_breakeven_reference_route(symbol: str = Query("BTC")):
    """#413+#404 Live Breakeven — VWAP reference price."""
    from bd_platform.oracle_vwap_layer import build_breakeven_vwap_price

    result = build_breakeven_vwap_price(symbol)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/oracle-vwap/reconciliation-tests")
async def oracle_vwap_reconciliation_tests_route():
    from bd_platform.oracle_vwap_layer import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/net-edge-truth/status")
async def net_edge_truth_status_route():
    """#417 Net-Edge Truth Score — Intelligence Ledger core scoring engine."""
    from bd_platform.net_edge_truth_layer import net_edge_truth_layer_status

    return net_edge_truth_layer_status()


@router.get("/intelligence-ledger/net-edge-truth")
async def net_edge_truth_panel_route(
    opportunity_id: str | None = Query(None),
):
    from bd_platform.net_edge_truth_layer import build_truth_score_panel

    return build_truth_score_panel(opportunity_id=opportunity_id)


@router.get("/intelligence-ledger/net-edge-truth/portfolio")
async def net_edge_truth_portfolio_route(
    portfolio_id: str = Query("demo_portfolio"),
):
    from bd_platform.net_edge_truth_layer import build_portfolio_net_edge_scores

    return build_portfolio_net_edge_scores(portfolio_id)


@router.get("/intelligence-ledger/net-edge-truth/history")
async def net_edge_truth_history_route():
    from bd_platform.net_edge_truth_layer import build_truth_score_history_panel

    return build_truth_score_history_panel()


@router.get("/intelligence-ledger/net-edge-truth/regression")
async def net_edge_truth_regression_route():
    from bd_platform.net_edge_truth_layer import run_regression_fixtures

    return run_regression_fixtures()


@router.get("/intelligence-ledger/intelligence-layer/net-edge-truth")
async def intelligence_ledger_net_edge_truth_route():
    from bd_platform.net_edge_truth_layer import build_intelligence_ledger_integration

    return build_intelligence_ledger_integration()


@router.get("/intelligence-ledger/net-edge-truth/reconciliation-tests")
async def net_edge_truth_reconciliation_tests_route():
    from bd_platform.net_edge_truth_layer import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/fill-feasibility/status")
async def fill_feasibility_simulator_status_route():
    """#415 Fill Feasibility Simulator — Liquidity Depth Analyzer."""
    from bd_platform.fill_feasibility_simulator import fill_feasibility_simulator_status

    return fill_feasibility_simulator_status()


@router.get("/intelligence-ledger/fill-feasibility")
async def fill_feasibility_panel_route(
    symbol: str = Query("BTC/USDT"),
    venue: str = Query("binance"),
    size: float = Query(5.0, gt=0),
):
    from bd_platform.fill_feasibility_simulator import build_fill_feasibility_panel

    return build_fill_feasibility_panel(symbol=symbol, venue=venue, size=size)


@router.get("/intelligence-ledger/fill-feasibility/heatmap")
async def fill_feasibility_heatmap_route(symbol: str = Query("BTC/USDT")):
    from bd_platform.fill_feasibility_simulator import build_liquidity_heatmap

    return build_liquidity_heatmap(symbol)


@router.get("/intelligence-ledger/fill-feasibility/arbitrage")
async def fill_feasibility_arbitrage_route(
    symbol: str = Query("BTC/USDT"),
    size: float = Query(1.0, gt=0),
):
    from bd_platform.fill_feasibility_simulator import build_arbitrage_feasibility_panel

    return build_arbitrage_feasibility_panel(symbol, size=size)


@router.get("/intelligence-ledger/fill-feasibility/market-radar")
async def fill_feasibility_market_radar_route(symbol: str = Query("BTC/USDT")):
    from bd_platform.fill_feasibility_simulator import build_market_radar_panel

    return build_market_radar_panel(symbol)


@router.get("/intelligence-ledger/intelligence-layer/fill-feasibility")
async def intelligence_ledger_fill_feasibility_route():
    from bd_platform.fill_feasibility_simulator import build_intelligence_ledger_integration

    return build_intelligence_ledger_integration()


@router.get("/intelligence-ledger/fill-feasibility/reconciliation-tests")
async def fill_feasibility_reconciliation_tests_route():
    from bd_platform.fill_feasibility_simulator import run_reconciliation_tests

    return run_reconciliation_tests()


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


@router.get("/intelligence-ledger/market-radar/volatility-analytics")
async def market_radar_volatility_analytics_route(asset: str = Query("BTC")):
    """#498 Volatility Analytics — realized vol dashboard (merged into Market Radar)."""
    from bd_platform.market_radar_indicators import build_volatility_analytics_dashboard

    result = build_volatility_analytics_dashboard(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/market-radar/panel")
async def market_radar_combined_panel_route(
    exchange: str = Query("binance"),
    asset: str = Query("BTC"),
):
    """Market Radar combined panel — exchange activity + volatility analytics."""
    from bd_platform.market_radar_indicators import build_market_radar_panel

    return build_market_radar_panel(exchange, asset)


@router.get("/intelligence-ledger/market-radar/reconciliation-tests")
async def market_radar_reconciliation_tests_route():
    from bd_platform.market_radar_indicators import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/market-radar/transaction-flow")
async def market_radar_transaction_flow_route(root_address: str = Query("0xbinance_hot")):
    """#615 Transaction Flow View — merged into Market Radar."""
    from bd_platform.transaction_flow_view import build_market_radar_transaction_flow_view

    return build_market_radar_transaction_flow_view(root_address)


@router.get("/intelligence-ledger/market-radar/transaction-flow/trace")
async def market_radar_transaction_flow_trace_route(
    root_address: str = Query("0xbinance_hot"),
    target_entity: str = Query("coinbase"),
):
    from bd_platform.transaction_flow_view import trace_path

    return trace_path(root_address, target_entity)


@router.get("/intelligence-ledger/market-radar/transaction-flow/reconciliation-tests")
async def transaction_flow_reconciliation_route():
    from bd_platform.transaction_flow_view import run_reconciliation_tests

    return run_reconciliation_tests()


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


@router.get("/intelligence-ledger/market-radar/basis-monitor")
async def market_radar_basis_monitor_route(limit: int = Query(5, ge=1, le=20)):
    """#440 Basis Divergence Scanner — top-N spot-perp basis opportunities for Market Radar."""
    from bd_platform.market_data_engine import build_basis_monitor_widget

    return build_basis_monitor_widget(limit=limit)


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


@router.get("/intelligence-ledger/data-layer/prediction-trends/status")
async def prediction_trend_analyzer_status_route():
    """#580 Prediction Trend Analyzer — contextual prediction-market probabilities."""
    from bd_platform.prediction_trend_analyzer import prediction_trend_analyzer_status

    return prediction_trend_analyzer_status()


@router.get("/intelligence-ledger/data-layer/prediction-trends")
async def prediction_trend_analyzer_panel_route():
    from bd_platform.prediction_trend_analyzer import build_prediction_trend_panel

    return build_prediction_trend_panel()


@router.get("/intelligence-ledger/data-layer/prediction-trends/reconciliation-tests")
async def prediction_trend_analyzer_reconciliation_tests_route():
    from bd_platform.prediction_trend_analyzer import run_reconciliation_tests

    return run_reconciliation_tests()


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
    sort_by: str | None = Query(None),
    sort_order: str = Query("asc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
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

    return run_screener(
        filters or None,
        saved_screener_id=saved_screener_id,
        user_id=user_id,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/intelligence-ledger/intelligence-layer/market-data-screener/reconciliation-tests")
async def market_data_screener_reconciliation_tests_route():
    from bd_platform.custom_market_data_screener import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/intelligence-layer/market-data-screener/saved")
async def custom_market_data_screener_saved_route():
    from bd_platform.custom_market_data_screener import list_saved_screeners

    return list_saved_screeners()


@router.get("/intelligence-ledger/intelligence-layer/market-data-screener/smart-money")
async def smart_money_token_screener_route(
    smart_money_inflow_min: float | None = Query(None),
    liquidity_min: float | None = Query(None),
    saved_screener_id: str | None = Query(None),
    sort_by: str | None = Query(None),
    sort_order: str = Query("asc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: str = Query("default"),
):
    """#597 Smart Money Token Screener — user-controlled filters, explain each match."""
    from bd_platform.custom_market_data_screener import run_smart_money_token_screener

    filters: dict[str, Any] = {}
    if smart_money_inflow_min is not None:
        filters["smart_money_inflow_min"] = {"min": smart_money_inflow_min}
    if liquidity_min is not None:
        filters["liquidity_min"] = {"min": liquidity_min}

    return run_smart_money_token_screener(
        filters or None,
        saved_screener_id=saved_screener_id,
        user_id=user_id,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


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


@router.get("/intelligence-ledger/data-layer/infrastructure/price-volume-market-metrics")
async def price_volume_market_metrics_route(asset: str = Query("BTC")):
    """#581 Price / Volume / Market Metrics — foundation task in Data Infrastructure."""
    from bd_platform.data_infrastructure_layer import build_price_volume_market_metrics_panel

    result = build_price_volume_market_metrics_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/infrastructure/custom-alerts/status")
async def custom_alerts_status_route():
    """#532 Custom Alerts — backend enforced, rate limits, tx evidence."""
    from bd_platform.custom_alerts import custom_alerts_status

    return custom_alerts_status()


@router.get("/intelligence-ledger/infrastructure/custom-alerts")
async def custom_alerts_panel_route(user_id: str = Query("default")):
    from bd_platform.custom_alerts import build_custom_alerts_panel

    return build_custom_alerts_panel(user_id=user_id)


@router.get("/intelligence-ledger/infrastructure/custom-alerts/reconciliation-tests")
async def custom_alerts_reconciliation_tests_route():
    from bd_platform.custom_alerts import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/data-layer/social-sentiment/status")
async def social_sentiment_layer_status_route():
    """#588 Social Sentiment Layer — absorbs #595, #596, #600."""
    from bd_platform.social_sentiment_layer import social_sentiment_layer_status

    return social_sentiment_layer_status()


@router.get("/intelligence-ledger/data-layer/social-sentiment")
async def social_sentiment_layer_panel_route(asset: str = Query("BTC")):
    from bd_platform.social_sentiment_layer import build_social_sentiment_panel

    result = build_social_sentiment_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/data-layer/social-sentiment/reconciliation-tests")
async def social_sentiment_reconciliation_tests_route():
    from bd_platform.social_sentiment_layer import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/data-layer/social-sentiment/entity-tagged-feed")
async def entity_tagged_sentiment_feed_route(asset: str = Query("BTC")):
    """#595/#596 Entity-Tagged Sentiment Feed — sub-module of #588 Social Sentiment Layer."""
    from bd_platform.social_sentiment_layer import build_entity_tagged_sentiment_feed

    result = build_entity_tagged_sentiment_feed(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


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


@router.get("/intelligence-ledger/intelligence-layer/price-move-correlation-layer")
async def price_move_event_correlation_layer_route(
    asset: str = Query("BTC"),
    event_id: str | None = Query(None),
    candle_id: str | None = Query(None),
):
    """#556+#519+#582 unified Price-Move Event Correlation Layer epic."""
    from bd_platform.flow_to_price_event_correlator import build_price_move_event_correlation_layer_panel

    return build_price_move_event_correlation_layer_panel(
        asset=asset, event_id=event_id, candle_id=candle_id,
    )


@router.get("/intelligence-ledger/intelligence-layer/flow-to-price-correlator/reconciliation-tests")
async def flow_to_price_reconciliation_tests_route():
    from bd_platform.flow_to_price_event_correlator import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/intelligence-layer/market-anomaly/status")
async def market_anomaly_detection_status_route():
    """#583 Market Anomaly Detection Module — statistical multi-signal flags only."""
    from bd_platform.market_anomaly_detection_module import market_anomaly_detection_status

    return market_anomaly_detection_status()


@router.get("/intelligence-ledger/intelligence-layer/market-anomaly")
async def market_anomaly_detection_panel_route(asset: str = Query("ALT")):
    from bd_platform.market_anomaly_detection_module import build_market_anomaly_panel

    result = build_market_anomaly_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/market-anomaly/reconciliation-tests")
async def market_anomaly_reconciliation_tests_route():
    from bd_platform.market_anomaly_detection_module import run_reconciliation_tests

    return run_reconciliation_tests()


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
    """#524 sub-module feed — task not ticket (#523-530, #599)."""
    if sub_module_id == "599":
        from bd_platform.hype_vs_reality_signal import build_hype_vs_reality_panel

        return build_hype_vs_reality_panel(asset)

    from bd_platform.cross_domain_market_context_layer import build_sub_module_feed

    result = build_sub_module_feed(sub_module_id, asset=asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/hype-vs-reality/status")
async def hype_vs_reality_signal_status_route():
    """#599 Hype vs Reality Signal — merged into #524. No chatbot advisor role."""
    from bd_platform.hype_vs_reality_signal import hype_vs_reality_signal_status

    return hype_vs_reality_signal_status()


@router.get("/intelligence-ledger/intelligence-layer/hype-vs-reality")
async def hype_vs_reality_signal_panel_route(asset: str = Query("BTC")):
    """#599 — Confirmed / Social-only / On-chain-only / Contradictory badge feed."""
    from bd_platform.hype_vs_reality_signal import build_hype_vs_reality_panel

    result = build_hype_vs_reality_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/hype-vs-reality/reconciliation-tests")
async def hype_vs_reality_reconciliation_tests_route():
    from bd_platform.hype_vs_reality_signal import run_reconciliation_tests

    return run_reconciliation_tests()


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
    from bd_platform.onchain_metrics_library import build_onchain_metrics_library_panel_async

    return await build_onchain_metrics_library_panel_async(asset)


@router.get("/intelligence-ledger/onchain-layer/metrics-library/network-api")
async def network_data_pro_metrics_route(asset: str = Query("BTC")):
    """#574 Network Data Pro Metrics — institutional API (sub-task of #577)."""
    from bd_platform.onchain_metrics_library import build_network_data_pro_api_async

    return await build_network_data_pro_api_async(asset)


@router.get("/intelligence-ledger/onchain-layer/metrics-library/live")
async def onchain_metrics_live_route(asset: str = Query("BTC")):
    """Live indexer fetch — mempool.space, blockchain.info, Blockchair, Blockscout."""
    from bd_platform.onchain_live_indexer import fetch_live_onchain_metrics

    return await fetch_live_onchain_metrics(asset)


@router.get("/intelligence-ledger/onchain-layer/metrics-library/historical-qa")
async def onchain_metrics_historical_qa_route():
    from bd_platform.onchain_metrics_library import run_historical_qa_tests

    return run_historical_qa_tests()


@router.get("/intelligence-ledger/onchain-layer/metrics-library/usage")
async def onchain_usage_intelligence_route(asset: str = Query("BTC")):
    """#578 On-Chain Usage Intelligence — sub-task of #577 Metrics Library."""
    from bd_platform.onchain_metrics_library import build_usage_intelligence_dashboard

    result = build_usage_intelligence_dashboard(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/metrics-library/transaction-volume")
async def transaction_volume_intelligence_route(asset: str = Query("BTC")):
    """#612 Transaction Volume Intelligence — merged into #577."""
    from bd_platform.onchain_metrics_library import build_transaction_volume_intelligence

    result = build_transaction_volume_intelligence(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/metrics-library/transaction-volume/parity-qa")
async def transaction_volume_parity_qa_route():
    from bd_platform.onchain_metrics_library import run_tx_volume_historical_qa

    return run_tx_volume_historical_qa()


@router.get("/intelligence-ledger/onchain-layer/metrics-library/whale-vs-retail")
async def whale_vs_retail_flow_route(asset: str = Query("BTC")):
    """#634 Whale vs Retail Flow — merged into #577."""
    from bd_platform.onchain_metrics_library import build_whale_vs_retail_flow_panel

    result = build_whale_vs_retail_flow_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/whale-clustering/status")
async def whale_clustering_engine_status_route():
    """#637 Whale Clustering Engine — On-Chain Intelligence Core."""
    from bd_platform.whale_clustering_engine import whale_clustering_engine_status

    return whale_clustering_engine_status()


@router.get("/intelligence-ledger/onchain-layer/whale-clustering")
async def whale_clustering_panel_route(cluster_id: str | None = Query(None)):
    """#637 Whale Clustering Engine — cluster view panel."""
    from bd_platform.whale_clustering_engine import build_whale_cluster_panel

    return build_whale_cluster_panel(cluster_id)


@router.get("/intelligence-ledger/onchain-layer/whale-clustering/address")
async def whale_clustering_address_route(address: str = Query(..., min_length=3)):
    """#637 cluster affiliation for a single address."""
    from bd_platform.whale_clustering_engine import build_cluster_view

    result = build_cluster_view(address)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/onchain-layer/whale-clustering/reconciliation-tests")
async def whale_clustering_reconciliation_route():
    from bd_platform.whale_clustering_engine import run_reconciliation_tests

    return run_reconciliation_tests()


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


@router.get("/intelligence-ledger/portfolio-layer/non-custodial-wallet-tracker")
async def non_custodial_wallet_tracker_route(
    address: str = Query("0x0000000000000000000000000000000000000001"),
    chain: str = Query("ethereum"),
):
    """#579 Non-Custodial Wallet Balance Tracker — holdings + data alerts (no risk output)."""
    from bd_platform.portfolio_intelligence_layer import build_non_custodial_wallet_balance_tracker

    result = build_non_custodial_wallet_balance_tracker(address, chain=chain)
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


@router.get("/intelligence-ledger/data-layer/protocol-valuation/realized-cap")
async def protocol_valuation_realized_cap_route(
    asset_id: str = Query("bitcoin"),
    entity_adjusted: bool = Query(True),
):
    """#584/#585 Realized Cap & Realized Price Intelligence."""
    from bd_platform.protocol_valuation_layer import build_realized_cap_panel

    result = build_realized_cap_panel(asset_id, entity_adjusted=entity_adjusted)
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


@router.get("/intelligence-ledger/data-layer/asset-registry/status")
async def asset_registry_status_route():
    """#402 Asset Registry — 105-coin Data Engine seed + metadata enrichment."""
    from bd_platform.asset_registry import asset_registry_status

    return asset_registry_status()


@router.get("/intelligence-ledger/data-layer/asset-registry")
async def asset_registry_panel_route(
    entity_id: str | None = Query(None),
    symbol: str | None = Query(None),
):
    from bd_platform.asset_registry import build_asset_registry_panel

    result = build_asset_registry_panel(entity_id=entity_id, symbol=symbol or "BTC")
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/data-layer/asset-registry/universe")
async def asset_registry_universe_route():
    from bd_platform.asset_registry import build_universe_panel

    return build_universe_panel()


@router.get("/intelligence-ledger/data-layer/asset-registry/reconciliation-tests")
async def asset_registry_reconciliation_tests_route():
    from bd_platform.asset_registry import run_reconciliation_tests

    return run_reconciliation_tests()


@router.get("/intelligence-ledger/market-radar/asset-registry")
async def market_radar_asset_registry_route():
    """#402 Market Radar integration — 105-asset universe."""
    from bd_platform.asset_registry import build_market_radar_integration

    return build_market_radar_integration()


@router.get("/intelligence-ledger/portfolio-ai/asset-registry")
async def portfolio_ai_asset_registry_route(symbol: str | None = Query(None)):
    """#402 Portfolio AI integration — exposure context per asset."""
    from bd_platform.asset_registry import build_portfolio_ai_integration

    result = build_portfolio_ai_integration(symbol=symbol)
    if symbol and not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/intelligence-layer/asset-registry")
async def intelligence_ledger_asset_registry_route():
    """#402 Intelligence Ledger integration — canonical entity IDs."""
    from bd_platform.asset_registry import build_intelligence_ledger_integration

    return build_intelligence_ledger_integration()


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


@router.get("/internal/system-performance/status")
async def system_performance_monitor_status_route(_admin: dict = Depends(require_admin)):
    """#414 System Performance Monitor — Sprint-0 internal observability (admin only)."""
    from bd_platform.system_performance_monitor import system_performance_monitor_status

    return system_performance_monitor_status()


@router.get("/internal/system-performance")
async def system_performance_monitor_panel_route(_admin: dict = Depends(require_admin)):
    from bd_platform.system_performance_monitor import build_performance_panel

    return build_performance_panel()


@router.get("/internal/system-performance/reconciliation-tests")
async def system_performance_reconciliation_tests_route(_admin: dict = Depends(require_admin)):
    from bd_platform.system_performance_monitor import run_reconciliation_tests

    return run_reconciliation_tests()


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


@router.get("/intelligence-ledger/onchain-metrics/methodology")
async def onchain_metrics_methodology_registry_route():
    """#656 Data Methodology Registry — merged into #577."""
    from bd_platform.onchain_metrics_library import build_methodology_registry

    return build_methodology_registry()


@router.get("/intelligence-ledger/onchain-metrics/methodology/{metric_id}")
async def onchain_metrics_methodology_page_route(metric_id: str):
    from bd_platform.onchain_metrics_library import build_methodology_page

    result = build_methodology_page(metric_id)
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
