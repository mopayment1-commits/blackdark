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


# ─── Legal & Commercial (#57–#61) + Retail Intelligence (#62–#66) ─────────────


@router.get("/legal/disclosure/status")
async def service_disclosure_status_route():
    from bd_platform.legal_commercial_layer import service_disclosure_status_57

    return service_disclosure_status_57()


@router.get("/legal/commercial/status")
async def legal_commercial_status_route():
    from bd_platform.legal_commercial_layer import (
        aml_compliance_status_59,
        gdpr_compliance_status_58,
        payment_security_status_61,
        service_disclosure_status_57,
        subscription_tier_status_60,
    )

    return {
        "disclosure_57": service_disclosure_status_57(),
        "gdpr_58": gdpr_compliance_status_58(),
        "aml_59": aml_compliance_status_59(),
        "subscription_60": subscription_tier_status_60(),
        "payment_security_61": payment_security_status_61(),
    }


@router.post("/legal/disclosure/attach")
async def service_disclosure_attach_route(data: dict = Body(default={})):
    from bd_platform.legal_commercial_layer import attach_service_disclosure_57

    return attach_service_disclosure_57(data.get("payload") or data, locale=data.get("locale", "en"))


@router.post("/legal/aml/evaluate")
async def aml_evaluate_route(data: dict = Body(default={}), _admin: dict = Depends(require_admin)):
    from bd_platform.legal_commercial_layer import evaluate_aml_gate_59

    return evaluate_aml_gate_59(
        amount_usd=float(data.get("amount_usd", 0)),
        email=str(data.get("email", "")),
        name=str(data.get("name", "")),
        pattern_score=float(data.get("pattern_score", 0)),
    )


@router.get("/legal/tiers/limits")
async def tier_limits_route(tier: str = Query("free")):
    from bd_platform.legal_commercial_layer import get_tier_limits_60, pricing_transparency_manifest_60

    return {"limits": get_tier_limits_60(tier), "transparency": pricing_transparency_manifest_60()}


@router.get("/legal/commercial/e2e")
async def legal_commercial_e2e_route(_admin: dict = Depends(require_admin)):
    from bd_platform.legal_commercial_layer import run_legal_commercial_e2e_57_61

    return run_legal_commercial_e2e_57_61()


@router.get("/intelligence/daily-top3")
async def daily_top3_route(tier: str = Query("free"), locale: str = Query("en")):
    from bd_platform.retail_intelligence_layer import build_daily_top3_62

    return build_daily_top3_62(user_tier=tier, locale=locale)


@router.post("/intelligence/clear-answer")
async def clear_answer_route(data: dict = Body(default={})):
    from bd_platform.retail_intelligence_layer import build_one_clear_answer_63

    return build_one_clear_answer_63(
        verdict=data.get("verdict", "Neutral"),
        reasons=data.get("reasons"),
        risk_score=float(data.get("risk_score", 5.0)),
        locale=data.get("locale", "en"),
        raw_indicators=data.get("raw_indicators"),
    )


@router.get("/intelligence/glossary")
async def glossary_route(locale: str = Query("en")):
    from bd_platform.retail_intelligence_layer import glossary_manifest_64

    return glossary_manifest_64(locale=locale)


@router.post("/intelligence/contextual-alert/evaluate")
async def contextual_alert_route(data: dict = Body(default={})):
    from bd_platform.retail_intelligence_layer import evaluate_contextual_alert_65

    return evaluate_contextual_alert_65(
        user_id=str(data.get("user_id", "anonymous")),
        user_tier=str(data.get("user_tier", "free")),
        price=float(data.get("price", 0)),
        opportunity_level=float(data.get("opportunity_level", 0)),
        volume_zscore=float(data.get("volume_zscore", 0)),
        asset=str(data.get("asset", "BTC")),
        locale=data.get("locale", "en"),
    )


@router.post("/intelligence/discipline/compare")
async def discipline_compare_route(data: dict = Body(default={})):
    from bd_platform.retail_intelligence_layer import compare_discipline_66

    return compare_discipline_66(
        user_action=str(data.get("user_action", "")),
        user_price=float(data.get("user_price", 0)),
        system_verdict=str(data.get("system_verdict", "")),
        system_price=float(data.get("system_price", 0)),
        system_risk_score=float(data.get("system_risk_score", 5)),
        asset=str(data.get("asset", "BTC")),
    )


@router.get("/intelligence/retail/e2e")
async def retail_intelligence_e2e_route(_admin: dict = Depends(require_admin)):
    from bd_platform.retail_intelligence_layer import run_retail_intelligence_e2e_62_66

    return run_retail_intelligence_e2e_62_66()


# ─── Pro Trader & Portfolio UX (#67–#76) ────────────────────────────────────────


