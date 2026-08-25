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


@router.get("/intelligence-ledger/correlation/status")
async def correlation_lead_lag_status_route():
    """#271 Correlation & Lead-Lag Module — Analyst Suite, no causation language."""
    from bd_platform.correlation_lead_lag import correlation_lead_lag_status

    return correlation_lead_lag_status()


@router.get("/intelligence-ledger/correlation")
async def correlation_lead_lag_analysis_route(
    metric_a: str = Query("price"),
    metric_b: str = Query("active_addresses"),
    asset: str = Query("BTC"),
    window_days: int = Query(30, description="7 | 30 | 90 | 365"),
):
    """#271 correlation + lead-lag panel — daily batch, no causation language."""
    from bd_platform.correlation_lead_lag import build_correlation_analysis

    key_a = f"{asset.upper()}:{metric_b}"
    result = build_correlation_analysis(key_a, metric_b, window_days=window_days)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/intelligence-ledger/mindshare/status")
async def mindshare_intelligence_status_route():
    """#272 Social Signal & Mindshare — provider + filtering layer."""
    from bd_platform.mindshare_intelligence import mindshare_intelligence_status

    return mindshare_intelligence_status()


@router.get("/intelligence-ledger/mindshare")
async def mindshare_intelligence_panel_route(asset: str = Query("BTC")):
    """#272 mindshare panel — no raw social pipeline."""
    from bd_platform.mindshare_intelligence import build_mindshare_panel

    result = build_mindshare_panel(asset)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


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

