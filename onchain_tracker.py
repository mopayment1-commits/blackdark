"""
BLACKDARK — On-Chain Inflow/Outflow Whale Tracker Matrix (Point 42).

Models large exchange deposit/withdrawal flows, classifies distribution vs
accumulation regimes, and exposes multi-modal scoring hooks for the engine.
"""

from __future__ import annotations

import hashlib
import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

import aiohttp
from pydantic import BaseModel, Field

import config
logger = logging.getLogger("BLACKDARK.OnChainTracker")

SignalType = Literal["distribution_risk", "accumulation_signal"]
FlowSource = Literal["simulated", "api"]


class ExchangeFlowMetrics(BaseModel):
    asset: str
    inflow_usd: float = Field(ge=0)
    outflow_usd: float = Field(ge=0)
    net_flow_usd: float
    large_tx_count: int = Field(ge=0)
    source: FlowSource = "simulated"
    timestamp: str


class OnChainSignal(BaseModel):
    signal_type: SignalType
    asset: str
    net_flow_usd: float
    inflow_usd: float
    outflow_usd: float
    z_score: float
    severity: float = Field(ge=0.0, le=100.0)
    message: str


class AssetOnChainStatus(BaseModel):
    asset: str
    net_flow_usd: float
    inflow_usd: float
    outflow_usd: float
    bias: Literal["distribution", "accumulation", "neutral"]
    signals: list[OnChainSignal] = Field(default_factory=list)


@dataclass
class _NetFlowHistory:
    values: deque[float] = field(default_factory=lambda: deque(maxlen=config.ONCHAIN_HISTORY_WINDOW))