@router.get("/portfolio/health-score")
async def portfolio_health_score_route(
    concentration_pct: float = Query(50.0),
    volatility_score: float = Query(5.0),
    correlation_score: float = Query(5.0),
    diversification_score: float = Query(5.0),
):
    from bd_platform.pro_trader_layer import compute_health_score_67

    return compute_health_score_67(
        concentration_pct=concentration_pct,
        volatility_score=volatility_score,
        correlation_score=correlation_score,
        diversification_score=diversification_score,
    )


@router.post("/share/card")
async def share_card_route(data: dict = Body(default={})):
    from bd_platform.pro_trader_layer import build_share_card_68

    return build_share_card_68(
        card_type=str(data.get("card_type", "insight")),
        title=str(data.get("title", "")),
        summary=str(data.get("summary", "")),
        risk_score=float(data.get("risk_score", 5.0)),
        locale=str(data.get("locale", "en")),
        asset=str(data.get("asset", "")),
        health_score=data.get("health_score"),
        utm_campaign=str(data.get("utm_campaign", "share_card")),
    )


@router.get("/onboarding/ttv")
async def ttv_onboarding_route():
    from bd_platform.pro_trader_layer import get_onboarding_config_69

    return get_onboarding_config_69()


@router.post("/onboarding/ttv/track")
async def ttv_track_route(data: dict = Body(default={})):
    from bd_platform.pro_trader_layer import evaluate_ttv_flow_69, track_ttv_event_69

    elapsed = float(data.get("elapsed_seconds", 0))
    if data.get("event"):
        track_ttv_event_69(event=str(data["event"]), elapsed_seconds=elapsed, user_id=str(data.get("user_id", "guest")))
    return evaluate_ttv_flow_69(elapsed_seconds=elapsed)


@router.post("/intelligence/filter")
async def opportunity_filter_route(data: dict = Body(default={})):
    from bd_platform.pro_trader_layer import apply_opportunity_filter_70, save_filter_preset_70

    if data.get("save_preset"):
        return save_filter_preset_70(
            user_id=str(data.get("user_id", "user")),
            preset_name=str(data.get("preset_name", "default")),
            filters=data.get("filters") or {},
        )
    return apply_opportunity_filter_70(
        candidates=data.get("candidates"),
        filters=data.get("filters"),
        preset_name=str(data.get("preset_name", "")),
        user_tier=str(data.get("user_tier", "pro")),
    )


@router.post("/oracle/on-chain/narrative")
async def whale_narrative_route(data: dict = Body(default={})):
    from bd_platform.pro_trader_layer import build_whale_narrative_71

    return build_whale_narrative_71(
        wallet=str(data.get("wallet", "0x1234...5678")),
        amount_eth=float(data.get("amount_eth", 0)),
        direction=str(data.get("direction", "to_exchange")),
        to_cold=bool(data.get("to_cold", False)),
        tx_hash=str(data.get("tx_hash", "")),
    )


@router.post("/oracle/on-chain/classify")
async def noise_filter_route(data: dict = Body(default={})):
    from bd_platform.pro_trader_layer import classify_onchain_signal_72

    return classify_onchain_signal_72(
        movement_type=str(data.get("movement_type", "transfer")),
        same_entity=bool(data.get("same_entity", False)),
        is_collateral=bool(data.get("is_collateral", False)),
        is_exchange_internal=bool(data.get("is_exchange_internal", False)),
        amount_usd=float(data.get("amount_usd", 0)),
    )


@router.get("/intelligence/multi-dim")
async def multi_dim_route(
    asset: str = Query("BTC"),
    technical: float = Query(5.0),
    on_chain: float = Query(5.0),
    sentiment: float = Query(5.0),
    macro: float = Query(5.0),
):
    from bd_platform.pro_trader_layer import build_multi_dim_analysis_73

    return build_multi_dim_analysis_73(
        asset=asset, technical=technical, on_chain=on_chain, sentiment=sentiment, macro=macro
    )


@router.post("/intelligence/backtest")
async def backtest_route(data: dict = Body(default={})):
    from bd_platform.pro_trader_layer import run_backtest_74

    return run_backtest_74(
        rules=data.get("rules"),
        days=int(data.get("days", 90)),
        asset=str(data.get("asset", "BTC")),
    )


@router.get("/alerts/policy")
async def alert_policy_route(tier: str = Query("free")):
    from bd_platform.pro_trader_layer import get_alert_policy_75

    return get_alert_policy_75(user_tier=tier)


@router.post("/portfolio/journal")
async def journal_add_route(data: dict = Body(default={})):
    from bd_platform.pro_trader_layer import add_journal_entry_76, update_journal_actual_76

    if data.get("entry_id") and data.get("actual_price") is not None:
        return update_journal_actual_76(entry_id=str(data["entry_id"]), actual_price=float(data["actual_price"]))
    return add_journal_entry_76(
        asset=str(data.get("asset", "BTC")),
        price=float(data.get("price", 0)),
        prediction=str(data.get("prediction", "")),
        reason=str(data.get("reason", "")),
        user_email=str(data.get("user_email", "")),
    )


