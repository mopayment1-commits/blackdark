from fastapi import FastAPI, Request, HTTPException, Header, BackgroundTasks, Body, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import aiohttp
import asyncio
import json
import logging
import os
import stripe
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import config

logger = logging.getLogger("BLACKDARK.Dashboard")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

STRIPE_TIERS = {
    "pro": {"amount": 2900, "name": "BLACKDARK Pro"},
    "whale": {"amount": 19900, "name": "BLACKDARK Whale"},
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
    if price_at <= 0:
        return "unknown", 0.0
    change_pct = ((price_after - price_at) / price_at) * 100
    verdict_upper = verdict.upper()
    if verdict_upper == "BUY":
        if change_pct > 1.5:
            return "correct", min(100.0, 55.0 + change_pct * 4.0)
        if change_pct > -2.0:
            return "partial", max(35.0, 45.0 + change_pct * 5.0)
        return "incorrect", max(0.0, 25.0 + change_pct * 2.0)
    if verdict_upper == "SELL":
        if change_pct < -1.5:
            return "correct", min(100.0, 55.0 + abs(change_pct) * 4.0)
        if change_pct < 2.0:
            return "partial", max(35.0, 45.0 - change_pct * 5.0)
        return "incorrect", max(0.0, 25.0 - change_pct * 2.0)
    if abs(change_pct) <= 3.0:
        return "correct", min(100.0, 70.0 - abs(change_pct) * 3.0)
    return "partial", max(30.0, 50.0 - abs(change_pct) * 2.0)


async def _resolve_mature_oracle_predictions() -> int:
    from database import fetch_unresolved_oracle_predictions, resolve_oracle_prediction
    from datetime import timedelta

    unresolved = await fetch_unresolved_oracle_predictions(limit=200)
    resolved_count = 0
    now = datetime.now(timezone.utc)
    for pred in unresolved:
        raw_ts = str(pred.get("timestamp") or "")
        try:
            ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
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


async def _log_oracle_prediction(payload: dict) -> None:
    from database import insert_oracle_prediction

    try:
        await insert_oracle_prediction(
            asset=str(payload.get("symbol") or ""),
            price_at_prediction=float(payload.get("price") or 0),
            verdict=str(payload.get("verdict") or "WAIT"),
            opportunity_score=int(payload.get("opportunity_score") or 0),
            confidence=int(payload.get("confidence") or 0),
        )
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
    risk_score = min(10, max(1, int(round(weighted_beta * 10))))
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

    return {
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
        "recommendations": recommendations,
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    from database import init_db

    await init_db()
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

    aggregator_task: asyncio.Task | None = None
    run_agg = os.getenv("RUN_AGGREGATOR", "true").lower() in {"1", "true", "yes"}
    if run_agg:
        os.environ.setdefault("MANIFEST_AUTO_APPROVE", "true")
        os.environ.setdefault("MANIFEST_REQUIRE_REVIEW", "false")

        async def _aggregator_wrapper() -> None:
            try:
                from aggregator import run_aggregator

                await run_aggregator()
            except asyncio.CancelledError:
                logger.info("Aggregator background task cancelled.")
            except Exception:
                logger.exception("Aggregator background task failed.")

        aggregator_task = asyncio.create_task(_aggregator_wrapper())
        logger.info("Aggregator background task started (RUN_AGGREGATOR=true).")

    from telegram_monitor import start_telegram_monitor

    telegram_task = await start_telegram_monitor()
    from telegram_bot_poller import start_telegram_poller

    telegram_poller_task = await start_telegram_poller()

    ingestion_task: asyncio.Task | None = None
    if os.getenv("INGESTION_ENABLED", "true").lower() in {"1", "true", "yes"}:
        async def _ingestion_wrapper() -> None:
            try:
                from ingestion_scheduler import start_ingestion_scheduler

                bootstrap = os.getenv("INGESTION_BOOTSTRAP_ON_START", "true").lower() in {
                    "1",
                    "true",
                    "yes",
                }
                await start_ingestion_scheduler(bootstrap=bootstrap)
            except asyncio.CancelledError:
                logger.info("Ingestion scheduler cancelled.")
            except Exception:
                logger.exception("Ingestion scheduler failed.")

        ingestion_task = asyncio.create_task(_ingestion_wrapper())
        logger.info("Ingestion scheduler task started (INGESTION_ENABLED=true).")

    forecast_audit_task: asyncio.Task | None = None
    if os.getenv("FORECAST_ENABLED", "true").lower() in {"1", "true", "yes"}:

        async def _forecast_audit_loop() -> None:
            interval = max(300, int(os.getenv("FORECAST_AUDIT_INTERVAL_SEC", "3600")))
            while True:
                try:
                    from forecast_engine import run_forecast_audit

                    audit = await run_forecast_audit()
                    from ml.labeling_pipeline import resolve_mature_predictions

                    oracle_resolved = await resolve_mature_predictions()
                    oracle_resolved_count = (oracle_resolved or {}).get("resolved_24h", 0)
                    retrain_result = None
                    if os.getenv("ORACLE_RETRAIN_ENABLED", "true").lower() in {"1", "true", "yes"}:
                        from oracle_retrainer import run_oracle_retrain_step

                        retrain_result = await run_oracle_retrain_step()
                    if audit.get("resolved") or oracle_resolved_count or (retrain_result or {}).get("adjusted"):
                        logger.info(
                            "Forecast/oracle audit | forecasts_resolved=%s oracle_resolved=%s retrain=%s",
                            audit.get("resolved", 0),
                            oracle_resolved_count,
                            (retrain_result or {}).get("adjusted"),
                        )
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Forecast audit loop failed.")
                await asyncio.sleep(interval)

        forecast_audit_task = asyncio.create_task(_forecast_audit_loop())
        logger.info("Forecast audit loop started (FORECAST_ENABLED=true).")

    ml_flywheel_started = False
    if config.ML_FLYWHEEL_ENABLED:
        from ml_flywheel_scheduler import start_ml_flywheel

        await start_ml_flywheel()
        ml_flywheel_started = True
        logger.info("ML flywheel started (ML_FLYWHEEL_ENABLED=true).")

    weekly_report_task: asyncio.Task | None = None
    if os.getenv("WEEKLY_REPORT_AUTO", "false").lower() in {"1", "true", "yes"}:

        async def _weekly_report_loop() -> None:
            interval_hours = max(24, int(os.getenv("WEEKLY_REPORT_INTERVAL_HOURS", "168")))
            while True:
                try:
                    from weekly_report import build_weekly_report

                    report = await build_weekly_report(persist=True)
                    logger.info("Weekly report generated | id=%s", report.get("report_id"))
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Weekly report auto-generation failed.")
                await asyncio.sleep(interval_hours * 3600)

        weekly_report_task = asyncio.create_task(_weekly_report_loop())
        logger.info("Weekly report scheduler started.")

    daily_report_task: asyncio.Task | None = None
    if os.getenv("DAILY_REPORT_AUTO", "false").lower() in {"1", "true", "yes"}:

        async def _daily_report_loop() -> None:
            interval_hours = max(12, int(os.getenv("DAILY_REPORT_INTERVAL_HOURS", "24")))
            while True:
                try:
                    from daily_report import build_daily_report

                    report = await build_daily_report(persist=True)
                    logger.info("Daily report generated | id=%s", report.get("report_id"))
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Daily report auto-generation failed.")
                await asyncio.sleep(interval_hours * 3600)

        daily_report_task = asyncio.create_task(_daily_report_loop())
        logger.info("Daily report scheduler started.")

    auto_exec_task: asyncio.Task | None = None
    if os.getenv("AUTO_EXECUTION_LOOP", "false").lower() in {"1", "true", "yes"}:
        from execution_engine import start_auto_execution_loop

        auto_exec_task = await start_auto_execution_loop()

    db_maintenance_task: asyncio.Task | None = None
    if os.getenv("DB_MAINTENANCE_AUTO", "false").lower() in {"1", "true", "yes"}:

        async def _db_maintenance_loop() -> None:
            interval_hours = max(6, int(os.getenv("DB_MAINTENANCE_INTERVAL_HOURS", "24")))
            while True:
                try:
                    from db_upgrade import run_sqlite_maintenance

                    await run_sqlite_maintenance(vacuum=False)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("DB maintenance loop failed.")
                await asyncio.sleep(interval_hours * 3600)

        db_maintenance_task = asyncio.create_task(_db_maintenance_loop())
        logger.info("DB maintenance scheduler started.")

    cloud_sync_task: asyncio.Task | None = None
    if os.getenv("CLOUD_SYNC_ENABLED", "false").lower() in {"1", "true", "yes"}:

        async def _cloud_sync_loop() -> None:
            interval_hours = max(1, int(os.getenv("CLOUD_SYNC_INTERVAL_HOURS", "6")))
            while True:
                try:
                    from cloud_syncer import is_cloud_sync_configured, run_cloud_sync_once

                    if is_cloud_sync_configured():
                        results = await run_cloud_sync_once()
                        logger.info("Cloud sync batch finished | files=%d", len(results))
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Cloud sync loop failed.")
                await asyncio.sleep(interval_hours * 3600)

        cloud_sync_task = asyncio.create_task(_cloud_sync_loop())
        logger.info("Cloud sync scheduler started (CLOUD_SYNC_ENABLED=true).")

    yield

    if ml_flywheel_started:
        from ml_flywheel_scheduler import stop_ml_flywheel

        await stop_ml_flywheel()

    if cloud_sync_task is not None:
        cloud_sync_task.cancel()
        try:
            await cloud_sync_task
        except asyncio.CancelledError:
            pass

    if db_maintenance_task is not None:
        db_maintenance_task.cancel()
        try:
            await db_maintenance_task
        except asyncio.CancelledError:
            pass

    if auto_exec_task is not None:
        from execution_engine import stop_auto_execution_loop

        await stop_auto_execution_loop()

    if weekly_report_task is not None:
        weekly_report_task.cancel()
        try:
            await weekly_report_task
        except asyncio.CancelledError:
            pass

    if daily_report_task is not None:
        daily_report_task.cancel()
        try:
            await daily_report_task
        except asyncio.CancelledError:
            pass

    if forecast_audit_task is not None:
        forecast_audit_task.cancel()
        try:
            await forecast_audit_task
        except asyncio.CancelledError:
            pass

    if ingestion_task is not None:
        from ingestion_scheduler import stop_ingestion_scheduler

        await stop_ingestion_scheduler()
        ingestion_task.cancel()
        try:
            await ingestion_task
        except asyncio.CancelledError:
            pass

    if telegram_task is not None:
        from telegram_monitor import stop_telegram_monitor

        await stop_telegram_monitor()

    if telegram_poller_task is not None:
        from telegram_bot_poller import stop_telegram_poller

        await stop_telegram_poller()

    if aggregator_task is not None:
        aggregator_task.cancel()
        try:
            await aggregator_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="BLACKDARK", version="1.0.0", lifespan=lifespan)

STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


async def optional_user(authorization: str | None = Header(None, alias="Authorization")) -> dict | None:
    from auth_service import get_user_from_token

    if not authorization:
        return None
    token = authorization[7:] if authorization.startswith("Bearer ") else authorization
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


def _normalize_oracle_symbol(symbol: str) -> tuple[str, str]:
    cleaned = symbol.upper().strip().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        return cleaned[:-4], cleaned
    return cleaned, f"{cleaned}USDT"


async def _fetch_binance_ticker(pair: str) -> dict | None:
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return {
                    "price": float(data["lastPrice"]),
                    "change_24h": float(data["priceChangePercent"]),
                    "volume": float(data["volume"]),
                    "quote_volume": float(data.get("quoteVolume") or 0),
                }
    except (aiohttp.ClientError, KeyError, TypeError, ValueError):
        return None


async def _fetch_binance_market_overview(limit: int | None = None) -> list[dict]:
    """Tracked assets first, then top USDT pairs by 24h quote volume from Binance."""
    if limit is None:
        limit = config.MARKET_RADAR_LIMIT
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []
                rows = await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return []

    by_symbol: dict[str, dict] = {}
    all_candidates: list[dict] = []
    for row in rows:
        symbol = row.get("symbol", "")
        if not symbol.endswith("USDT"):
            continue
        asset = symbol[:-4]
        if _is_stablecoin(asset):
            continue
        try:
            quote_volume = float(row.get("quoteVolume") or 0)
            change = float(row.get("priceChangePercent") or 0)
            price = float(row.get("lastPrice") or 0)
        except (TypeError, ValueError):
            continue
        if quote_volume < 10_000_000:
            continue
        score = _oracle_score(quote_volume, change)
        verdict, _ = _oracle_verdict(score, asset, price)
        item = {
            "symbol": asset,
            "price": price,
            "change_24h": change,
            "volume_24h": quote_volume,
            "score": score,
            "verdict": verdict,
            "sector": _sector_for_asset(asset),
        }
        by_symbol[asset] = item
        all_candidates.append(item)

    all_candidates.sort(key=lambda x: x["volume_24h"], reverse=True)
    priority: list[dict] = []
    seen: set[str] = set()
    for asset in config.tracked_asset_list():
        if asset in by_symbol:
            priority.append(by_symbol[asset])
            seen.add(asset)
    for candidate in all_candidates:
        if len(priority) >= limit:
            break
        if candidate["symbol"] not in seen:
            priority.append(candidate)
            seen.add(candidate["symbol"])
    return priority[:limit]


async def _fetch_live_whale_signal(pair: str, price: float) -> str:
    """Detect large aggressive trades on Binance (live whale activity)."""
    url = f"https://api.binance.com/api/v3/aggTrades?symbol={pair}&limit=200"
    threshold_usd = 75_000
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return "No significant whale activity"
                trades = await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return "No significant whale activity"

    buy_blocks = 0
    sell_blocks = 0
    max_notional = 0.0
    for trade in trades:
        try:
            qty = float(trade["q"])
            trade_price = float(trade["p"])
            notional = qty * trade_price
        except (KeyError, TypeError, ValueError):
            continue
        if notional < threshold_usd:
            continue
        max_notional = max(max_notional, notional)
        # m=true → buyer is maker → aggressive seller; m=false → aggressive buyer
        if trade.get("m"):
            sell_blocks += 1
        else:
            buy_blocks += 1

    if buy_blocks >= 3 and buy_blocks > sell_blocks:
        return f"Whale accumulation detected — {buy_blocks} large buy blocks (max ${max_notional:,.0f})"
    if sell_blocks >= 3 and sell_blocks > buy_blocks:
        return f"Whale distribution detected — {sell_blocks} large sell blocks (max ${max_notional:,.0f})"
    if buy_blocks or sell_blocks:
        return f"Mixed whale activity — {buy_blocks} buys / {sell_blocks} sells above ${threshold_usd:,.0f}"
    return "No significant whale activity in recent trades"


def _oracle_score(volume: float, change: float) -> int:
    score = 50
    if volume > 1_000_000_000:
        score += 20
    elif volume > 100_000_000:
        score += 15
    elif volume > 10_000_000:
        score += 10
    if 0 < change < 3:
        score += 20
    elif 3 <= change < 8:
        score += 15
    elif 8 <= change < 15:
        score += 5
    elif change >= 15:
        score -= 15
    elif -3 < change <= 0:
        score -= 5
    elif -8 < change <= -3:
        score -= 15
    elif change <= -8:
        score -= 25
    return max(0, min(100, score))


_STABLECOINS = frozenset(
    {"USDC", "USDT", "USD1", "DAI", "FDUSD", "USDE", "USDS", "TUSD", "BUSD", "EURC", "RLUSD", "USDG"}
)


def _is_stablecoin(asset: str) -> bool:
    return asset.upper() in _STABLECOINS


def _oracle_verdict(score: int, asset: str, price: float) -> tuple[str, str]:
    if _is_stablecoin(asset):
        return "WAIT", f"{asset} is a stablecoin — not a trading opportunity (Score: {score}/100)"
    if score >= 75:
        return "BUY", f"Strong buy signal for {asset} at ${price:,.0f} (Score: {score}/100)"
    if score >= 50:
        return "WAIT", f"Hold {asset} and watch for breakout (Score: {score}/100)"
    if score >= 30:
        return "CAUTION", f"Weak momentum on {asset}, be careful (Score: {score}/100)"
    return "SELL", f"Consider exiting {asset}, bearish trend (Score: {score}/100)"


def _oracle_sentiment(change: float) -> str:
    if change > 2:
        return "Bullish"
    if change < -2:
        return "Bearish"
    return "Neutral"


def _fear_greed_index(change: float, quote_volume: float) -> tuple[int, str]:
    fg = min(100, max(0, int(50 + change * 2 + (quote_volume / 1e9) * 10)))
    if fg > 75:
        label = "Extreme Greed"
    elif fg > 55:
        label = "Greed"
    elif fg > 45:
        label = "Neutral"
    elif fg > 25:
        label = "Fear"
    else:
        label = "Extreme Fear"
    return fg, label


def _oracle_confidence(score: int, change: float, quote_volume: float) -> int:
    return min(100, max(50, int(score * 0.8 + abs(change) * 2 + (quote_volume / 1e9) * 5)))


def _risk_level(score: int) -> str:
    if score > 75:
        return "Low"
    if score > 55:
        return "Medium"
    if score > 40:
        return "High"
    return "Extreme"


def _whale_alert_message(quote_volume: float, change: float) -> str:
    if quote_volume > 50_000_000:
        return "Whale accumulation detected — high volume inflow"
    if quote_volume > 10_000_000:
        return "Moderate whale interest"
    if change < -5:
        return "Whale distribution detected — large sell pressure"
    return "No significant whale activity"


def _oracle_action(score: int, price: float, support: float, resistance: float) -> str:
    if score >= 70:
        return f"Buy now at ${price:,.0f} with stop-loss at ${support * 0.97:,.0f}"
    if score >= 55:
        return f"Consider buying near ${support:,.0f}"
    if score >= 40:
        return f"Wait for pullback to ${support:,.0f}"
    return f"Sell with stop-loss at ${resistance:,.0f}"


def _oracle_narrative(
    asset: str,
    change: float,
    quote_volume: float,
    score: int,
    sentiment: str,
    fear_greed: str,
    confidence: int,
    trend_direction: str,
    risk_level: str,
    support: float,
    resistance: float,
    action: str,
    market_summary: str,
) -> str:
    if _is_stablecoin(asset):
        return f"{asset} is pegged — hold for stability, not for trading gains."

    direction = "surging" if change > 2 else "rising" if change > 0 else "falling"
    whale_phrase = (
        "massive whale inflow"
        if quote_volume > 50_000_000
        else "moderate interest"
        if quote_volume > 10_000_000
        else "low activity"
    )
    signal = (
        "strong buy signal"
        if score >= 70
        else "buy signal"
        if score >= 55
        else "hold"
        if score >= 40
        else "sell signal"
    )
    return (
        f"ACTION: {action} — {market_summary} — "
        f"{risk_level} Risk — {trend_direction} — {asset} is {direction} {change:+.2f}% "
        f"with {whale_phrase} — Support: ${support:,.0f} | Resistance: ${resistance:,.0f} — "
        f"{sentiment} sentiment — {signal} — "
        f"Confidence: {confidence}% — {fear_greed}"
    )


def _timestamp_human(now: datetime | None = None) -> str:
    ts = now or datetime.now(timezone.utc)
    return ts.strftime("%B %d, %Y at %I:%M %p UTC")


def _build_full_oracle_response(
    asset: str,
    price: float,
    volume: float,
    quote_volume: float,
    change: float,
    *,
    whale_alert: str | None = None,
) -> dict:
    score = _oracle_score(quote_volume, change)
    if _is_stablecoin(asset):
        score = min(score, 55)
    verdict, oracle_text = _oracle_verdict(score, asset, price)

    sentiment = _oracle_sentiment(change)
    fg_score, fear_greed = _fear_greed_index(change, quote_volume)
    confidence = _oracle_confidence(score, change, quote_volume)
    trend_direction = _trend_direction(change)
    risk = _risk_level(score)
    support = round(price * 0.97, -2)
    resistance = round(price * 1.03, -2)
    prediction_low = round(price * (1 + (change / 100) * 0.5), -2)
    prediction_high = round(price * (1 + (change / 100) * 1.5), -2)
    volatility = "Low" if abs(change) < 2 else "Medium" if abs(change) < 5 else "High"
    liquidity, _ = _liquidity_label(quote_volume)
    market_summary = f"Market: {sentiment} | Volatility: {volatility} | Liquidity: {liquidity}"
    action = _oracle_action(score, price, support, resistance)
    whale_alert = whale_alert or _whale_alert_message(quote_volume, change)
    narrative = _oracle_narrative(
        asset,
        change,
        quote_volume,
        score,
        sentiment,
        fear_greed,
        confidence,
        trend_direction,
        risk,
        support,
        resistance,
        action,
        market_summary,
    )
    now = datetime.now(timezone.utc)

    return {
        "symbol": asset,
        "price": price,
        "change_24h": change,
        "volume": volume,
        "volume_24h": quote_volume,
        "opportunity_score": score,
        "verdict": verdict,
        "oracle": oracle_text,
        "fear_greed": fear_greed,
        "fear_greed_score": fg_score,
        "support": support,
        "resistance": resistance,
        "next_24h_low": prediction_low,
        "next_24h_high": prediction_high,
        "trend_direction": trend_direction,
        "confidence": confidence,
        "action": action,
        "market_summary": market_summary,
        "risk_level": risk,
        "sentiment": sentiment,
        "narrative": narrative,
        "whale_alert": whale_alert,
        "data_source": "Binance Live API | Real-time",
        "timestamp_human": _timestamp_human(now),
        "timestamp": now.isoformat(),
        "disclaimer": "Not financial advice. Do your own research (DYOR).",
    }


def _trend_direction(change: float) -> str:
    if change > 2:
        return "Uptrend"
    if change < -2:
        return "Downtrend"
    return "Sideways"


def _liquidity_label(quote_volume: float) -> tuple[str, int]:
    if quote_volume > 500_000_000:
        return "High", 92
    if quote_volume > 50_000_000:
        return "Medium", 68
    return "Low", 38


def _compute_ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for value in values[period:]:
        ema = value * multiplier + ema * (1 - multiplier)
    return ema


def _compute_rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for idx in range(1, len(closes)):
        delta = closes[idx] - closes[idx - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def _rsi_signal_label(rsi: float) -> str:
    if rsi >= 70:
        return "Overbought"
    if rsi >= 55:
        return "Bullish momentum"
    if rsi >= 45:
        return "Neutral"
    if rsi >= 30:
        return "Bearish momentum"
    return "Oversold"


def _macd_trend_label(closes: list[float]) -> str:
    if len(closes) < 26:
        return "Insufficient candle data"
    ema12 = _compute_ema(closes, 12)
    ema26 = _compute_ema(closes, 26)
    if ema12 is None or ema26 is None:
        return "Insufficient candle data"
    macd = ema12 - ema26
    prev_closes = closes[:-1]
    prev_ema12 = _compute_ema(prev_closes, 12)
    prev_ema26 = _compute_ema(prev_closes, 26)
    if prev_ema12 is None or prev_ema26 is None:
        return "MACD consolidating"
    prev_macd = prev_ema12 - prev_ema26
    if macd > 0 and macd > prev_macd:
        return "Bullish crossover — momentum rising"
    if macd < 0 and macd < prev_macd:
        return "Bearish crossover — momentum falling"
    if macd > prev_macd:
        return "MACD turning up — early bullish shift"
    if macd < prev_macd:
        return "MACD turning down — early bearish shift"
    return "MACD flat — consolidation phase"


def _ema_position_label(price: float, closes: list[float]) -> str:
    ema50 = _compute_ema(closes, 50) if len(closes) >= 50 else None
    ema200 = _compute_ema(closes, 200) if len(closes) >= 200 else _compute_ema(closes, min(len(closes), 100))
    if ema50 is None:
        return "Insufficient EMA data"
    above50 = price >= ema50
    if ema200 is None:
        return "Price above 50 EMA" if above50 else "Price below 50 EMA"
    above200 = price >= ema200
    if above50 and above200:
        return "Price trading above 50 & 200 EMA — bullish structure"
    if above50 and not above200:
        return "Price above 50 EMA, below 200 EMA — recovery attempt"
    if not above50 and above200:
        return "Price below 50 EMA, holding 200 EMA — pullback zone"
    return "Price below key EMAs — downtrend structure"


async def _fetch_binance_klines(pair: str, interval: str = "1h", limit: int = 200) -> list[float]:
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}"
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []
                rows = await resp.json()
        return [float(row[4]) for row in rows if isinstance(row, list) and len(row) > 4]
    except (aiohttp.ClientError, TypeError, ValueError):
        return []


def _parse_alert_metadata(row: dict) -> dict:
    raw = row.get("metadata_json")
    if not raw:
        return row if row.get("pattern") else {}
    try:
        return json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (TypeError, json.JSONDecodeError):
        return {}


def _normalize_whale_alert_row(alert: dict) -> dict:
    if alert.get("metadata_json") is not None or alert.get("flow_type"):
        return alert
    meta = {
        "pattern": alert.get("pattern"),
        "liquidity_exchange": alert.get("liquidity_exchange"),
        "manipulation_score": alert.get("manipulation_score"),
        "volume_spike_ratio": alert.get("volume_spike_ratio"),
        "liquidity_drop_ratio": alert.get("liquidity_drop_ratio"),
        "iceberg_trade_count": alert.get("iceberg_trade_count"),
    }
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "flow_type": "manipulation_alert",
        "exchange": alert.get("volume_exchange"),
        "symbol": alert.get("symbol"),
        "asset": alert.get("asset"),
        "sector": alert.get("sector"),
        "side": alert.get("side"),
        "notional_usd": alert.get("volume_usd"),
        "metadata_json": json.dumps({k: v for k, v in meta.items() if v is not None}),
    }