_net_flow_history: dict[str, _NetFlowHistory] = defaultdict(_NetFlowHistory)


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _stable_noise(asset: str, salt: str) -> float:
    digest = hashlib.sha256(f"{asset}:{salt}:{int(time.time() // 300)}".encode()).hexdigest()
    return (int(digest[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0


def _simulate_asset_flow(asset: str) -> ExchangeFlowMetrics:
    """
    Deterministic simulated exchange flow snapshot.

    Used when no external on-chain API is configured.
    """
    base_scale = {
        "BTC": 8_000_000.0,
        "ETH": 4_500_000.0,
        "SOL": 1_800_000.0,
        "BNB": 900_000.0,
        "XRP": 700_000.0,
    }.get(asset, 500_000.0)

    inflow_noise = _stable_noise(asset, "inflow")
    outflow_noise = _stable_noise(asset, "outflow")
    inflow_usd = max(0.0, base_scale * (1.0 + inflow_noise * 0.35))
    outflow_usd = max(0.0, base_scale * (1.0 + outflow_noise * 0.35))
    net_flow_usd = inflow_usd - outflow_usd
    large_tx_count = max(0, int(abs(net_flow_usd) / config.ONCHAIN_LARGE_FLOW_USD))

    return ExchangeFlowMetrics(
        asset=asset,
        inflow_usd=round(inflow_usd, 2),
        outflow_usd=round(outflow_usd, 2),
        net_flow_usd=round(net_flow_usd, 2),
        large_tx_count=large_tx_count,
        source="simulated",
        timestamp=_utcnow_iso(),
    )


async def _fetch_onchain_flows_api(session: aiohttp.ClientSession) -> list[ExchangeFlowMetrics]:
    url = str(config.ONCHAIN_API_URL or "").strip()
    if not url:
        return []

    timeout = aiohttp.ClientTimeout(total=config.ONCHAIN_FETCH_TIMEOUT_SECONDS)
    headers = {}
    if config.ONCHAIN_API_KEY:
        headers["Authorization"] = f"Bearer {config.ONCHAIN_API_KEY}"

    async with session.get(url, headers=headers, timeout=timeout) as response:
        response.raise_for_status()
        payload = await response.json()

    rows = payload.get("flows") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return []

    flows: list[ExchangeFlowMetrics] = []
    for row in rows:
        try:
            asset = str(row.get("asset") or row.get("symbol") or "").upper()
            if not asset:
                continue
            inflow_usd = float(row.get("inflow_usd") or row.get("inflow") or 0.0)
            outflow_usd = float(row.get("outflow_usd") or row.get("outflow") or 0.0)
            flows.append(
                ExchangeFlowMetrics(
                    asset=asset,
                    inflow_usd=max(0.0, inflow_usd),
                    outflow_usd=max(0.0, outflow_usd),
                    net_flow_usd=inflow_usd - outflow_usd,
                    large_tx_count=int(row.get("large_tx_count") or 0),
                    source="api",
                    timestamp=str(row.get("timestamp") or _utcnow_iso()),
                )
            )
        except (TypeError, ValueError):
            logger.warning(
                "Skipping malformed on-chain flow row: %s",
                str(row).replace("\r", " ").replace("\n", " "),
            )
            continue
    return flows


async def _fetch_api_flows_with_simulated_missing(
    assets: list[str],
) -> list[ExchangeFlowMetrics] | None:
    session: aiohttp.ClientSession | None = None
    try:
        session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=config.ONCHAIN_FETCH_TIMEOUT_SECONDS)
        )
        api_flows = await _fetch_onchain_flows_api(session)
        if not api_flows:
            return None
        present = {flow.asset for flow in api_flows}
        flows = list(api_flows)
        for asset in assets:
            if asset not in present:
                flows.append(_simulate_asset_flow(asset))
        return flows
    except Exception:
        logger.exception("On-chain API fetch failed safely; falling back to simulation.")
        return None
    finally:
        if session is not None and not session.closed:
            await session.close()


async def process_onchain_flows() -> list[ExchangeFlowMetrics]:
    """
    Parse or simulate exchange inflow/outflow metrics for core assets.

    Never raises; returns simulated metrics on fetch/parse failure.
    """
    assets = list(config.CORE_COINS)
    source = str(config.ONCHAIN_DATA_SOURCE or "simulated").strip().lower()

    if source == "api" and config.ONCHAIN_API_URL:
        flows = await _fetch_api_flows_with_simulated_missing(assets)
        if flows is not None:
            return flows

    return [_simulate_asset_flow(asset) for asset in assets]


def _update_net_flow_history(asset: str, net_flow_usd: float) -> list[float]:
    history = _net_flow_history[asset]
    history.values.append(net_flow_usd)
    return list(history.values)


def classify_onchain_signal(
    flow: ExchangeFlowMetrics,
    *,
    history: list[float] | None = None,
) -> OnChainSignal | None:
    """
    Distribution & accumulation signal engine.

    Net inflow spike  -> Distribution Risk (sell pressure)
    Net outflow spike -> Accumulation Signal (buy support)
    """
    try:
        hist = history if history is not None else _update_net_flow_history(
            flow.asset, flow.net_flow_usd
        )
        if len(hist) < config.ONCHAIN_MIN_HISTORY_POINTS:
            return None

        mean_net = statistics.fmean(hist)
        stdev = statistics.pstdev(hist) if len(hist) > 1 else abs(mean_net) or 1e-6
        stdev = max(stdev, config.ONCHAIN_MIN_STDEV_USD)
        z_score = (flow.net_flow_usd - mean_net) / stdev

        signal_type: SignalType | None = None
        if flow.net_flow_usd > 0 and z_score >= config.ONCHAIN_SPIKE_Z_THRESHOLD:
            signal_type = "distribution_risk"
        elif flow.net_flow_usd < 0 and z_score <= -config.ONCHAIN_SPIKE_Z_THRESHOLD:
            signal_type = "accumulation_signal"

        if signal_type is None:
            return None

        severity = min(
            100.0,
            abs(z_score) * 15.0 + (abs(flow.net_flow_usd) / config.ONCHAIN_LARGE_FLOW_USD) * 10.0,
        )
        if signal_type == "distribution_risk":
            message = (
                f"Distribution Risk on {flow.asset}: exchange inflow spike "
                f"${flow.net_flow_usd:,.0f} net (z={z_score:.2f})."
            )
        else:
            message = (
                f"Accumulation Signal on {flow.asset}: exchange outflow spike "
                f"${abs(flow.net_flow_usd):,.0f} net (z={z_score:.2f})."
            )

        return OnChainSignal(
            signal_type=signal_type,
            asset=flow.asset,
            net_flow_usd=flow.net_flow_usd,
            inflow_usd=flow.inflow_usd,
            outflow_usd=flow.outflow_usd,
            z_score=round(z_score, 4),
            severity=round(severity, 2),
            message=message,
        )
    except Exception:
        logger.exception(
            "On-chain signal classification failed | asset=%s",
            str(flow.asset).replace("\r", " ").replace("\n", " "),
        )
        return None


def _asset_bias(net_flow_usd: float) -> Literal["distribution", "accumulation", "neutral"]:
    if net_flow_usd >= config.ONCHAIN_NEUTRAL_BAND_USD:
        return "distribution"
    if net_flow_usd <= -config.ONCHAIN_NEUTRAL_BAND_USD:
        return "accumulation"
    return "neutral"


def _status_bias_and_signals(status: Any) -> tuple[str, list[Any]]:
    if isinstance(status, dict):
        return str(status.get("bias") or "neutral"), status.get("signals") or []
    return status.bias, status.signals


def _onchain_signal_score_delta(signal: Any) -> tuple[float, float]:
    if isinstance(signal, dict):
        severity = float(signal.get("severity") or 0.0)
        signal_type = str(signal.get("signal_type") or "")
    else:
        severity = float(signal.severity)
        signal_type = signal.signal_type
    weight = severity / 100.0
    if signal_type == "accumulation_signal":
        return config.ONCHAIN_SCORE_BOOST_MAX * weight, 0.0
    if signal_type == "distribution_risk":
        return 0.0, config.ONCHAIN_DISTRIBUTION_PENALTY_MAX * weight
    return 0.0, 0.0


def analyze_onchain_flows(
    flows: list[ExchangeFlowMetrics],
) -> tuple[list[OnChainSignal], dict[str, AssetOnChainStatus]]:
    signals: list[OnChainSignal] = []
    statuses: dict[str, AssetOnChainStatus] = {}

    for flow in flows:
        try:
            history = _update_net_flow_history(flow.asset, flow.net_flow_usd)
            signal = classify_onchain_signal(flow, history=history)
            asset_signals = [signal] if signal is not None else []
            if signal is not None:
                signals.append(signal)

            statuses[flow.asset] = AssetOnChainStatus(
                asset=flow.asset,
                net_flow_usd=flow.net_flow_usd,
                inflow_usd=flow.inflow_usd,
                outflow_usd=flow.outflow_usd,
                bias=_asset_bias(flow.net_flow_usd),
                signals=asset_signals,
            )
        except Exception:
            logger.exception(
                "On-chain flow analysis failed | asset=%s",
                str(flow.asset).replace("\r", " ").replace("\n", " "),
            )
            continue

    return signals, statuses


def onchain_score_adjustment_for_asset(asset: str, context: dict[str, Any]) -> float:
    """Map on-chain posture into Opportunity Score boost/penalty."""
    try:
        adjustments = context.get("onchain_score_adjustments") or {}
        if asset in adjustments:
            return float(adjustments[asset])

        statuses = context.get("onchain_by_asset") or {}
        status = statuses.get(asset)
        if status is None:
            return 0.0

        bias, signals = _status_bias_and_signals(status)

        boost = 0.0
        penalty = 0.0
        if bias == "accumulation":
            boost = config.ONCHAIN_SCORE_BOOST_MAX * 0.6
        elif bias == "distribution":
            penalty = config.ONCHAIN_DISTRIBUTION_PENALTY_MAX * 0.5

        for signal in signals:
            signal_boost, signal_penalty = _onchain_signal_score_delta(signal)
            boost += signal_boost
            penalty += signal_penalty

        return round(
            max(
                -config.ONCHAIN_DISTRIBUTION_PENALTY_MAX,
                min(config.ONCHAIN_SCORE_BOOST_MAX, boost - penalty),
            ),
            2,
        )
    except Exception:
        logger.exception("On-chain score adjustment failed | asset=%s", str(asset).replace("\r", " ").replace("\n", " "))
        return 0.0


def get_onchain_status_for_asset(asset: str, context: dict[str, Any]) -> dict[str, Any] | None:
    status = (context.get("onchain_by_asset") or {}).get(asset)
    if status is None:
        return None
    return status if isinstance(status, dict) else status.model_dump()


def get_oracle_onchain_clause(asset: str, context: dict[str, Any] | None) -> str | None:
    """Short clause injected into the single-sentence oracle output."""
    if not context:
        return None
    try:
        status = get_onchain_status_for_asset(asset, context)
        if not status:
            return None

        signals = status.get("signals") or []
        if signals:
            top = signals[0]
            if isinstance(top, dict):
                return str(top.get("message") or top.get("signal_type"))
            return str(getattr(top, "message", None) or getattr(top, "signal_type", None))

        bias = str(status.get("bias") or "neutral")
        net_flow = float(status.get("net_flow_usd") or 0.0)
        if bias == "neutral":
            return f"On-chain exchange flow neutral (${net_flow:+,.0f} net)."
        label = "Accumulation support" if bias == "accumulation" else "Distribution pressure"
        return f"{label} on-chain (${net_flow:+,.0f} net exchange flow)."
    except Exception:
        return None


def inject_oracle_onchain_analytics(
    oracle_sentence: str,
    asset: str,
    context: dict[str, Any] | None,
) -> str:
    clause = get_oracle_onchain_clause(asset, context)
    if not clause:
        return oracle_sentence
    return f"{oracle_sentence} On-chain: {clause}"


async def build_onchain_context() -> dict[str, Any]:
    flows = await process_onchain_flows()
    signals, statuses = analyze_onchain_flows(flows)

    status_payload = {key: value.model_dump() for key, value in statuses.items()}
    signal_payload = [signal.model_dump() for signal in signals]
    score_adjustments = {
        asset: onchain_score_adjustment_for_asset(
            asset,
            {
                "onchain_by_asset": status_payload,
                "onchain_signals": signal_payload,
            },
        )
        for asset in status_payload
    }

    base = {
        "onchain_flows": [flow.model_dump() for flow in flows],
        "onchain_signals": signal_payload,
        "onchain_by_asset": status_payload,
        "onchain_score_adjustments": score_adjustments,
    }
    try:
        from blackdark.ingestion.exchange_flow_metric import enrich_onchain_context

        return await enrich_onchain_context(base)
    except Exception:
        logger.debug("token exchange flow enrichment skipped")
        return base


async def build_onchain_context_safe() -> dict[str, Any]:
    try:
        return await build_onchain_context()
    except Exception:
        logger.exception("On-chain context build failed safely; returning empty context.")
        return {
            "onchain_flows": [],
            "onchain_signals": [],
            "onchain_by_asset": {},
            "onchain_score_adjustments": {},
        }


def merge_onchain_context(
    base_context: dict[str, Any] | None,
    onchain_context: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = dict(base_context or {})
    if onchain_context:
        merged.update(onchain_context)
    return merged