@router.get("/portfolio/journal")
async def journal_list_route():
    from bd_platform.pro_trader_layer import build_journal_tab_76

    return build_journal_tab_76()


@router.get("/pro-trader/e2e")
async def pro_trader_e2e_route(_admin: dict = Depends(require_admin)):
    from bd_platform.pro_trader_layer import run_pro_trader_e2e_67_76

    return run_pro_trader_e2e_67_76()


# ─── Whales & Institutional (#77–#86) ─────────────────────────────────────────


@router.get("/portfolio/advanced-risk")
async def advanced_risk_route(
    concentration_pct: float = Query(50.0),
    btc_shock_pct: float = Query(-20.0),
):
    from bd_platform.whales_institutional_layer import build_advanced_risk_report_77

    holdings = [{"symbol": "BTC", "value_usd": concentration_pct * 1000, "btc_beta": 1.0}]
    return build_advanced_risk_report_77(holdings, btc_shock_pct=btc_shock_pct)


@router.get("/intelligence/impact-analysis")
async def impact_analysis_route(
    order_usd: float = Query(...),
    asset: str = Query("BTC"),
    depth_usd: float = Query(5_000_000),
):
    from bd_platform.whales_institutional_layer import build_impact_analysis_78

    return build_impact_analysis_78(order_usd=order_usd, asset=asset, depth_usd=depth_usd)


@router.get("/intelligence/execution-status")
async def execution_rejected_status_route():
    from bd_platform.whales_institutional_layer import execution_routing_status_78

    return execution_routing_status_78()


@router.post("/oracle/on-chain/surveillance")
async def wallet_surveillance_route(data: dict = Body(default={})):
    from bd_platform.whales_institutional_layer import analyze_wallet_surveillance_79

    return analyze_wallet_surveillance_79(
        wallet=str(data.get("wallet", "")),
        suspicious_query_count=int(data.get("suspicious_query_count", 0)),
        mev_bot_hits=int(data.get("mev_bot_hits", 0)),
    )


@router.get("/radar/exchange-health")
async def exchange_health_route(exchange: str = Query("binance")):
    from bd_platform.whales_institutional_layer import build_exchange_health_80

    return build_exchange_health_80(exchange=exchange)


@router.post("/portfolio/unified-view")
async def unified_portfolio_route(data: dict = Body(default={})):
    from bd_platform.whales_institutional_layer import build_unified_portfolio_view_81

    return build_unified_portfolio_view_81(positions=data.get("positions"))


@router.post("/radar/alerts/liquidation")
async def liquidation_alert_route(data: dict = Body(default={})):
    from bd_platform.whales_institutional_layer import evaluate_liquidation_alert_82

    return evaluate_liquidation_alert_82(
        asset=str(data.get("asset", "BTC")),
        price=float(data.get("price", 0)),
        liquidation_level=float(data.get("liquidation_level", 0)),
        open_interest_usd=float(data.get("open_interest_usd", 0)),
    )


@router.get("/institution/smb-status")
async def smb_institution_deferred_route():
    from bd_platform.whales_institutional_layer import smb_institution_status_83

    return smb_institution_status_83()


@router.get("/transparency/performance")
async def performance_ledger_route():
    from bd_platform.whales_institutional_layer import build_performance_ledger_view_84

    return build_performance_ledger_view_84()


@router.post("/transparency/performance/record")
async def performance_record_route(data: dict = Body(default={}), _admin: dict = Depends(require_admin)):
    from bd_platform.whales_institutional_layer import record_performance_entry_84

    return record_performance_entry_84(
        asset=str(data.get("asset", "BTC")),
        insight=str(data.get("insight", "")),
        risk_score=float(data.get("risk_score", 5)),
        confidence=float(data.get("confidence", 5)),
        response_id=str(data.get("response_id", "")),
    )


@router.get("/docs/openapi-status")
async def openapi_status_route():
    from bd_platform.whales_institutional_layer import openapi_documentation_status_85

    return openapi_documentation_status_85()


@router.get("/transparency/methodology")
async def methodology_route(locale: str = Query("en")):
    from bd_platform.whales_institutional_layer import build_methodology_docs_86

    return build_methodology_docs_86(locale=locale)


@router.get("/whales-institutional/e2e")
async def whales_institutional_e2e_route(_admin: dict = Depends(require_admin)):
    from bd_platform.whales_institutional_layer import run_whales_institutional_e2e_77_86

    return run_whales_institutional_e2e_77_86()


