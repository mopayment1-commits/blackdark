import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import aiohttp
import stripe
from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    Body,
    Cookie,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.gzip import GZipMiddleware

import encoding_bootstrap  # noqa: F401 — UTF-8 for Arabic (console + JSON)

_ROOT = Path(__file__).resolve().parent
load_dotenv(_ROOT / ".env")
# Launch secrets file (gitignored) — used for local go-live verification
load_dotenv(_ROOT / ".env.launch.local", override=False)

import config
from security_auth import (
    is_admin_user,
    require_admin,
    require_admin_dev,
    require_pro_or_above,
    require_whale,
)
from security_models import (
    ExecutionAutoBody,
    ExecutionOrderBody,
    RiskFreezeBody,
)

logger = logging.getLogger("BLACKDARK.Dashboard")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

STRIPE_TIERS = {
    "pro": {"amount": 2900, "name": "Decision Pro"},
    "whale": {"amount": 19900, "name": "Whale Desk"},
}  # legacy ref — billing_service.STRIPE_TIERS is canonical


def _sector_for_asset(asset: str) -> str:
    return config.SECTOR_MAP.get(asset.upper(), "Other")


def _btc_beta_estimate(asset: str) -> float:
    betas = {
        "BTC": 1.0,
        "WBTC": 1.0,
        "ETH": 0.85,
        "SOL": 0.78,
        "BNB": 0.72,
        "XRP": 0.65,
    }
    return betas.get(asset.upper(), 0.6)


def _score_prediction_accuracy(
    verdict: str, price_at: float, price_after: float
) -> tuple[str, float]:
    """Delegate to shared labeling scorer so public/internal verdicts stay consistent."""
    from ml.labeling_pipeline import score_verdict_accuracy

    outcome, accuracy, _direction = score_verdict_accuracy(verdict, price_at, price_after)
    return outcome, accuracy


async def _resolve_mature_oracle_predictions() -> int:
    from datetime import timedelta

    from database import fetch_unresolved_oracle_predictions, resolve_oracle_prediction

    unresolved = await fetch_unresolved_oracle_predictions(limit=200)
    resolved_count = 0
    now = datetime.now(UTC)
    for pred in unresolved:
        raw_ts = str(pred.get("timestamp") or "")
        try:
            ts = datetime.fromisoformat(raw_ts)
        except ValueError:
            continue
        if now - ts < timedelta(hours=24):
            continue
        asset = str(pred.get("asset") or "")
        _, pair = _normalize_oracle_symbol(asset)
        ticker = await _fetch_binance_ticker(pair)
        if ticker is None:
            continue
        price_after = float(ticker["price"])
        outcome, accuracy = _score_prediction_accuracy(
            str(pred.get("verdict") or ""),
            float(pred.get("price_at_prediction") or 0),
            price_after,
        )
        await resolve_oracle_prediction(int(pred["id"]), price_after, outcome, accuracy)
        resolved_count += 1
    return resolved_count


async def _log_oracle_prediction(payload: dict) -> int | None:
    """Persist Oracle decision and return the audit prediction_id (D1)."""
    from ml.labeling_pipeline import log_oracle_signal

    try:
        return await log_oracle_signal(
            asset=str(payload.get("symbol") or payload.get("asset") or ""),
            price=float(payload.get("price") or 0),
            verdict=str(payload.get("verdict") or "WAIT"),
            opportunity_score=float(payload.get("opportunity_score") or 0),
            confidence=float(payload.get("confidence") or payload.get("confidence_percent") or 0),
            kind=str(payload.get("kind") or "oracle_api"),
            market_regime=str(payload.get("market_regime") or "neutral"),
        )
    except Exception:
        logger.exception("Oracle flywheel logging failed")
        return None


async def _record_behavior(
    event_type: str,
    *,
    user: dict | None = None,
    asset: str | None = None,
    payload: dict | None = None,
) -> None:
    from behavior_data_service import record_behavior_event

    email = (user or {}).get("email")
    tier = (user or {}).get("tier")
    session_id = (user or {}).get("token") if not email else None
    await record_behavior_event(
        event_type,
        user_email=email,
        tier=tier,
        asset=asset,
        session_id=session_id,
        payload=payload,
    )
    try:
        from observability import increment_metric

        increment_metric("behavior_events_total")
    except Exception:
        pass


async def _analyze_portfolio_holdings(assets: list) -> dict:
    holdings: list[dict] = []
    total_value = 0.0
    weighted_beta = 0.0

    for item in assets:
        symbol = str(item.get("symbol") or "").upper().strip()
        amount = float(item.get("amount") or 0)
        if not symbol or amount <= 0:
            continue
        _, pair = _normalize_oracle_symbol(symbol)
        ticker = await _fetch_binance_ticker(pair)
        price = float(ticker["price"]) if ticker else float(item.get("price") or 0)
        value = amount * price
        total_value += value
        beta = _btc_beta_estimate(symbol)
        holdings.append(
            {
                "symbol": symbol,
                "amount": amount,
                "price": price,
                "value_usd": round(value, 2),
                "sector": _sector_for_asset(symbol),
                "btc_beta": beta,
            }
        )

    if total_value > 0:
        weighted_beta = sum((h["value_usd"] / total_value) * h["btc_beta"] for h in holdings)

    btc_drop_pct = 15.0
    estimated_loss = total_value * weighted_beta * (btc_drop_pct / 100.0)
    risk_score = min(10, max(1, round(weighted_beta * 10)))
    if risk_score >= 8:
        risk_level = "HIGH"
    elif risk_score >= 5:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    recommendations: list[str] = []
    if weighted_beta > 0.75:
        recommendations.append("High BTC correlation — diversify into uncorrelated assets")
    if len(holdings) < 3:
        recommendations.append("Portfolio is concentrated — add 2+ more assets")
    if not recommendations:
        recommendations.append("Balanced portfolio structure for current holdings")

    plain = (
        f"In plain language: your book is {risk_level.lower()} risk "
        f"(score {risk_score}/10). Weighted BTC sensitivity is about "
        f"{weighted_beta:.0%}. If BTC falls {btc_drop_pct:.0f}%, expect roughly "
        f"${estimated_loss:,.0f} drawdown on current holdings. "
        f"{recommendations[0]}"
    )
    try:
        from decision_certificate import compliance_footer_block

        compliance = compliance_footer_block(
            surface="portfolio_ai",
            trust_basis="holdings beta model + public_accuracy_ledger",
            data_sources="live spot marks · weighted BTC beta heuristic",
        )
    except Exception:
        compliance = {
            "disclaimer": "Not financial advice. Verify claims on the Public Accuracy Ledger.",
        }

    result = {
        "holdings": holdings,
        "total_value": round(total_value, 2),
        "total_value_formatted": f"${total_value:,.2f}",
        "btc_correlation": f"{weighted_beta:.1%}",
        "btc_beta_weighted": round(weighted_beta, 3),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "scenario_btc_drop_pct": btc_drop_pct,
        "estimated_loss_usd": round(estimated_loss, 2),
        "estimated_loss_formatted": f"${estimated_loss:,.2f}",
        "scenario_note": (
            f"If BTC drops {btc_drop_pct:.0f}%, estimated portfolio loss "
            f"${estimated_loss:,.0f} based on weighted beta {weighted_beta:.2f}"
        ),
        "plain_language": plain,
        "recommendations": recommendations,
        "compliance_footer": compliance,
        "hero": "portfolio_ai",
    }
    try:
        from heroes_quality import build_portfolio_clarity

        clarity = build_portfolio_clarity(result)
        result["one_sentence"] = clarity["one_sentence"]
        result["clarity"] = clarity
    except Exception:
        result["one_sentence"] = (
            f"Your portfolio looks {risk_level.lower()} risk ({risk_score}/10)."
        )
    return result

