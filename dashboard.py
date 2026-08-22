import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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

from api.openapi_responses import COMMON_ERROR_RESPONSES
from starlette.middleware.gzip import GZipMiddleware

import encoding_bootstrap  # noqa: F401 — UTF-8 for Arabic (console + JSON)

# Sonar S1192: duplicated string literals
STR_UTILITY_HTML = 'utility.html'
PATH_CREATE_CHECKOUT_SESSION_TIER_PRO = '/create-checkout-session?tier=pro'
PATH_ORACLE_ACCURACY = '/oracle-accuracy'
STR_BTC_USDT = 'BTC/USDT'
STR_INVALID_B2B_API_KEY = 'Invalid B2B API key'
STR_LOGIN_REQUIRED = 'Login required'
STR_VERIFY_EMAIL = 'Verify email'

_ROOT = Path(__file__).resolve().parent
load_dotenv(_ROOT / ".env")
# Launch secrets file (gitignored) — used for local go-live verification
load_dotenv(_ROOT / ".env.launch.local", override=False)

import config
from safe_errors import public_error
from security_auth import (
    is_admin_user,
    require_admin,
    require_admin_dev,
    require_authenticated,
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
    "whale": {"amount": 4900, "name": "Decision Desk"},
}  # legacy ref — billing_service.STRIPE_TIERS is canonical



def _legal_terms_ack_ok(request: Request) -> bool:
    """Layer-4 gate: visitor acknowledged Terms (cookie) or is an authenticated session."""
    if (request.cookies.get("bd_terms_ack") or "").strip() == "1":
        return True
    # Registered users already accepted Terms at signup (auth_service.register_user).
    auth = (request.headers.get("Authorization") or "").strip()
    if auth.lower().startswith("bearer ") and len(auth) > 20:
        return True
    token = (request.cookies.get("bd_token") or "").strip()
    return bool(token)


def _require_terms_ack_or_403(request: Request):
    if _legal_terms_ack_ok(request):
        return None
    return JSONResponse(
        {
            "ok": False,
            "error": "terms_ack_required",
            "message": "Acknowledge Terms before using decision surfaces.",
            "ack_path": "/api/legal/ack-terms",
            "terms_path": "/terms",
        },
        status_code=403,
    )

def _cookie_secure(request: Request | None = None) -> bool:
    if os.getenv("COOKIE_SECURE", "").strip().lower() in {"1", "true", "yes"}:
        return True
    return bool(request is not None and (request.url.scheme or "").lower() == "https")


def render_page(request: Request, name: str, context: dict[str, Any] | None = None) -> HTMLResponse:
    """Render a Jinja template with full i18n context (lang switcher + t())."""
    from i18n_service import template_context

    ctx = template_context(request, context)
    response = templates.TemplateResponse(request, name, ctx)
    response.set_cookie(
        "bd_lang",
        str(ctx.get("lang") or "en"),
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(request),
    )
    return response


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
    _increment_behavior_metric()


def _increment_behavior_metric() -> None:
    try:
        from observability import increment_metric

        increment_metric("behavior_events_total")
    except Exception:
        pass


async def _portfolio_holding(item: dict) -> tuple[dict | None, float]:
    # Accept documented aliases: asset/symbol + amount/quantity/qty
    symbol = str(item.get("symbol") or item.get("asset") or "").upper().strip()
    amount = float(item.get("amount") or item.get("quantity") or item.get("qty") or 0)
    if not symbol or amount <= 0:
        return None, 0.0
    _, pair = _normalize_oracle_symbol(symbol)
    ticker = await _fetch_binance_ticker(pair)
    price = float(ticker["price"]) if ticker else float(item.get("price") or 0)
    value = amount * price
    beta = _btc_beta_estimate(symbol)
    return (
        {
            "symbol": symbol,
            "amount": amount,
            "price": price,
            "value_usd": round(value, 2),
            "sector": _sector_for_asset(symbol),
            "btc_beta": beta,
        },
        value,
    )


def _portfolio_risk_level(risk_score: int) -> str:
    if risk_score >= 8:
        return "HIGH"
    if risk_score >= 5:
        return "MEDIUM"
    return "LOW"


def _portfolio_recommendations(weighted_beta: float, holdings_count: int) -> list[str]:
    recommendations: list[str] = []
    if weighted_beta > 0.75:
        recommendations.append("High BTC correlation — diversify into uncorrelated assets")
    if holdings_count < 3:
        recommendations.append("Portfolio is concentrated — add 2+ more assets")
    if not recommendations:
        recommendations.append("Balanced portfolio structure for current holdings")
    return recommendations


def _portfolio_compliance_footer() -> dict:
    try:
        from decision_certificate import compliance_footer_block

        return compliance_footer_block(
            surface="portfolio_ai",
            trust_basis="holdings beta model + public_accuracy_ledger",
            data_sources="live spot marks · weighted BTC beta heuristic",
        )
    except Exception:
        return {
            "disclaimer": "Not financial advice. Verify claims on the Public Accuracy Ledger.",
        }


def _attach_portfolio_clarity(result: dict, risk_level: str, risk_score: int) -> None:
    try:
        from heroes_quality import build_portfolio_clarity

        clarity = build_portfolio_clarity(result)
        result["one_sentence"] = clarity["one_sentence"]
        result["clarity"] = clarity
    except Exception:
        result["one_sentence"] = (
            f"Your portfolio looks {risk_level.lower()} risk ({risk_score}/10)."
        )


async def _analyze_portfolio_holdings(assets: list) -> dict:
    holdings: list[dict] = []
    total_value = 0.0

    for item in assets:
        holding, value = await _portfolio_holding(item)
        if holding is None:
            continue
        holdings.append(holding)
        total_value += value

    weighted_beta = 0.0
    if total_value > 0:
        weighted_beta = sum((h["value_usd"] / total_value) * h["btc_beta"] for h in holdings)

    btc_drop_pct = 15.0
    estimated_loss = total_value * weighted_beta * (btc_drop_pct / 100.0)
    risk_score = min(10, max(1, round(weighted_beta * 10)))
    risk_level = _portfolio_risk_level(risk_score)
    recommendations = _portfolio_recommendations(weighted_beta, len(holdings))
    plain = (
        f"In plain language: your book is {risk_level.lower()} risk "
        f"(score {risk_score}/10). Weighted BTC sensitivity is about "
        f"{weighted_beta:.0%}. If BTC falls {btc_drop_pct:.0f}%, expect roughly "
        f"${estimated_loss:,.0f} drawdown on current holdings. "
        f"{recommendations[0]}"
    )

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
        "compliance_footer": _portfolio_compliance_footer(),
        "hero": "portfolio_ai",
    }
    _attach_portfolio_clarity(result, risk_level, risk_score)
    return result

# Set True only after init_db succeeds. Used by /health/ready.
_BOOT_DB_READY = False
_BOOT_DB_OK = False


async def _initialize_database_ready_state() -> None:
    global _BOOT_DB_READY, _BOOT_DB_OK
    try:
        from database import init_db

        await init_db()
        _BOOT_DB_OK = True
        _BOOT_DB_READY = True
    except Exception:
        logger.exception("init_db failed — API stays up for live probes; ready stays closed")
        _BOOT_DB_OK = False
        local_dev = os.getenv("LOCAL_DEV", "false").lower() in {"1", "true", "yes"}
        env = (os.getenv("ENV") or "").strip().lower()
        _BOOT_DB_READY = local_dev and env not in {"production", "prod"}


def _initialize_sentry_safe() -> None:
    try:
        from observability import init_sentry

        init_sentry()
    except Exception:
        logger.exception("Sentry init failed")


def log_production_guard_safe() -> None:
    try:
        from production_guard import evaluate_production_guard

        report = evaluate_production_guard()
        fails = report.get("required_failures") or []
        if fails:
            logger.warning(
                "Production guard REQUIRED failures (boot continued): %s",
                ",".join(str(x) for x in fails),
            )
    except Exception:
        logger.exception("Unable to log production guard")


def _check_production_guard() -> None:
    try:
        from production_guard import enforce_production_guard, is_production, log_production_guard

        if is_production():
            # Soft during boot so Redis/B2B hubs still start when billing/MFA/replicas
            # are pending. Opt into process kill with PRODUCTION_GUARD_HARD_EXIT=true.
            hard = os.getenv("PRODUCTION_GUARD_HARD_EXIT", "false").lower() in {
                "1",
                "true",
                "yes",
            }
            enforce_production_guard(raise_on_fail=hard)
            if not hard:
                log_production_guard_safe()
        else:
            log_production_guard()
    except Exception:
        logger.exception("Production guard check failed")
        from production_guard import is_production

        if is_production() and os.getenv("PRODUCTION_GUARD_HARD_EXIT", "false").lower() in {
            "1",
            "true",
            "yes",
        }:
            raise


async def _load_risk_freeze_safe() -> None:
    try:
        from risk_manager import load_persistent_freeze

        await load_persistent_freeze()
    except Exception:
        logger.exception("Risk freeze load failed")


