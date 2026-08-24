"""Platform API router — all 40 roadmap endpoints."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from typing import Annotated

from api.deps import require_feature
from security_auth import optional_user_from_request, require_admin, require_authenticated

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


# ── Feature #118 — Local ETL data foundation (infrastructure) ────────────────


@router.get("/infra/etl/status")
async def etl_status_route():
    """ETL pipeline health — ops/infrastructure (#118)."""
    from bd_platform.local_data_etl import etl_health_status

    return await etl_health_status()


@router.post("/infra/etl/run", responses=COMMON_ERROR_RESPONSES)
async def etl_run_route(
    body: dict[str, Any] = Body(default_factory=dict),
    _admin: dict = Depends(require_admin),
):
    """Trigger one ETL cycle — admin only (#118)."""
    from bd_platform.local_data_etl import run_etl_cycle

    assets = body.get("assets")
    if assets is not None and not isinstance(assets, list):
        raise HTTPException(status_code=400, detail="assets must be a list of symbols")
    return await run_etl_cycle(assets=assets)


@router.get("/infra/etl/query")
async def etl_query_route(
    domain: str | None = Query(None, pattern="^(market|onchain|user)$"),
    asset: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    """Query cleaned structured data — ≤1s SLA with Redis cache (#118)."""
    from bd_platform.local_data_etl import query_clean_data

    return await query_clean_data(domain=domain, asset=asset, limit=limit)  # type: ignore[arg-type]


@router.get("/infra/etl/export")
async def etl_export_route(
    domain: str | None = Query(None, pattern="^(market|onchain|user)$"),
    limit: int = Query(500, ge=1, le=5000),
    _admin: dict = Depends(require_admin),
):
    """Export cleaned dataset to data/etl/reports/ (#118)."""
    from bd_platform.local_data_etl import export_clean_data

    return await export_clean_data(domain=domain, limit=limit)  # type: ignore[arg-type]


# ── Features #133 + #127 + #194 — Price aggregation (invisible infrastructure) ─


@router.get("/infra/prices/aggregate")
async def price_aggregate_route(
    asset: str = Query("BTC"),
    use_cache: bool = Query(True),
):
    """Volume-weighted price aggregation with outlier filtering (#133 + #194)."""
    from bd_platform.price_aggregation_engine import aggregate_prices

    return await aggregate_prices(asset, use_cache=use_cache)


@router.get("/infra/prices/live")
async def price_live_refresh_route(asset: str = Query("BTC")):
    """Invisible live price refresh — WS/Redis → REST fallback (#127)."""
    from bd_platform.price_aggregation_engine import refresh_live_price

    return await refresh_live_price(asset)


@router.get("/infra/prices/status")
async def price_aggregation_status_route():
    """Price aggregation + live refresh pipeline health (#133 + #127)."""
    from bd_platform.price_aggregation_engine import price_aggregation_status

    return price_aggregation_status()


@router.get("/infra/connectors/status")
async def connector_layer_status_route():
    """Unified connector layer registry (#194)."""
    from bd_platform.unified_connector_layer import connector_layer_status

    return connector_layer_status()


# ── Feature #175 — Flexible Connector Microservice ─────────────────────────────


@router.get("/infra/connectors/registry")
async def connector_registry_dashboard_route(asset: str = Query("BTC")):
    """User-visible connector registry — health, coverage, freshness (#175)."""
    from bd_platform.flexible_connector_microservice import connector_registry_dashboard

    return await connector_registry_dashboard(asset)


@router.get("/infra/connectors/certification")
async def connector_certification_route(asset: str = Query("BTC")):
    """Connector health certification pass (#175)."""
    from bd_platform.flexible_connector_microservice import run_connector_certification

    return await run_connector_certification(asset)


@router.get("/infra/connectors/failover")
async def connector_failover_route(
    asset: str = Query("BTC"),
    preferred: str | None = Query(None, description="Comma-separated connector ids"),
):
    """Failover fetch — no synthetic success (#175)."""
    from bd_platform.flexible_connector_microservice import fetch_with_failover

    pref = [p.strip() for p in preferred.split(",") if p.strip()] if preferred else None
    return await fetch_with_failover(asset, preferred=pref)


@router.get("/infra/connectors/microservice/status")
async def flexible_connector_status_route():
    """Flexible Connector Microservice status (#175)."""
    from bd_platform.flexible_connector_microservice import flexible_connector_status

    return flexible_connector_status()


# ── Features #108 + #120 + #119 — Transfer network & cross-platform optimizer ─


@router.get("/transfer/networks")
async def transfer_networks_route(
    asset: str = Query("USDT"),
    amount_usd: float = Query(1000.0, ge=10.0, le=10_000_000.0),
    user_id: str | None = Query(None),
):
    """Best transfer networks ranked by speed/cost/security (#108 + #120)."""
    from bd_platform.transfer_network_utility import rank_transfer_networks

    return await rank_transfer_networks(asset, amount_usd=amount_usd, user_id=user_id)


@router.get("/transfer/networks/status")
async def transfer_networks_status_route():
    from bd_platform.transfer_network_utility import transfer_network_status

    return transfer_network_status()


@router.get("/transfer/network-prefs")
async def transfer_network_prefs_get(
    user_id: str = Query(..., min_length=1),
    asset: str = Query("USDT"),
):
    """User's saved transfer network (#120)."""
    from bd_platform.transfer_network_utility import get_user_network_preference

    pref = get_user_network_preference(user_id, asset)
    return {"ok": True, "feature": "#120", "user_id": user_id, "asset": asset.upper(), "preference": pref}


@router.post("/transfer/network-prefs", responses=COMMON_ERROR_RESPONSES)
async def transfer_network_prefs_set(body: dict[str, Any] = Body(...)):
    """Save user's preferred transfer network (#120)."""
    from bd_platform.transfer_network_utility import set_user_network_preference

    user_id = str(body.get("user_id") or "")
    asset = str(body.get("asset") or "USDT")
    network_id = str(body.get("network_id") or "")
    if not user_id or not network_id:
        raise HTTPException(status_code=400, detail="user_id and network_id required")
    return set_user_network_preference(user_id, asset, network_id)


@router.get("/transfer/optimizer")
async def cross_platform_transfer_optimizer_route(
    asset: str = Query("USDT"),
    source_cex: str = Query("binance"),
    dest_cex: str = Query("kraken"),
    amount_usd: float = Query(1000.0, ge=10.0, le=10_000_000.0),
    user_id: str | None = Query(None),
):
    """Cross-Platform Transfer Optimizer (#119) — fee-saving routes, not profit."""
    from bd_platform.cross_platform_transfer_optimizer import optimize_cross_platform_transfer

    return await optimize_cross_platform_transfer(
        asset=asset,
        source_cex=source_cex,
        dest_cex=dest_cex,
        amount_usd=amount_usd,
        user_id=user_id,
    )


@router.get("/transfer/optimizer/status")
async def transfer_optimizer_status_route():
    from bd_platform.cross_platform_transfer_optimizer import transfer_optimizer_status

    return transfer_optimizer_status()


@router.get("/transfer/widget")
async def transfer_deposit_widget_route(
    asset: str = Query("USDT"),
    amount_usd: float = Query(1000.0, ge=10.0, le=10_000_000.0),
    user_id: str | None = Query(None),
    surface: str = Query("transfer", pattern="^(transfer|deposit|withdraw)$"),
):
    """#120 embedded network widget — integrated with #108 on transfer/deposit pages."""
    from bd_platform.transfer_network_utility import transfer_deposit_widget

    return await transfer_deposit_widget(asset, amount_usd=amount_usd, user_id=user_id, surface=surface)


# ── Market Radar — #121 Large Liquidity, #114+#122 Listing Intelligence ─────


@router.get("/market-radar/large-liquidity-events")
async def large_liquidity_events_route(limit: int = Query(10, ge=1, le=30)):
    """Large Liquidity Event Alert (#121) — data + analysis, not buy advice."""
    from bd_platform.large_liquidity_event_alert import scan_large_liquidity_events

    return await scan_large_liquidity_events(limit=limit)


@router.get("/market-radar/listing-intelligence")
async def listing_intelligence_route(limit: int = Query(20, ge=1, le=50)):
    """Listing Intelligence Engine (#114 + #122 + #129) — detect + opportunity analysis."""
    from bd_platform.listing_intelligence_engine import scan_listing_intelligence

    return await scan_listing_intelligence(limit=limit)


@router.get("/market-radar/listing-opportunity")
async def listing_opportunity_route(
    symbol: str = Query(..., min_length=1, max_length=20),
    exchange: str = Query("binance"),
    liquidity_usd: float | None = Query(None, ge=0),
    opening_price_usd: float | None = Query(None, ge=0),
):
    """#129 — post-listing opportunity analysis for a single symbol."""
    from bd_platform.listing_intelligence_engine import analyze_listing_opportunity_for_symbol

    return await analyze_listing_opportunity_for_symbol(
        symbol,
        exchange=exchange,
        liquidity_usd=liquidity_usd,
        opening_price_usd=opening_price_usd,
    )


@router.get("/market-radar/unusual-liquidity")
async def unusual_liquidity_route(limit: int = Query(10, ge=1, le=30)):
    """Unusual Liquidity Alert Engine (#131) — on-chain + CEX depth severity alerts."""
    from bd_platform.unusual_liquidity_alert_engine import scan_unusual_liquidity_events

    return await scan_unusual_liquidity_events(limit=limit)


# ── Feature #130 — Fee Database (internal service) ───────────────────────────


@router.get("/infra/fees/status")
async def fee_database_status_route():
    """Fee Database internal service health (#130)."""
    from bd_platform.fee_database_service import fee_database_status

    return fee_database_status()


@router.get("/infra/fees/lookup")
async def fee_database_lookup_route(
    exchange_id: str = Query(..., min_length=1),
    symbol: str = Query("BTC/USDT"),
):
    """Fee matrix lookup — maker/taker/withdrawal/deposit (#130)."""
    from bd_platform.fee_database_service import lookup_fee_matrix

    return lookup_fee_matrix(exchange_id, symbol=symbol)


@router.get("/infra/fees/transaction-cost")
async def fee_transaction_cost_route(
    exchange_id: str = Query(..., min_length=1),
    symbol: str = Query("BTC/USDT"),
    notional_usd: float = Query(1000.0, ge=0),
    side: str = Query("buy", pattern="^(buy|sell)$"),
    use_maker: bool = Query(False),
    include_withdrawal: bool = Query(False),
    include_deposit: bool = Query(False),
):
    """Full transaction cost breakdown — fees + spread (#130)."""
    from bd_platform.fee_database_service import calculate_transaction_cost

    return await calculate_transaction_cost(
        exchange_id,
        symbol,
        notional_usd,
        side=side,
        use_maker=use_maker,
        include_withdrawal=include_withdrawal,
        include_deposit=include_deposit,
    )


# ── Feature #136 — Price spread calculator (internal function) ─────────────────


@router.get("/infra/spread/status")
async def spread_calculator_status_route():
    """Price spread calculator health (#136 internal function)."""
    from bd_platform.price_spread_calculator import spread_calculator_status

    return spread_calculator_status()


@router.get("/infra/spread/calculate")
async def spread_calculator_route(
    buy_price: float = Query(..., gt=0),
    sell_price: float = Query(..., gt=0),
    notional_usd: float = Query(1000.0, ge=1),
    buy_exchange: str = Query("binance"),
    sell_exchange: str = Query("okx"),
    symbol: str = Query("BTC/USDT"),
    include_transfer_fees: bool = Query(True),
):
    """#136 — gross → net spread with fees (#130 + #113). Internal ops only."""
    from bd_platform.price_spread_calculator import calculate_price_spread

    return calculate_price_spread(
        buy_price=buy_price,
        sell_price=sell_price,
        notional_usd=notional_usd,
        buy_exchange=buy_exchange,
        sell_exchange=sell_exchange,
        symbol=symbol,
        include_transfer_fees=include_transfer_fees,
    )


# ── Feature #147 — Data Validation Layer (with #133) ─────────────────────────


@router.get("/infra/validation/status")
async def data_validation_status_route():
    """Data Validation Layer health (#147 internal protection)."""
    from bd_platform.data_validation_layer import validation_layer_status

    return validation_layer_status()


# ── Feature #149 — Confidence Engine (Phase 1 rule-based) ────────────────────


@router.get("/confidence/score")
async def confidence_score_route(asset: str = Query("BTC")):
    """Confidence Engine Phase 1 — rule-based score 0-100 (#149)."""
    from bd_platform.confidence_engine import score_asset_confidence

    return await score_asset_confidence(asset)


@router.get("/confidence/status")
async def confidence_engine_status_route():
    """Confidence Engine roadmap and phase status (#149)."""
    from bd_platform.confidence_engine import confidence_engine_status

    return confidence_engine_status()


# ── Feature #151 — Market Health Dashboard ───────────────────────────────────


@router.get("/market-health/dashboard")
async def market_health_dashboard_route(asset: str = Query("BTC")):
    """Market Health Dashboard (#151) — 4 pillars + #109 risk hook."""
    from bd_platform.market_health_engine import build_market_health_dashboard

    return await build_market_health_dashboard(asset)


@router.get("/market-health/status")
async def market_health_status_route():
    """Market Health Engine status (#151)."""
    from bd_platform.market_health_engine import market_health_status

    return market_health_status()


# ── Feature #153 — Execution Quality Score ─────────────────────────────────────


@router.get("/infra/execution-quality/score")
async def execution_quality_score_route(
    asset: str = Query("ETH"),
    amount_usd: float = Query(5000.0, ge=100.0, le=10_000_000.0),
    side: str = Query("buy", pattern="^(buy|sell)$"),
    chain: str = Query("ethereum"),
):
    """Execution Quality Score (#153) — per-venue slippage comparison."""
    from bd_platform.execution_quality_score import compute_execution_quality_score

    return await compute_execution_quality_score(
        asset,
        amount_usd=amount_usd,
        side=side,  # type: ignore[arg-type]
        chain=chain,
    )


@router.get("/infra/execution-quality/status")
async def execution_quality_status_route():
    """Execution Quality Score status (#153)."""
    from bd_platform.execution_quality_score import execution_quality_status

    return execution_quality_status()


# ── Feature #165 — API Security Encryption ───────────────────────────────────


@router.get("/security/keys/status")
async def api_security_keys_status_route(
    user: dict = Depends(require_authenticated),
):
    """API Security Encryption status (#165) — key metadata without secrets."""
    from bd_platform.api_security_encryption import list_user_key_status, security_encryption_status

    return {
        "platform": security_encryption_status(),
        "user_keys": list_user_key_status(user.get("id") or user.get("email") or "0"),
    }


@router.post("/security/keys/store", responses=COMMON_ERROR_RESPONSES)
async def api_security_keys_store_route(
    body: dict[str, Any] = Body(...),
    user: dict = Depends(require_authenticated),
):
    """Store encrypted API secret (#165) — no plaintext persistence/logging."""
    from bd_platform.api_security_encryption import store_user_api_secret

    label = str(body.get("label") or "default")
    secret = str(body.get("secret") or "")
    scopes = body.get("scopes") or ["read"]
    exchange = str(body.get("exchange") or "generic")
    return store_user_api_secret(
        user_id=user.get("id") or user.get("email") or "0",
        label=label,
        plaintext=secret,
        scopes=scopes if isinstance(scopes, list) else ["read"],
        exchange=exchange,
    )


@router.post("/security/keys/revoke", responses=COMMON_ERROR_RESPONSES)
async def api_security_keys_revoke_route(
    body: dict[str, Any] = Body(...),
    user: dict = Depends(require_authenticated),
):
    """Immediate key revocation (#165)."""
    from bd_platform.api_security_encryption import revoke_user_api_secret

    key_id = str(body.get("key_id") or "")
    if not key_id:
        raise HTTPException(status_code=400, detail="key_id required")
    return revoke_user_api_secret(
        user_id=user.get("id") or user.get("email") or "0",
        key_id=key_id,
    )


@router.post("/security/keys/rotate", responses=COMMON_ERROR_RESPONSES)
async def api_security_keys_rotate_route(
    body: dict[str, Any] = Body(...),
    user: dict = Depends(require_authenticated),
):
    """Key rotation drill (#165)."""
    from bd_platform.api_security_encryption import rotate_user_api_secret

    key_id = str(body.get("key_id") or "")
    new_secret = str(body.get("new_secret") or "")
    if not key_id or not new_secret:
        raise HTTPException(status_code=400, detail="key_id and new_secret required")
    return rotate_user_api_secret(
        user_id=user.get("id") or user.get("email") or "0",
        key_id=key_id,
        new_plaintext=new_secret,
    )


@router.get("/security/encryption/status")
async def api_security_encryption_status_route(_admin: dict = Depends(require_admin)):
    """Platform-wide API security encryption posture (#165)."""
    from bd_platform.api_security_encryption import security_encryption_status

    return security_encryption_status()


# ── Feature #167 — CLI Access (Institution tier) ─────────────────────────────


@router.get("/cli/status")
async def cli_status_route(user: dict = Depends(require_feature("cli_access"))):
    """CLI status — Institution tier REST wrapper health (#167)."""
    import os

    from blackdark.cli.main import __version__

    return {
        "ok": True,
        "feature_id": 167,
        "cli_version": __version__,
        "api_url": os.getenv("BLACKDARK_API_URL", "http://127.0.0.1:8000"),
        "tier": user.get("tier"),
        "cli_api_parity": True,
        "commands": [
            "price",
            "alert list",
            "portfolio check",
            "market-health",
            "confidence",
            "execution-quality",
            "macro",
            "spread",
            "transfer",
            "entity",
            "tx",
            "dd",
            "status",
        ],
    }


@router.get("/cli/portfolio-check")
async def cli_portfolio_check_route(
    asset: str = Query("BTC"),
    user: dict = Depends(require_feature("cli_access")),
):
    """Portfolio risk check for CLI — uses market health + confidence (#167)."""
    from bd_platform.confidence_engine import score_asset_confidence
    from bd_platform.market_health_engine import build_market_health_dashboard

    sym = asset.upper().replace("/USDT", "")
    health, confidence = await asyncio.gather(
        build_market_health_dashboard(sym),
        score_asset_confidence(sym),
    )
    risk_hook = health.get("portfolio_risk_109") or {}
    headline = (
        f"Portfolio check — {sym}: market health {health.get('overall_status')} "
        f"({health.get('overall_score')}), confidence {confidence.get('confidence_score')}. "
        f"Risk action: {risk_hook.get('recommended_action', 'review')}."
    )
    return {
        "ok": True,
        "feature_id": 167,
        "asset": sym,
        "headline": headline,
        "market_health": {
            "status": health.get("overall_status"),
            "score": health.get("overall_score"),
            "reason": health.get("classification_reason"),
        },
        "confidence": confidence,
        "portfolio_risk_109": risk_hook,
        "tier": user.get("tier"),
    }


# ── Feature #173 — Due Diligence Report Engine (BLACKDARK Research) ───────────


@router.get("/research/dd-report")
async def due_diligence_report_route(
    asset: str = Query("BTC"),
    mode: str = Query("one_page", pattern="^(one_page|full)$"),
    _user: dict = Depends(require_feature("due_diligence_reports")),
):
    """BLACKDARK Research — auto-generated DD report (#173)."""
    from bd_platform.due_diligence_report_engine import build_due_diligence_report

    report = await build_due_diligence_report(asset, mode=mode)  # type: ignore[arg-type]
    return {"ok": True, "report": report}


@router.get("/research/dd-report/status")
async def due_diligence_report_status_route():
    """DD Report Engine status (#173)."""
    from bd_platform.due_diligence_report_engine import due_diligence_report_status

    return due_diligence_report_status()


# ── Feature #177 — Chart / Idea Sharing (Growth Engine) ──────────────────────


@router.post("/share/charts", responses=COMMON_ERROR_RESPONSES)
async def create_chart_share_route(
    body: dict[str, Any] = Body(...),
    user: dict = Depends(require_authenticated),
):
    """Create chart/idea share draft (#177)."""
    from bd_platform.chart_sharing_service import create_chart_share

    return create_chart_share(
        owner_id=str(user.get("id") or user.get("email") or "0"),
        title=str(body.get("title") or "Untitled"),
        chart_type=str(body.get("chart_type") or "idea"),
        chart_data=body.get("chart_data") if isinstance(body.get("chart_data"), dict) else {},
        notes=str(body.get("notes") or ""),
        privacy=str(body.get("privacy") or "private"),  # type: ignore[arg-type]
    )


@router.post("/share/charts/{share_id}/publish", responses=COMMON_ERROR_RESPONSES)
async def publish_chart_share_route(
    share_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    user: dict = Depends(require_authenticated),
):
    """Publish immutable snapshot with privacy controls (#177)."""
    from bd_platform.chart_sharing_service import publish_chart_share

    return publish_chart_share(
        share_id=share_id,
        owner_id=str(user.get("id") or user.get("email") or "0"),
        privacy=str(body.get("privacy") or "unlisted"),  # type: ignore[arg-type]
    )


@router.put("/share/charts/{share_id}", responses=COMMON_ERROR_RESPONSES)
async def update_chart_share_route(
    share_id: str,
    body: dict[str, Any] = Body(...),
    user: dict = Depends(require_authenticated),
):
    """Update draft — published immutable snapshot unchanged (#177)."""
    from bd_platform.chart_sharing_service import update_chart_share

    return update_chart_share(
        share_id=share_id,
        owner_id=str(user.get("id") or user.get("email") or "0"),
        title=body.get("title"),
        chart_data=body.get("chart_data") if isinstance(body.get("chart_data"), dict) else None,
        notes=body.get("notes"),
        privacy=body.get("privacy"),  # type: ignore[arg-type]
    )


@router.get("/share/charts")
async def list_chart_shares_route(user: dict = Depends(require_authenticated)):
    """List user's chart shares (#177)."""
    from bd_platform.chart_sharing_service import list_user_chart_shares

    return list_user_chart_shares(str(user.get("id") or user.get("email") or "0"))


@router.get("/share/chart/{slug}")
async def public_chart_view_route(slug: str):
    """Public/unlisted immutable chart snapshot (#177)."""
    from bd_platform.chart_sharing_service import get_public_chart_view

    result = get_public_chart_view(slug)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/share/status")
async def chart_sharing_status_route():
    """Chart sharing engine status (#177)."""
    from bd_platform.chart_sharing_service import chart_sharing_status

    return chart_sharing_status()


# ── Features #141 + #104 — Macro Context Engine ──────────────────────────────


@router.get("/macro/context")
async def macro_context_route(asset: str = Query("BTC")):
    """Macro Context Engine (#141 + #104) — relationship-based macro context."""
    from bd_platform.macro_context_engine import build_macro_relationships

    return await build_macro_relationships(asset)


@router.get("/macro/context/status")
async def macro_context_status_route():
    """Macro Context Engine health (#141 + #104)."""
    from bd_platform.macro_context_engine import macro_context_engine_status

    return macro_context_engine_status()


# ── Risk Signals — #123 Withdrawal Closure + #110 Exchange Health ────────────


@router.get("/risk/withdrawal-closures")
async def withdrawal_closures_route(limit: int = Query(50, ge=1, le=100)):
    """Per-asset withdrawal closure alerts (#123) — integrated with #109/#134."""
    from bd_platform.withdrawal_closure_alert import scan_withdrawal_closures

    return scan_withdrawal_closures(limit=limit)


@router.post("/risk/withdrawal-closures/record", responses=COMMON_ERROR_RESPONSES)
async def withdrawal_closure_record_route(
    body: dict[str, Any] = Body(...),
    _admin: dict = Depends(require_admin),
):
    """Record a withdrawal closure event (admin/ingestion hook)."""
    from bd_platform.withdrawal_closure_alert import record_withdrawal_closure

    return record_withdrawal_closure(
        exchange_id=str(body.get("exchange_id") or ""),
        asset=str(body.get("asset") or ""),
        withdrawal_score=float(body.get("withdrawal_score") or 20),
        health_score=float(body.get("health_score") or 45),
        badge=str(body.get("badge") or "caution"),
        duration_minutes=float(body["duration_minutes"]) if body.get("duration_minutes") is not None else None,
    )


@router.get("/exchange-health/status")
async def exchange_health_status_route(
    exchange_id: str | None = Query(None),
    min_alert_level: str = Query("low"),
):
    """Exchange Health Monitor (#110) + platform status (#134)."""
    from bd_platform.exchange_health_monitor import exchange_health_status

    return exchange_health_status(exchange_id=exchange_id, min_alert_level=min_alert_level)


@router.get("/exchange-trust/dashboard")
async def exchange_trust_dashboard_route(
    exchange_id: str | None = Query(None),
):
    """Unified Trust Layer — Exchange Quality Score (#132) + Platform Status (#134)."""
    from bd_platform.exchange_health_monitor import exchange_trust_dashboard

    return exchange_trust_dashboard(exchange_id=exchange_id)


@router.get("/exchange-trust/quality")
async def exchange_quality_score_route(
    exchange_id: str | None = Query(None),
):
    """Exchange Quality Score (#132) — transparent methodology, A+ to D badges."""
    from bd_platform.exchange_quality_score import score_all_exchanges, score_exchange

    if exchange_id:
        return score_exchange(exchange_id)
    return score_all_exchanges()


@router.get("/market-radar/order-flow")
async def order_flow_analytics_route(
    asset: str = Query("BTC"),
    limit: int = Query(10, ge=1, le=30),
):
    """Order Flow Analytics (#135) — buy/sell walls in plain language."""
    from bd_platform.order_flow_analytics import scan_order_flow

    return await scan_order_flow(asset, limit=limit)


# ── Feature #125 — Single-Sentence Financial Oracle ─────────────────────────


@router.get("/oracle/single-sentence")
async def single_sentence_oracle_route(
    asset: str = Query("BTC", min_length=1, max_length=20),
    user: Annotated[dict | None, Depends(optional_user_from_request)] = None,
):
    """Single-Sentence Financial Oracle (#125) — Bullish/Neutral/Bearish + one reason."""
    from bd_platform.single_sentence_financial_oracle import query_single_sentence_oracle

    return await query_single_sentence_oracle(asset, user=user)


@router.get("/oracle/single-sentence/status")
async def single_sentence_oracle_status_route():
    from bd_platform.single_sentence_financial_oracle import oracle_feature_status

    return oracle_feature_status()


# ── Feature #126 — Monetization Tiers Core ───────────────────────────────────


@router.get("/billing/monetization-tiers")
async def monetization_tiers_route(
    variant: str | None = Query(None, pattern="^(A|B)$"),
):
    """3-tier commercial catalog (#126) with A/B pricing."""
    from bd_platform.monetization_tiers_core import monetization_catalog

    return monetization_catalog(variant=variant)  # type: ignore[arg-type]


@router.get("/billing/monetization-status")
async def monetization_status_route():
    from bd_platform.monetization_tiers_core import monetization_status

    return monetization_status()


@router.get("/billing/entitlements")
async def monetization_entitlements_route(tier: str = Query("free")):
    from bd_platform.monetization_tiers_core import entitlements_for_commercial_tier

    return entitlements_for_commercial_tier(tier)