# Set True only after init_db succeeds. Used by /health/ready.
_BOOT_DB_READY = False
_BOOT_DB_OK = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Yield immediately so Railway /health/live passes, then boot in background."""
    global _BOOT_DB_READY, _BOOT_DB_OK

    async def _background_boot() -> None:
        global _BOOT_DB_READY, _BOOT_DB_OK
        try:
            from database import init_db

            await init_db()
            _BOOT_DB_OK = True
            _BOOT_DB_READY = True
        except Exception:
            logger.exception("init_db failed — API stays up for live probes; ready stays closed")
            _BOOT_DB_OK = False
            # Local/dev: allow ready so smoke tests don't hang forever
            local_dev = os.getenv("LOCAL_DEV", "false").lower() in {"1", "true", "yes"}
            env = (os.getenv("ENV") or "").strip().lower()
            _BOOT_DB_READY = local_dev and env not in {"production", "prod"}

        try:
            from observability import init_sentry

            init_sentry()
        except Exception:
            logger.exception("Sentry init failed")

        try:
            from production_guard import enforce_production_guard, is_production, log_production_guard

            if is_production():
                # Fail closed in production — do not swallow
                enforce_production_guard()
            else:
                log_production_guard()
        except Exception:
            logger.exception("Production guard check failed")
            from production_guard import is_production

            if is_production():
                raise

        try:
            from risk_manager import load_persistent_freeze

            await load_persistent_freeze()
        except Exception:
            logger.exception("Risk freeze load failed")

        _ms_mode = getattr(config, "SERVICE_MODE", "all").strip().lower()
        if _ms_mode == "web":
            try:
                from microservices.lifecycle import ServiceContext, startup

                _ms_ctx = ServiceContext()
                await startup("web", _ms_ctx)
                app.state.ms_ctx = _ms_ctx
            except Exception:
                logger.exception("Web microservice startup failed")
            try:
                from uptime_probe_loop import start_uptime_probe_loop

                app.state.uptime_probe_task = await start_uptime_probe_loop()
            except Exception:
                logger.exception("Uptime self-probe failed in web mode")
            return

        try:
            from startup_orchestrator import RuntimeState, run_background_startup

            runtime = RuntimeState()
            app.state.runtime = runtime
            await run_background_startup(runtime)
        except Exception:
            logger.exception("Background startup failed")

    boot_task = asyncio.create_task(_background_boot(), name="blackdark-boot")
    logger.info("BLACKDARK API live — DB/services loading in background.")
    yield

    boot_task.cancel()
    await asyncio.gather(boot_task, return_exceptions=True)

    _ms_ctx = getattr(app.state, "ms_ctx", None)
    if _ms_ctx is not None:
        try:
            from microservices.lifecycle import shutdown

            await shutdown(_ms_ctx)
        except Exception:
            logger.exception("Web microservice shutdown failed")
        return

    runtime = getattr(app.state, "runtime", None)
    if runtime is not None:
        try:
            from startup_orchestrator import shutdown_runtime

            await shutdown_runtime(runtime)
        except Exception:
            logger.exception("Background shutdown failed")


# Public /docs is our evidence/read developer page (not full Swagger dump).
# Full schema remains at /api/docs/openapi.json; filtered at /api/docs/public-openapi.json.
app = FastAPI(
    title="BLACKDARK",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
)

# Compress HTML/CSS/JS/JSON for Lighthouse text-compression + faster FCP/LCP.
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)


def _public_base_url(request: Request | None = None) -> str:
    """Absolute public origin for robots/sitemap (never trust arbitrary Host alone)."""
    from urllib.parse import urlparse

    configured = (os.getenv("APP_BASE_URL") or "").strip().rstrip("/")
    if configured:
        return configured
    if request is None:
        return "https://blackdark.io"
    parsed = urlparse(str(request.base_url))
    host = (parsed.hostname or "localhost").lower()
    if host not in {"localhost", "127.0.0.1", "::1"} and not host.endswith(".localhost"):
        host = "localhost"
    scheme = "https" if parsed.scheme == "https" else "http"
    netloc = host if not parsed.port else f"{host}:{parsed.port}"
    return f"{scheme}://{netloc}"


# CORS allowlist (never '*' with credentials) — added before route middleware stack.
try:
    from security_middleware import apply_cors

    apply_cors(app)
except Exception:
    pass

try:
    from security_middleware import SecurityHeadersMiddleware

    app.add_middleware(SecurityHeadersMiddleware)
except Exception:
    pass


@app.middleware("http")
async def utf8_response_headers(request: Request, call_next):
    """Ensure JSON/HTML responses declare UTF-8 (Arabic text in browser)."""
    response = await call_next(request)
    ct = (response.headers.get("content-type") or "").lower()
    if "charset=" not in ct:
        if "application/json" in ct:
            response.headers["content-type"] = "application/json; charset=utf-8"
        elif "text/html" in ct:
            response.headers["content-type"] = "text/html; charset=utf-8"
    path = request.url.path or ""
    if (
        path.startswith("/static/")
        and response.status_code == 200
        and path.endswith((".woff2", ".css", ".js", ".png", ".webp", ".svg"))
    ):
        response.headers.setdefault(
            "Cache-Control", "public, max-age=604800, stale-while-revalidate=86400"
        )
    return response


@app.middleware("http")
async def viral_capacity_middleware(request: Request, call_next):
    """Load shedding + shared rate limits under viral / production traffic."""
    from viral_capacity import viral_protection_middleware

    return await viral_protection_middleware(request, call_next)


@app.middleware("http")
async def observability_metrics_middleware(request: Request, call_next):
    from observability import increment_metric

    increment_metric("http_requests_total")
    try:
        return await call_next(request)
    except Exception:
        increment_metric("errors_total")
        raise


try:
    from platform_api import router as platform_router

    app.include_router(platform_router)
except ImportError:
    pass

try:
    from api.routers.observability import router as observability_router

    app.include_router(observability_router)
except ImportError:
    pass

try:
    from api.routers.auth import router as auth_router

    app.include_router(auth_router)
except ImportError:
    pass

try:
    from api.routers.billing import router as billing_router

    app.include_router(billing_router)
except ImportError:
    pass

try:
    from api.routers.arbitrage import router as arbitrage_router

    app.include_router(arbitrage_router)
except ImportError:
    pass

try:
    from api.routers.oracle import router as oracle_router

    app.include_router(oracle_router)
except ImportError:
    pass

try:
    from api.routers.market import router as market_router

    app.include_router(market_router)
except ImportError:
    pass

try:
    from api.routers.user import router as user_router

    app.include_router(user_router)
except ImportError:
    pass

try:
    from api.routers.privacy import router as privacy_router

    app.include_router(privacy_router)
except ImportError:
    pass

try:
    from api.routers.gtm import router as gtm_router

    app.include_router(gtm_router)
except ImportError:
    pass

try:
    from api.routers.heroes import router as heroes_router

    app.include_router(heroes_router)
except Exception:
    logger.exception("Heroes router unavailable")

try:
    from api.routers.telegram import router as telegram_router

    app.include_router(telegram_router)
except ImportError:
    pass

try:
    from graphql_schema import create_graphql_router

    app.include_router(create_graphql_router(), prefix="")
except ImportError:
    pass

STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


async def optional_user(
    authorization: str | None = Header(None, alias="Authorization"),
    bd_token: str | None = Cookie(None, alias="bd_token"),
) -> dict | None:
    from auth_service import get_user_from_token

    token: str | None = None
    if authorization:
        token = authorization[7:] if authorization.startswith("Bearer ") else authorization
    elif bd_token:
        token = bd_token.strip()
    if not token:
        return None
    return await get_user_from_token(token.strip())


def require_feature(feature: str):
    async def _dependency(user: dict | None = Depends(optional_user)) -> dict | None:
        from auth_service import feature_allowed

        if not feature_allowed(user, feature):
            tier = (user or {}).get("tier") or "free"
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "upgrade_required",
                    "feature": feature,
                    "current_tier": tier,
                    "message": f"This feature requires an upgrade. Current plan: {tier}.",
                    "upgrade_url": "/create-checkout-session?tier=pro",
                },
            )
        return user

    return _dependency



# --- market / oracle helpers: market_context.py (shared by chat, voice, SSE) ---
from market_context import (
    build_full_oracle_response as _build_full_oracle_response,
    compute_rsi as _compute_rsi,
    ema_position_label as _ema_position_label,
    fetch_binance_klines as _fetch_binance_klines,
    fetch_binance_market_overview as _fetch_binance_market_overview,
    fetch_binance_ticker as _fetch_binance_ticker,
    fetch_cvvd_whale_alert as _fetch_cvvd_whale_alert,
    fetch_cvvd_whale_context as _fetch_cvvd_whale_context,
    fetch_live_whale_signal as _fetch_live_whale_signal,
    is_stablecoin as _is_stablecoin,
    liquidity_label as _liquidity_label,
    macd_trend_label as _macd_trend_label,
    normalize_oracle_symbol as _normalize_oracle_symbol,
    oracle_action as _oracle_action,
    oracle_confidence as _oracle_confidence,
    oracle_sentiment as _oracle_sentiment,
    oracle_verdict as _oracle_verdict,
    parse_alert_metadata as _parse_alert_metadata,
    rsi_signal_label as _rsi_signal_label,
    trend_direction as _trend_direction,
    whale_alerts_for_asset as _whale_alerts_for_asset,
)


def _compound_to_score(compound: float) -> int:
    return int(max(0, min(100, round(50 + compound * 50))))


def _compound_label(compound: float) -> str:
    if compound >= 0.35:
        return "Bullish"
    if compound <= -0.35:
        return "Bearish"
    return "Neutral"


async def _build_opportunity_explanation(
    asset: str,
    price: float,
    change: float,
    quote_volume: float,
    score: int,
    verdict: str,
    pair: str | None = None,
) -> dict:
    """Multi-factor explanation from live technical, CVVD whale, sentiment, and on-chain feeds."""
    from onchain_tracker import build_onchain_context_safe, get_onchain_status_for_asset
    from oracle_data_hub import build_hub_context_safe, hub_score_adjustment
    from sentiment_engine import build_sentiment_context_safe

    if pair:
        resolved_pair = pair
    else:
        _, resolved_pair = _normalize_oracle_symbol(asset)

    closes = await _fetch_binance_klines(resolved_pair)
    rsi = _compute_rsi(closes)
    if rsi is None:
        rsi = round(max(18.0, min(82.0, 50.0 + change * 4.5)), 1)
        rsi_source = "estimated_from_24h_change"
    else:
        rsi_source = "binance_1h_candles"

    macd_trend = _macd_trend_label(closes) if closes else "Insufficient candle data"
    ema_position = _ema_position_label(price, closes) if closes else _ema_position_label(price, [price])

    liquidity, liquidity_score = _liquidity_label(quote_volume)
    trend = _trend_direction(change)

    whale_context = await _fetch_cvvd_whale_context(refresh=False)
    asset_alerts = _whale_alerts_for_asset(whale_context["whale_alerts"], asset)
    if asset_alerts:
        top = asset_alerts[0]
        meta = _parse_alert_metadata(top)
        pattern = str(meta.get("pattern") or "manipulation").replace("_", " ")
        whale_flow = f"CVVD {pattern} — {top.get('side') or 'mixed'!s} — ${float(top.get('notional_usd') or 0):,.0f}"
        spike = float(meta.get("volume_spike_ratio") or 0)
        volume_anomaly = (
            f"Cross-venue spike {spike:.1f}x vs baseline"
            if spike > 1.2
            else "Elevated institutional footprint"
        )
        whale_alert_text = (
            f"{pattern} detected — score {float(meta.get('manipulation_score') or 0):.0f}/100"
        )
    else:
        live_phrase = await _fetch_live_whale_signal(resolved_pair, price)
        whale_flow = live_phrase
        volume_anomaly = (
            "High 24h quote volume vs typical range"
            if quote_volume > 50_000_000
            else "Normal institutional range"
        )
        whale_alert_text = live_phrase

    sentiment_ctx = await build_sentiment_context_safe([asset])
    compound = float((sentiment_ctx.get("sentiment_compound_index") or {}).get(asset.upper(), 0.0))
    news_sentiment = _compound_to_score(compound)
    news_label = _compound_label(compound)
    social_buzz = int(max(15, min(95, round(48 + score * 0.35 + abs(compound) * 40))))

    onchain_ctx = await build_onchain_context_safe()
    onchain_status = get_onchain_status_for_asset(asset, onchain_ctx)
    if onchain_status:
        bias = str(onchain_status.get("bias") or "neutral")
        net_flow = float(onchain_status.get("net_flow_usd") or 0)
        onchain_note = f"Exchange flow {bias} (${net_flow:+,.0f} net)"
    else:
        onchain_note = "On-chain flow data unavailable for this asset"

    hub_ctx = await build_hub_context_safe(asset)
    hub_delta, hub_reasons, hub_risks = hub_score_adjustment(asset, hub_ctx)
    hub_score_adj = round(hub_delta)

    support = round(price * 0.97, -2)
    resistance = round(price * 1.03, -2)
    volatility = "Low" if abs(change) < 2 else "Medium" if abs(change) < 5 else "High"
    vol_warning = (
        "Elevated volatility — widen stops"
        if abs(change) >= 5
        else "Moderate swings expected"
        if abs(change) >= 2
        else "Low volatility environment"
    )

    # Hero #1 — Top-3 factors for <5s understanding (with real sources).
    top_factors = [
        {
            "factor": "Technical structure",
            "detail": f"RSI {rsi} ({_rsi_signal_label(rsi)}) · {macd_trend}",
            "source": rsi_source,
            "weight_hint": "high" if abs(float(rsi) - 50) > 12 else "medium",
        },
        {
            "factor": "Whale / institutional flow",
            "detail": whale_alert_text,
            "source": "CVVD whale detection",
            "weight_hint": "high" if asset_alerts else "medium",
        },
        {
            "factor": "Sentiment + on-chain",
            "detail": f"{news_label} news · {onchain_note}",
            "source": "sentiment index + exchange flows",
            "weight_hint": "medium",
        },
    ]

    return {
        "symbol": asset,
        "verdict": verdict,
        "opportunity_score": score,
        "simulated": False,
        "top_3_factors": top_factors,
        "checklist": [
            {"label": "Score", "value": score, "ok": score >= 55},
            {"label": "Liquidity", "value": liquidity, "ok": liquidity_score >= 60},
            {"label": "Whale context", "value": "present" if asset_alerts else "quiet", "ok": True},
            {"label": "Volatility", "value": volatility, "ok": abs(change) < 8},
        ],
        "data_sources": [
            "Binance Live API (price + 1h candles)",
            "CVVD Cross-Venue Whale Detection",
            "Rolling Compound Sentiment Index",
            "On-Chain Exchange Flow Tracker",
            "Oracle Data Hub (news, macro, derivatives, aggregators, free LLMs)",
        ],
        "disclaimer": "Not financial advice. Do your own research (DYOR).",
        "technical_analysis": {
            "rsi": rsi,
            "rsi_signal": _rsi_signal_label(rsi),
            "rsi_source": rsi_source,
            "macd_trend": macd_trend,
            "ema_position": ema_position,
        },
        "market_context": {
            "volume_analysis": f"24h quote volume ${quote_volume:,.0f}",
            "liquidity_score": liquidity_score,
            "liquidity_label": liquidity,
            "trend_direction": trend,
            "onchain_flow": onchain_note,
        },
        "whale_activity": {
            "flow": whale_flow,
            "volume_anomaly": volume_anomaly,
            "alert": whale_alert_text,
            "cvvd_alerts_count": len(asset_alerts),
        },
        "sentiment": {
            "news_sentiment_score": news_sentiment,
            "news_label": news_label,
            "compound_index": round(compound, 3),
            "social_buzz_score": social_buzz,
            "social_label": "High" if social_buzz >= 70 else "Moderate" if social_buzz >= 45 else "Low",
            "fear_greed_index": (hub_ctx.get("sentiment") or {}).get("fear_greed_index"),
            "fear_greed_label": (hub_ctx.get("sentiment") or {}).get("fear_greed_label"),
            "coingecko_trending": (hub_ctx.get("sentiment") or {}).get("coingecko_trending"),
        },
        "oracle_data_hub": {
            "enabled": hub_ctx.get("enabled", False),
            "score_adjustment": hub_score_adj,
            "macro_regime": (hub_ctx.get("macro") or {}).get("macro_regime_proxy"),
            "derivatives_bias": (hub_ctx.get("derivatives") or {}).get("derivatives_bias"),
            "geopolitical_headlines": (hub_ctx.get("geo_news") or {}).get("geopolitical_headline_count"),
            "top_headlines": (hub_ctx.get("geo_news") or {}).get("headlines", [])[:5],
            "market_cap_change_24h_pct": (
                (hub_ctx.get("aggregators") or {}).get("coingecko_global") or {}
            ).get("market_cap_change_24h_pct"),
            "hub_reasons": hub_reasons[:3],
            "hub_risks": hub_risks[:3],
            "free_llm_providers": hub_ctx.get("free_llm_providers"),
            "pillars": hub_ctx.get("pillars"),
        },
        "risk_factors": {
            "support": support,
            "resistance": resistance,
            "volatility": volatility,
            "volatility_warning": vol_warning,
        },
        "timestamp": datetime.now(UTC).isoformat(),
    }

# ========== LANDING PAGE (ROOT) ==========
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", _footer_ctx())


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    return templates.TemplateResponse(request, "profile.html", _footer_ctx())


@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    return templates.TemplateResponse(request, "reset_password.html", _footer_ctx())


@app.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page(request: Request, token: str = ""):
    """Browser entry — delegates to API verify then redirects to profile."""
    if not token:
        return templates.TemplateResponse(
            request,
            "utility.html",
            {
                "page": "verify_email",
                "title": "Verify email",
                "lead": "Missing verification token. Use the link from your email, or resend from Profile.",
            },
        )
    # Prefer API redirect path for cookie/session consistency.
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=f"/api/auth/verify-email?token={token}", status_code=302)


# Auth routes → api/routers/auth.py
# GTM / platform stats → api/routers/gtm.py
# Telegram → api/routers/telegram.py

@app.post("/api/promo/redeem")
async def promo_redeem(data: dict = Body(...), user: dict | None = Depends(optional_user)):
    from auth_service import redeem_promo_code

    if not user:
        raise HTTPException(status_code=401, detail="Login required to redeem promo code")
    try:
        return await redeem_promo_code(user["email"], str(data.get("code") or ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat")
async def ai_chat(
    data: dict = Body(...),
    user: dict | None = Depends(require_feature("ai_chat")),
):
    from chat_service import process_chat

    message = str(data.get("message") or data.get("text") or "").strip()
    history = data.get("history") or []
    return await process_chat(message, history=history)


@app.get("/api/journal")
async def journal_list(user: dict | None = Depends(optional_user)):
    from auth_service import feature_allowed
    from database import fetch_journal_entries

    if not user or not feature_allowed(user, "journal"):
        raise HTTPException(status_code=401, detail="Login required for Trading Journal")
    return {"entries": await fetch_journal_entries(user["email"])}


@app.post("/api/journal")
async def journal_create(data: dict = Body(...), user: dict | None = Depends(optional_user)):
    from auth_service import feature_allowed
    from database import insert_journal_entry

    if not user or not feature_allowed(user, "journal"):
        raise HTTPException(status_code=401, detail="Login required")
    asset = str(data.get("asset") or "BTC").upper()
    action = str(data.get("action") or "note").lower()
    entry_id = await insert_journal_entry(
        user["email"],
        asset,
        action,
        notes=str(data.get("notes") or ""),
        oracle_verdict=str(data.get("oracle_verdict") or ""),
        entry_price=float(data["entry_price"]) if data.get("entry_price") else None,
    )
    return {"success": True, "id": entry_id}


@app.patch("/api/journal/{entry_id}")
async def journal_update(entry_id: int, data: dict = Body(...), user: dict | None = Depends(optional_user)):
    from database import update_journal_entry

    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    ok = await update_journal_entry(
        entry_id,
        user["email"],
        exit_price=float(data["exit_price"]) if data.get("exit_price") is not None else None,
        pnl_usd=float(data["pnl_usd"]) if data.get("pnl_usd") is not None else None,
        notes=data.get("notes"),
        status=str(data.get("status") or "closed"),
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True}


@app.delete("/api/journal/{entry_id}")
async def journal_delete(entry_id: int, user: dict | None = Depends(optional_user)):
    from database import delete_journal_entry

    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    if not await delete_journal_entry(entry_id, user["email"]):
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True}


@app.get("/api/alerts/telegram/status")
async def telegram_status():
    from telegram_monitor import telegram_configured

    return {
        "configured": telegram_configured(),
        "bot_token_set": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "default_chat_set": bool(os.getenv("TELEGRAM_CHAT_ID")),
        "monitor_enabled": os.getenv("TELEGRAM_ALERTS_ENABLED", "true").lower() in {"1", "true", "yes"},
        "interval_seconds": int(os.getenv("TELEGRAM_ALERT_INTERVAL_SECONDS", "90")),
    }


@app.post("/api/alerts/telegram/test")
async def telegram_test(
    data: dict = Body(default={}),
    user: dict = Depends(require_authenticated),
):
    """Authenticated only — send test to the caller's own chat_id (or admin override)."""
    from telegram_monitor import send_test_telegram

    requested = (data.get("telegram_chat_id") or data.get("chat_id") or "").strip() or None
    profile_chat = None
    try:
        from database import fetch_user_profile

        profile = await fetch_user_profile(user["email"])
        profile_chat = (profile or {}).get("telegram_chat_id")
    except Exception:
        pass
    # Non-admins may only target their own stored chat id (or default bot chat).
    if requested and not is_admin_user(user):
        if not profile_chat or str(requested) != str(profile_chat):
            raise HTTPException(
                status_code=403,
                detail="chat_id must match your profile telegram_chat_id (or omit to use default)",
            )
    chat_id = requested or profile_chat
    return await send_test_telegram(chat_id)