async def _start_web_microservice(app: FastAPI) -> None:
    try:
        from microservices.lifecycle import ServiceContext, startup

        ms_ctx = ServiceContext()
        await startup("web", ms_ctx)
        app.state.ms_ctx = ms_ctx
    except Exception:
        logger.exception("Web microservice startup failed")
    try:
        from uptime_probe_loop import start_uptime_probe_loop

        app.state.uptime_probe_task = start_uptime_probe_loop()
    except Exception:
        logger.exception("Uptime self-probe failed in web mode")


async def _start_background_runtime(app: FastAPI) -> None:
    try:
        from startup_orchestrator import RuntimeState, run_background_startup

        runtime = RuntimeState()
        app.state.runtime = runtime
        await run_background_startup(runtime)
    except Exception:
        logger.exception("Background startup failed")


async def _background_boot(app: FastAPI) -> None:
    """Start runtime services before guard so pending ops secrets do not leave Redis/B2B dead."""
    await _initialize_database_ready_state()
    _initialize_sentry_safe()
    await _load_risk_freeze_safe()
    if getattr(config, "SERVICE_MODE", "all").strip().lower() == "web":
        await _start_web_microservice(app)
    else:
        await _start_background_runtime(app)
    try:
        _check_production_guard()
    except Exception:
        logger.exception("Production guard check failed after runtime start")
        app.state.production_guard_failed = True
        if os.getenv("PRODUCTION_GUARD_HARD_EXIT", "false").lower() in {"1", "true", "yes"}:
            raise


async def _shutdown_lifespan_services(app: FastAPI, boot_task: asyncio.Task[Any]) -> None:
    boot_task.cancel()
    await asyncio.gather(boot_task, return_exceptions=True)
    if await _shutdown_web_microservice(app):
        return
    await _shutdown_background_runtime(app)


async def _shutdown_web_microservice(app: FastAPI) -> bool:
    ms_ctx = getattr(app.state, "ms_ctx", None)
    if ms_ctx is None:
        return False
    try:
        from microservices.lifecycle import shutdown

        await shutdown(ms_ctx)
    except Exception:
        logger.exception("Web microservice shutdown failed")
    return True