# ─── Institutional B2B (#87–#94) ────────────────────────────────────────────────


@router.post("/intelligence/export/ic-report")
@router.post("/portfolio/export/ic-report")
async def ic_report_route(data: dict = Body(default={})):
    from bd_platform.institutional_b2b_layer import build_ic_report_87

    return build_ic_report_87(
        source=str(data.get("source", "intelligence")),
        asset=str(data.get("asset", "BTC")),
        verdict=str(data.get("verdict", "Neutral")),
        risk_score=float(data.get("risk_score", 6.0)),
        holdings=data.get("holdings"),
        locale=str(data.get("locale", "en")),
    )


@router.get("/team/rbac/status")
async def team_rbac_status_route():
    from bd_platform.institutional_b2b_layer import team_rbac_status_88

    return team_rbac_status_88()


@router.post("/team/rbac/check")
async def team_rbac_check_route(data: dict = Body(default={})):
    from bd_platform.institutional_b2b_layer import check_team_permission_88

    return check_team_permission_88(
        role=str(data.get("role", "guest")),
        action=str(data.get("action", "view")),
        user_email=str(data.get("user_email", "")),
        resource=str(data.get("resource", "")),
        ip=str(data.get("ip", "")),
    )


@router.get("/institution/sla-status")
async def sla_deferred_route():
    from bd_platform.institutional_b2b_layer import sla_status_89

    return sla_status_89()


@router.get("/institution/white-label-status")
async def white_label_deferred_route():
    from bd_platform.institutional_b2b_layer import white_label_status_90

    return white_label_status_90()


@router.get("/radar/technical/vwap")
async def vwap_route():
    from bd_platform.institutional_b2b_layer import compute_vwap_deviation_91

    return compute_vwap_deviation_91()


@router.get("/radar/exchange-health/full")
async def exchange_health_counterparty_route(
    exchange: str = Query("binance"),
    withdrawal_latency_hours: float = Query(12.0),
):
    from bd_platform.institutional_b2b_layer import build_exchange_health_with_counterparty_92

    return build_exchange_health_with_counterparty_92(
        exchange=exchange, withdrawal_latency_hours=withdrawal_latency_hours
    )


@router.post("/portfolio/confidence-calibration")
async def confidence_calibration_route(data: dict = Body(default={})):
    from bd_platform.institutional_b2b_layer import compute_confidence_calibration_93

    return compute_confidence_calibration_93(
        declared_confidence_pct=float(data.get("declared_confidence_pct", 80)),
        journal_entries=data.get("journal_entries"),
    )


@router.get("/institution/audit-export/status")
async def audit_export_status_route():
    from bd_platform.institutional_b2b_layer import audit_export_status_94

    return audit_export_status_94()


@router.get("/institution/audit-export")
async def audit_export_route(fmt: str = Query("json")):
    from bd_platform.institutional_b2b_layer import export_rbac_audit_94

    return export_rbac_audit_94(fmt=fmt)


@router.get("/institutional-b2b/e2e")
async def institutional_b2b_e2e_route(_admin: dict = Depends(require_admin)):
    from bd_platform.institutional_b2b_layer import run_institutional_b2b_e2e_87_94

    return run_institutional_b2b_e2e_87_94()


# ─── Infrastructure & Intelligence (#95–#104) ───────────────────────────────────


@router.get("/admin/analytics")
async def usage_analytics_route(_admin: dict = Depends(require_admin)):
    from bd_platform.infra_intelligence_layer import build_admin_analytics_dashboard_95

    return build_admin_analytics_dashboard_95()


@router.post("/admin/analytics/track")
async def usage_analytics_track_route(data: dict = Body(default={}), _admin: dict = Depends(require_admin)):
    from bd_platform.infra_intelligence_layer import track_usage_event_95

    return track_usage_event_95(
        endpoint=str(data.get("endpoint", "/unknown")),
        event_type=str(data.get("event_type", "api_call")),
        feature=str(data.get("feature", "")),
        duration_ms=float(data.get("duration_ms", 0)),
        error=bool(data.get("error", False)),
        user_id=str(data.get("user_id", "")),
    )


@router.get("/data-engine/streaming/status")
async def streaming_stack_status_route():
    from bd_platform.infra_intelligence_layer import streaming_stack_status_96

    return streaming_stack_status_96()


@router.post("/data-engine/streaming/enqueue")
async def streaming_enqueue_route(data: dict = Body(default={})):
    from bd_platform.infra_intelligence_layer import enqueue_stream_event_96

    return enqueue_stream_event_96(source=str(data.get("source", "oracle")), payload=data.get("payload"))


