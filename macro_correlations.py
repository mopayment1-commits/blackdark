"""
BLACKDARK — Macro Liquidity & Traditional Markets Correlation Index (Phase 4).

Polls DXY, S&P 500, and BTC/Gold ratio signals, classifies macro regime,
persists logs, and exposes slippage/score weight hooks for the engine.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

import aiohttp
from pydantic import BaseModel, Field

import config
from database import fetch_latest_macro_market_log, init_db, insert_macro_market_log

logger = logging.getLogger("BLACKDARK.MacroCorrelations")

MacroRegime = Literal["Risk-On", "Risk-Off", "Neutral"]
MacroSource = Literal["yahoo", "mock", "cache"]


class MacroIndicators(BaseModel):
    dxy_score: float
    spx_score: float
    btc_gold_ratio: float
    btc_gold_score: float
    source: MacroSource = "mock"
    timestamp: str


class MacroRegimeSnapshot(BaseModel):
    dxy_score: float
    spx_score: float
    btc_gold_ratio: float
    btc_gold_score: float
    macro_regime: MacroRegime
    volatility_buffer: float = Field(ge=0.0)
    slippage_multiplier: float = Field(gt=0.0)
    score_weight: float = Field(gt=0.0)
    timestamp: str
    source: MacroSource = "mock"


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _stable_noise(label: str, salt: str) -> float:
    digest = hashlib.sha256(
        f"{label}:{salt}:{int(time.time() // config.MACRO_POLL_INTERVAL_SECONDS)}".encode()
    ).hexdigest()
    return (int(digest[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0


def _mock_macro_indicators() -> MacroIndicators:
    dxy_score = round(_stable_noise("dxy", "macro") * 0.35, 4)
    spx_score = round(_stable_noise("spx", "macro") * 0.45, 4)
    btc_gold_ratio = round(8.5 + _stable_noise("btc_gold_ratio", "macro") * 0.8, 4)
    btc_gold_score = round(_stable_noise("btc_gold", "macro") * 0.25, 4)
    return MacroIndicators(
        dxy_score=dxy_score,
        spx_score=spx_score,
        btc_gold_ratio=btc_gold_ratio,
        btc_gold_score=btc_gold_score,
        source="mock",
        timestamp=_utcnow_iso(),
    )


async def _fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    *,
    params: dict[str, Any] | None = None,
) -> Any:
    async with session.get(url, params=params) as response:
        response.raise_for_status()
        return await response.json()


async def _fetch_yahoo_pct_change(
    session: aiohttp.ClientSession,
    symbol: str,
) -> float | None:
    try:
        payload = await _fetch_json(
            session,
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            params={"interval": "1d", "range": "5d"},
        )
        result = (payload.get("chart") or {}).get("result") or []
        if not result:
            return None
        closes = (
            ((result[0].get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
        )
        valid = [float(value) for value in closes if value is not None]
        if len(valid) < 2 or valid[-2] == 0:
            return None
        return round((valid[-1] - valid[-2]) / valid[-2], 4)
    except Exception:
        logger.warning("Yahoo macro fetch failed safely | symbol=%s", symbol)
        return None


async def _fetch_yahoo_last_price(
    session: aiohttp.ClientSession,
    symbol: str,
) -> float | None:
    try:
        payload = await _fetch_json(
            session,
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            params={"interval": "1d", "range": "1d"},
        )
        result = (payload.get("chart") or {}).get("result") or []
        if not result:
            return None
        closes = (
            ((result[0].get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
        )
        valid = [float(value) for value in closes if value is not None]
        return valid[-1] if valid else None
    except Exception:
        logger.warning("Yahoo price fetch failed safely | symbol=%s", symbol)
        return None


async def fetch_macro_indicators() -> MacroIndicators:
    """
    Pull or mock real-time macro indicators for DXY, SPX, and BTC/Gold ratio.
    """
    if config.MACRO_DATA_SOURCE == "mock":
        return _mock_macro_indicators()

    timeout = aiohttp.ClientTimeout(total=config.MACRO_FETCH_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        dxy_task = _fetch_yahoo_pct_change(session, config.MACRO_YAHOO_DXY_SYMBOL)
        spx_task = _fetch_yahoo_pct_change(session, config.MACRO_YAHOO_SPX_SYMBOL)
        btc_task = _fetch_yahoo_last_price(session, config.MACRO_YAHOO_BTC_SYMBOL)
        gold_task = _fetch_yahoo_last_price(session, config.MACRO_YAHOO_GOLD_SYMBOL)
        results = await asyncio.gather(
            dxy_task,
            spx_task,
            btc_task,
            gold_task,
            return_exceptions=True,
        )

    dxy_score = results[0] if isinstance(results[0], float) else None
    spx_score = results[1] if isinstance(results[1], float) else None
    btc_price = results[2] if isinstance(results[2], float) else None
    gold_price = results[3] if isinstance(results[3], float) else None

    if config.MACRO_DATA_SOURCE == "mixed" and (
        dxy_score is None or spx_score is None or btc_price is None or gold_price is None
    ):
        mock = _mock_macro_indicators()
        return MacroIndicators(
            dxy_score=dxy_score if dxy_score is not None else mock.dxy_score,
            spx_score=spx_score if spx_score is not None else mock.spx_score,
            btc_gold_ratio=(
                round(btc_price / gold_price, 4)
                if btc_price and gold_price
                else mock.btc_gold_ratio
            ),
            btc_gold_score=mock.btc_gold_score,
            source="mock" if dxy_score is None and spx_score is None else "yahoo",
            timestamp=_utcnow_iso(),
        )

    if dxy_score is None or spx_score is None or not btc_price or not gold_price:
        logger.warning("Macro indicator fetch incomplete; using mock fallback.")
        return _mock_macro_indicators()

    btc_gold_ratio = round(btc_price / gold_price, 4)
    return MacroIndicators(
        dxy_score=dxy_score,
        spx_score=spx_score,
        btc_gold_ratio=btc_gold_ratio,
        btc_gold_score=round((btc_gold_ratio / 8.5) - 1.0, 4),
        source="yahoo",
        timestamp=_utcnow_iso(),
    )


def compute_macro_regime(indicators: MacroIndicators) -> MacroRegimeSnapshot:
    """
    Classify the macro environment as Risk-On, Risk-Off, or Neutral.

    Risk-On: stocks rising, dollar falling.
    Risk-Off: dollar spiking, stocks crashing.
    """
    dxy_score = indicators.dxy_score
    spx_score = indicators.spx_score

    risk_off = (
        dxy_score >= config.MACRO_RISK_OFF_DXY_THRESHOLD
        and spx_score <= config.MACRO_RISK_OFF_SPX_THRESHOLD
    )
    risk_on = (
        dxy_score <= config.MACRO_RISK_ON_DXY_THRESHOLD
        and spx_score >= config.MACRO_RISK_ON_SPX_THRESHOLD
    )

    if risk_off:
        regime: MacroRegime = "Risk-Off"
        volatility_buffer = config.MACRO_VOLATILITY_BUFFER_RISK_OFF
        slippage_multiplier = config.MACRO_SLIPPAGE_MULTIPLIER_RISK_OFF
        score_weight = config.MACRO_SCORE_WEIGHT_RISK_OFF
    elif risk_on:
        regime = "Risk-On"
        volatility_buffer = config.MACRO_VOLATILITY_BUFFER_RISK_ON
        slippage_multiplier = config.MACRO_SLIPPAGE_MULTIPLIER_RISK_ON
        score_weight = config.MACRO_SCORE_WEIGHT_RISK_ON
    else:
        regime = "Neutral"
        volatility_buffer = config.MACRO_VOLATILITY_BUFFER_NEUTRAL
        slippage_multiplier = config.MACRO_SLIPPAGE_MULTIPLIER_NEUTRAL
        score_weight = config.MACRO_SCORE_WEIGHT_NEUTRAL

    return MacroRegimeSnapshot(
        dxy_score=dxy_score,
        spx_score=spx_score,
        btc_gold_ratio=indicators.btc_gold_ratio,
        btc_gold_score=indicators.btc_gold_score,
        macro_regime=regime,
        volatility_buffer=volatility_buffer,
        slippage_multiplier=slippage_multiplier,
        score_weight=score_weight,
        timestamp=indicators.timestamp,
        source=indicators.source,
    )


def macro_context_from_snapshot(snapshot: MacroRegimeSnapshot) -> dict[str, Any]:
    return {
        "macro_regime": snapshot.macro_regime,
        "macro_dxy_score": snapshot.dxy_score,
        "macro_spx_score": snapshot.spx_score,
        "macro_btc_gold_ratio": snapshot.btc_gold_ratio,
        "macro_btc_gold_score": snapshot.btc_gold_score,
        "macro_volatility_buffer": snapshot.volatility_buffer,
        "macro_slippage_multiplier": snapshot.slippage_multiplier,
        "macro_score_weight": snapshot.score_weight,
        "macro_timestamp": snapshot.timestamp,
        "macro_source": snapshot.source,
    }


def macro_context_from_row(row: dict[str, Any]) -> dict[str, Any]:
    indicators = MacroIndicators(
        dxy_score=float(row.get("dxy_score") or 0.0),
        spx_score=float(row.get("spx_score") or 0.0),
        btc_gold_ratio=float(row.get("btc_gold_ratio") or 0.0),
        btc_gold_score=float(row.get("btc_gold_score") or 0.0),
        source="cache",
        timestamp=str(row.get("timestamp") or _utcnow_iso()),
    )
    snapshot = compute_macro_regime(indicators)
    snapshot.volatility_buffer = float(row.get("volatility_buffer") or snapshot.volatility_buffer)
    return macro_context_from_snapshot(snapshot)


async def persist_macro_regime(snapshot: MacroRegimeSnapshot) -> None:
    await insert_macro_market_log(
        dxy_score=snapshot.dxy_score,
        spx_score=snapshot.spx_score,
        macro_regime=snapshot.macro_regime,
        volatility_buffer=snapshot.volatility_buffer,
        timestamp=snapshot.timestamp,
    )


async def get_latest_macro_regime() -> dict[str, Any]:
    """Export hook: latest macro regime context for valuation."""
    try:
        row = await fetch_latest_macro_market_log()
        if row:
            return macro_context_from_row(
                {
                    **row,
                    "btc_gold_ratio": row.get("btc_gold_ratio", 0.0),
                    "btc_gold_score": row.get("btc_gold_score", 0.0),
                }
            )
    except Exception:
        logger.exception("Latest macro regime load failed safely.")

    snapshot = compute_macro_regime(_mock_macro_indicators())
    return macro_context_from_snapshot(snapshot)


async def build_macro_context() -> dict[str, Any]:
    indicators = await fetch_macro_indicators()
    snapshot = compute_macro_regime(indicators)
    await persist_macro_regime(snapshot)
    return macro_context_from_snapshot(snapshot)


async def build_macro_context_safe() -> dict[str, Any]:
    try:
        return await build_macro_context()
    except Exception:
        logger.exception("Macro context build failed safely; returning neutral defaults.")
        snapshot = compute_macro_regime(_mock_macro_indicators())
        return macro_context_from_snapshot(snapshot)


def merge_macro_context(
    base_context: dict[str, Any] | None,
    macro_context: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = dict(base_context or {})
    if macro_context:
        merged.update(macro_context)
    return merged


def macro_volatility_buffer_bps(context: dict[str, Any] | None) -> float:
    if not context:
        return config.SLIPPAGE_BUFFER_BPS
    try:
        return float(context.get("macro_volatility_buffer", config.SLIPPAGE_BUFFER_BPS))
    except Exception:
        return config.SLIPPAGE_BUFFER_BPS


def macro_slippage_multiplier(context: dict[str, Any] | None) -> float:
    if not context:
        return 1.0
    try:
        return max(0.1, float(context.get("macro_slippage_multiplier", 1.0)))
    except Exception:
        return 1.0


def macro_score_weight(context: dict[str, Any] | None) -> float:
    if not context:
        return 1.0
    try:
        return max(0.1, float(context.get("macro_score_weight", 1.0)))
    except Exception:
        return 1.0


def apply_macro_score_weight(score: float, context: dict[str, Any] | None) -> float:
    return round(score * macro_score_weight(context), 2)


@dataclass
class MacroCorrelationsEngine:
    """Async macro polling service for the arbitrage engine."""

    _shutdown: asyncio.Event = field(default_factory=asyncio.Event)
    _last_cycle_at: float = field(default=0.0)

    async def close(self) -> None:
        self._shutdown.set()

    async def run_cycle(self, *, force: bool = False) -> dict[str, Any]:
        now = time.monotonic()
        if (
            not force
            and self._last_cycle_at > 0.0
            and (now - self._last_cycle_at) < config.MACRO_POLL_INTERVAL_SECONDS
        ):
            try:
                return await get_latest_macro_regime()
            except Exception:
                logger.exception("Cached macro regime load failed; refreshing cycle.")

        await init_db()
        context = await build_macro_context_safe()
        self._last_cycle_at = time.monotonic()
        logger.info(
            "Macro cycle complete | regime=%s dxy=%+.3f spx=%+.3f buffer=%.1fbps slip_x=%.2f score_x=%.2f",
            context.get("macro_regime"),
            float(context.get("macro_dxy_score", 0.0)),
            float(context.get("macro_spx_score", 0.0)),
            float(context.get("macro_volatility_buffer", 0.0)),
            float(context.get("macro_slippage_multiplier", 1.0)),
            float(context.get("macro_score_weight", 1.0)),
        )
        return context

    async def run_loop(self) -> None:
        logger.info(
            "Macro correlations loop started | interval=%ss source=%s",
            config.MACRO_POLL_INTERVAL_SECONDS,
            config.MACRO_DATA_SOURCE,
        )
        while not self._shutdown.is_set():
            try:
                await self.run_cycle()
            except Exception:
                logger.exception("Macro cycle failed; continuing.")

            try:
                await asyncio.wait_for(
                    self._shutdown.wait(),
                    timeout=config.MACRO_POLL_INTERVAL_SECONDS,
                )
                break
            except TimeoutError:
                continue

        logger.info("Macro correlations loop stopped.")