async def _shutdown_background_runtime(app: FastAPI) -> None:
    runtime = getattr(app.state, "runtime", None)
    if runtime is None:
        return
    try:
        from startup_orchestrator import shutdown_runtime

        await shutdown_runtime(runtime)
    except Exception:
        logger.exception("Background shutdown failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Yield immediately so Railway /health/live passes, then boot in background."""
    boot_task = asyncio.create_task(_background_boot(app), name="blackdark-boot")
    logger.info("BLACKDARK API live — DB/services loading in background.")
    yield
    await _shutdown_lifespan_services(app, boot_task)


# Public /docs is our evidence/read developer page (not full Swagger dump).
# Full schema remains at /api/docs/openapi.json; filtered at /api/docs/public-openapi.json.
app = FastAPI(
    title="BLACKDARK",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
    responses=COMMON_ERROR_RESPONSES,
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
        and path.endswith((".woff2", ".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".svg"))
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
    from api.routers.admin_billing import router as admin_billing_router

    app.include_router(admin_billing_router)
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
    from api.routers.didit_webhook import router as didit_webhook_router

    app.include_router(didit_webhook_router)
except Exception:
    logger.exception("Didit webhook router unavailable")

try:
    from api.routers.institutional import router as institutional_router
    from api.routers.institutional import sso_router as institutional_sso_router

    app.include_router(institutional_sso_router)
    app.include_router(institutional_router)
except Exception:
    logger.exception("Institutional router unavailable")

try:
    from api.routers.cap646 import router as cap646_router

    app.include_router(cap646_router)
except Exception:
    logger.exception("CAP646 router unavailable")

try:
    from api.routers.rvm import router as rvm_router

    app.include_router(rvm_router)
except Exception:
    logger.exception("RVM router unavailable")

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
        token = authorization.removeprefix("Bearer ")
    elif bd_token:
        from security_middleware import cookie_to_session_bearer

        token = cookie_to_session_bearer(bd_token)
    if not token:
        return None
    return await get_user_from_token(token.strip())


def require_feature(feature: str):
    def _dependency(user: dict | None = Depends(optional_user)) -> dict | None:
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
                    "upgrade_url": PATH_CREATE_CHECKOUT_SESSION_TIER_PRO,
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


async def _technical_explanation_context(
    resolved_pair: str,
    price: float,
    change: float,
) -> dict[str, Any]:
    closes = await _fetch_binance_klines(resolved_pair)
    rsi = _compute_rsi(closes)
    rsi_source = "binance_1h_candles"
    if rsi is None:
        rsi = round(max(18.0, min(82.0, 50.0 + change * 4.5)), 1)
        rsi_source = "estimated_from_24h_change"
    return {
        "closes": closes,
        "rsi": rsi,
        "rsi_source": rsi_source,
        "macd_trend": _macd_trend_label(closes) if closes else "Insufficient candle data",
        "ema_position": _ema_position_label(price, closes) if closes else _ema_position_label(price, [price]),
    }


async def _whale_explanation_context(
    asset: str,
    resolved_pair: str,
    price: float,
    quote_volume: float,
) -> dict[str, Any]:
    whale_context = await _fetch_cvvd_whale_context(refresh=False)
    asset_alerts = _whale_alerts_for_asset(whale_context["whale_alerts"], asset)
    if asset_alerts:
        return _whale_alert_explanation(asset_alerts)
    live_phrase = await _fetch_live_whale_signal(resolved_pair, price)
    return {
        "asset_alerts": asset_alerts,
        "whale_flow": live_phrase,
        "volume_anomaly": (
            "High 24h quote volume vs typical range"
            if quote_volume > 50_000_000
            else "Normal institutional range"
        ),
        "whale_alert_text": live_phrase,
    }


def _whale_alert_explanation(asset_alerts: list[dict[str, Any]]) -> dict[str, Any]:
    top = asset_alerts[0]
    meta = _parse_alert_metadata(top)
    pattern = str(meta.get("pattern") or "manipulation").replace("_", " ")
    spike = float(meta.get("volume_spike_ratio") or 0)
    return {
        "asset_alerts": asset_alerts,
        "whale_flow": (
            f"CVVD {pattern} — {top.get('side') or 'mixed'!s} — "
            f"${float(top.get('notional_usd') or 0):,.0f}"
        ),
        "volume_anomaly": (
            f"Cross-venue spike {spike:.1f}x vs baseline"
            if spike > 1.2
            else "Elevated institutional footprint"
        ),
        "whale_alert_text": (
            f"{pattern} detected — score {float(meta.get('manipulation_score') or 0):.0f}/100"
        ),
    }


async def _sentiment_explanation_context(asset: str, score: int) -> dict[str, Any]:
    from sentiment_engine import build_sentiment_context_safe

    sentiment_ctx = await build_sentiment_context_safe([asset])
    compound = float((sentiment_ctx.get("sentiment_compound_index") or {}).get(asset.upper(), 0.0))
    social_buzz = int(max(15, min(95, round(48 + score * 0.35 + abs(compound) * 40))))
    return {
        "compound": compound,
        "news_sentiment": _compound_to_score(compound),
        "news_label": _compound_label(compound),
        "social_buzz": social_buzz,
        "social_label": _social_buzz_label(social_buzz),
    }


def _social_buzz_label(social_buzz: int) -> str:
    if social_buzz >= 70:
        return "High"
    if social_buzz >= 45:
        return "Moderate"
    return "Low"


async def _onchain_explanation_note(asset: str) -> str:
    from onchain_tracker import build_onchain_context_safe, get_onchain_status_for_asset

    onchain_ctx = await build_onchain_context_safe()
    onchain_status = get_onchain_status_for_asset(asset, onchain_ctx)
    if not onchain_status:
        return "On-chain flow data unavailable for this asset"
    bias = str(onchain_status.get("bias") or "neutral")
    net_flow = float(onchain_status.get("net_flow_usd") or 0)
    return f"Exchange flow {bias} (${net_flow:+,.0f} net)"


def _volatility_context(price: float, change: float) -> dict[str, Any]:
    abs_change = abs(change)
    if abs_change < 2:
        volatility = "Low"
        vol_warning = "Low volatility environment"
    elif abs_change < 5:
        volatility = "Medium"
        vol_warning = "Moderate swings expected"
    else:
        volatility = "High"
        vol_warning = "Elevated volatility — widen stops"
    return {
        "support": round(price * 0.97, -2),
        "resistance": round(price * 1.03, -2),
        "volatility": volatility,
        "vol_warning": vol_warning,
    }


def _top_opportunity_factors(
    tech: dict[str, Any],
    whale: dict[str, Any],
    sentiment: dict[str, Any],
    onchain_note: str,
) -> list[dict[str, Any]]:
    return [
        {
            "factor": "Technical structure",
            "detail": f"RSI {tech['rsi']} ({_rsi_signal_label(tech['rsi'])}) · {tech['macd_trend']}",
            "source": tech["rsi_source"],
            "weight_hint": "high" if abs(float(tech["rsi"]) - 50) > 12 else "medium",
        },
        {
            "factor": "Whale / institutional flow",
            "detail": whale["whale_alert_text"],
            "source": "CVVD whale detection",
            "weight_hint": "high" if whale["asset_alerts"] else "medium",
        },
        {
            "factor": "Sentiment + on-chain",
            "detail": f"{sentiment['news_label']} news · {onchain_note}",
            "source": "sentiment index + exchange flows",
            "weight_hint": "medium",
        },
    ]


def _explanation_checklist(
    score: int,
    liquidity: str,
    liquidity_score: int,
    whale: dict[str, Any],
    risk: dict[str, Any],
    change: float,
) -> list[dict[str, Any]]:
    whale_value = "present" if whale["asset_alerts"] else "quiet"
    return [
        {"label": "Score", "value": score, "ok": score >= 55},
        {"label": "Liquidity", "value": liquidity, "ok": liquidity_score >= 60},
        {"label": "Whale context", "value": whale_value, "ok": True},
        {"label": "Volatility", "value": risk["volatility"], "ok": abs(change) < 8},
    ]


def _technical_analysis_block(tech: dict[str, Any]) -> dict[str, Any]:
    return {
        "rsi": tech["rsi"],
        "rsi_signal": _rsi_signal_label(tech["rsi"]),
        "rsi_source": tech["rsi_source"],
        "macd_trend": tech["macd_trend"],
        "ema_position": tech["ema_position"],
    }


def _market_context_block(
    quote_volume: float,
    liquidity_score: int,
    liquidity: str,
    trend: str,
    onchain_note: str,
) -> dict[str, Any]:
    return {
        "volume_analysis": f"24h quote volume ${quote_volume:,.0f}",
        "liquidity_score": liquidity_score,
        "liquidity_label": liquidity,
        "trend_direction": trend,
        "onchain_flow": onchain_note,
    }


def _whale_activity_block(whale: dict[str, Any]) -> dict[str, Any]:
    return {
        "flow": whale["whale_flow"],
        "volume_anomaly": whale["volume_anomaly"],
        "alert": whale["whale_alert_text"],
        "cvvd_alerts_count": len(whale["asset_alerts"]),
    }


def _sentiment_block(sentiment: dict[str, Any], hub_ctx: dict[str, Any]) -> dict[str, Any]:
    hub_sentiment = hub_ctx.get("sentiment") or {}
    return {
        "news_sentiment_score": sentiment["news_sentiment"],
        "news_label": sentiment["news_label"],
        "compound_index": round(sentiment["compound"], 3),
        "social_buzz_score": sentiment["social_buzz"],
        "social_label": sentiment["social_label"],
        "fear_greed_index": hub_sentiment.get("fear_greed_index"),
        "fear_greed_label": hub_sentiment.get("fear_greed_label"),
        "coingecko_trending": hub_sentiment.get("coingecko_trending"),
    }


def _oracle_data_hub_block(
    hub_ctx: dict[str, Any],
    hub_score_adj: int,
    hub_reasons: list[str],
    hub_risks: list[str],
) -> dict[str, Any]:
    aggregators = (hub_ctx.get("aggregators") or {}).get("coingecko_global") or {}
    return {
        "enabled": hub_ctx.get("enabled", False),
        "score_adjustment": hub_score_adj,
        "macro_regime": (hub_ctx.get("macro") or {}).get("macro_regime_proxy"),
        "derivatives_bias": (hub_ctx.get("derivatives") or {}).get("derivatives_bias"),
        "geopolitical_headlines": (hub_ctx.get("geo_news") or {}).get("geopolitical_headline_count"),
        "top_headlines": (hub_ctx.get("geo_news") or {}).get("headlines", [])[:5],
        "market_cap_change_24h_pct": aggregators.get("market_cap_change_24h_pct"),
        "hub_reasons": hub_reasons[:3],
        "hub_risks": hub_risks[:3],
        "free_llm_providers": hub_ctx.get("free_llm_providers"),
        "pillars": hub_ctx.get("pillars"),
    }


def _risk_factors_block(risk: dict[str, Any]) -> dict[str, Any]:
    return {
        "support": risk["support"],
        "resistance": risk["resistance"],
        "volatility": risk["volatility"],
        "volatility_warning": risk["vol_warning"],
    }


def _opportunity_explanation_payload(pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": pack["asset"],
        "verdict": pack["verdict"],
        "opportunity_score": pack["score"],
        "simulated": False,
        "top_3_factors": pack["top_factors"],
        "checklist": _explanation_checklist(
            pack["score"],
            pack["liquidity"],
            pack["liquidity_score"],
            pack["whale"],
            pack["risk"],
            pack["change"],
        ),
        "data_sources": [
            "Binance Live API (price + 1h candles)",
            "CVVD Cross-Venue Whale Detection",
            "Rolling Compound Sentiment Index",
            "On-Chain Exchange Flow Tracker",
            "Oracle Data Hub (news, macro, derivatives, aggregators, free LLMs)",
        ],
        "disclaimer": "Not financial advice. Do your own research (DYOR).",
        "technical_analysis": _technical_analysis_block(pack["tech"]),
        "market_context": _market_context_block(
            pack["quote_volume"],
            pack["liquidity_score"],
            pack["liquidity"],
            pack["trend"],
            pack["onchain_note"],
        ),
        "whale_activity": _whale_activity_block(pack["whale"]),
        "sentiment": _sentiment_block(pack["sentiment"], pack["hub_ctx"]),
        "oracle_data_hub": _oracle_data_hub_block(
            pack["hub_ctx"],
            pack["hub_score_adj"],
            pack["hub_reasons"],
            pack["hub_risks"],
        ),
        "risk_factors": _risk_factors_block(pack["risk"]),
        "timestamp": datetime.now(UTC).isoformat(),
    }


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
    from oracle_data_hub import build_hub_context_safe, hub_score_adjustment

    resolved_pair = pair or _normalize_oracle_symbol(asset)[1]
    tech = await _technical_explanation_context(resolved_pair, price, change)
    liquidity, liquidity_score = _liquidity_label(quote_volume)
    trend = _trend_direction(change)
    whale = await _whale_explanation_context(asset, resolved_pair, price, quote_volume)
    sentiment = await _sentiment_explanation_context(asset, score)
    onchain_note = await _onchain_explanation_note(asset)

    hub_ctx = await build_hub_context_safe(asset)
    hub_delta, hub_reasons, hub_risks = hub_score_adjustment(asset, hub_ctx)
    hub_score_adj = round(hub_delta)

    risk = _volatility_context(price, change)

    # Hero #1 — Top-3 factors for <5s understanding (with real sources).
    top_factors = _top_opportunity_factors(tech, whale, sentiment, onchain_note)

    return _opportunity_explanation_payload(
        {
            "asset": asset,
            "verdict": verdict,
            "score": score,
            "top_factors": top_factors,
            "liquidity": liquidity,
            "liquidity_score": liquidity_score,
            "whale": whale,
            "risk": risk,
            "change": change,
            "tech": tech,
            "quote_volume": quote_volume,
            "trend": trend,
            "onchain_note": onchain_note,
            "sentiment": sentiment,
            "hub_ctx": hub_ctx,
            "hub_score_adj": hub_score_adj,
            "hub_reasons": hub_reasons,
            "hub_risks": hub_risks,
        }
    )

# ========== LANDING PAGE (ROOT) ==========
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return render_page(request, "login.html", _footer_ctx())


@app.get("/register")
async def register_alias():
    """Signup URL must not 404 — register is a tab on /login."""
    return RedirectResponse(url="/login?tab=register", status_code=307)


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    return render_page(request, "profile.html", _footer_ctx())


@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    return render_page(request, "reset_password.html", _footer_ctx())


@app.get("/verify-email", response_class=HTMLResponse, responses=COMMON_ERROR_RESPONSES)
async def verify_email_page(request: Request, token: str = ""):
    """Browser entry — verify server-side, then redirect to a fixed profile URL."""
    from fastapi.responses import RedirectResponse

    if not token:
        return templates.TemplateResponse(
            request,
            STR_UTILITY_HTML,
            {
                "page": "verify_email",
                "title": STR_VERIFY_EMAIL,
                "lead": "Missing verification token. Use the link from your email, or resend from Profile.",
            },
        )
    # Allowlist token charset; consume here so Location never embeds user input.
    safe = "".join(ch for ch in str(token) if ch.isalnum() or ch in "-_.")
    if len(safe) < 16:
        return templates.TemplateResponse(
            request,
            STR_UTILITY_HTML,
            {
                "page": "verify_email",
                "title": STR_VERIFY_EMAIL,
                "lead": "Invalid or expired verification link. Resend from Profile.",
            },
        )
    try:
        from database import mark_email_verified
        from identity_service import consume_auth_token

        user_id = await consume_auth_token(safe, "email_verify")
        await mark_email_verified(user_id)
    except ValueError:
        return templates.TemplateResponse(
            request,
            STR_UTILITY_HTML,
            {
                "page": "verify_email",
                "title": STR_VERIFY_EMAIL,
                "lead": "Invalid or expired verification link. Resend from Profile.",
            },
        )
    return RedirectResponse(url="/profile?verified=1", status_code=302)


# Auth routes → api/routers/auth.py
# GTM / platform stats → api/routers/gtm.py
# Telegram → api/routers/telegram.py

@app.post("/api/promo/redeem", responses=COMMON_ERROR_RESPONSES)
async def promo_redeem(data: dict = Body(...), user: dict | None = Depends(optional_user)):
    from auth_service import redeem_promo_code

    if not user:
        raise HTTPException(status_code=401, detail="Login required to redeem promo code")
    try:
        return await redeem_promo_code(user["email"], str(data.get("code") or ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat", responses=COMMON_ERROR_RESPONSES)
async def ai_chat(
    data: dict = Body(...),
    user: dict | None = Depends(require_feature("ai_chat")),
):
    from chat_service import process_chat

    message = str(data.get("message") or data.get("text") or "").strip()
    history = data.get("history") or []
    return await process_chat(message, history=history)


@app.get("/api/journal", responses=COMMON_ERROR_RESPONSES)
async def journal_list(user: dict | None = Depends(optional_user)):
    from auth_service import feature_allowed
    from database import fetch_journal_entries

    if not user or not feature_allowed(user, "journal"):
        raise HTTPException(status_code=401, detail="Login required for Trading Journal")
    return {"entries": await fetch_journal_entries(user["email"])}


@app.post("/api/journal", responses=COMMON_ERROR_RESPONSES)
async def journal_create(data: dict = Body(...), user: dict | None = Depends(optional_user)):
    from auth_service import feature_allowed
    from database import insert_journal_entry

    if not user or not feature_allowed(user, "journal"):
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
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


@app.patch("/api/journal/{entry_id}", responses=COMMON_ERROR_RESPONSES)
async def journal_update(entry_id: int, data: dict = Body(...), user: dict | None = Depends(optional_user)):
    from database import update_journal_entry

    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
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


@app.delete("/api/journal/{entry_id}", responses=COMMON_ERROR_RESPONSES)
async def journal_delete(entry_id: int, user: dict | None = Depends(optional_user)):
    from database import delete_journal_entry

    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
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


@app.post("/api/alerts/telegram/test", responses=COMMON_ERROR_RESPONSES)
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
    if (
        requested
        and not is_admin_user(user)
        and (not profile_chat or str(requested) != str(profile_chat))
    ):
        raise HTTPException(
            status_code=403,
            detail="chat_id must match your profile telegram_chat_id (or omit to use default)",
        )
    chat_id = requested or profile_chat
    return await send_test_telegram(chat_id)


def _footer_ctx() -> dict:
    from site_services import footer_manifest

    return {"footer": footer_manifest()}


# Short in-process cache for the public landing shell (per locale).
# Cuts repeat Jinja work under local Soft Launch / burst refresh.
_landing_html_cache: dict[str, tuple[float, str]] = {}
_LANDING_HTML_CACHE_TTL = float(os.getenv("LANDING_HTML_CACHE_TTL_SEC", "45"))


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    import time

    from i18n_service import resolve_request_lang, template_context

    lang = resolve_request_lang(request)
    now = time.time()
    hit = _landing_html_cache.get(lang)
    if hit and (now - hit[0]) < _LANDING_HTML_CACHE_TTL:
        response = HTMLResponse(hit[1])
        response.set_cookie(
            "bd_lang",
            lang,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            samesite="lax",
            secure=_cookie_secure(request),
        )
        response.headers["X-Landing-Cache"] = "HIT"
        return response

    ctx = template_context(request, _footer_ctx())
    html = templates.get_template("landing.html").render({"request": request, **ctx})
    _landing_html_cache[lang] = (now, html)
    # Bound memory if many locales are probed.
    if len(_landing_html_cache) > 32:
        oldest = sorted(_landing_html_cache.items(), key=lambda kv: kv[1][0])[:8]
        for key, _ in oldest:
            _landing_html_cache.pop(key, None)
    response = HTMLResponse(html)
    response.set_cookie(
        "bd_lang",
        lang,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(request),
    )
    response.headers["X-Landing-Cache"] = "MISS"
    return response


@app.get("/api/i18n/locales")
async def api_i18n_locales():
    from i18n_service import i18n_manifest

    return i18n_manifest()


@app.get("/api/i18n/catalog", responses=COMMON_ERROR_RESPONSES)
async def api_i18n_catalog(lang: str = "en"):
    from i18n_service import catalog_for, locale_meta, normalize_lang

    code = normalize_lang(lang)
    return {"lang": code, "locale": locale_meta(code), "catalog": catalog_for(code)}


@app.get("/favicon.ico", responses=COMMON_ERROR_RESPONSES)
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
        PATH_ORACLE_ACCURACY,
        "/kill-rate",
        "/contradiction-replay",
        "/proof-arena",
        "/since-you-left",
        "/anti-hype",
        "/corpus-passport",
        "/miss-feed",
        "/coverage-honesty",
        "/priority-chain",
        "/zero-tolerance",
        "/emotion-tax",
        "/allocator-receipt",
        "/transfer-intent",
        "/silence-index",
        "/alert-passport",
        "/visibility-cost",
        "/validity-decay",
        "/desk-duel",
        "/trust-debt",
        "/unique-ten",
        "/institutional",
        "/model-card",
        "/d5-honesty",
        "/b2b/committee-one-pager",
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
    return render_page(request, "dashboard.html", _footer_ctx())


@app.get("/discipline-mirror", response_class=HTMLResponse)
async def discipline_mirror_page(request: Request):
    """Private Discipline Mirror UI — never public ledger."""
    return render_page(request, "discipline.html", _footer_ctx())


@app.get("/kill-rate", response_class=HTMLResponse)
async def kill_rate_page(request: Request):
    return render_page(request, "kill_rate.html", _footer_ctx())


@app.get("/contradiction-replay", response_class=HTMLResponse)
async def contradiction_replay_page(request: Request):
    return render_page(request, "contradiction_replay.html", _footer_ctx())


@app.get("/proof-arena", response_class=HTMLResponse)
async def proof_arena_page(request: Request):
    return render_page(request, "proof_arena.html", _footer_ctx())


@app.get("/b2b/committee-one-pager", response_class=HTMLResponse)
async def committee_one_pager_page(request: Request):
    return render_page(request, "committee_one_pager.html", _footer_ctx())


@app.get("/since-you-left", response_class=HTMLResponse)
async def since_you_left_page(request: Request):
    return render_page(request, "since_you_left.html", _footer_ctx())


@app.get("/anti-hype", response_class=HTMLResponse)
async def anti_hype_page(request: Request):
    return render_page(request, "anti_hype.html", _footer_ctx())


@app.get("/corpus-passport", response_class=HTMLResponse)
async def corpus_passport_page(request: Request):
    return render_page(request, "corpus_passport.html", _footer_ctx())


@app.get("/miss-feed", response_class=HTMLResponse)
async def miss_feed_page(request: Request):
    return render_page(request, "miss_feed.html", _footer_ctx())


@app.get("/coverage-honesty", response_class=HTMLResponse)
async def coverage_honesty_page(request: Request):
    return render_page(request, "coverage_honesty.html", _footer_ctx())


@app.get("/priority-chain", response_class=HTMLResponse)
async def priority_chain_page(request: Request):
    return render_page(request, "priority_chain.html", _footer_ctx())


@app.get("/zero-tolerance", response_class=HTMLResponse)
async def zero_tolerance_page(request: Request):
    return render_page(request, "zero_tolerance.html", _footer_ctx())


@app.get("/emotion-tax", response_class=HTMLResponse)
async def emotion_tax_page(request: Request):
    return render_page(request, "emotion_tax.html", _footer_ctx())


@app.get("/allocator-receipt", response_class=HTMLResponse)
async def allocator_receipt_page(request: Request):
    return render_page(request, "allocator_receipt.html", _footer_ctx())


@app.get("/transfer-intent", response_class=HTMLResponse)
async def transfer_intent_page(request: Request):
    return render_page(request, "transfer_intent.html", _footer_ctx())


@app.get("/silence-index", response_class=HTMLResponse)
async def silence_index_page(request: Request):
    return render_page(request, "silence_index.html", _footer_ctx())


@app.get("/alert-passport", response_class=HTMLResponse)
async def alert_passport_page(request: Request):
    return render_page(request, "alert_passport.html", _footer_ctx())


@app.get("/visibility-cost", response_class=HTMLResponse)
async def visibility_cost_page(request: Request):
    return render_page(request, "visibility_cost.html", _footer_ctx())


@app.get("/validity-decay", response_class=HTMLResponse)
async def validity_decay_page(request: Request):
    return render_page(request, "validity_decay.html", _footer_ctx())


@app.get("/desk-duel", response_class=HTMLResponse)
async def desk_duel_page(request: Request):
    return render_page(request, "desk_duel.html", _footer_ctx())


@app.get("/trust-debt", response_class=HTMLResponse)
async def trust_debt_page(request: Request):
    return render_page(request, "trust_debt.html", _footer_ctx())


@app.get("/unique-ten", response_class=HTMLResponse)
async def unique_ten_page(request: Request):
    return render_page(request, "unique_ten.html", _footer_ctx())


@app.get("/institutional", response_class=HTMLResponse)
async def institutional_hub_page(request: Request):
    return render_page(request, "institutional.html", _footer_ctx())


@app.get("/cap646", response_class=HTMLResponse)
async def cap646_hub_page(request: Request):
    return render_page(request, "cap646_hub.html", _footer_ctx())


@app.get("/model-card", response_class=HTMLResponse)
async def model_card_page(request: Request):
    return render_page(request, "model_card.html", _footer_ctx())


@app.get("/d5-honesty", response_class=HTMLResponse)
async def d5_honesty_page(request: Request):
    return render_page(request, "d5_honesty.html", _footer_ctx())


@app.get("/api/public/d5-honesty")
async def api_public_d5_honesty():
    from d5_regime_honesty import build_d5_honesty_board

    return build_d5_honesty_board()


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

    return RedirectResponse(url=PATH_ORACLE_ACCURACY, status_code=307)


@app.get("/docs", response_class=HTMLResponse)
async def public_developer_docs_page(request: Request):
    """Limited public developer docs (evidence/read APIs) — not full execution surface."""
    from public_api_docs import public_docs_manifest

    return render_page(
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



def _parse_trust_pulse_previous_factors(previous_factors: str | None) -> list[dict[str, str]] | None:
    """Parse optional previous_factors JSON for Trust Pulse continuity."""
    if not previous_factors:
        return None
    import json as _json

    try:
        parsed = _json.loads(previous_factors)
    except (TypeError, ValueError):
        return None
    if not isinstance(parsed, list):
        return None
    factors: list[dict[str, str]] = []
    for f in parsed[:5]:
        if isinstance(f, dict):
            factors.append(
                {
                    "factor": str(f.get("factor") or "")[:120],
                    "detail": str(f.get("detail") or "")[:200],
                    "source": str(f.get("source") or "")[:80],
                }
            )
        else:
            factors.append({"factor": str(f)[:120], "detail": "", "source": ""})
    return factors


@app.get("/api/trust-pulse", responses=COMMON_ERROR_RESPONSES)
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
    from trust_pulse import build_trust_pulse

    tier = (user or {}).get("tier") or "free"
    try:
        return await build_trust_pulse(
            symbol,
            tier=str(tier),
            ux_mode=ux_mode,
            lang=lang,
            previous_action=previous_action,
            previous_seen_at=previous_seen_at,
            previous_factors=_parse_trust_pulse_previous_factors(previous_factors),
            force_refresh=force,
            # Soft cache miss may persist once; force only refreshes identity — no spam
            persist=None,
        )
    except ValueError as exc:
        # Do not echo exception text to clients (CodeQL information exposure).
        raise HTTPException(
            status_code=404, detail="Trust Pulse unavailable for this symbol"
        ) from exc


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
    return render_page(request, "platform.html", _footer_ctx())


@app.get("/capabilities", response_class=HTMLResponse)
async def capabilities_page(request: Request):
    from trust_os import trust_os_manifest

    manifest = trust_os_manifest()
    return templates.TemplateResponse(
        request,
        STR_UTILITY_HTML,
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
        STR_UTILITY_HTML,
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
        STR_UTILITY_HTML,
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
        STR_UTILITY_HTML,
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
        STR_UTILITY_HTML,
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
        STR_UTILITY_HTML,
        {
            "page": "faq",
            "title": "FAQ",
            "lead": "Straight answers on Proof Pass, Decision Pro, Decision Desk, sharing, and AI Chat.",
            "faq": FAQ_ITEMS,
            **_footer_ctx(),
        },
    )


@app.get("/how-it-works", response_class=HTMLResponse)
async def how_it_works_page(request: Request):
    from site_services import HOW_IT_WORKS_STEPS

    return templates.TemplateResponse(
        request,
        STR_UTILITY_HTML,
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
        STR_UTILITY_HTML,
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
        STR_UTILITY_HTML,
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
        STR_UTILITY_HTML,
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
        STR_UTILITY_HTML,
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
        STR_UTILITY_HTML,
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


@app.post("/api/feedback", responses=COMMON_ERROR_RESPONSES)
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
async def _oracle_explain_market(symbol: str) -> tuple[str, str, dict]:
    asset, pair = _normalize_oracle_symbol(symbol)
    market = await _fetch_binance_ticker(pair)
    if market is None:
        raise HTTPException(status_code=404, detail=f"Symbol {asset} not found.")
    return asset, pair, market


async def _attach_explain_forecast(payload: dict, asset: str, price: float, score: int, verdict: str, change: float, quote_volume: float) -> None:
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


def _attach_explain_admin_fields(payload: dict, unified: dict, user: dict | None) -> None:
    payload["unified_engine"] = unified.get("engine")
    payload["market_regime"] = unified.get("market_regime")
    if user and is_admin_user(user):
        payload["modal_breakdown"] = unified.get("modal_breakdown")
    else:
        payload["weights_protected"] = True


def _sanitize_explain_payload(payload: dict, asset: str, user: dict | None) -> dict:
    from security_sanitize import sanitize_explanation_payload, sanitize_oracle_payload

    if user and is_admin_user(user):
        return sanitize_explanation_payload(payload)
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
    return payload


def _queue_oracle_explain_tasks(
    background_tasks: BackgroundTasks,
    *,
    asset: str,
    price: float,
    verdict: str,
    score: int,
    confidence: float,
    user: dict | None,
) -> None:
    background_tasks.add_task(
        _log_oracle_prediction,
        {
            "symbol": asset,
            "asset": asset,
            "price": price,
            "verdict": verdict,
            "opportunity_score": score,
            "confidence": confidence,
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


@app.get("/oracle/{symbol}/explain", responses=COMMON_ERROR_RESPONSES)
async def oracle_explain(
    symbol: str,
    background_tasks: BackgroundTasks,
    user: dict | None = Depends(optional_user),
) -> JSONResponse:
    asset, pair, market = await _oracle_explain_market(symbol)
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
    _attach_explain_admin_fields(payload, unified, user)
    payload["opportunity_score"] = score
    payload["verdict"] = verdict
    await _attach_explain_forecast(payload, asset, price, score, verdict, change, quote_volume)
    payload = _sanitize_explain_payload(payload, asset, user)
    _queue_oracle_explain_tasks(
        background_tasks,
        asset=asset,
        price=price,
        verdict=verdict,
        score=score,
        confidence=payload.get("confidence") or _oracle_confidence(score, change, quote_volume),
        user=user,
    )
    return JSONResponse(payload)


async def _compute_oracle_quick_payload(
    asset: str,
    pair: str,
    lang: str,
    ux_mode: str,
) -> dict:
    from live_book_hub import get_best_price

    from live_book_hub import get_best_price, is_quote_fresh

    row = get_best_price("binance", f"{asset}/USDT")
    market = _quick_ws_market(row) if row and is_quote_fresh("binance", f"{asset}/USDT") else None
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
    decision_sentence = _quick_decision_sentence(lang, decision_action, asset, score, action)
    return _quick_payload(
        asset,
        price,
        change,
        verdict,
        decision_action,
        decision_sentence,
        score,
        action,
        sentiment,
        ux_mode,
        lang,
    )


def _quick_ws_market(row: dict | None) -> dict | None:
    if not row or not row.get("mid"):
        return None
    return {
        "price": float(row["mid"]),
        "change_24h": 0.0,
        "volume": 0.0,
        "quote_volume": 0.0,
        "source": "websocket_live",
    }


def _quick_decision_sentence(
    lang: str,
    decision_action: str,
    asset: str,
    score: int,
    action: str,
) -> str:
    try:
        from i18n_service import decision_sentence as _dec

        return _dec(lang, decision_action, asset, score)
    except Exception:
        return (
            f"{decision_action} on {asset} — score {score}. "
            f"Analytical summary (not advice): {action}"
        )


def _quick_payload(
    asset: str,
    price: float,
    change: float,
    verdict: str,
    decision_action: str,
    decision_sentence: str,
    score: int,
    action: str,
    sentiment: str,
    ux_mode: str,
    lang: str,
) -> dict:
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


def _queue_oracle_quick_tasks(background_tasks: BackgroundTasks, asset: str, payload: dict) -> None:
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


def _attach_quick_certificate(payload: dict) -> None:
    try:
        from decision_certificate import build_decision_certificate, compliance_footer_block

        payload.setdefault("tier", "free")
        # Enrich quick payload so certificate carries advisory truth + half-life
        # (full multimodal oracle already attaches these via decision_enrichment).
        if "net_edge_truth" not in payload or "opportunity_half_life" not in payload:
            try:
                from decision_enrichment import _attach_half_life, _attach_net_edge_truth

                asset = str(payload.get("symbol") or payload.get("asset") or "BTC")
                score = float(payload.get("opportunity_score") or 0)
                verdict = str(payload.get("verdict") or payload.get("decision_action") or "WAIT")
                if "net_edge_truth" not in payload:
                    _attach_net_edge_truth(payload, asset, score, verdict, 0.0)
                if "opportunity_half_life" not in payload:
                    _attach_half_life(payload, asset)
            except Exception:
                pass
        # Explicit I DON'T KNOW token when score is in the dead-zone (no edge).
        score_i = int(payload.get("opportunity_score") or 0)
        if 45 <= score_i <= 55 and not payload.get("idk_token"):
            payload["idk_token"] = "I_DONT_KNOW"
            payload["idk_reason"] = "opportunity_score_dead_zone"
            if str(payload.get("decision_action") or "").upper() in {"WAIT", "HOLD", ""}:
                payload["decision_action"] = "I_DONT_KNOW"
                payload["decision_sentence"] = (
                    f"I DON'T KNOW on {payload.get('symbol') or 'asset'} — "
                    f"score {score_i} is inside the dead-zone; no certified edge."
                )
                payload["oracle"] = payload["decision_sentence"]
        payload["decision_certificate"] = build_decision_certificate(payload)
        payload["compliance_footer"] = compliance_footer_block(
            surface="single_sentence_oracle_quick",
            trust_basis="public_accuracy_ledger + quick_rules_engine",
        )
    except Exception:
        pass


def _attach_quick_freshness(payload: dict, asset: str) -> dict:
    try:
        from data_freshness import attach_oracle_freshness

        return attach_oracle_freshness({**payload, "asset": asset})
    except Exception:
        return payload


@app.get("/oracle/{symbol}/quick", responses=COMMON_ERROR_RESPONSES)
async def oracle_quick(
    symbol: str,
    background_tasks: BackgroundTasks,
    lang: str = "en",
    ux_mode: str = "beginner",
) -> JSONResponse:
    """Instant verdict + ACTION line — viral-hardened (cache + semaphore)."""
    import time

    from viral_capacity import quick_cache_get, quick_cache_set, run_oracle_bounded

    t0 = time.perf_counter()
    asset, pair = _normalize_oracle_symbol(symbol)
    cached = quick_cache_get(asset, lang, ux_mode)
    if cached is not None:
        cached["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return JSONResponse(cached)

    try:
        payload = await run_oracle_bounded(
            lambda: _compute_oracle_quick_payload(asset, pair, lang, ux_mode)
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("oracle_quick failed")
        raise HTTPException(status_code=502, detail="Oracle upstream unavailable") from exc
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    payload["latency_ms"] = latency_ms
    payload["meets_latency_target"] = latency_ms <= 100

    _queue_oracle_quick_tasks(background_tasks, asset, payload)
    _attach_quick_certificate(payload)
    payload = _attach_quick_freshness(payload, asset)
    from security_sanitize import sanitize_oracle_payload

    clean = sanitize_oracle_payload(payload)
    quick_cache_set(asset, lang, ux_mode, clean)
    return JSONResponse(clean)


def _reserved_oracle_response(symbol: str, request: Request) -> Any | None:
    if symbol.strip().lower() == "accuracy":
        return render_page(request, "oracle_accuracy.html", _footer_ctx())
    blocked = _require_terms_ack_or_403(request)
    if blocked is not None:
        return blocked
    return None


async def _enforce_oracle_quota(user: dict | None) -> None:
    from auth_service import check_oracle_quota

    allowed, message = await check_oracle_quota(user)
    if allowed:
        return
    raise HTTPException(
        status_code=403,
        detail={
            "error": "quota_exceeded",
            "message": message,
            "upgrade_url": PATH_CREATE_CHECKOUT_SESSION_TIER_PRO,
        },
    )


async def _oracle_market_inputs(symbol: str) -> tuple[str, str, dict[str, Any], float, float, float, float]:
    asset, pair = _normalize_oracle_symbol(symbol)
    market = await _fetch_binance_ticker(pair)
    if market is None:
        raise HTTPException(status_code=404, detail=f"Symbol {asset} not found.")
    price = market["price"]
    volume = market["volume"]
    quote_volume = market["quote_volume"] or (volume * price)
    change = market["change_24h"]
    return asset, pair, market, price, volume, quote_volume, change


async def _fetch_whale_alert_safe(asset: str, pair: str, price: float) -> Any | None:
    try:
        return await _fetch_cvvd_whale_alert(asset, pair, price)
    except Exception:
        logger.exception("Whale alert fetch failed")
        return None


async def _compute_unified_oracle_safe(
    asset: str,
    price: float,
    quote_volume: float,
    change: float,
) -> dict[str, Any]:
    try:
        from oracle_unified import compute_unified_oracle

        return await compute_unified_oracle(asset, price, quote_volume, change)
    except Exception:
        logger.exception("Unified oracle engine unavailable — falling back to technical score")
        from market_context import oracle_score

        return {
            "opportunity_score": oracle_score(quote_volume, change),
            "verdict": None,
            "confidence": None,
            "engine": "technical_fallback_v1",
        }


async def _build_primary_oracle_payload(
    asset: str,
    pair: str,
    price: float,
    volume: float,
    quote_volume: float,
    change: float,
) -> dict[str, Any]:
    whale_alert = await _fetch_whale_alert_safe(asset, pair, price)
    unified = await _compute_unified_oracle_safe(asset, price, quote_volume, change)
    payload = _build_full_oracle_response(
        asset,
        price,
        volume,
        quote_volume,
        change,
        whale_alert=whale_alert,
        unified=unified,
    )
    payload = await _attach_oracle_explanation_safe(payload, asset, pair, price, quote_volume, change)
    return await _enrich_oracle_forecast_safe(payload)


async def _attach_oracle_explanation_safe(
    payload: dict[str, Any],
    asset: str,
    pair: str,
    price: float,
    quote_volume: float,
    change: float,
) -> dict[str, Any]:
    try:
        payload["explanation"] = await _build_opportunity_explanation(
            asset,
            price,
            change,
            quote_volume,
            payload["opportunity_score"],
            payload["verdict"],
            pair=pair,
        )
    except Exception:
        logger.exception("Oracle explanation unavailable")
        payload["explanation"] = {"summary": "Technical oracle response (extended explanation unavailable)."}
    return payload


async def _enrich_oracle_forecast_safe(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        from forecast_engine import enrich_oracle_payload

        return await enrich_oracle_payload(payload)
    except Exception:
        logger.exception("Oracle forecast enrichment unavailable")
        return payload


def _enrich_oracle_decision_safe(payload: dict[str, Any], ux_mode: str, lang: str) -> dict[str, Any]:
    try:
        from decision_enrichment import enrich_oracle_decision
        from ux_mode import normalize_lang, normalize_ux_mode

        return enrich_oracle_decision(
            payload,
            ux_mode=normalize_ux_mode(ux_mode),
            lang=normalize_lang(lang),
            register_signal=True,
        )
    except Exception:
        logger.exception("Constitution decision enrichment unavailable")
        return payload


async def _attach_oracle_prediction_proof(payload: dict[str, Any], asset: str) -> dict[str, Any]:
    try:
        prediction_id = await _log_oracle_prediction(payload)
    except Exception:
        logger.exception("Oracle prediction_id attach failed")
        return payload
    if prediction_id is None:
        return payload
    payload["prediction_id"] = prediction_id
    _attach_signal_registry_prediction(payload, asset, prediction_id)
    _attach_chain_hash_proof(payload, prediction_id)
    return payload


def _attach_signal_registry_prediction(payload: dict[str, Any], asset: str, prediction_id: Any) -> None:
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
            payload["signal_registry"] = _signal_registry_payload(linked)
    except Exception:
        logger.debug("signal registry prediction_id attach failed", exc_info=True)


def _signal_registry_payload(linked: dict[str, Any]) -> dict[str, Any]:
    return {
        "signal_id": linked.get("signal_id"),
        "prediction_id": linked.get("prediction_id"),
        "features_hash": linked.get("features_hash"),
        "label": linked.get("label"),
        "definition": linked.get("definition"),
        "source": linked.get("source"),
        "weight": linked.get("weight"),
        "performance": linked.get("performance"),
    }


def _attach_chain_hash_proof(payload: dict[str, Any], prediction_id: Any) -> None:
    try:
        from oracle_audit_chain import chain_summary

        recent = (chain_summary(limit=8) or {}).get("recent_records") or []
        for entry in reversed(recent):
            if str(entry.get("prediction_id")) == str(prediction_id):
                payload["chain_hash"] = entry.get("chain_hash")
                payload["proof"] = {
                    "prediction_id": prediction_id,
                    "chain_hash": entry.get("chain_hash"),
                    "public_page": PATH_ORACLE_ACCURACY,
                }
                break
    except Exception:
        logger.debug("chain_hash attach failed", exc_info=True)


def _attach_oracle_certificate(payload: dict[str, Any], user: dict | None) -> None:
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


def _attach_oracle_scenarios_safe(payload: dict[str, Any]) -> None:
    try:
        from oracle_scenarios import build_oracle_scenarios

        payload["scenarios"] = build_oracle_scenarios(payload)
    except Exception:
        logger.debug("Oracle scenarios attach failed", exc_info=True)


def _attach_oqs_why_safe(payload: dict[str, Any]) -> None:
    try:
        from heroes_quality import build_oqs_why_block

        payload["oqs_why"] = build_oqs_why_block(payload)
        _copy_oqs_factors_to_explanation(payload)
    except Exception:
        logger.debug("OQS why block attach failed", exc_info=True)


def _copy_oqs_factors_to_explanation(payload: dict[str, Any]) -> None:
    top_factors = (payload.get("oqs_why") or {}).get("top_3_factors")
    if not top_factors:
        return
    expl = payload.get("explanation") or {}
    if isinstance(expl, dict) and not expl.get("top_3_factors"):
        payload["explanation"] = {**expl, "top_3_factors": top_factors}


async def _dispatch_oracle_act_alert_safe(payload: dict[str, Any], asset: str) -> None:
    if str(payload.get("decision_action") or "").upper() != "ACT":
        return
    try:
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


def _queue_oracle_behavior_task(
    background_tasks: BackgroundTasks,
    user: dict | None,
    asset: str,
    payload: dict[str, Any],
) -> None:
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


def _increment_oracle_queries_metric() -> None:
    try:
        from observability import increment_metric

        increment_metric("oracle_queries_total")
    except Exception:
        pass


def _attach_oracle_freshness_safe(payload: dict[str, Any], asset: str) -> dict[str, Any]:
    try:
        from data_freshness import attach_oracle_freshness

        return attach_oracle_freshness({**payload, "asset": asset})
    except Exception:
        logger.debug("Oracle freshness attach failed", exc_info=True)
        return payload


def _apply_zero_tolerance_safe(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        from zero_tolerance import apply_zero_tolerance

        return apply_zero_tolerance(payload)
    except Exception:
        logger.debug("Zero-tolerance attach failed", exc_info=True)
        return payload


def _sanitize_oracle_response(payload: dict[str, Any], user: dict | None) -> dict[str, Any]:
    from regulatory_compliance_guard import apply_regulatory_compliance
    from security_sanitize import sanitize_oracle_payload

    if user and is_admin_user(user):
        return apply_regulatory_compliance(payload)
    return sanitize_oracle_payload(payload)


@app.get("/oracle/{symbol}", responses=COMMON_ERROR_RESPONSES)
async def oracle(
    symbol: str,
    request: Request,
    background_tasks: BackgroundTasks,
    user: dict | None = Depends(optional_user),
    ux_mode: str = "beginner",
    lang: str = "en",
):
    reserved = _reserved_oracle_response(symbol, request)
    if reserved is not None:
        return reserved

    try:
        await _enforce_oracle_quota(user)
        asset, pair, _market, price, volume, quote_volume, change = await _oracle_market_inputs(symbol)
        payload = await _build_primary_oracle_payload(
            asset,
            pair,
            price,
            volume,
            quote_volume,
            change,
        )
        payload = _enrich_oracle_decision_safe(payload, ux_mode, lang)
        payload = await _attach_oracle_prediction_proof(payload, asset)
        _attach_oracle_certificate(payload, user)
        _attach_oracle_scenarios_safe(payload)
        _attach_oqs_why_safe(payload)
        await _dispatch_oracle_act_alert_safe(payload, asset)
        _queue_oracle_behavior_task(background_tasks, user, asset, payload)
        _increment_oracle_queries_metric()
        payload = _attach_oracle_freshness_safe(payload, asset)
        payload = _apply_zero_tolerance_safe(payload)
        try:
            cleaned = _sanitize_oracle_response(payload, user)
        except Exception:
            logger.exception("oracle sanitize failed")
            cleaned = payload
        return JSONResponse(cleaned)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("oracle primary failed")
        raise HTTPException(status_code=502, detail="Oracle upstream unavailable") from exc


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
    from sentiment_engine import build_sentiment_context_safe, score_live_headlines_overview

    assets = [item.upper() for item in config.WHITELIST_ASSETS]
    ctx = await build_sentiment_context_safe(assets)
    indices = ctx.get("sentiment_compound_index") or {}
    live = await score_live_headlines_overview(assets)
    rows = []
    for asset in assets:
        compound = float(indices.get(asset, 0.0))
        live_row = (live.get("by_asset") or {}).get(asset) or {}
        if abs(compound) < 1e-9 and live_row.get("compound_index") is not None:
            compound = float(live_row.get("compound_index") or 0.0)
        score = _compound_to_score(compound)
        rows.append(
            {
                "asset": asset,
                "compound_index": round(compound, 3),
                "sentiment_score": score,
                "label": _compound_label(compound),
                "sector": _sector_for_asset(asset),
                "live_headlines": live_row.get("headline_count") or 0,
                "analyzer": live_row.get("analyzer"),
            }
        )
    rows.sort(key=lambda x: x["sentiment_score"], reverse=True)
    non_neutral = sum(1 for r in rows if r["sentiment_score"] != 50)
    return {
        "assets": rows,
        "data_source": live.get("data_source") or "Rolling Compound Sentiment Index",
        "live_refresh": bool(live.get("ok")),
        "non_neutral_count": non_neutral,
        "stub": non_neutral == 0,
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
async def universe_phase_b_probe(symbol: str = STR_BTC_USDT):
    from ccxt_market_fetcher import probe_phase_b_exchanges

    return await probe_phase_b_exchanges(sample_symbol=symbol)


@app.get("/api/universe/phase-b2/probe")
async def universe_phase_b2_probe(symbol: str = STR_BTC_USDT):
    from coingecko_cex_fetcher import probe_coingecko_exchanges

    return await probe_coingecko_exchanges(sample_symbol=symbol)


@app.get("/api/universe/phase-c/probe")
async def universe_phase_c_probe(symbol: str = STR_BTC_USDT):
    from dex_fetcher import probe_dex_venues

    return await probe_dex_venues(sample_symbol=symbol)


@app.get("/api/universe/phase-d/probe")
async def universe_phase_d_probe(symbol: str = STR_BTC_USDT):
    from perp_dex_fetcher import probe_perp_dex_venues

    return await probe_perp_dex_venues(sample_symbol=symbol)


@app.get("/api/universe/full-probe")
async def universe_full_probe(symbol: str = STR_BTC_USDT):
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
    try:
        from platform_universe import build_manifest_universe_block, compute_universe_coverage
        from universe_rollout import live_rollout_status, rollout_summary_json

        return {
            "ok": True,
            "coverage": await compute_universe_coverage(),
            "registry": build_manifest_universe_block(),
            "rollout": rollout_summary_json(),
            "live": await live_rollout_status(),
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": type(exc).__name__,
            "timestamp": datetime.now(UTC).isoformat(),
        }


@app.post("/api/universe/activate-full")
async def universe_activate_full(_admin: dict = Depends(require_admin)):
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
    try:
        return await _ingestion_status_body()
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}


async def _ingestion_status_body():
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

@app.get(PATH_ORACLE_ACCURACY, response_class=HTMLResponse)
@app.get("/oracle/accuracy", response_class=HTMLResponse)
async def oracle_accuracy_page(request: Request):
    # Public ledger must stay visible without an ack wall (hits + misses).
    return render_page(request, "oracle_accuracy.html", _footer_ctx())


# ML experience routes → api/routers/oracle.py

@app.get("/api/b2b/feed", responses=COMMON_ERROR_RESPONSES)
async def b2b_feed(x_api_key: str = Header(..., alias="X-API-Key")):
    from whale_tracker import InstitutionalDataExporter

    exporter = InstitutionalDataExporter()
    try:
        return await exporter.export_institutional_feed(provided_key=x_api_key)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=public_error(exc, fallback=STR_INVALID_B2B_API_KEY)) from exc


@app.get("/api/b2b/demo", responses=COMMON_ERROR_RESPONSES)
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
        "pricing_usd_monthly": 49,
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
        await websocket.close(code=1008, reason=STR_INVALID_B2B_API_KEY)
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
            "demo_key": (config.B2B_DEMO_API_KEY if os.getenv("EXPOSE_B2B_DEMO_KEY", "").lower() in {"1", "true", "yes"} else "contact-sales"),
            "feed_version": config.B2B_FEED_VERSION,
            **_footer_ctx(),
        },
    )



@app.post("/api/legal/ack-terms")
async def api_legal_ack_terms():
    """Record Terms acknowledgement (Layer-4 legal shield) for anonymous visitors."""
    resp = JSONResponse({"ok": True, "acked": True})
    resp.set_cookie(
        "bd_terms_ack",
        "1",
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(),
    )
    return resp


@app.get("/system/info", responses=COMMON_ERROR_RESPONSES)
async def system_info(request: Request, user: dict | None = Depends(optional_user)):
    """Classified system surface — requires Terms ack; auth required for payload."""
    blocked = _require_terms_ack_or_403(request)
    if blocked is not None:
        return blocked
    if not user:
        return JSONResponse({"ok": False, "error": "auth_required"}, status_code=401)
    return {
        "ok": True,
        "classification": "internal",
        "product": "BLACKDARK Trust OS",
        "disclaimer": "Not financial advice. Decision evidence only. Four-layer legal shield applies.",
        "user_id": user.get("id"),
        "tier": user.get("tier"),
    }


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


@app.get("/terms", response_class=HTMLResponse, responses=COMMON_ERROR_RESPONSES)
async def terms_page(request: Request):
    return _legal_page(request, "terms")


@app.get("/privacy", response_class=HTMLResponse, responses=COMMON_ERROR_RESPONSES)
async def privacy_page(request: Request):
    return _legal_page(request, "privacy")


@app.get("/disclaimer", response_class=HTMLResponse, responses=COMMON_ERROR_RESPONSES)
async def disclaimer_page(request: Request):
    return _legal_page(request, "disclaimer")


@app.get("/refund", response_class=HTMLResponse, responses=COMMON_ERROR_RESPONSES)
async def refund_page(request: Request):
    return _legal_page(request, "refund")


@app.get("/sla", response_class=HTMLResponse, responses=COMMON_ERROR_RESPONSES)
async def sla_page(request: Request):
    return _legal_page(request, "sla")


@app.get("/msa", response_class=HTMLResponse, responses=COMMON_ERROR_RESPONSES)
async def msa_page(request: Request):
    return _legal_page(request, "msa")


@app.get("/cookies", response_class=HTMLResponse, responses=COMMON_ERROR_RESPONSES)
async def cookies_page(request: Request):
    return _legal_page(request, "cookies")


@app.get("/api/b2b/demo/proposal", responses=COMMON_ERROR_RESPONSES)
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


@app.get("/api/b2b/proposal", responses=COMMON_ERROR_RESPONSES)
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
        raise HTTPException(status_code=403, detail=STR_INVALID_B2B_API_KEY) from exc


# Arbitrage API routes → api/routers/arbitrage.py

@app.post("/api/simulate/trade", responses=COMMON_ERROR_RESPONSES)
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


@app.get("/api/simulate/history", responses=COMMON_ERROR_RESPONSES)
async def simulate_history(
    limit: int = 15,
    _user: dict | None = Depends(require_feature("research_lab")),
):
    from database import fetch_simulation_logs

    return {"simulations": await fetch_simulation_logs(limit=limit)}


@app.post("/api/alerts/subscribe", responses=COMMON_ERROR_RESPONSES)
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
                "upgrade_url": PATH_CREATE_CHECKOUT_SESSION_TIER_PRO,
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


@app.get("/api/alerts/inbox", responses=COMMON_ERROR_RESPONSES)
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


@app.post("/api/alerts/inbox/{alert_id}/read", responses=COMMON_ERROR_RESPONSES)
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


@app.get("/api/execution/keys/status", responses=COMMON_ERROR_RESPONSES)
async def execution_keys_status_api(_user: dict = Depends(require_whale)):
    from execution_keys import execution_keys_status

    status = execution_keys_status()
    status.pop("keys_file", None)
    return status


@app.post("/api/execution/keys/activate", responses=COMMON_ERROR_RESPONSES)
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


@app.post("/api/execution/order", responses=COMMON_ERROR_RESPONSES)
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


@app.get("/api/research/asset/{symbol}", responses=COMMON_ERROR_RESPONSES)
async def research_asset(symbol: str, notional: float = 10_000):
    from research_lab import compute_financial_models

    return await compute_financial_models(symbol, notional=notional)


@app.get("/api/research/export", responses=COMMON_ERROR_RESPONSES)
async def research_export(x_api_key: str = Header(..., alias="X-API-Key")):
    from research_lab import export_signed_research

    try:
        return await export_signed_research(x_api_key)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=STR_INVALID_B2B_API_KEY) from exc



@app.post("/api/voice/command", responses=COMMON_ERROR_RESPONSES)
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

    try:
        return await build_weekly_report(persist=persist)
    except Exception as exc:
        logger.exception("weekly report failed")
        raise HTTPException(status_code=502, detail="Weekly report unavailable") from exc


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

    try:
        return await build_daily_report(persist=persist)
    except Exception as exc:
        logger.exception("daily report failed")
        raise HTTPException(status_code=502, detail="Daily report unavailable") from exc


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


@app.get("/api/retention/status", responses=COMMON_ERROR_RESPONSES)
async def api_retention_status(user: dict | None = Depends(optional_user)):
    from database import fetch_active_subscription_for_email
    from retention_service import build_retention_status

    sub = None
    if user:
        sub = await fetch_active_subscription_for_email(user["email"])
    return await build_retention_status(user, sub)


@app.get("/api/subscriber/value", responses=COMMON_ERROR_RESPONSES)
async def api_subscriber_value(user: dict | None = Depends(optional_user)):
    from retention_service import build_subscriber_value_digest

    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    tier = str(user.get("tier") or "free")
    if tier == "free":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "upgrade_required",
                "message": "Subscriber value digest requires Pro or Whale.",
                "upgrade_url": PATH_CREATE_CHECKOUT_SESSION_TIER_PRO,
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

    return hot_tier_status()


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
    from postgres_backend import use_postgres
    from security_auth import login_rate_limit_backend
    from security_posture import security_posture_report

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


@app.get("/api/options/oms")
async def api_options_oms_list(
    user: dict | None = Depends(optional_user),
):
    from paper_options_oms import list_paper_orders

    email = str((user or {}).get("email") or "")
    return list_paper_orders(user_email=email or None)


@app.post("/api/options/oms", responses=COMMON_ERROR_RESPONSES)
async def api_options_oms_create(
    body: dict = Body(...),
    user: dict | None = Depends(require_feature("research_lab")),
):
    from paper_options_oms import create_paper_order

    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    return create_paper_order(
        user_email=str(user["email"]),
        asset=str(body.get("asset") or "BTC"),
        side=str(body.get("side") or "buy"),
        option_type=str(body.get("option_type") or body.get("type") or "call"),
        quantity=float(body.get("quantity") or 1),
        limit_price=float(body["limit_price"]) if body.get("limit_price") is not None else None,
    )


@app.get("/api/oms/status")
async def api_oms_status():
    from paper_options_oms import oms_status

    return oms_status()


@app.get("/api/b2b/white-label")
async def api_b2b_white_label():
    from b2b_packaging_api import white_label_status

    return white_label_status()


@app.get("/api/b2b/super-terminal")
async def api_b2b_super_terminal():
    from b2b_packaging_api import super_terminal_status

    return super_terminal_status()


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


@app.get("/api/build-info", responses=COMMON_ERROR_RESPONSES)
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

@app.post("/portfolio/analyze", responses=COMMON_ERROR_RESPONSES)
async def portfolio_analyze(
    payload: list | dict = Body(...),
    _user: dict | None = Depends(require_feature("portfolio_ai")),
):
    if isinstance(payload, dict):
        assets = payload.get("holdings") or payload.get("assets") or payload.get("positions") or []
    else:
        assets = payload
    if not isinstance(assets, list) or not assets:
        raise HTTPException(status_code=400, detail="No assets provided")
    return await _analyze_portfolio_holdings(assets)

@app.post("/join-waitlist", responses=COMMON_ERROR_RESPONSES)
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
async def services_status(request: Request):
    from microservices.lifecycle import current_mode, service_info
    from service_bus import bus_stats

    ms_ctx = getattr(request.app.state, "ms_ctx", None)
    return {
        **service_info(ms_ctx),
        "service_mode_runtime": current_mode(),
        "service_bus": bus_stats(),
        "production_guard_failed": bool(getattr(request.app.state, "production_guard_failed", False)),
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


@app.get("/create-checkout-session", responses=COMMON_ERROR_RESPONSES)
async def checkout_get(tier: str = "pro", user: dict | None = Depends(optional_user)):
    """Landing page links use GET — redirect to Lemon Squeezy or Stripe."""
    email = user.get("email") if user else None
    user_id = int(user["id"]) if user and user.get("id") else None
    payload = _create_stripe_checkout(tier, customer_email=email, user_id=user_id)
    return RedirectResponse(url=payload["url"], status_code=303)


@app.post("/create-checkout-session", responses=COMMON_ERROR_RESPONSES)
async def checkout_post(tier: str = "pro", user: dict | None = Depends(optional_user)):
    email = user.get("email") if user else None
    user_id = int(user["id"]) if user and user.get("id") else None
    return _create_stripe_checkout(tier, customer_email=email, user_id=user_id)


@app.post("/webhook", responses=COMMON_ERROR_RESPONSES)
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
    return render_page(request, "success.html", _footer_ctx())


@app.get("/cancel", response_class=HTMLResponse)
async def checkout_cancel(request: Request):
    return templates.TemplateResponse(
        request,
        STR_UTILITY_HTML,
        {
            "page": "cancel",
            "title": "Checkout cancelled",
            "lead": "No charge was made. You can restart Decision Pro anytime — or stay on Proof Pass.",
            **_footer_ctx(),
        },
    )


@app.get("/landing", response_class=HTMLResponse)
async def landing_alias(request: Request):
    return await landing_page(request)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    # Container platforms set HOST=0.0.0.0; local default stays loopback-only.
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=port)