@router.post("/intelligence/feedback")
async def flywheel_feedback_route(data: dict = Body(default={})):
    from bd_platform.infra_intelligence_layer import submit_insight_feedback_97

    return submit_insight_feedback_97(
        insight_id=str(data.get("insight_id", "")),
        feedback=str(data.get("feedback", "neutral")),  # type: ignore[arg-type]
        actual_outcome=str(data.get("actual_outcome", "")),
    )


@router.get("/registry/status")
async def sovereign_registry_status_route(_admin: dict = Depends(require_admin)):
    from bd_platform.infra_intelligence_layer import sovereign_registry_status_98

    return sovereign_registry_status_98()


@router.post("/registry/register")
async def sovereign_registry_register_route(data: dict = Body(default={}), _admin: dict = Depends(require_admin)):
    from bd_platform.infra_intelligence_layer import register_canonical_signal_98

    return register_canonical_signal_98(
        name=str(data.get("name", "")),
        formula=str(data.get("formula", "")),
        data_source=str(data.get("data_source", "")),
        signal_type=str(data.get("signal_type", "custom")),
    )


@router.post("/radar/sentiment/filter")
@router.post("/oracle/on-chain/filter")
async def sybil_filter_route(data: dict = Body(default={})):
    from bd_platform.infra_intelligence_layer import filter_sybil_clusters_99

    return filter_sybil_clusters_99(data.get("wallets") or [])


@router.get("/oracle/validate")
async def oracle_freshness_route(
    primary_ms: float = Query(1_000_000),
    secondary_ms: float = Query(1_000_200),
):
    from bd_platform.infra_intelligence_layer import validate_oracle_freshness_101

    return validate_oracle_freshness_101(
        primary_timestamp_ms=primary_ms,
        secondary_timestamp_ms=secondary_ms,
    )


@router.get("/oracle/on-chain/defi/il-score")
async def il_vulnerability_route(
    price_ratio: float = Query(1.2),
    volatility_30d: float = Query(0.45),
    liquidity_depth_usd: float = Query(5_000_000),
):
    from bd_platform.infra_intelligence_layer import compute_il_vulnerability_102

    return compute_il_vulnerability_102(
        price_ratio=price_ratio,
        volatility_30d=volatility_30d,
        liquidity_depth_usd=liquidity_depth_usd,
    )


@router.get("/radar/market-health")
async def leverage_overhang_route(
    open_interest_usd: float = Query(8_000_000_000),
    average_leverage: float = Query(12.0),
    spot_liquidity_usd: float = Query(2_500_000_000),
):
    from bd_platform.infra_intelligence_layer import compute_leverage_overhang_104

    return compute_leverage_overhang_104(
        open_interest_usd=open_interest_usd,
        average_leverage=average_leverage,
        spot_liquidity_usd=spot_liquidity_usd,
    )


@router.get("/infra-intelligence/e2e")
async def infra_intelligence_e2e_route(_admin: dict = Depends(require_admin)):
    from bd_platform.infra_intelligence_layer import run_infra_intelligence_e2e_95_104

    return run_infra_intelligence_e2e_95_104()


# ─── Market Analysis (#105–#116) ──────────────────────────────────────────────────


@router.get("/radar/market-health/contagion")
async def contagion_vector_route():
    from bd_platform.market_analysis_layer import compute_contagion_vector_106

    return compute_contagion_vector_106()


@router.get("/radar/market-health/gcli")
async def gcli_route():
    from bd_platform.market_analysis_layer import compute_gcli_112

    return compute_gcli_112()


@router.get("/radar/market-health/ls-ratio")
async def whale_ls_ratio_route():
    from bd_platform.market_analysis_layer import compute_whale_ls_ratio_114

    return compute_whale_ls_ratio_114()


@router.get("/radar/market-health/full")
async def market_health_bundle_route():
    from bd_platform.market_analysis_layer import attach_market_health_bundle_106_112_114
    from bd_platform.infra_intelligence_layer import compute_leverage_overhang_104

    bundle = attach_market_health_bundle_106_112_114()
    bundle["leverage_overhang"] = compute_leverage_overhang_104()
    return bundle


@router.get("/radar/technical/orderbook-skew")
async def orderbook_skew_route(
    bid_depth_usd: float = Query(12_000_000),
    ask_depth_usd: float = Query(8_000_000),
    exchange: str = Query("binance"),
):
    from bd_platform.market_analysis_layer import compute_orderbook_skew_108

    return compute_orderbook_skew_108(bid_depth_usd=bid_depth_usd, ask_depth_usd=ask_depth_usd, exchange=exchange)


@router.get("/radar/technical/orderflow-imbalance")
async def imbalance_delta_route():
    from bd_platform.market_analysis_layer import compute_imbalance_delta_113

    return compute_imbalance_delta_113()