def _footer_ctx() -> dict:
    from site_services import footer_manifest

    return {"footer": footer_manifest()}


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse(request, "landing.html", _footer_ctx())


@app.get("/favicon.ico")
async def favicon():
    """Browsers probe /favicon.ico — serve the PWA icon to avoid console 404 noise."""
    icon = STATIC_DIR / "icon-192.png"
    if not icon.is_file():
        raise HTTPException(status_code=404, detail="favicon missing")
    return FileResponse(icon, media_type="image/png")


@app.get("/robots.txt")
async def robots_txt(request: Request):
    from fastapi.responses import PlainTextResponse

    base = _public_base_url(request)
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin/\n"
        "Disallow: /api/auth/\n"
        f"Sitemap: {base}/sitemap.xml\n"
    )
    return PlainTextResponse(body, media_type="text/plain")


@app.get("/sitemap.xml")
async def sitemap_xml(request: Request):
    from html import escape

    from fastapi.responses import Response

    # Prefer configured public origin; never reflect arbitrary Host headers into XML.
    base = _public_base_url(request)
    paths = [
        "/",
        "/dashboard",
        "/oracle-accuracy",
        "/docs",
        "/b2b",
        "/discipline-mirror",
        "/capabilities",
        "/platform",
        "/login",
        "/faq",
        "/how-it-works",
        "/about",
        "/status",
        "/changelog",
        "/feedback",
        "/contact",
        "/legal",
        "/cookies",
        "/data-room",
        "/compliance",
    ]
    urls = "\n".join(
        f"  <url><loc>{escape(base + p, quote=True)}</loc><changefreq>daily</changefreq></url>"
        for p in paths
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>\n"
    )
    return Response(content=xml, media_type="application/xml")


# ========== DASHBOARD ==========
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", _footer_ctx())


@app.get("/discipline-mirror", response_class=HTMLResponse)
async def discipline_mirror_page(request: Request):
    """Private Discipline Mirror UI — never public ledger."""
    return templates.TemplateResponse(request, "discipline.html", _footer_ctx())


@app.get("/my/discipline-mirror")
async def discipline_mirror_alias():
    """Critical-report alias — same private mirror, no seventh product."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/discipline-mirror", status_code=307)


@app.get("/errors")
async def public_errors_alias():
    """Public admission of misses — alias into the Accuracy Ledger losing section."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/oracle-accuracy#losing", status_code=307)


@app.get("/public/accuracy-ledger")
async def public_accuracy_ledger_alias():
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/oracle-accuracy", status_code=307)


@app.get("/docs", response_class=HTMLResponse)
async def public_developer_docs_page(request: Request):
    """Limited public developer docs (evidence/read APIs) — not full execution surface."""
    from public_api_docs import public_docs_manifest

    return templates.TemplateResponse(
        request,
        "docs_public.html",
        {"title": "Developer Docs", "manifest": public_docs_manifest(), **_footer_ctx()},
    )


@app.get("/docs/public", response_class=HTMLResponse)
async def public_developer_docs_alias(request: Request):
    return await public_developer_docs_page(request)


@app.get("/api/dashboard/stream")
async def dashboard_live_stream():
    from dashboard_sse import dashboard_sse_generator

    return StreamingResponse(
        dashboard_sse_generator(interval_sec=15.0),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/trust-pulse")
async def api_trust_pulse(
    symbol: str = "BTC",
    previous_action: str | None = None,
    previous_seen_at: str | None = None,
    previous_factors: str | None = None,
    force: bool = False,
    ux_mode: str = "beginner",
    lang: str = "en",
    user: dict | None = Depends(optional_user),
):
    """First-open Trust Pulse — one live decision + Why + proof + freshness."""
    import json as _json

    from trust_pulse import build_trust_pulse

    tier = (user or {}).get("tier") or "free"
    factors_prev = None
    if previous_factors:
        try:
            parsed = _json.loads(previous_factors)
            if isinstance(parsed, list):
                factors_prev = [
                    {
                        "factor": str(f.get("factor") if isinstance(f, dict) else f)[:120],
                        "detail": str((f.get("detail") if isinstance(f, dict) else "") or "")[:200],
                        "source": str((f.get("source") if isinstance(f, dict) else "") or "")[:80],
                    }
                    for f in parsed[:5]
                ]
        except Exception:
            factors_prev = None
    try:
        return await build_trust_pulse(
            symbol,
            tier=str(tier),
            ux_mode=ux_mode,
            lang=lang,
            previous_action=previous_action,
            previous_seen_at=previous_seen_at,
            previous_factors=factors_prev,
            force_refresh=force,
            # Soft cache miss may persist once; force only refreshes identity — no spam
            persist=None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/trust-pulse/stream")
async def api_trust_pulse_stream(
    symbol: str = "BTC",
    user: dict | None = Depends(optional_user),
):
    """SSE heartbeat + decision_changed for Trust Pulse (no prediction spam)."""
    from trust_pulse import trust_pulse_sse_generator

    tier = (user or {}).get("tier") or "free"
    return StreamingResponse(
        trust_pulse_sse_generator(symbol, tier=str(tier)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/trust-pulse/manifest")
async def api_trust_pulse_manifest():
    from trust_pulse import trust_pulse_manifest

    return trust_pulse_manifest()


@app.get("/admin/launch", response_class=HTMLResponse)
async def admin_launch_page(request: Request, _admin: dict = Depends(require_admin_dev)):
    return templates.TemplateResponse(request, "admin_launch.html")


@app.get("/admin/plan", response_class=HTMLResponse)
@app.get("/plan", response_class=HTMLResponse)
async def admin_plan_page(request: Request, _admin: dict = Depends(require_admin_dev)):
    return templates.TemplateResponse(request, "admin_plan.html")


@app.get("/admin/roadmap", response_class=HTMLResponse)
async def admin_roadmap_page(request: Request, _admin: dict = Depends(require_admin_dev)):
    return templates.TemplateResponse(request, "admin_roadmap.html")


@app.get("/api/plan/audit")
async def api_plan_audit(_admin: dict = Depends(require_admin_dev)):
    from plan_audit import plan_audit

    return plan_audit()


@app.get("/api/roadmap/audit")
async def api_roadmap_audit(_admin: dict = Depends(require_admin_dev)):
    from bd_platform.roadmap_audit import run_roadmap_audit

    return run_roadmap_audit()


@app.get("/api/admin/launch-checklist")
async def admin_launch_checklist_api(_admin: dict = Depends(require_admin_dev)):
    from launch_checklist import launch_checklist

    return launch_checklist()


@app.get("/platform", response_class=HTMLResponse)
async def platform_hub_page(request: Request):
    return templates.TemplateResponse(request, "platform.html", _footer_ctx())


@app.get("/capabilities", response_class=HTMLResponse)
async def capabilities_page(request: Request):
    from trust_os import trust_os_manifest

    manifest = trust_os_manifest()
    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "capabilities",
            "title": "Capabilities — Trust OS",
            "lead": (
                "Four UX lenses — Prove → Operate → Desk → Room — over one Trust OS. "
                "Four doors: Decide · Verify · My book · Alerts. Six heroes. No ARENA. "
                "Don't trust us. Verify us. API: /api/lenses"
            ),
            "trust_os": manifest,
            **_footer_ctx(),
        },
    )


@app.get("/compliance", response_class=HTMLResponse)
async def compliance_page(request: Request):
    """Anti-Hype / Legal Shield public page — engineering posture, not a license."""
    from trust_os import trust_os_manifest

    manifest = trust_os_manifest()
    regulatory = {}
    try:
        from regulatory_compliance_guard import regulatory_compliance_status

        regulatory = regulatory_compliance_status()
    except Exception:
        regulatory = {"status": "engineering_posture_only"}
    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "compliance",
            "title": "Anti-Hype Compliance",
            "lead": (
                "Engineering posture and overclaim denylist — not SEC/MiCA licensing, "
                "not SOC 2 / ISO 27001 certification. Don't trust us. Verify us."
            ),
            "trust_os": manifest,
            "regulatory": regulatory,
            **_footer_ctx(),
        },
    )


@app.get("/data-room", response_class=HTMLResponse)
async def data_room_page(request: Request):
    """Committee-facing data room index (HTML)."""
    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "data_room",
            "title": "Data Room",
            "lead": (
                "Allocator / acquirer diligence index — Prove-it surfaces, evidence pack, "
                "and honest capacity posture. Canonical docs live under /docs/DATA_ROOM.md."
            ),
            **_footer_ctx(),
        },
    )