def _whale_alerts_for_asset(alerts: list[dict], asset: str) -> list[dict]:
    target = asset.upper()
    matched: list[dict] = []
    for alert in alerts:
        row = _normalize_whale_alert_row(alert)
        if str(row.get("asset") or "").upper() == target:
            matched.append(row)
    return matched


async def _fetch_cvvd_whale_context(refresh: bool = False) -> dict:
    from whale_tracker import (
        get_latest_institutional_context,
        persist_manipulation_alerts,
        scan_whale_trades,
    )

    context = await get_latest_institutional_context()
    alerts = [_normalize_whale_alert_row(a) for a in context.get("whale_alerts", [])]
    sector_flows = context.get("sector_flows", [])

    if refresh or not alerts:
        live = await scan_whale_trades()
        if live:
            await persist_manipulation_alerts(live)
            alerts = [_normalize_whale_alert_row(a.model_dump()) for a in live]
            context = await get_latest_institutional_context()
            sector_flows = context.get("sector_flows", [])

    return {
        "whale_alerts": alerts,
        "sector_flows": sector_flows,
        "live_scan": refresh or not context.get("whale_alerts"),
    }


async def _fetch_cvvd_whale_alert(asset: str, pair: str, price: float) -> str:
    context = await _fetch_cvvd_whale_context(refresh=False)
    asset_alerts = _whale_alerts_for_asset(context["whale_alerts"], asset)
    if asset_alerts:
        top = asset_alerts[0]
        meta = _parse_alert_metadata(top)
        pattern = str(meta.get("pattern") or "cross_venue_manipulation").replace("_", " ")
        score = float(meta.get("manipulation_score") or 0)
        notional = float(top.get("notional_usd") or 0)
        side = str(top.get("side") or "unknown")
        exchange = str(top.get("exchange") or meta.get("volume_exchange") or "multi-venue").upper()
        return (
            f"CVVD {pattern} on {exchange} — {side} side — "
            f"${notional:,.0f} volume — manipulation score {score:.0f}/100"
        )

    return await _fetch_live_whale_signal(pair, price)


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
    from sentiment_engine import build_sentiment_context_safe
    from oracle_data_hub import build_hub_context_safe, hub_score_adjustment

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
        whale_flow = f"CVVD {pattern} — {str(top.get('side') or 'mixed')} — ${float(top.get('notional_usd') or 0):,.0f}"
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
    hub_score_adj = int(round(hub_delta))

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

    return {
        "symbol": asset,
        "verdict": verdict,
        "opportunity_score": score,
        "simulated": False,
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ========== LANDING PAGE (ROOT) ==========
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.post("/api/auth/register")
async def auth_register(data: dict = Body(...)):
    from auth_service import register_user

    try:
        return await register_user(
            str(data.get("email") or ""),
            str(data.get("password") or ""),
            str(data.get("name") or ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/auth/login")
async def auth_login(data: dict = Body(...)):
    from auth_service import login_user

    try:
        return await login_user(
            str(data.get("email") or ""),
            str(data.get("password") or ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.post("/api/auth/logout")
async def auth_logout(user: dict | None = Depends(optional_user)):
    from auth_service import logout_user

    if user and user.get("token"):
        await logout_user(str(user["token"]))
    return {"success": True}


@app.get("/api/auth/me")
async def auth_me(user: dict | None = Depends(optional_user)):
    from auth_service import tier_payload
    from database import fetch_active_subscription_for_email, fetch_user_profile

    if user is None:
        return {"authenticated": False, "tier": tier_payload(None)}
    sub = await fetch_active_subscription_for_email(user["email"])
    profile = await fetch_user_profile(user["email"])
    return {
        "authenticated": True,
        "user": user,
        "profile": profile,
        "tier": tier_payload(user, sub),
        "subscription": sub,
        "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY")),
    }


@app.patch("/api/auth/profile")
async def auth_profile_update(
    data: dict = Body(...),
    user: dict | None = Depends(optional_user),
):
    from database import update_user_telegram_chat_id

    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    telegram_chat_id = (data.get("telegram_chat_id") or "").strip() or None
    if telegram_chat_id is not None:
        await update_user_telegram_chat_id(user["email"], telegram_chat_id)
    return {"success": True, "telegram_chat_id": telegram_chat_id}


@app.get("/api/billing/status")
async def billing_status(user: dict | None = Depends(optional_user)):
    from billing_service import stripe_configured
    from database import fetch_active_subscription_for_email, fetch_user_stripe_customer_id

    if not user:
        return {"authenticated": False, "stripe_configured": stripe_configured()}
    sub = await fetch_active_subscription_for_email(user["email"])
    return {
        "authenticated": True,
        "stripe_configured": stripe_configured(),
        "stripe_customer_id": await fetch_user_stripe_customer_id(user["email"]),
        "subscription": sub,
        "tier": user.get("tier"),
        "has_billing_portal": bool(await fetch_user_stripe_customer_id(user["email"])),
    }


@app.post("/api/billing/checkout")
async def billing_checkout(
    data: dict = Body(default={}),
    user: dict | None = Depends(optional_user),
):
    from billing_service import create_checkout_session, stripe_configured

    if not stripe_configured():
        raise HTTPException(status_code=503, detail="Stripe not configured")
    tier = str(data.get("tier") or "pro")
    email = user.get("email") if user else None
    user_id = int(user["id"]) if user and user.get("id") else None
    try:
        return create_checkout_session(tier, customer_email=email, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/billing/portal")
async def billing_portal(user: dict | None = Depends(optional_user)):
    from billing_service import create_billing_portal_session, stripe_configured
    from database import fetch_user_stripe_customer_id

    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    if not stripe_configured():
        raise HTTPException(status_code=503, detail="Stripe not configured")
    customer_id = await fetch_user_stripe_customer_id(user["email"])
    if not customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer — subscribe first")
    try:
        return create_billing_portal_session(customer_id)
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/platform/stats")
async def platform_stats():
    from database import fetch_platform_user_stats
    from billing_service import stripe_configured

    stats = await fetch_platform_user_stats()
    stats["stripe_configured"] = stripe_configured()
    stats["telegram_configured"] = bool(
        os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")
    )
    return stats


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
async def telegram_test(data: dict = Body(default={})):
    from telegram_monitor import send_test_telegram

    chat_id = (data.get("telegram_chat_id") or data.get("chat_id") or "").strip() or None
    return await send_test_telegram(chat_id)


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse(request, "landing.html")

# ========== DASHBOARD ==========
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "index.html")

# ========== API ENDPOINTS ==========
@app.get("/oracle/{symbol}/explain")
async def oracle_explain(symbol: str) -> JSONResponse:
    asset, pair = _normalize_oracle_symbol(symbol)
    market = await _fetch_binance_ticker(pair)
    if market is None:
        raise HTTPException(status_code=404, detail=f"Symbol {asset} not found.")

    price = market["price"]
    volume = market["volume"]
    quote_volume = market["quote_volume"] or (volume * price)
    change = market["change_24h"]
    score = _oracle_score(quote_volume, change)
    verdict, _ = _oracle_verdict(score, asset, price)

    payload = await _build_opportunity_explanation(
        asset, price, change, quote_volume, score, verdict, pair=pair
    )
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
    return JSONResponse(payload)


@app.get("/oracle/{symbol}")
async def oracle(
    symbol: str,
    background_tasks: BackgroundTasks,
    user: dict | None = Depends(optional_user),
) -> JSONResponse:
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
    whale_alert = await _fetch_cvvd_whale_alert(asset, pair, price)

    payload = _build_full_oracle_response(
        asset, price, volume, quote_volume, change, whale_alert=whale_alert
    )
    payload["explanation"] = await _build_opportunity_explanation(
        asset, price, change, quote_volume, payload["opportunity_score"], payload["verdict"], pair=pair
    )
    from forecast_engine import enrich_oracle_payload

    payload = await enrich_oracle_payload(payload)
    background_tasks.add_task(_log_oracle_prediction, payload)
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/whale/scan")
async def whale_scan() -> dict:
    """Trigger a fresh CVVD scan across all venues."""
    context = await _fetch_cvvd_whale_context(refresh=True)
    return {
        "alerts_found": len(context.get("whale_alerts", [])),
        "whale_alerts": context.get("whale_alerts", [])[:20],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/market/overview")
async def market_overview():
    assets = await _fetch_binance_market_overview()
    sectors: dict[str, list] = {}
    for asset in assets:
        sector = asset.get("sector") or _sector_for_asset(asset["symbol"])
        sectors.setdefault(sector, []).append(asset)
    return {
        "assets": assets,
        "sectors": sectors,
        "tracked_count": len(config.EXTENDED_TRACKED_ASSETS),
        "top_gainers": sorted(assets, key=lambda x: x["change_24h"], reverse=True)[:3],
        "top_losers": sorted(assets, key=lambda x: x["change_24h"])[:3],
        "market_status": "active",
        "data_source": "Binance Live API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/market/open-interest")
async def market_open_interest():
    from market_intel import fetch_open_interest

    rows = await fetch_open_interest()
    return {
        "assets": rows,
        "count": len(rows),
        "data_source": "Binance Futures API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


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


@app.get("/api/market/sectors")
async def market_sectors():
    """Sector radar — SII inflow scores + live asset performance per sector."""
    assets = await _fetch_binance_market_overview()
    whale_ctx = await _fetch_cvvd_whale_context(refresh=False)
    sii_by_sector: dict[str, float] = {}
    for row in whale_ctx.get("sector_flows", []):
        meta = _parse_alert_metadata(row)
        sector_name = str(row.get("sector") or "")
        if sector_name:
            sii_by_sector[sector_name] = float(meta.get("sii_score") or 0)

    sector_assets: dict[str, list] = {}
    for asset in assets:
        sector = asset.get("sector") or _sector_for_asset(asset["symbol"])
        sector_assets.setdefault(sector, []).append(asset)

    sectors_out = []
    for sector_name, sector_list in sector_assets.items():
        avg_change = sum(a["change_24h"] for a in sector_list) / len(sector_list)
        avg_score = sum(a["score"] for a in sector_list) / len(sector_list)
        sectors_out.append(
            {
                "sector": sector_name,
                "sii_score": round(sii_by_sector.get(sector_name, 0.0), 2),
                "asset_count": len(sector_list),
                "avg_change_24h": round(avg_change, 2),
                "avg_opportunity_score": round(avg_score, 1),
                "heat_label": (
                    "Hot"
                    if avg_change > 2 or sii_by_sector.get(sector_name, 0) > 25
                    else "Cool"
                    if avg_change < -2
                    else "Neutral"
                ),
                "top_assets": sorted(sector_list, key=lambda x: x["score"], reverse=True)[:3],
            }
        )

    sectors_out.sort(key=lambda x: x["sii_score"], reverse=True)
    return {
        "sectors": sectors_out,
        "data_source": "CVVD SII + Binance Live",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


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
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/oracle/data-hub")
async def oracle_data_hub_overview():
    from oracle_data_hub import build_hub_context_safe

    ctx = await build_hub_context_safe("BTC")
    return ctx


@app.get("/api/oracle/data-hub/{symbol}")
async def oracle_data_hub_asset(symbol: str):
    from oracle_data_hub import build_hub_context_safe, hub_score_adjustment

    asset = symbol.upper().replace("USDT", "").replace("/", "")
    ctx = await build_hub_context_safe(asset)
    delta, reasons, risks = hub_score_adjustment(asset, ctx)
    ctx["score_adjustment"] = delta
    ctx["hub_reasons"] = reasons
    ctx["hub_risks"] = risks
    return ctx


@app.get("/api/macro/overview")
async def macro_overview():
    from oracle_data_hub import fetch_macro_mesh
    import aiohttp

    timeout = aiohttp.ClientTimeout(total=config.ORACLE_HUB_FETCH_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        macro = await fetch_macro_mesh(session)
    return {
        "macro": macro,
        "data_source": "Oracle Data Hub — Yahoo Finance extended",
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
    from ccxt_market_fetcher import probe_phase_b_exchanges
    from coingecko_cex_fetcher import probe_coingecko_exchanges
    from dex_fetcher import probe_dex_venues
    from perp_dex_fetcher import probe_perp_dex_venues
    import aggregator

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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/universe/status")
async def universe_status():
    from platform_universe import build_manifest_universe_block, compute_universe_coverage

    return {
        "coverage": await compute_universe_coverage(),
        "registry": build_manifest_universe_block(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/ingestion/status")
async def ingestion_status():
    from data_lake import lake_status
    from data_sources_registry import DATA_SOURCES, registry_summary
    from ingestion_scheduler import scheduler_running
    from binance_ws_ingest import ws_stats
    import os

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
async def ingestion_run_once():
    """Manual one-shot ingest (bootstrap all categories)."""
    from ingestion_fetchers import ingest_all_categories

    summary = await ingest_all_categories()
    return {"status": "complete", "categories": summary}


@app.get("/api/forecast/audit")
async def forecast_audit():
    from database import fetch_forecast_audit_stats
    from forecast_engine import run_forecast_audit

    audit_run = await run_forecast_audit()
    stats = await fetch_forecast_audit_stats(limit=25)
    stats["newly_resolved"] = audit_run.get("resolved", 0)
    stats["checked"] = audit_run.get("checked", 0)
    return stats


@app.get("/api/forecast/{symbol}")
async def forecast_asset(symbol: str):
    from forecast_engine import build_asset_forecast

    asset, pair = _normalize_oracle_symbol(symbol)
    market = await _fetch_binance_ticker(pair)
    current_price = float(market["price"]) if market else None
    forecast = await build_asset_forecast(asset, current_price=current_price)
    return {
        "asset": asset,
        "forecast": forecast,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/oracle/audit")
async def oracle_audit():
    from database import fetch_oracle_audit_stats
    from ml.labeling_pipeline import resolve_mature_predictions

    resolved_now = await resolve_mature_predictions()
    stats = await fetch_oracle_audit_stats(limit=25)
    stats["newly_resolved"] = (resolved_now or {}).get("resolved_24h", 0)
    stats["labeling"] = resolved_now
    return stats


@app.get("/api/ml/status")
async def ml_status():
    from ml.train_baseline import model_status

    return await model_status()


@app.post("/api/ml/flywheel/run")
async def ml_flywheel_run():
    from ml.labeling_pipeline import run_labeling_flywheel_cycle

    return await run_labeling_flywheel_cycle()


@app.post("/api/ml/train")
async def ml_train():
    from ml.train_baseline import train_oracle_direction_model

    return await train_oracle_direction_model()


@app.get("/api/ml/predict/{asset}")
async def ml_predict(asset: str, price: float | None = None):
    from ml.inference import predict_direction

    return await predict_direction(asset, price=price)


@app.get("/api/oracle/accuracy/public")
async def oracle_accuracy_public():
    from ml.public_accuracy import build_public_accuracy_payload

    payload = await build_public_accuracy_payload()
    payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    return payload


@app.get("/oracle-accuracy", response_class=HTMLResponse)
async def oracle_accuracy_page(request: Request):
    return templates.TemplateResponse(request, "oracle_accuracy.html")


@app.post("/api/ml/train/ensemble")
async def ml_train_ensemble():
    from ml.train_ensemble import train_direction_ensemble

    return await train_direction_ensemble()


@app.get("/api/ml/experience")
async def ml_experience():
    from ml.experience_log import fetch_recent_experiences, load_experience_summary

    return {
        "summary": load_experience_summary(),
        "recent": fetch_recent_experiences(limit=50),
    }


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
    return {
        "product": "BLACKDARK Institutional Manipulation Feed",
        "feed_version": config.B2B_FEED_VERSION,
        "demo_key": config.B2B_DEMO_API_KEY,
        "demo_endpoint": "/api/b2b/demo",
        "authenticated_endpoint": "/api/b2b/feed",
        "header": "X-API-Key",
        "pricing_usd_monthly": 199,
        "one_pager_url": "/b2b",
        "methodology": {
            "cvvd": "Cross-Venue Volume Discrepancy",
            "sii": "Sector Inflow Index",
        },
    }


@app.get("/b2b", response_class=HTMLResponse)
async def b2b_page(request: Request):
    return templates.TemplateResponse(
        request,
        "b2b.html",
        {
            "demo_key": config.B2B_DEMO_API_KEY,
            "feed_version": config.B2B_FEED_VERSION,
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
        {"page": page, **content},
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


@app.get("/api/arbitrage/opportunities")
async def arbitrage_opportunities(
    quote_amount: float | None = None,
    live: bool = True,
    min_profit: float = 0.0,
):
    from arbitrage_service import process_arbitrage_alerts, scan_arbitrage_opportunities

    result = await scan_arbitrage_opportunities(
        quote_amount=quote_amount,
        prefer_live=live,
        min_profit_usdt=min_profit,
    )
    alerts = await process_arbitrage_alerts(result)
    result["alerts_triggered"] = alerts
    return result


@app.post("/api/arbitrage/scan")
async def arbitrage_scan(
    quote_amount: float | None = None,
    _user: dict | None = Depends(require_feature("arbitrage")),
):
    """Force a live cross-venue arbitrage scan."""
    from arbitrage_service import process_arbitrage_alerts, scan_arbitrage_opportunities

    result = await scan_arbitrage_opportunities(quote_amount=quote_amount, prefer_live=True)
    alerts = await process_arbitrage_alerts(result)
    result["alerts_triggered"] = alerts
    return result


@app.get("/api/arbitrage/compare/{symbol}")
async def arbitrage_compare(symbol: str, quote_amount: float | None = None):
    from arbitrage_service import compare_symbol_across_exchanges

    return await compare_symbol_across_exchanges(symbol, quote_amount=quote_amount)


@app.get("/api/arbitrage/feed-lag/{symbol}")
async def arbitrage_feed_lag(symbol: str):
    from arbitrage_service import compare_symbol_across_exchanges

    compare = await compare_symbol_across_exchanges(symbol)
    return compare.get("feed_lag") or {"opportunities": [], "symbol": symbol}


@app.get("/api/arbitrage/durations")
async def arbitrage_durations(limit: int = 20):
    from opportunity_tracker import export_state

    state = export_state()
    state["active"] = state.get("active", [])[:limit]
    return state


@app.get("/api/oracle/weights")
async def oracle_weights(symbol: str = "BTC"):
    from weight_aggregator import compute_modal_breakdown, get_core_score_weights, get_dimension_weights

    from whale_tracker import get_latest_institutional_context

    ctx = await get_latest_institutional_context()
    breakdown = compute_modal_breakdown(symbol.upper(), ctx)
    return {
        "symbol": symbol.upper(),
        "dimension_weights": get_dimension_weights(),
        "core_weights": get_core_score_weights(),
        "breakdown": breakdown,
    }


@app.post("/api/oracle/retrain")
async def oracle_retrain_manual():
    from oracle_retrainer import run_oracle_retrain_step

    return await run_oracle_retrain_step()


@app.get("/api/arbitrage/alerts")
async def arbitrage_alerts(limit: int = 20):
    from database import fetch_arbitrage_alert_log

    rows = await fetch_arbitrage_alert_log(limit=limit)
    return {
        "alerts": rows,
        "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")),
        "email_configured": bool(os.getenv("SMTP_HOST")),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/simulate/trade")
async def simulate_trade(data: dict = Body(...)):
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
async def simulate_arbitrage(data: dict = Body(...)):
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
async def simulate_history(limit: int = 15):
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
async def alerts_test():
    from alert_service import send_test_alert

    return await send_test_alert()


@app.post("/api/execution/auto")
async def execution_auto_toggle(data: dict = Body(...)):
    from execution_engine import set_auto_execution

    enabled = bool(data.get("enabled"))
    return await set_auto_execution(enabled)


@app.post("/api/execution/cycle")
async def execution_auto_cycle():
    from execution_engine import run_auto_execution_cycle

    return await run_auto_execution_cycle()


@app.get("/api/execution/status")
async def execution_status():
    from execution_engine import get_execution_status

    return await get_execution_status()


@app.post("/api/execution/panic")
async def execution_panic():
    from execution_engine import trigger_panic

    return await trigger_panic()


@app.post("/api/execution/resume")
async def execution_resume():
    from execution_engine import resume_execution

    return await resume_execution()


@app.post("/api/execution/order")
async def execution_order(data: dict = Body(...)):
    from execution_engine import execute_order

    try:
        return await execute_order(
            str(data.get("symbol") or "BTC"),
            str(data.get("side") or "buy").lower(),  # type: ignore[arg-type]
            float(data.get("amount_usd") or 100),
            dry_run=bool(data.get("dry_run", True)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/execution/logs")
async def execution_logs(limit: int = 15):
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


@app.get("/api/arbitrage/catalog")
async def arbitrage_catalog(category: str | None = None, status: str | None = None):
    from arbitrage_catalog import get_catalog

    return get_catalog(category=category, status=status)


@app.get("/api/arbitrage/catalog/scan")
async def arbitrage_catalog_scan(
    quote_amount: float | None = None,
    min_score: float = 0.0,
    _user: dict | None = Depends(require_feature("arbitrage_catalog")),
):
    from arbitrage_catalog import scan_arbitrage_catalog

    return await scan_arbitrage_catalog(quote_amount=quote_amount, min_score=min_score)


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
async def weekly_report_endpoint(persist: bool = True):
    from weekly_report import build_weekly_report

    return await build_weekly_report(persist=persist)


@app.get("/api/reports/weekly/history")
async def weekly_report_history(limit: int = 12):
    from database import fetch_weekly_reports

    return {"reports": await fetch_weekly_reports(limit=limit)}


@app.get("/api/reports/weekly/markdown")
async def weekly_report_markdown():
    from weekly_report import build_weekly_report, report_to_markdown

    report = await build_weekly_report(persist=False)
    body = report_to_markdown(report)
    return Response(content=body, media_type="text/markdown; charset=utf-8")


@app.get("/api/reports/daily")
async def daily_report_endpoint(persist: bool = True):
    from daily_report import build_daily_report

    return await build_daily_report(persist=persist)


@app.get("/api/reports/daily/markdown")
async def daily_report_markdown():
    from daily_report import build_daily_report, daily_report_markdown as to_md

    report = await build_daily_report(persist=False)
    return Response(content=to_md(report), media_type="text/markdown; charset=utf-8")


@app.get("/api/ta/{symbol}")
async def ta_bundle(symbol: str):
    from technical_analysis import build_ta_bundle

    return await build_ta_bundle(symbol.upper())


@app.get("/api/arbitrage/pricing-errors/{symbol}")
async def arbitrage_pricing_errors(symbol: str):
    from arbitrage_service import compare_symbol_across_exchanges

    compare = await compare_symbol_across_exchanges(symbol)
    return compare.get("pricing_errors") or {"opportunities": [], "symbol": symbol}


@app.get("/api/database/health")
async def database_health():
    from db_upgrade import database_health_report

    return await database_health_report()


@app.post("/api/database/maintenance")
async def database_maintenance(vacuum: bool = False):
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


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "BLACKDARK",
        "version": "1.0.0",
        "ui_language": "en",
    }


@app.get("/api/build-info")
async def build_info():
    """Verify which commit Railway is actually running."""
    return {
        "ui_language": "en",
        "release": "2026-07-24-launch-en-v2",
        "git_commit": os.getenv("RAILWAY_GIT_COMMIT_SHA") or os.getenv("GIT_COMMIT"),
        "git_branch": os.getenv("RAILWAY_GIT_BRANCH"),
        "git_message": os.getenv("RAILWAY_GIT_COMMIT_MESSAGE"),
        "service": "blackdark",
    }

@app.post("/portfolio/analyze")
async def portfolio_analyze(assets: list = Body(...)):
    if not assets:
        raise HTTPException(status_code=400, detail="No assets provided")
    return await _analyze_portfolio_holdings(assets)

@app.post("/join-waitlist")
async def join_waitlist(data: dict):
    from database import insert_waitlist_signup

    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Valid email required")

    result = await insert_waitlist_signup(email, name)
    if result.get("duplicate"):
        raise HTTPException(status_code=409, detail="Email already registered")

    position = result.get("position", 0)
    return {
        "success": True,
        "position": position,
        "message": f"Welcome to the dark side! You are #{position} on the waitlist.",
    }


@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """Telegram Bot API webhook — /start subscribes to 3 free alerts/day."""
    from alert_service import send_telegram_message
    from telegram_free_alerts import handle_bot_command

    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    message = data.get("message") or data.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = str(message.get("text") or "").strip()
    username = chat.get("username")

    if not chat_id or not text:
        return {"ok": True}

    if text.startswith("/"):
        reply = await handle_bot_command(str(chat_id), text, username=username)
        if reply:
            await send_telegram_message(reply, chat_id=str(chat_id))
    return {"ok": True}


@app.get("/api/telegram/free/status")
async def telegram_free_status():
    from database import count_telegram_free_subscribers
    from telegram_free_alerts import FREE_DAILY_ALERT_LIMIT

    return {
        "enabled": os.getenv("TELEGRAM_FREE_ALERTS_ENABLED", "true").lower() in {"1", "true", "yes"},
        "daily_limit": FREE_DAILY_ALERT_LIMIT,
        "active_subscribers": await count_telegram_free_subscribers(),
        "bot_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "bot_username": os.getenv("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@"),
        "commands": ["/start", "/stop", "/status", "/accuracy"],
    }


@app.post("/api/telegram/free/broadcast")
async def telegram_free_broadcast():
    from telegram_free_alerts import dispatch_free_telegram_alerts

    return await dispatch_free_telegram_alerts()


def _create_stripe_checkout(tier: str, customer_email: str | None = None, user_id: int | None = None) -> dict:
    from billing_service import create_checkout_session, stripe_configured

    if not stripe_configured():
        raise HTTPException(status_code=503, detail="Stripe not configured")
    try:
        return create_checkout_session(tier, customer_email=customer_email, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/create-checkout-session")
async def checkout_get(tier: str = "pro", user: dict | None = Depends(optional_user)):
    """Landing page links use GET — redirect straight to Stripe."""
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


@app.get("/success", response_class=HTMLResponse)
async def checkout_success(request: Request):
    return templates.TemplateResponse(request, "success.html")


@app.get("/cancel", response_class=HTMLResponse)
async def checkout_cancel(request: Request):
    return HTMLResponse(
        "<html><body style='background:#0a0a0f;color:#e4e4e7;font-family:sans-serif;"
        "text-align:center;padding:4rem'><h1>Checkout cancelled</h1>"
        "<p><a href='/' style='color:#22d3ee'>Back to BLACKDARK</a></p></body></html>"
    )


@app.get("/landing", response_class=HTMLResponse)
async def landing_alias(request: Request):
    return templates.TemplateResponse(request, "landing.html")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)