@router.get("/radar/technical/volume-velocity")
async def volume_velocity_route(
    volume_current: float = Query(3_000_000_000),
    volume_previous: float = Query(1_000_000_000),
):
    from bd_platform.market_analysis_layer import compute_volume_velocity_115

    return compute_volume_velocity_115(volume_current=volume_current, volume_previous=volume_previous)


@router.get("/oracle/on-chain/derivatives/delta-flow")
@router.get("/radar/derivatives/delta-pressure")
async def delta_hedging_flow_route():
    from bd_platform.market_analysis_layer import compute_delta_hedging_flow_116

    return compute_delta_hedging_flow_116()


@router.get("/market-analysis/e2e")
async def market_analysis_e2e_route(_admin: dict = Depends(require_admin)):
    from bd_platform.market_analysis_layer import run_market_analysis_e2e_105_116

    return run_market_analysis_e2e_105_116()


# ─── Advanced TA & Risk (#117–#128) ───────────────────────────────────────────────


@router.get("/radar/technical/liquidity-vacuum")
async def liquidity_vacuum_route(
    best_bid: float = Query(64980),
    lowest_ask: float = Query(65120),
    mid_price: float = Query(65050),
):
    from bd_platform.advanced_ta_risk_layer import compute_liquidity_vacuum_117

    return compute_liquidity_vacuum_117(best_bid=best_bid, lowest_ask=lowest_ask, mid_price=mid_price)


@router.get("/radar/technical/structural-break")
async def structural_break_route():
    from bd_platform.advanced_ta_risk_layer import compute_structural_break_122

    return compute_structural_break_122()


@router.get("/radar/technical/volume-profile")
async def volume_profile_route(period: str = Query("session")):
    from bd_platform.advanced_ta_risk_layer import compute_volume_profile_poc_123

    return compute_volume_profile_poc_123(period=period)


@router.get("/radar/technical/fvg-detector")
async def fvg_detector_route():
    from bd_platform.advanced_ta_risk_layer import detect_fair_value_gaps_124

    return detect_fair_value_gaps_124()


@router.get("/radar/technical/orderbook-inefficiency")
async def orderbook_inefficiency_route():
    from bd_platform.advanced_ta_risk_layer import orderbook_inefficiency_insight_127

    return orderbook_inefficiency_insight_127()


@router.get("/radar/on-chain/gas-alert")
async def gas_spike_alert_route(current_gwei: float = Query(150), avg_7d_gwei: float = Query(50)):
    from bd_platform.advanced_ta_risk_layer import gas_spike_alert_119

    return gas_spike_alert_119(current_gwei=current_gwei, avg_7d_gwei=avg_7d_gwei)


@router.get("/oracle/on-chain/dex-risk")
async def dex_front_running_risk_route():
    from bd_platform.advanced_ta_risk_layer import dex_front_running_risk_126

    return dex_front_running_risk_126()


@router.get("/portfolio/journal/attribution")
async def pnl_attribution_route(actual_pnl_usd: float = Query(5000)):
    from bd_platform.advanced_ta_risk_layer import compute_pnl_attribution_121

    return compute_pnl_attribution_121(actual_pnl_usd=actual_pnl_usd)


@router.get("/portfolio/leverage-risk")
async def leverage_risk_route(leverage: float = Query(10.0), volatility_30d_pct: float = Query(5.0)):
    from bd_platform.advanced_ta_risk_layer import compute_leverage_risk_analysis_120

    return compute_leverage_risk_analysis_120(leverage=leverage, volatility_30d_pct=volatility_30d_pct)


@router.get("/institution/custody-status")
async def custody_tracking_status_route():
    from bd_platform.advanced_ta_risk_layer import custody_tracking_status_125

    return custody_tracking_status_125()


@router.get("/intelligence/jargon")
async def jargon_explanation_route(term: str = Query("Impermanent Loss"), locale: str = Query("en")):
    from bd_platform.advanced_ta_risk_layer import jargon_explanation_128

    return jargon_explanation_128(term, locale=locale)


@router.get("/advanced-ta-risk/e2e")
async def advanced_ta_risk_e2e_route(_admin: dict = Depends(require_admin)):
    from bd_platform.advanced_ta_risk_layer import run_advanced_ta_risk_e2e_117_128

    return run_advanced_ta_risk_e2e_117_128()


# ─── On-Chain Platform (#129–#139) ────────────────────────────────────────────────


@router.post("/oracle/on-chain/sybil-clustering")
async def sybil_clustering_route(data: dict = Body(default={})):
    from bd_platform.onchain_platform_layer import cluster_sybil_identities_129

    return cluster_sybil_identities_129(data.get("wallets") or [])


@router.get("/oracle/on-chain/tx-risk")
async def tx_risk_insight_route(swap_usd: float = Query(10000), pair: str = Query("ETH/USDC")):
    from bd_platform.onchain_platform_layer import transaction_risk_insight_130

    return transaction_risk_insight_130(swap_usd=swap_usd, pair=pair)