@app.get("/api/trust-os")
async def api_trust_os():
    """Honest acquisition framing — four value layers + overclaim denylist."""
    from trust_os import trust_os_manifest

    return trust_os_manifest()


@app.get("/api/scale/readiness")
async def api_scale_readiness():
    """Honest concurrent-scale posture for ops and diligence."""
    from scale_readiness import scale_readiness_report

    return scale_readiness_report()


@app.get("/api/viral/readiness")
async def api_viral_readiness():
    """Viral launch capacity posture — protections + HA prerequisites."""
    from viral_capacity import viral_readiness_report

    return viral_readiness_report()


@app.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    from site_services import contact_channels

    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "contact",
            "title": "Contact",
            "lead": "Reach the team for support, partnerships, and allocator diligence.",
            "contact": contact_channels(),
            **_footer_ctx(),
        },
    )


@app.get("/complaints", response_class=HTMLResponse)
async def complaints_page(request: Request):
    from site_services import contact_channels

    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "complaints",
            "title": "Complaints",
            "lead": "Escalation path for claim disputes, accuracy, and billing issues.",
            "contact": contact_channels(),
            **_footer_ctx(),
        },
    )


@app.get("/faq", response_class=HTMLResponse)
async def faq_page(request: Request):
    from site_services import FAQ_ITEMS

    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "faq",
            "title": "FAQ",
            "lead": "Straight answers on Proof Pass, Decision Pro, Whale Desk, sharing, and AI Chat.",
            "faq": FAQ_ITEMS,
            **_footer_ctx(),
        },
    )


@app.get("/how-it-works", response_class=HTMLResponse)
async def how_it_works_page(request: Request):
    from site_services import HOW_IT_WORKS_STEPS

    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "how_it_works",
            "title": "How it works",
            "lead": "Decide. Prove it. Verify on the Public Accuracy Ledger.",
            "steps": HOW_IT_WORKS_STEPS,
            **_footer_ctx(),
        },
    )


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    from site_services import about_blurb

    about = about_blurb()
    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "about",
            "title": about["title"],
            "lead": "Trust OS for crypto decision intelligence — one product, four lenses.",
            "about": about,
            **_footer_ctx(),
        },
    )


@app.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    from site_services import public_status_report

    status = public_status_report()
    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "status",
            "title": "System status",
            "lead": "Public engineering posture — no secrets, no contractual SLA unless contracted.",
            "status": status,
            **_footer_ctx(),
        },
    )


@app.get("/changelog", response_class=HTMLResponse)
async def changelog_page(request: Request):
    from site_services import CHANGELOG

    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "changelog",
            "title": "Changelog",
            "lead": "What shipped on the Trust OS trust rail.",
            "changelog": CHANGELOG,
            **_footer_ctx(),
        },
    )


@app.get("/feedback", response_class=HTMLResponse)
async def feedback_page(request: Request):
    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "feedback",
            "title": "Feedback & suggestions",
            "lead": "Tell us what to improve. Never include card numbers or passwords.",
            **_footer_ctx(),
        },
    )


@app.get("/legal", response_class=HTMLResponse)
async def legal_hub_page(request: Request):
    from site_services import legal_hub_manifest

    hub = legal_hub_manifest()
    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "legal_hub",
            "title": hub["title"],
            "lead": hub["lead"],
            "legal_pages": hub["pages"],
            **_footer_ctx(),
        },
    )


@app.get("/api/site-services")
async def api_site_services():
    from site_services import site_services_manifest

    return site_services_manifest()


@app.get("/api/status")
async def api_public_status():
    from site_services import public_status_report

    return public_status_report()


@app.get("/api/changelog")
async def api_changelog():
    from site_services import CHANGELOG

    return {"entries": CHANGELOG}


@app.get("/api/faq")
async def api_faq():
    from site_services import FAQ_ITEMS

    return {"items": FAQ_ITEMS}