@router.get("/portfolio/dust-analysis")
async def dust_analysis_route():
    from bd_platform.onchain_platform_layer import analyze_dust_assets_131

    return analyze_dust_assets_131()


@router.get("/oracle/on-chain/security/flash-loan-scan")
async def flash_loan_scan_route(protocol: str = Query("aave_v3")):
    from bd_platform.onchain_platform_layer import scan_flash_loan_vulnerabilities_132

    return scan_flash_loan_vulnerabilities_132(protocol=protocol)


@router.get("/radar/market-health/macro")
async def macro_event_nexus_route(event: str = Query("CPI")):
    from bd_platform.onchain_platform_layer import compute_macro_event_nexus_133

    return compute_macro_event_nexus_133(event=event)


@router.get("/radar/derivatives/delta-convergence")
async def delta_convergence_route():
    from bd_platform.onchain_platform_layer import compute_delta_convergence_134

    return compute_delta_convergence_134()


@router.get("/radar/market-health/liquidity-vortex")
async def liquidity_vortex_route():
    from bd_platform.onchain_platform_layer import locate_liquidity_vortex_135

    return locate_liquidity_vortex_135()


@router.post("/support/chat")
async def support_chat_route(data: dict = Body(default={})):
    from bd_platform.onchain_platform_layer import support_chat_response_136

    return support_chat_response_136(message=str(data.get("message", "")), user_tier=str(data.get("user_tier", "free")))


@router.get("/business/b2b-status")
async def b2b_relationships_route():
    from bd_platform.onchain_platform_layer import b2b_relationships_status_137

    return b2b_relationships_status_137()


@router.get("/institution/features-status")
async def institution_features_route():
    from bd_platform.onchain_platform_layer import institution_features_status_138

    return institution_features_status_138()


@router.get("/portfolio/stress-alert")
async def portfolio_stress_alert_route(portfolio_loss_pct_1h: float = Query(15.0), risk_score: float = Query(9.0)):
    from bd_platform.onchain_platform_layer import portfolio_stress_alert_139

    return portfolio_stress_alert_139(portfolio_loss_pct_1h=portfolio_loss_pct_1h, risk_score=risk_score)


@router.get("/onchain-platform/e2e")
async def onchain_platform_e2e_route(_admin: dict = Depends(require_admin)):
    from bd_platform.onchain_platform_layer import run_onchain_platform_e2e_129_139

    return run_onchain_platform_e2e_129_139()


# ─── Data Sources & Intelligence (#140–#152) ─────────────────────────────────────


@router.get("/institution/white-label-status")
async def white_label_status_route():
    from bd_platform.data_sources_layer import white_label_status_140

    return white_label_status_140()


@router.get("/radar/sentiment/feeds/coindesk")
async def coindesk_feed_route():
    from bd_platform.data_sources_layer import ingest_coindesk_feed_141

    return ingest_coindesk_feed_141()


@router.get("/radar/sentiment/sources/santiment")
async def santiment_sentiment_route(asset: str = Query("BTC")):
    from bd_platform.data_sources_layer import ingest_santiment_metrics_142

    return ingest_santiment_metrics_142(asset=asset)


@router.get("/radar/events/calendar")
async def event_calendar_route():
    from bd_platform.data_sources_layer import ingest_event_calendar_143

    return ingest_event_calendar_143()


@router.get("/oracle/on-chain/sources/whale-alert")
async def whale_alert_route():
    from bd_platform.data_sources_layer import ingest_whale_alert_144

    return ingest_whale_alert_144()


@router.get("/oracle/sources/cmc")
async def cmc_oracle_route(symbol: str = Query("BTC"), price: float = Query(65050.0)):
    from bd_platform.data_sources_layer import ingest_cmc_price_145

    return ingest_cmc_price_145(symbol=symbol, price=price)


@router.get("/oracle/sources/coinbase")
async def coinbase_oracle_route(symbol: str = Query("BTC-USD"), price: float = Query(65045.0)):
    from bd_platform.data_sources_layer import ingest_coinbase_price_146

    return ingest_coinbase_price_146(symbol=symbol, price=price)


@router.get("/oracle/consensus")
async def oracle_consensus_route(
    primary_price: float = Query(65050.0),
    cmc_price: float = Query(65050.0),
    coinbase_price: float = Query(65045.0),
):
    from bd_platform.data_sources_layer import validate_oracle_consensus_145_146

    return validate_oracle_consensus_145_146(
        primary_price=primary_price,
        cmc_price=cmc_price,
        coinbase_price=coinbase_price,
    )


@router.get("/signal-engine/status")
async def signal_engine_status_route():
    from bd_platform.data_sources_layer import signal_engine_status_147

    return signal_engine_status_147()


@router.get("/oracle/on-chain/sources/santiment")
async def santiment_onchain_route(asset: str = Query("BTC")):
    from bd_platform.data_sources_layer import ingest_santiment_metrics_142

    return ingest_santiment_metrics_142(asset=asset)


@router.get("/oracle/on-chain/sources/blockchain-com")
async def blockchain_com_route(block_height: int = Query(850_000)):
    from bd_platform.data_sources_layer import ingest_blockchain_com_148

    return ingest_blockchain_com_148(block_height=block_height)


@router.get("/oracle/on-chain/defi/defillama")
async def defillama_onchain_route(protocol: str = Query("aave")):
    from bd_platform.data_sources_layer import ingest_defillama_149

    return ingest_defillama_149(protocol=protocol)


@router.get("/radar/defi")
async def defillama_radar_route(protocol: str = Query("aave")):
    from bd_platform.data_sources_layer import ingest_defillama_149

    return ingest_defillama_149(protocol=protocol)


@router.get("/intelligence/score")
async def opportunity_score_route():
    from bd_platform.data_sources_layer import compute_opportunity_score_150

    return compute_opportunity_score_150()


@router.get("/intelligence/explain")
async def explain_opportunity_route(asset: str = Query("BTC")):
    from bd_platform.data_sources_layer import explain_opportunity_151

    return explain_opportunity_151(asset=asset)


@router.get("/alerts/execution-status")
async def alerts_execution_status_route():
    from bd_platform.data_sources_layer import alerts_execution_status_152

    return alerts_execution_status_152()


@router.get("/data-sources/e2e")
async def data_sources_e2e_route(_admin: dict = Depends(require_admin)):
    from bd_platform.data_sources_layer import run_data_sources_e2e_140_152

    return run_data_sources_e2e_140_152()


# ─── Intelligence & Analysis (#153–#163) ────────────────────────────────────────


@router.get("/intelligence/arbitrage")
async def arbitrage_mind_route(asset: str = Query("BTC")):
    from bd_platform.intelligence_analysis_layer import analyze_arbitrage_opportunity_153

    return analyze_arbitrage_opportunity_153(asset=asset)


@router.get("/intelligence/financial-brain-status")
async def financial_brain_status_route():
    from bd_platform.intelligence_analysis_layer import financial_brain_status_154

    return financial_brain_status_154()


@router.get("/intelligence/stat-arb")
async def stat_arb_insight_route(z_score: float = Query(2.3)):
    from bd_platform.intelligence_analysis_layer import stat_arb_insight_155

    return stat_arb_insight_155(z_score=z_score)


@router.get("/data-engine/asset-registry")
async def asset_registry_route():
    from bd_platform.intelligence_analysis_layer import asset_registry_105_coins_156

    return asset_registry_105_coins_156()


@router.get("/oracle/on-chain/advanced-status")
async def onchain_advanced_status_route():
    from bd_platform.intelligence_analysis_layer import onchain_advanced_status_157

    return onchain_advanced_status_157()


@router.get("/data-engine/multi-venue-websocket")
async def multi_venue_websocket_route():
    from bd_platform.intelligence_analysis_layer import multi_venue_websocket_status_158

    return multi_venue_websocket_status_158()


@router.get("/oracle/on-chain/gas-profile")
async def gas_volatility_profile_route(current_gwei: float = Query(18.0)):
    from bd_platform.intelligence_analysis_layer import compute_gas_volatility_profile_159

    return compute_gas_volatility_profile_159(current_gwei=current_gwei)


@router.get("/radar/technical/volatility-squeeze")
async def volatility_squeeze_route():
    from bd_platform.intelligence_analysis_layer import detect_volatility_squeeze_160

    return detect_volatility_squeeze_160()


@router.get("/alerts/delivery")
async def alert_delivery_route(channel: str = Query("telegram"), user_tier: str = Query("pro")):
    from bd_platform.intelligence_analysis_layer import alert_delivery_status_161

    return alert_delivery_status_161(channel=channel, user_tier=user_tier)


@router.get("/ui/data-grid-status")
async def data_grid_ui_status_route():
    from bd_platform.intelligence_analysis_layer import data_grid_ui_status_162

    return data_grid_ui_status_162()


@router.get("/intelligence/export/institutional-insight")
async def institutional_insight_report_route(asset: str = Query("BTC"), locale: str = Query("en")):
    from bd_platform.intelligence_analysis_layer import build_institutional_insight_report_163

    return build_institutional_insight_report_163(asset=asset, locale=locale)


@router.get("/intelligence-analysis/e2e")
async def intelligence_analysis_e2e_route(_admin: dict = Depends(require_admin)):
    from bd_platform.intelligence_analysis_layer import run_intelligence_analysis_e2e_153_163

    return run_intelligence_analysis_e2e_153_163()