@app.post("/api/feedback")
async def api_feedback(data: dict = Body(...)):
    from site_services import submit_feedback

    try:
        return submit_feedback(
            category=str(data.get("category") or "suggestion"),
            message=str(data.get("message") or ""),
            email=str(data.get("email") or ""),
            page=str(data.get("page") or ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/platform/coin/{coin_id}", response_class=HTMLResponse)
async def platform_coin_page(request: Request, coin_id: str):
    return templates.TemplateResponse(
        request, "coin.html", {"coin_id": coin_id, **_footer_ctx()}
    )


# ========== API ENDPOINTS ==========
@app.get("/oracle/{symbol}/explain")
async def oracle_explain(
    symbol: str,
    background_tasks: BackgroundTasks,
    user: dict | None = Depends(optional_user),
) -> JSONResponse:
    asset, pair = _normalize_oracle_symbol(symbol)
    market = await _fetch_binance_ticker(pair)
    if market is None:
        raise HTTPException(status_code=404, detail=f"Symbol {asset} not found.")

    price = market["price"]
    volume = market["volume"]
    quote_volume = market["quote_volume"] or (volume * price)
    change = market["change_24h"]

    from oracle_unified import compute_unified_oracle

    unified = await compute_unified_oracle(asset, price, quote_volume, change)
    score = unified["opportunity_score"]
    verdict = unified["verdict"]

    payload = await _build_opportunity_explanation(
        asset, price, change, quote_volume, score, verdict, pair=pair
    )
    payload["unified_engine"] = unified.get("engine")
    payload["market_regime"] = unified.get("market_regime")
    if user and is_admin_user(user):
        payload["modal_breakdown"] = unified.get("modal_breakdown")
    else:
        payload["weights_protected"] = True
    payload["opportunity_score"] = score
    payload["verdict"] = verdict
    from forecast_engine import enrich_oracle_payload

    forecast_stub = {
        "symbol": asset,
        "price": price,
        "confidence": _oracle_confidence(score, change, quote_volume),
        "verdict": verdict,
        "next_24h_low": price * 0.97,
        "next_24h_high": price * 1.03,
    }
    enriched = await enrich_oracle_payload(forecast_stub)
    payload["forecast"] = enriched.get("forecast")
    payload["forecast_summary"] = enriched.get("forecast_summary")

    from security_sanitize import sanitize_explanation_payload, sanitize_oracle_payload

    if user and is_admin_user(user):
        payload = sanitize_explanation_payload(payload)
    else:
        base = sanitize_oracle_payload(
            {
                "symbol": asset,
                "verdict": payload.get("verdict"),
                "opportunity_score": payload.get("opportunity_score"),
                "explanation": payload,
            }
        )
        payload = sanitize_explanation_payload(payload)
        payload["regulatory_classification"] = base.get("regulatory_classification")
        payload["disclaimer"] = base.get("disclaimer")
        payload["is_investment_advice"] = False
    background_tasks.add_task(
        _log_oracle_prediction,
        {
            "symbol": asset,
            "asset": asset,
            "price": price,
            "verdict": verdict,
            "opportunity_score": score,
            "confidence": payload.get("confidence") or _oracle_confidence(score, change, quote_volume),
            "kind": "oracle_explain",
        },
    )
    background_tasks.add_task(
        _record_behavior,
        "oracle_explain",
        user=user,
        asset=asset,
        payload={"verdict": verdict, "opportunity_score": score},
    )
    return JSONResponse(payload)


@app.get("/oracle/{symbol}/quick")
async def oracle_quick(
    symbol: str,
    background_tasks: BackgroundTasks,
    lang: str = "en",
    ux_mode: str = "beginner",
) -> JSONResponse:
    """Instant verdict + ACTION line — viral-hardened (cache + semaphore)."""
    import time

    from live_book_hub import get_best_price
    from viral_capacity import quick_cache_get, quick_cache_set, run_oracle_bounded

    t0 = time.perf_counter()
    asset, pair = _normalize_oracle_symbol(symbol)
    cached = quick_cache_get(asset, lang, ux_mode)
    if cached is not None:
        cached["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return JSONResponse(cached)

    async def _compute() -> dict:
        row = get_best_price("binance", f"{asset}/USDT")
        market = None
        if row and row.get("mid"):
            market = {
                "price": float(row["mid"]),
                "change_24h": 0.0,
                "volume": 0.0,
                "quote_volume": 0.0,
                "source": "websocket_live",
            }
        if market is None:
            market = await _fetch_binance_ticker(pair)
        if market is None:
            raise HTTPException(status_code=404, detail=f"Symbol {asset} not found.")

        price = market["price"]
        quote_volume = market["quote_volume"] or (market["volume"] * price)
        change = market["change_24h"]

        from market_context import oracle_score

        score = oracle_score(quote_volume, change)
        if _is_stablecoin(asset):
            score = min(score, 55)
        verdict, _ = _oracle_verdict(score, asset, price)
        support = round(price * 0.97, -2)
        resistance = round(price * 1.03, -2)
        action = _oracle_action(score, price, support, resistance)
        sentiment = _oracle_sentiment(change)
        decision_action = "ACT" if str(verdict).upper() in {"BUY", "ACT", "BULLISH"} else "WAIT"
        try:
            from i18n_service import decision_sentence as _dec

            decision_sentence = _dec(lang, decision_action, asset, score)
        except Exception:
            decision_sentence = (
                f"{decision_action} on {asset} — score {score}. "
                f"Analytical summary (not advice): {action}"
            )
        return {
            "symbol": asset,
            "price": price,
            "change_24h": change,
            "verdict": verdict,
            "decision_action": decision_action,
            "decision_sentence": decision_sentence,
            "opportunity_score": score,
            "action": action,
            "action_line": f"Analytics summary: {action}",
            "oracle": decision_sentence,
            "sentiment": sentiment,
            "engine": "quick_rules_v1",
            "latency_target_ms": 100,
            "ux_mode": ux_mode,
            "lang": lang,
            "viral_cache": "miss",
        }

    payload = await run_oracle_bounded(_compute)
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    payload["latency_ms"] = latency_ms
    payload["meets_latency_target"] = latency_ms <= 100

    background_tasks.add_task(
        _log_oracle_prediction,
        {
            "symbol": asset,
            "asset": asset,
            "price": payload.get("price"),
            "verdict": payload.get("verdict"),
            "opportunity_score": payload.get("opportunity_score"),
            "confidence": payload.get("opportunity_score"),
            "kind": "oracle_quick",
        },
    )
    background_tasks.add_task(
        _record_behavior,
        "oracle_query",
        asset=asset,
        payload={
            "verdict": payload.get("verdict"),
            "opportunity_score": payload.get("opportunity_score"),
            "engine": "quick_rules_v1",
        },
    )

    try:
        from decision_certificate import build_decision_certificate, compliance_footer_block

        payload.setdefault("tier", "free")
        payload["decision_certificate"] = build_decision_certificate(payload)
        payload["compliance_footer"] = compliance_footer_block(
            surface="single_sentence_oracle_quick",
            trust_basis="public_accuracy_ledger + quick_rules_engine",
        )
    except Exception:
        pass
    try:
        from data_freshness import attach_oracle_freshness

        payload = attach_oracle_freshness({**payload, "asset": asset})
    except Exception:
        pass
    from security_sanitize import sanitize_oracle_payload

    clean = sanitize_oracle_payload(payload)
    quick_cache_set(asset, lang, ux_mode, clean)
    return JSONResponse(clean)


@app.get("/oracle/{symbol}")
async def oracle(
    symbol: str,
    request: Request,
    background_tasks: BackgroundTasks,
    user: dict | None = Depends(optional_user),
    ux_mode: str = "beginner",
    lang: str = "en",
):
    # Reserved path — must not be captured as a trading symbol
    if symbol.strip().lower() == "accuracy":
        return templates.TemplateResponse(request, "oracle_accuracy.html", _footer_ctx())

    from auth_service import check_oracle_quota

    allowed, message = await check_oracle_quota(user)
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "quota_exceeded",
                "message": message,
                "upgrade_url": "/create-checkout-session?tier=pro",
            },
        )

    asset, pair = _normalize_oracle_symbol(symbol)
    market = await _fetch_binance_ticker(pair)
    if market is None:
        raise HTTPException(status_code=404, detail=f"Symbol {asset} not found.")

    price = market["price"]
    volume = market["volume"]
    quote_volume = market["quote_volume"] or (volume * price)
    change = market["change_24h"]
    whale_alert = None
    try:
        whale_alert = await _fetch_cvvd_whale_alert(asset, pair, price)
    except Exception:
        logger.exception("Whale alert fetch failed")

    try:
        from oracle_unified import compute_unified_oracle

        unified = await compute_unified_oracle(asset, price, quote_volume, change)
    except Exception:
        logger.exception("Unified oracle engine unavailable — falling back to technical score")
        from market_context import oracle_score

        unified = {
            "opportunity_score": oracle_score(quote_volume, change),
            "verdict": None,
            "confidence": None,
            "engine": "technical_fallback_v1",
        }

    payload = _build_full_oracle_response(
        asset, price, volume, quote_volume, change,
        whale_alert=whale_alert,
        unified=unified,
    )
    try:
        payload["explanation"] = await _build_opportunity_explanation(
            asset, price, change, quote_volume, payload["opportunity_score"], payload["verdict"], pair=pair
        )
    except Exception:
        logger.exception("Oracle explanation unavailable")
        payload["explanation"] = {"summary": "Technical oracle response (extended explanation unavailable)."}
    try:
        from forecast_engine import enrich_oracle_payload

        payload = await enrich_oracle_payload(payload)
    except Exception:
        logger.exception("Oracle forecast enrichment unavailable")

    # Constitution differentiators on the primary user path (D3/D4/D7/D8 + UX mode)
    try:
        from decision_enrichment import enrich_oracle_decision
        from ux_mode import normalize_lang, normalize_ux_mode

        payload = enrich_oracle_decision(
            payload,
            ux_mode=normalize_ux_mode(ux_mode),
            lang=normalize_lang(lang),
            register_signal=True,
        )
    except Exception:
        logger.exception("Constitution decision enrichment unavailable")

    # D1: await audit log so response carries a real prediction_id (not signal_id).
    try:
        prediction_id = await _log_oracle_prediction(payload)
        if prediction_id is not None:
            payload["prediction_id"] = prediction_id
            # D8: bind audit prediction_id onto the sovereign registry row
            try:
                from signal_registry import attach_prediction_id, register_from_evaluation

                sig = (payload.get("signal_registry") or {}).get("signal_id")
                linked = attach_prediction_id(str(sig), prediction_id) if sig else None
                if not linked:
                    linked = register_from_evaluation(
                        {
                            "kind": payload.get("kind") or "oracle_direction",
                            "asset": asset,
                            "opportunity_score": payload.get("opportunity_score"),
                            "oracle": {"verdict": payload.get("verdict")},
                            "prediction_id": prediction_id,
                            "payload": payload,
                        }
                    )
                if linked:
                    payload["signal_registry"] = {
                        "signal_id": linked.get("signal_id"),
                        "prediction_id": linked.get("prediction_id"),
                        "features_hash": linked.get("features_hash"),
                        "label": linked.get("label"),
                        "definition": linked.get("definition"),
                        "source": linked.get("source"),
                        "weight": linked.get("weight"),
                        "performance": linked.get("performance"),
                    }
            except Exception:
                logger.debug("signal registry prediction_id attach failed", exc_info=True)
            try:
                from oracle_audit_chain import chain_summary

                recent = (chain_summary(limit=8) or {}).get("recent_records") or []
                for entry in reversed(recent):
                    if str(entry.get("prediction_id")) == str(prediction_id):
                        payload["chain_hash"] = entry.get("chain_hash")
                        payload["proof"] = {
                            "prediction_id": prediction_id,
                            "chain_hash": entry.get("chain_hash"),
                            "public_page": "/oracle-accuracy",
                        }
                        break
            except Exception:
                logger.debug("chain_hash attach failed", exc_info=True)
    except Exception:
        logger.exception("Oracle prediction_id attach failed")

    # Hero #6 — Decision Certificate on every primary Oracle response.
    try:
        from decision_certificate import build_decision_certificate, compliance_footer_block

        payload["tier"] = (user or {}).get("tier") or "free"
        payload["decision_certificate"] = build_decision_certificate(payload)
        payload["compliance_footer"] = compliance_footer_block(
            surface="single_sentence_oracle",
            trust_basis="public_accuracy_ledger + decision_certificate",
        )
    except Exception:
        logger.debug("Decision certificate attach failed", exc_info=True)

    # Lightweight Bull / Base / Bear fan-out (not Monte Carlo desk)
    try:
        from oracle_scenarios import build_oracle_scenarios

        payload["scenarios"] = build_oracle_scenarios(payload)
    except Exception:
        logger.debug("Oracle scenarios attach failed", exc_info=True)

    # Hero #1 — Why in <5s (normalized Top-3 for UI)
    try:
        from heroes_quality import build_oqs_why_block

        payload["oqs_why"] = build_oqs_why_block(payload)
        if payload["oqs_why"].get("top_3_factors"):
            expl = payload.get("explanation") or {}
            if isinstance(expl, dict) and not expl.get("top_3_factors"):
                expl = {**expl, "top_3_factors": payload["oqs_why"]["top_3_factors"]}
                payload["explanation"] = expl
    except Exception:
        logger.debug("OQS why block attach failed", exc_info=True)

    # Durable product alert without Telegram when Oracle says ACT.
    try:
        if str(payload.get("decision_action") or "").upper() == "ACT":
            from alert_service import dispatch_alert

            sentence = str(payload.get("decision_sentence") or payload.get("verdict") or "ACT")
            await dispatch_alert(
                f"Oracle ACT · {asset}",
                sentence,
                payload={
                    "asset": asset,
                    "prediction_id": payload.get("prediction_id"),
                    "opportunity_score": payload.get("opportunity_score"),
                    "verdict": payload.get("verdict"),
                    "source": "oracle_act",
                },
                channels=["in_app"],
            )
    except Exception:
        logger.debug("Oracle ACT in-app alert failed", exc_info=True)

    background_tasks.add_task(
        _record_behavior,
        "oracle_query",
        user=user,
        asset=asset,
        payload={
            "verdict": payload.get("verdict"),
            "opportunity_score": payload.get("opportunity_score"),
            "ux_mode": payload.get("ux_mode"),
            "prediction_id": payload.get("prediction_id"),
            "signal_id": (payload.get("signal_registry") or {}).get("signal_id"),
        },
    )
    try:
        from observability import increment_metric

        increment_metric("oracle_queries_total")
    except Exception:
        pass

    try:
        from data_freshness import attach_oracle_freshness

        payload = attach_oracle_freshness({**payload, "asset": asset})
    except Exception:
        logger.debug("Oracle freshness attach failed", exc_info=True)

    from regulatory_compliance_guard import apply_regulatory_compliance
    from security_sanitize import sanitize_oracle_payload

    payload = apply_regulatory_compliance(payload) if user and is_admin_user(user) else sanitize_oracle_payload(payload)
    return JSONResponse(payload)


@app.get("/api/whale-activity")
async def whale_activity(refresh: bool = False) -> dict:
    """CVVD whale intelligence — cross-venue manipulation alerts + sector inflow."""
    context = await _fetch_cvvd_whale_context(refresh=refresh)
    sector_rows: list[dict] = []
    for row in context.get("sector_flows", []):
        meta = _parse_alert_metadata(row)
        sector_rows.append(
            {
                "sector": row.get("sector"),
                "sii_score": float(meta.get("sii_score") or row.get("net_flow_usd") or 0),
                "net_flow_usd": float(meta.get("net_flow_usd") or 0),
                "flow_velocity_usd": float(meta.get("flow_velocity_usd") or 0),
                "timestamp": row.get("timestamp"),
            }
        )

    return {
        "whale_alerts": context.get("whale_alerts", []),
        "sector_flows": sector_rows,
        "data_source": "CVVD Cross-Venue Detection | Binance + OKX + Bybit",
        "live_scan": context.get("live_scan", False),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.post("/api/whale/scan")
async def whale_scan() -> dict:
    """Trigger a fresh CVVD scan across all venues."""
    context = await _fetch_cvvd_whale_context(refresh=True)
    return {
        "alerts_found": len(context.get("whale_alerts", [])),
        "whale_alerts": context.get("whale_alerts", [])[:20],
        "timestamp": datetime.now(UTC).isoformat(),
    }

# Market API routes → api/routers/market.py

@app.get("/api/analytics/profit")
async def analytics_profit():
    from market_intel import build_profit_analytics

    return await build_profit_analytics()


@app.get("/api/whale/gravity-map")
async def whale_gravity_map():
    from market_intel import build_whale_gravity_map

    whale_ctx = await _fetch_cvvd_whale_context(refresh=False)
    market = await _fetch_binance_market_overview()
    return build_whale_gravity_map(
        whale_ctx,
        market,
        parse_metadata=_parse_alert_metadata,
    )



@app.get("/api/execution/speed")
async def execution_speed_api():
    from plan_audit import execution_speed_snapshot

    return await execution_speed_snapshot()


@app.get("/api/sentiment/overview")
async def sentiment_overview():
    from sentiment_engine import build_sentiment_context_safe

    assets = [item.upper() for item in config.WHITELIST_ASSETS]
    ctx = await build_sentiment_context_safe(assets)
    indices = ctx.get("sentiment_compound_index") or {}
    rows = []
    for asset in assets:
        compound = float(indices.get(asset, 0.0))
        score = _compound_to_score(compound)
        rows.append(
            {
                "asset": asset,
                "compound_index": round(compound, 3),
                "sentiment_score": score,
                "label": _compound_label(compound),
                "sector": _sector_for_asset(asset),
            }
        )
    rows.sort(key=lambda x: x["sentiment_score"], reverse=True)
    return {
        "assets": rows,
        "data_source": "Rolling Compound Sentiment Index",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/api/onchain/overview")
async def onchain_overview():
    from onchain_tracker import build_onchain_context_safe

    ctx = await build_onchain_context_safe()
    statuses = ctx.get("onchain_by_asset") or {}
    rows = []
    for asset, status in statuses.items():
        if isinstance(status, dict):
            rows.append(
                {
                    "asset": asset,
                    "bias": status.get("bias"),
                    "net_flow_usd": status.get("net_flow_usd"),
                    "inflow_usd": status.get("inflow_usd"),
                    "outflow_usd": status.get("outflow_usd"),
                    "signals": status.get("signals") or [],
                }
            )
    rows.sort(key=lambda x: abs(float(x.get("net_flow_usd") or 0)), reverse=True)
    return {
        "assets": rows,
        "data_source": "On-Chain Exchange Flow Tracker",
        "timestamp": datetime.now(UTC).isoformat(),
    }


# Oracle + ML API routes → api/routers/oracle.py

@app.get("/api/macro/overview")
async def macro_overview():
    from oracle_data_hub import fetch_macro_mesh

    timeout = aiohttp.ClientTimeout(total=config.ORACLE_HUB_FETCH_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        macro = await fetch_macro_mesh(session)
    return {
        "macro": macro,
        "data_source": "Oracle Data Hub — Yahoo Finance extended",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/api/universe/phase-b/probe")
async def universe_phase_b_probe(symbol: str = "BTC/USDT"):
    from ccxt_market_fetcher import probe_phase_b_exchanges

    return await probe_phase_b_exchanges(sample_symbol=symbol)


@app.get("/api/universe/phase-b2/probe")
async def universe_phase_b2_probe(symbol: str = "BTC/USDT"):
    from coingecko_cex_fetcher import probe_coingecko_exchanges

    return await probe_coingecko_exchanges(sample_symbol=symbol)


@app.get("/api/universe/phase-c/probe")
async def universe_phase_c_probe(symbol: str = "BTC/USDT"):
    from dex_fetcher import probe_dex_venues

    return await probe_dex_venues(sample_symbol=symbol)


@app.get("/api/universe/phase-d/probe")
async def universe_phase_d_probe(symbol: str = "BTC/USDT"):
    from perp_dex_fetcher import probe_perp_dex_venues

    return await probe_perp_dex_venues(sample_symbol=symbol)


@app.get("/api/universe/full-probe")
async def universe_full_probe(symbol: str = "BTC/USDT"):
    import aggregator
    from ccxt_market_fetcher import probe_phase_b_exchanges
    from coingecko_cex_fetcher import probe_coingecko_exchanges
    from dex_fetcher import probe_dex_venues
    from perp_dex_fetcher import probe_perp_dex_venues

    native_ids = sorted(
        ex for ex in config.INGESTION_READY_EXCHANGES if ex in aggregator.MARKET_FETCHERS
    )
    return {
        "symbol": symbol,
        "fetchers_registered": len(aggregator.MARKET_FETCHERS),
        "ingestion_ready": len(config.INGESTION_READY_EXCHANGES),
        "native_plus_all_ids": len(native_ids),
        "phase_b_ccxt": await probe_phase_b_exchanges(sample_symbol=symbol),
        "phase_b2_coingecko": await probe_coingecko_exchanges(sample_symbol=symbol),
        "phase_c_dex": await probe_dex_venues(sample_symbol=symbol),
        "phase_d_perp": await probe_perp_dex_venues(sample_symbol=symbol),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/api/universe/status")
async def universe_status():
    from platform_universe import build_manifest_universe_block, compute_universe_coverage
    from universe_rollout import live_rollout_status, rollout_summary_json

    return {
        "coverage": await compute_universe_coverage(),
        "registry": build_manifest_universe_block(),
        "rollout": rollout_summary_json(),
        "live": await live_rollout_status(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.post("/api/universe/activate-full")
async def universe_activate_full():
    from universe_rollout import activate_full_universe, live_rollout_status

    result = activate_full_universe(save=True)
    result["live"] = await live_rollout_status()
    return result


@app.get("/api/universe/rollout")
async def universe_rollout_status_api():
    from universe_rollout import live_rollout_status, rollout_summary_json

    return {
        "summary": rollout_summary_json(),
        "live": await live_rollout_status(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/api/ingestion/status")
async def ingestion_status():
    import os

    from binance_ws_ingest import ws_stats
    from data_lake import lake_status
    from data_sources_registry import DATA_SOURCES, registry_summary
    from ingestion_scheduler import scheduler_running

    status = await lake_status()
    status["scheduler_running"] = scheduler_running()
    status["websocket"] = ws_stats()
    status["architecture"] = "scheduler + websocket → SQLite data_lake → oracle"
    status["exchanges"] = {
        "ingestion_ready": sorted(config.INGESTION_READY_EXCHANGES),
        "enabled_for_arbitrage": sorted(config.enabled_exchanges().keys()),
        "total_ready": len(config.INGESTION_READY_EXCHANGES),
    }
    try:
        from platform_universe import compute_universe_coverage

        status["universe"] = await compute_universe_coverage()
        status["assets"] = {
            "tracked": len(config.UNIVERSE_ASSETS),
            "target": status["universe"].get("target", {}).get("assets", 105),
        }
    except Exception:
        status["assets"] = {"tracked": len(config.UNIVERSE_ASSETS), "target": 105}
    status["registry"] = registry_summary()

    health_map = {row["source_id"]: row for row in status.get("health") or []}
    sources_detail = []
    for spec in DATA_SOURCES:
        row = health_map.get(spec.source_id) or {}
        key_ok = not spec.env_key or bool(os.getenv(spec.env_key))
        if row.get("last_ok_at"):
            state = "ok"
        elif spec.env_key and not key_ok:
            state = "needs_key"
        elif row.get("last_error_at"):
            state = "error"
        else:
            state = "pending"
        sources_detail.append(
            {
                "source_id": spec.source_id,
                "name": spec.name,
                "category": spec.category,
                "state": state,
                "env_key": spec.env_key,
                "last_ok_at": row.get("last_ok_at"),
                "last_error": row.get("last_error"),
            }
        )
    status["sources"] = sources_detail
    status["counts"] = {
        "ok": sum(1 for s in sources_detail if s["state"] == "ok"),
        "needs_key": sum(1 for s in sources_detail if s["state"] == "needs_key"),
        "error": sum(1 for s in sources_detail if s["state"] == "error"),
        "pending": sum(1 for s in sources_detail if s["state"] == "pending"),
    }
    return status


@app.get("/api/ingestion/run")
async def ingestion_run_once(_admin: dict = Depends(require_admin)):
    """Manual one-shot ingest (bootstrap all categories)."""
    from ingestion_fetchers import ingest_all_categories

    summary = await ingest_all_categories()
    return {"status": "complete", "categories": summary}


# Forecast + oracle audit routes → api/routers/oracle.py

@app.get("/oracle-accuracy", response_class=HTMLResponse)
@app.get("/oracle/accuracy", response_class=HTMLResponse)
async def oracle_accuracy_page(request: Request):
    return templates.TemplateResponse(request, "oracle_accuracy.html", _footer_ctx())


# ML experience routes → api/routers/oracle.py

@app.get("/api/b2b/feed")
async def b2b_feed(x_api_key: str = Header(..., alias="X-API-Key")):
    from whale_tracker import InstitutionalDataExporter

    exporter = InstitutionalDataExporter()
    try:
        return await exporter.export_institutional_feed(provided_key=x_api_key)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="Invalid B2B API key") from exc


@app.get("/api/b2b/demo")
async def b2b_demo_feed():
    """Public demo feed — limited records, no key required."""
    from whale_tracker import InstitutionalDataExporter

    exporter = InstitutionalDataExporter()
    try:
        feed = await exporter.export_institutional_feed(
            provided_key=config.B2B_DEMO_API_KEY,
            limit=config.B2B_DEMO_EXPORT_LIMIT,
        )
        feed["demo"] = True
        feed["upgrade_url"] = "/b2b"
        return feed
    except PermissionError:
        raise HTTPException(status_code=503, detail="B2B demo not configured") from None


@app.get("/api/b2b/info")
async def b2b_info():
    from b2b_websocket_hub import get_b2b_ws_hub

    ws_stats = get_b2b_ws_hub().stats()
    expose_demo = os.getenv("EXPOSE_B2B_DEMO_KEY", "").lower() in {"1", "true", "yes"}
    return {
        "product": "BLACKDARK Institutional Manipulation Feed",
        "feed_version": config.B2B_FEED_VERSION,
        "demo_key": config.B2B_DEMO_API_KEY if expose_demo else "contact-sales",
        "demo_endpoint": "/api/b2b/demo",
        "authenticated_endpoint": "/api/b2b/feed",
        "header": "X-API-Key",
        "websocket_endpoint": "/ws/b2b/feed",
        "websocket_auth": "api_key query parameter",
        "websocket_info_endpoint": "/api/b2b/ws/info",
        "websocket_enabled": ws_stats.get("enabled"),
        "websocket_latency_target_ms": ws_stats.get("latency_target_ms"),
        "pricing_usd_monthly": 199,
        "one_pager_url": "/b2b",
        "methodology": {
            "cvvd": "Cross-Venue Volume Discrepancy",
            "sii": "Sector Inflow Index",
        },
        "events": [
            "connected",
            "snapshot",
            "arbitrage_opportunity",
            "oracle_signal",
            "heartbeat",
        ],
    }


@app.get("/api/b2b/ws/info")
async def b2b_ws_info():
    from b2b_websocket_hub import get_b2b_ws_hub

    expose_demo = os.getenv("EXPOSE_B2B_DEMO_KEY", "").lower() in {"1", "true", "yes"}
    auth: dict[str, Any] = {"query": "api_key"}
    if expose_demo:
        auth["demo_key"] = config.B2B_DEMO_API_KEY
    else:
        auth["demo_key"] = "contact-sales"
    return {
        "endpoint": "/ws/b2b/feed",
        "auth": auth,
        "feed_version": config.B2B_FEED_VERSION,
        **get_b2b_ws_hub().stats(),
        "events": [
            "connected",
            "snapshot",
            "arbitrage_opportunity",
            "oracle_signal",
            "heartbeat",
        ],
    }


@app.websocket("/ws/b2b/feed")
async def b2b_websocket_feed(websocket: WebSocket, api_key: str = Query(..., min_length=8)):
    if not getattr(config, "B2B_WS_ENABLED", True):
        await websocket.close(code=1008, reason="B2B WebSocket disabled")
        return

    from b2b_websocket_hub import get_b2b_ws_hub
    from whale_tracker import InstitutionalDataExporter

    exporter = InstitutionalDataExporter()
    if not exporter.authorize(api_key):
        await websocket.close(code=1008, reason="Invalid B2B API key")
        return

    await websocket.accept()
    hub = get_b2b_ws_hub()
    is_demo = exporter.is_demo_key(api_key)
    client = None
    try:
        client = await hub.register(websocket, api_key, is_demo=is_demo)
        while True:
            msg = await websocket.receive_text()
            if msg.strip().lower() == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now(UTC).isoformat()})
    except WebSocketDisconnect:
        pass
    except RuntimeError as exc:
        await websocket.close(code=1008, reason=str(exc))
    except Exception:
        logger.exception("B2B WebSocket session error")
    finally:
        if client is not None:
            await hub.unregister(client)


@app.get("/b2b", response_class=HTMLResponse)
async def b2b_page(request: Request):
    return templates.TemplateResponse(
        request,
        "b2b.html",
        {
            "demo_key": config.B2B_DEMO_API_KEY,
            "feed_version": config.B2B_FEED_VERSION,
            **_footer_ctx(),
        },
    )


def _legal_page(request: Request, page: str):
    from legal_content import LEGAL_PAGES

    content = LEGAL_PAGES.get(page)
    if not content:
        raise HTTPException(status_code=404, detail="Legal page not found")
    return templates.TemplateResponse(
        request,
        "legal.html",
        {"page": page, **content, **_footer_ctx()},
    )


@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    return _legal_page(request, "terms")


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    return _legal_page(request, "privacy")


@app.get("/disclaimer", response_class=HTMLResponse)
async def disclaimer_page(request: Request):
    return _legal_page(request, "disclaimer")


@app.get("/refund", response_class=HTMLResponse)
async def refund_page(request: Request):
    return _legal_page(request, "refund")


@app.get("/cookies", response_class=HTMLResponse)
async def cookies_page(request: Request):
    return _legal_page(request, "cookies")


@app.get("/api/b2b/demo/proposal")
async def b2b_demo_proposal(client: str = "Demo Prospect"):
    """Public demo sales proposal — limited data, no API key."""
    from whale_tracker import InstitutionalDataExporter

    exporter = InstitutionalDataExporter()
    try:
        payload = await exporter.generate_sales_proposal_payload(
            provided_key=config.B2B_DEMO_API_KEY,
            client_name=client,
            lookback_limit=config.B2B_DEMO_EXPORT_LIMIT,
        )
        payload["demo"] = True
        payload["upgrade_url"] = "/b2b"
        return payload
    except PermissionError:
        raise HTTPException(status_code=503, detail="B2B demo not configured") from None


@app.get("/api/b2b/proposal")
async def b2b_proposal(
    client: str = "Prospect",
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    from whale_tracker import InstitutionalDataExporter

    exporter = InstitutionalDataExporter()
    try:
        return await exporter.generate_sales_proposal_payload(
            provided_key=x_api_key,
            client_name=client,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="Invalid B2B API key") from exc


# Arbitrage API routes → api/routers/arbitrage.py

@app.post("/api/simulate/trade")
async def simulate_trade(
    data: dict = Body(...),
    _user: dict | None = Depends(require_feature("research_lab")),
):
    from trade_simulator import simulate_spot_trade

    try:
        return await simulate_spot_trade(
            str(data.get("symbol") or "BTC"),
            str(data.get("side") or "buy").lower(),  # type: ignore[arg-type]
            float(data.get("amount_usd") or 100),
            hold_hours=int(data.get("hold_hours") or 24),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/simulate/arbitrage")
async def simulate_arbitrage(
    data: dict = Body(...),
    _user: dict | None = Depends(require_feature("research_lab")),
):
    from trade_simulator import simulate_arbitrage_trade

    return await simulate_arbitrage_trade(
        str(data.get("kind") or "cross_exchange"),
        float(data.get("quote_amount") or config.DEFAULT_QUOTE_AMOUNT),
        symbol=data.get("symbol"),
        buy_exchange=data.get("buy_exchange"),
        sell_exchange=data.get("sell_exchange"),
        exchange=data.get("exchange"),
        path=data.get("path"),
    )


@app.get("/api/simulate/history")
async def simulate_history(
    limit: int = 15,
    _user: dict | None = Depends(require_feature("research_lab")),
):
    from database import fetch_simulation_logs

    return {"simulations": await fetch_simulation_logs(limit=limit)}


@app.post("/api/alerts/subscribe")
async def alerts_subscribe(
    data: dict = Body(...),
    user: dict | None = Depends(optional_user),
):
    from alert_service import subscribe_alerts
    from auth_service import feature_allowed

    if not user or not feature_allowed(user, "alerts"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "upgrade_required",
                "feature": "alerts",
                "upgrade_url": "/create-checkout-session?tier=pro",
            },
        )
    try:
        if not data.get("email"):
            data = {**data, "email": user.get("email")}
        return await subscribe_alerts(data, user_email=user.get("email"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/alerts/test")
async def alerts_test(_admin: dict = Depends(require_admin)):
    from alert_service import send_test_alert

    return await send_test_alert()


@app.get("/api/alerts/inbox")
async def alerts_inbox(
    limit: int = 30,
    unread_only: bool = False,
    user: dict | None = Depends(optional_user),
):
    from in_app_alerts import inbox_stats, list_in_app_alerts

    email = (user or {}).get("email")
    return {
        "stats": inbox_stats(user_email=email),
        "alerts": list_in_app_alerts(limit=limit, user_email=email, unread_only=unread_only),
        "works_without_telegram": True,
    }


@app.post("/api/alerts/inbox/{alert_id}/read")
async def alerts_inbox_mark_read(
    alert_id: str,
    user: dict = Depends(require_authenticated),
):
    from in_app_alerts import mark_read

    row = mark_read(alert_id, user_email=str(user.get("email") or ""))
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"ok": True, "alert": row}


@app.post("/api/execution/auto")
async def execution_auto_toggle(body: ExecutionAutoBody, _user: dict = Depends(require_whale)):
    from execution_engine import set_auto_execution

    return await set_auto_execution(body.enabled)


@app.post("/api/execution/cycle")
async def execution_auto_cycle(_user: dict = Depends(require_whale)):
    from execution_engine import run_auto_execution_cycle

    return await run_auto_execution_cycle()


@app.get("/api/execution/status")
async def execution_status(_user: dict = Depends(require_pro_or_above)):
    from execution_engine import get_execution_status

    return await get_execution_status()


@app.get("/api/execution/keys/status")
async def execution_keys_status_api(_user: dict = Depends(require_whale)):
    from execution_keys import execution_keys_status

    status = execution_keys_status()
    status.pop("keys_file", None)
    return status


@app.post("/api/execution/keys/activate")
async def execution_keys_activate(request: Request, live: bool = False, user: dict = Depends(require_whale)):
    from execution_keys import activate_live_execution

    if live:
        from security_auth import verify_admin_key

        if not verify_admin_key(request.headers.get("X-Admin-Key")):
            raise HTTPException(
                status_code=403,
                detail="Live activation requires whale auth + X-Admin-Key",
            )
    host = request.client.host if request.client else ""
    if host not in {"127.0.0.1", "::1", "localhost"} and not live:
        from security_auth import verify_admin_key

        if not verify_admin_key(request.headers.get("X-Admin-Key")):
            raise HTTPException(status_code=403, detail="Admin required for remote activation")
    return await activate_live_execution(enable_live=live)


@app.post("/api/execution/cex-dex/cycle")
async def execution_cex_dex_cycle(quote_usd: float = 1000, _user: dict = Depends(require_whale)):
    """Whale CEX↔DEX cycle — forced dry-run unless LIVE_EXECUTION_ALLOW_API=true."""
    from bd_platform.cex_dex_executor import run_cex_dex_cycle

    allow_live = os.getenv("LIVE_EXECUTION_ALLOW_API", "false").lower() in {"1", "true", "yes"}
    return await run_cex_dex_cycle(quote_usd=quote_usd, dry_run=not allow_live)


@app.post("/api/execution/panic")
async def execution_panic(user: dict = Depends(require_whale)):
    from execution_engine import trigger_panic

    return await trigger_panic(user_id=int(user["id"]))


@app.post("/api/execution/resume")
async def execution_resume(_user: dict = Depends(require_whale)):
    from execution_engine import resume_execution

    return await resume_execution()


@app.post("/api/execution/order")
async def execution_order(body: ExecutionOrderBody, user: dict = Depends(require_whale)):
    from execution_engine import execute_order

    try:
        return await execute_order(
            body.symbol,
            body.side,  # type: ignore[arg-type]
            body.amount_usd,
            dry_run=True,
            user_id=int(user["id"]),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/execution/logs")
async def execution_logs(limit: int = 15, _user: dict = Depends(require_pro_or_above)):
    from database import fetch_execution_logs

    return {"logs": await fetch_execution_logs(limit=limit)}


@app.get("/api/research/lab")
async def research_lab_report(_user: dict | None = Depends(require_feature("research_lab"))):
    from research_lab import build_research_lab_report

    return await build_research_lab_report()


@app.get("/api/research/moat")
async def research_moat():
    from research_lab import compute_economic_moat

    return await compute_economic_moat()


@app.get("/api/moat/build-status")
async def moat_build_status():
    from data_moat_guard import build_moat_build_status, data_moat_guard_status

    status = await build_moat_build_status()
    status["guard"] = data_moat_guard_status()
    return status


@app.get("/api/acquisition/assets")
async def acquisition_assets_audit():
    from acquisition_assets_service import acquisition_assets_status, build_acquisition_asset_audit

    audit = await build_acquisition_asset_audit()
    audit["status"] = acquisition_assets_status()
    return audit


@app.get("/api/behavior/stats")
async def behavior_data_stats(days: int = 30):
    from behavior_data_service import behavior_data_status, fetch_behavior_asset_stats

    stats = await fetch_behavior_asset_stats(days=days)
    stats["status"] = behavior_data_status()
    return stats


@app.get("/api/research/asset/{symbol}")
async def research_asset(symbol: str, notional: float = 10_000):
    from research_lab import compute_financial_models

    return await compute_financial_models(symbol, notional=notional)


@app.get("/api/research/export")
async def research_export(x_api_key: str = Header(..., alias="X-API-Key")):
    from research_lab import export_signed_research

    try:
        return await export_signed_research(x_api_key)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="Invalid B2B API key") from exc



@app.post("/api/voice/command")
async def voice_command(
    data: dict = Body(...),
    _user: dict | None = Depends(require_feature("voice")),
):
    from database import increment_platform_metric
    from voice_service import process_voice_command

    text = str(data.get("text") or data.get("command") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text or command required")
    await increment_platform_metric("voice_commands")
    return await process_voice_command(text)


@app.get("/api/reports/weekly")
async def weekly_report_endpoint(
    persist: bool = True,
    _user: dict | None = Depends(require_feature("research_lab")),
):
    from weekly_report import build_weekly_report

    return await build_weekly_report(persist=persist)


@app.get("/api/reports/weekly/history")
async def weekly_report_history(
    limit: int = 12,
    _user: dict | None = Depends(require_feature("research_lab")),
):
    from database import fetch_weekly_reports

    return {"reports": await fetch_weekly_reports(limit=limit)}


@app.get("/api/reports/weekly/markdown")
async def weekly_report_markdown(
    _user: dict | None = Depends(require_feature("research_lab")),
):
    from weekly_report import build_weekly_report, report_to_markdown

    report = await build_weekly_report(persist=False)
    body = report_to_markdown(report)
    return Response(content=body, media_type="text/markdown; charset=utf-8")


@app.get("/api/reports/daily")
async def daily_report_endpoint(
    persist: bool = True,
    _user: dict | None = Depends(require_feature("research_lab")),
):
    from daily_report import build_daily_report

    return await build_daily_report(persist=persist)


@app.get("/api/reports/daily/markdown")
async def daily_report_markdown(
    _user: dict | None = Depends(require_feature("research_lab")),
):
    from daily_report import build_daily_report, daily_report_markdown as to_md

    report = await build_daily_report(persist=False)
    return Response(content=to_md(report), media_type="text/markdown; charset=utf-8")


@app.get("/api/ta/{symbol}")
async def ta_bundle(symbol: str):
    from technical_analysis import build_ta_bundle

    return await build_ta_bundle(symbol.upper())



@app.get("/api/database/health")
async def database_health():
    from db_upgrade import database_health_report

    return await database_health_report()


@app.get("/api/storage/status")
async def storage_status():
    from storage_tier_manager import storage_architecture_status

    return await storage_architecture_status()


@app.get("/api/storage/cost-guard")
async def storage_cost_guard_api():
    from storage_cost_guard import storage_cost_guard_status

    return storage_cost_guard_status()



@app.get("/api/sentiment/manipulation-guard")
async def api_sentiment_manipulation_guard():
    from sentiment_manipulation_guard import sentiment_manipulation_status

    return sentiment_manipulation_status()



@app.get("/api/security/api-keys")
async def api_key_security_status_api(_user: dict = Depends(require_whale)):
    from api_key_security_guard import api_key_security_status
    from wash_trade_guard import wash_trade_guard_status

    return {
        "api_key_security": api_key_security_status(),
        "wash_trade_guard": wash_trade_guard_status(),
    }


@app.get("/api/regulatory/compliance")
async def api_regulatory_compliance():
    from regulatory_compliance_guard import regulatory_compliance_status

    return regulatory_compliance_status()


@app.get("/api/retention/status")
async def api_retention_status(user: dict | None = Depends(optional_user)):
    from database import fetch_active_subscription_for_email
    from retention_service import build_retention_status

    sub = None
    if user:
        sub = await fetch_active_subscription_for_email(user["email"])
    return await build_retention_status(user, sub)


@app.get("/api/subscriber/value")
async def api_subscriber_value(user: dict | None = Depends(optional_user)):
    from retention_service import build_subscriber_value_digest

    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    tier = str(user.get("tier") or "free")
    if tier == "free":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "upgrade_required",
                "message": "Subscriber value digest requires Pro or Whale.",
                "upgrade_url": "/create-checkout-session?tier=pro",
            },
        )
    return await build_subscriber_value_digest(user["email"], tier)


@app.api_route("/api/storage/maintenance", methods=["GET", "POST"])
async def storage_maintenance(_admin: dict = Depends(require_admin_dev)):
    from storage_tier_manager import run_storage_maintenance_cycle

    return await run_storage_maintenance_cycle()


@app.api_route("/api/storage/legacy-purge", methods=["GET", "POST"])
async def storage_legacy_purge(_admin: dict = Depends(require_admin_dev)):
    """One-time: delete legacy pricing_logs from SQLite ops DB (localhost only)."""
    from storage_tier_manager import purge_legacy_ops_market_data

    return await purge_legacy_ops_market_data(vacuum=True)


@app.get("/api/storage/hot-tier")
async def storage_hot_tier():
    from hot_tier_reader import hot_tier_status

    return await hot_tier_status()


@app.post("/api/database/maintenance")
async def database_maintenance(vacuum: bool = False, _admin: dict = Depends(require_admin)):
    from db_upgrade import run_sqlite_maintenance

    return await run_sqlite_maintenance(vacuum=vacuum)


@app.get("/api/database/maintenance/history")
async def database_maintenance_history(limit: int = 10):
    from database import fetch_maintenance_runs

    return {"runs": await fetch_maintenance_runs(limit=limit)}


@app.get("/api/analytics/stats")
async def analytics_stats():
    from database import fetch_platform_analytics

    return await fetch_platform_analytics()


@app.post("/api/analytics/view")
async def analytics_view(data: dict = Body(default={})):
    from database import increment_platform_metric

    page = str(data.get("page") or "page_views")
    metric_map = {
        "dashboard": "dashboard_views",
        "landing": "landing_views",
        "page": "page_views",
    }
    metric = metric_map.get(page, page)
    return await increment_platform_metric(metric)


@app.get("/manifest.json")
async def pwa_manifest():
    manifest_path = STATIC_DIR / "manifest.json"
    if manifest_path.exists():
        return FileResponse(manifest_path, media_type="application/manifest+json")
    return JSONResponse({"name": "BLACKDARK", "display": "standalone"})


@app.get("/sw.js")
async def service_worker():
    sw_path = STATIC_DIR / "sw.js"
    if sw_path.exists():
        return FileResponse(sw_path, media_type="application/javascript")
    return Response(content="// BLACKDARK service worker unavailable", media_type="application/javascript")


@app.get("/api/low-latency/fast-scan")
async def api_fast_scan():
    from fast_scan_engine import run_fast_scan

    return run_fast_scan()


@app.get("/api/due-diligence/status")
async def api_due_diligence_status():
    from due_diligence import due_diligence_report

    return due_diligence_report()


@app.get("/api/due-diligence/latency")
async def api_due_diligence_latency():
    from latency_audit import latency_status

    return latency_status()


@app.get("/api/due-diligence/uptime")
async def api_due_diligence_uptime():
    from uptime_monitor import ha_architecture_status, uptime_stats

    return {"uptime": uptime_stats(window_hours=24), "ha": ha_architecture_status()}


@app.get("/api/due-diligence/coverage")
async def api_due_diligence_coverage():
    from due_diligence import run_profit_fee_coverage

    return run_profit_fee_coverage()


@app.get("/api/security/admin-mfa")
async def api_security_admin_mfa(_admin: dict = Depends(require_admin_dev)):
    """Admin MFA policy status (does not reveal ADMIN_TOTP_SECRET)."""
    from admin_mfa import mfa_status

    return mfa_status()


@app.get("/api/security/events")
async def api_security_events(
    limit: int = 50,
    kind: str | None = None,
    _admin: dict = Depends(require_admin),
):
    from security_events import recent_security_events, security_events_stats

    return {
        "stats": security_events_stats(),
        "events": recent_security_events(limit=min(limit, 200), kind=kind),
    }


@app.get("/api/security/status")
async def api_security_status():
    """Public security posture summary for due diligence (not a certification)."""
    from security_auth import login_rate_limit_backend
    from security_posture import security_posture_report

    from postgres_backend import use_postgres

    report = security_posture_report()
    vault_ok = bool(os.getenv("SECRETS_MASTER_KEY") or os.getenv("SECRETS_VAULT_KEY"))
    return {
        **report,
        "at_rest_encryption": {
            "status": "fernet_vault_when_configured" if vault_ok else "configure_SECRETS_MASTER_KEY",
            "user_keys": "encrypted",
            "iso_27001_certificate": False,
            "note": "Engineering posture with Fernet at-rest encryption ≠ ISO 27001 certification",
        },
        "database_posture": {
            "engine": "postgresql" if use_postgres() else "sqlite",
            "institutional_pitch_requires_postgres": True,
            "soft_launch_sqlite_ok": True,
        },
        "secrets_policy": {
            "hardcoded_keys_forbidden": True,
            "env_vault_required": True,
            "hashicorp_vault_required": False,
            "note": "Use env SECRETS_MASTER_KEY / SECRETS_VAULT_KEY — HashiCorp Vault is optional ops, not a ship claim",
        },
        "login_rate_limit_backend": login_rate_limit_backend(),
        "model_weights_key_configured": bool(os.getenv("MODEL_WEIGHTS_KEY")),
        "public_developer_docs": "/docs",
        "architecture_index": "ARCHITECTURE.md",
        "data_room": "/data-room",
        "scale_readiness": "/api/scale/readiness",
        "viral_readiness": "/api/viral/readiness",
        "hardening_doc": "docs/SECURITY_HARDENING.md",
    }


# User keys/risk → api/routers/user.py

@app.get("/api/risk/status")
async def api_risk_status(_user: dict = Depends(require_pro_or_above)):
    from risk_manager import risk_status

    return risk_status()


@app.post("/api/risk/freeze")
async def api_risk_freeze(body: RiskFreezeBody, _admin: dict = Depends(require_admin)):
    from risk_manager import freeze_trading

    return freeze_trading(body.reason)


@app.post("/api/risk/unfreeze")
async def api_risk_unfreeze(_admin: dict = Depends(require_admin)):
    from risk_manager import unfreeze_trading

    return unfreeze_trading()



@app.get("/api/options/overview")
async def api_options_overview():
    from options_fetcher import fetch_options_overview

    return await fetch_options_overview()


@app.get("/api/infra/metrics")
async def api_infra_metrics():
    from infra_metrics import collect_infra_metrics

    return collect_infra_metrics()


@app.get("/api/docs/openapi.json")
async def api_openapi_export():
    return app.openapi()


@app.get("/api/docs/public-openapi.json")
async def api_public_openapi_export():
    """Evidence/read OpenAPI only — omits admin/billing/execution write surfaces."""
    from public_api_docs import filter_openapi_for_public

    return filter_openapi_for_public(app.openapi())


@app.get("/api/docs/public-manifest")
async def api_public_docs_manifest():
    from public_api_docs import public_docs_manifest

    return public_docs_manifest()


@app.get("/health/live")
async def health_live():
    """Instant liveness probe — no DB/Redis (target <50ms)."""
    import time

    t0 = time.perf_counter()
    payload = {"status": "ok", "probe": "live", "ts": time.time()}
    try:
        from uptime_monitor import record_probe

        record_probe(ok=True, source="health_live", latency_ms=(time.perf_counter() - t0) * 1000)
    except Exception:
        pass
    return payload


@app.get("/health/ready")
async def health_ready():
    """Readiness — DB init succeeded + service bus (for load balancers)."""
    from fastapi.responses import JSONResponse

    from postgres_backend import pool_stats, use_postgres
    from service_bus import bus_stats

    engine = "postgresql" if use_postgres() else "sqlite"
    ready = bool(_BOOT_DB_READY and _BOOT_DB_OK)
    # Local soft-open only when explicitly allowed by lifespan
    if _BOOT_DB_READY and not _BOOT_DB_OK:
        ready = True  # local/dev soft path set by lifespan
    soft = os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}
    viral_mode = os.getenv("VIRAL_MODE", "true").lower() in {"1", "true", "yes"}
    viral_gate = False
    viral_redis = None
    # Strict viral prod: refuse ready traffic if Redis is down (Soft Launch exempt).
    if ready and viral_mode and not soft and os.getenv("ENV", "").lower() in {"production", "prod"}:
        try:
            from viral_capacity import redis_live

            viral_redis = redis_live()
            viral_gate = True
            if not viral_redis:
                ready = False
        except Exception:
            viral_gate = True
            viral_redis = False
            ready = False
    payload = {
        "status": "ok" if ready else "starting",
        "probe": "ready",
        "database_ready": bool(_BOOT_DB_OK),
        "database_engine": engine,
        "postgres_pool": pool_stats(),
        "service_bus": bus_stats(),
        "viral_redis_gate": viral_gate,
        "viral_redis_live": viral_redis,
    }
    if not ready:
        return JSONResponse(payload, status_code=503)
    return payload


@app.get("/health/viral")
async def health_viral():
    """Viral/HA admission probe — Redis + multi-instance + middleware (not Soft Launch)."""
    from fastapi.responses import JSONResponse
    from viral_capacity import viral_health_payload

    payload = viral_health_payload()
    if not payload.get("ok"):
        return JSONResponse(payload, status_code=503)
    return payload


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "BLACKDARK",
        "version": "1.0.0",
        "ui_language": "en",
        "probes": {
            "live": "/health/live",
            "ready": "/health/ready",
            "viral": "/health/viral",
        },
    }


@app.get("/api/build-info")
async def build_info():
    """Verify which commit Railway is actually running."""
    return {
        "ui_language": "en",
        "release": "2026-07-27-launch-phase-v8",
        "git_commit": os.getenv("RAILWAY_GIT_COMMIT_SHA") or os.getenv("GIT_COMMIT"),
        "git_branch": os.getenv("RAILWAY_GIT_BRANCH"),
        "git_message": os.getenv("RAILWAY_GIT_COMMIT_MESSAGE"),
        "service": "blackdark",
        "price_feed_ws_only": getattr(config, "PRICE_FEED_WS_ONLY", None),
        "price_probe": "/api/diagnostics/price/BTC",
    }

@app.post("/portfolio/analyze")
async def portfolio_analyze(
    assets: list = Body(...),
    _user: dict | None = Depends(require_feature("portfolio_ai")),
):
    if not assets:
        raise HTTPException(status_code=400, detail="No assets provided")
    return await _analyze_portfolio_holdings(assets)

@app.post("/join-waitlist")
async def join_waitlist(data: dict, background_tasks: BackgroundTasks):
    from database import insert_waitlist_signup

    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Valid email required")

    result = await insert_waitlist_signup(email, name)
    if result.get("duplicate"):
        raise HTTPException(status_code=409, detail="Email already registered")

    position = result.get("position", 0)
    background_tasks.add_task(
        _record_behavior,
        "waitlist_join",
        payload={"position": position, "name_provided": bool(name)},
    )
    return {
        "success": True,
        "position": position,
        "message": f"Welcome to the dark side! You are #{position} on the waitlist.",
    }


@app.get("/api/services/status")
async def services_status():
    from microservices.lifecycle import current_mode, service_info
    from service_bus import bus_stats

    return {
        **service_info(),
        "service_mode_runtime": current_mode(),
        "service_bus": bus_stats(),
        "deployment": {
            "docker_compose": "docker-compose.yml",
            "launcher": "python run_service.py <web|aggregator|arbitrage|ingestion|all>",
            "scale_hint": "Increase replicas per worker service + REDIS_URL for 1M users path",
        },
    }


@app.get("/api/feed/engine/status")
async def feed_engine_status_api():
    from price_stream_engine import feed_engine_status

    return feed_engine_status()


@app.get("/api/feed/stale-price-guard")
async def api_stale_price_guard():
    from stale_price_guard import stale_guard_status

    return stale_guard_status()


@app.get("/api/feed/ingress-guard")
async def api_ingress_guard():
    from exchange_ingress_guard import ingress_guard_status

    return ingress_guard_status()


@app.get("/api/low-latency/status")
async def low_latency_status():
    import config
    from exchange_ws_hub import ws_hub_stats
    from instant_alert_engine import engine_stats
    from live_book_hub import hub_stats
    from scan_coordinator import coordinator_stats

    return {
        "low_latency_mode": getattr(config, "LOW_LATENCY_MODE", True),
        "exchange_ws": ws_hub_stats(),
        "live_book_hub": hub_stats(),
        "instant_alerts": engine_stats(),
        "scan_coordinator": coordinator_stats(),
        "targets_ms": {
            "book_freshness": int(getattr(config, "LIVE_BOOK_MAX_AGE_MS", 300)),
            "execution_max_age": int(getattr(config, "EXECUTION_MAX_QUOTE_AGE_MS", 300)),
            "scan_pulse": int(float(os.getenv("INSTANT_ALERT_INTERVAL_SEC", "1")) * 1000),
            "execution_loop": int(getattr(config, "AUTO_EXECUTION_INTERVAL_SEC", 1)) * 1000,
        },
        "architecture": (
            "WS-only multiplexed streams (Binance/OKX/Bybit) → Redis → Kafka → live_book_hub"
            if getattr(config, "PRICE_FEED_WS_ONLY", True)
            else "WS bookTicker (Binance/OKX/Bybit) → live_book_hub → arbitrage → execute"
        ),
    }


@app.get("/api/alerts/instant/status")
async def instant_alert_status():
    import config
    from instant_alert_engine import engine_stats
    from market_cache import cache_stats
    from scan_coordinator import coordinator_stats

    stats = engine_stats()
    stats["poll_interval_seconds"] = config.POLL_INTERVAL_SECONDS
    stats["market_cache"] = cache_stats()
    stats["scan_coordinator"] = coordinator_stats()
    stats["arbitrage_prefer_live"] = getattr(config, "ARBITRAGE_PREFER_LIVE", False)
    stats["latency_target_ms"] = 800
    stats["binance_ws"] = __import__("binance_ws_ingest").ws_stats()
    return stats


def _create_stripe_checkout(tier: str, customer_email: str | None = None, user_id: int | None = None) -> dict:
    from billing_service import create_checkout_session, lemon_squeezy_checkout_url, stripe_configured

    ls_url = lemon_squeezy_checkout_url(tier)
    if ls_url:
        return {
            "url": ls_url,
            "provider": "lemon_squeezy",
            "tier": tier,
            "currency": "USD",
            "pci_note": "Card data collected only on Lemon Squeezy-hosted Checkout.",
        }

    if not stripe_configured():
        raise HTTPException(status_code=503, detail="Billing not configured")
    try:
        return create_checkout_session(tier, customer_email=customer_email, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/create-checkout-session")
async def checkout_get(tier: str = "pro", user: dict | None = Depends(optional_user)):
    """Landing page links use GET — redirect to Lemon Squeezy or Stripe."""
    email = user.get("email") if user else None
    user_id = int(user["id"]) if user and user.get("id") else None
    payload = _create_stripe_checkout(tier, customer_email=email, user_id=user_id)
    return RedirectResponse(url=payload["url"], status_code=303)


@app.post("/create-checkout-session")
async def checkout_post(tier: str = "pro", user: dict | None = Depends(optional_user)):
    email = user.get("email") if user else None
    user_id = int(user["id"]) if user and user.get("id") else None
    return _create_stripe_checkout(tier, customer_email=email, user_id=user_id)


@app.post("/webhook")
async def stripe_webhook(request: Request):
    from billing_service import handle_stripe_webhook_event

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    if not endpoint_secret:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid payload") from exc
    except stripe.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Invalid signature") from exc

    result = await handle_stripe_webhook_event(event)
    return {"received": True, **result}


@app.post("/webhook/lemon")
async def lemon_webhook_alias(request: Request):
    """Alias for Lemon Squeezy dashboard URL convenience (same as /api/billing/webhook/lemon)."""
    from api.routers.billing import lemon_webhook

    return await lemon_webhook(request)


@app.get("/app", response_class=HTMLResponse)
async def app_alias_redirect():
    """Orphan templates/index.html is not served — route users to the live dashboard."""
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/success", response_class=HTMLResponse)
async def checkout_success(request: Request):
    return templates.TemplateResponse(request, "success.html", _footer_ctx())


@app.get("/cancel", response_class=HTMLResponse)
async def checkout_cancel(request: Request):
    return templates.TemplateResponse(
        request,
        "utility.html",
        {
            "page": "cancel",
            "title": "Checkout cancelled",
            "lead": "No charge was made. You can restart Decision Pro anytime — or stay on Proof Pass.",
            **_footer_ctx(),
        },
    )


@app.get("/landing", response_class=HTMLResponse)
async def landing_alias(request: Request):
    return templates.TemplateResponse(request, "landing.html", _footer_ctx())


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    # Container platforms set HOST=0.0.0.0; local default stays loopback-only.
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=port)

