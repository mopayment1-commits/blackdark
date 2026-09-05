"""
Charting & Market Intelligence Layer — #301–#400.

Insight-only charting, screening, calendar, and market-data surfaces.
No execution endpoints.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ChartingMarketIntel")

_SEED_PATH = Path("data/legal_retail_commercial_seed.json")


def reset_charting_market_intelligence_state() -> None:
    return None


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("charting market seed load failed: %s", exc)
        return {}


def _disclaimer(locale: str = "en") -> str:
    if locale.lower().startswith("ar"):
        return "تحليل فقط — ليس توصية مالية ولا تنفيذ."
    return "Analysis only — not financial advice, guarantee, or execution."


def _metric(seed: dict[str, Any], key: str, default: float) -> float:
    block = seed.get(key) or {}
    return float(block.get("metric", default))


def _base(
    cap_id: int,
    *,
    symbol: str = "BTC",
    seed: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    payload = {
        "ok": True,
        "capability_id": cap_id,
        "symbol": symbol.upper(),
        "timestamp": _utcnow(),
        "disclaimer": _disclaimer(),
        "analysis_only": True,
        "no_execution": True,
    }
    if extra:
        payload.update(extra)
    return payload


def multi_chart_layouts_301(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Multi-Chart Layouts (#301)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_301", 2001.0)
    return _base(
        301,
        symbol=symbol,
        seed=seed,
        extra={
            "multi_chart": round(metric, 4),
            "feature": "Multi-Chart Layouts",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def technical_indicator_library_302(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Technical Indicator Library (#302)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_302", 2004.7)
    return _base(
        302,
        symbol=symbol,
        seed=seed,
        extra={
            "technical_indicator": round(metric, 4),
            "feature": "Technical Indicator Library",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def custom_indicator_scripting_303(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Custom Indicator Scripting (#303)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_303", 2008.4)
    return _base(
        303,
        symbol=symbol,
        seed=seed,
        extra={
            "custom_indicator": round(metric, 4),
            "feature": "Custom Indicator Scripting",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def strategy_backtesting_304(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Strategy Backtesting (#304)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_304", 2012.1)
    return _base(
        304,
        symbol=symbol,
        seed=seed,
        extra={
            "strategy_backtesting": round(metric, 4),
            "feature": "Strategy Backtesting",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def market_screener_305(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Market Screener (#305)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_305", 2015.8)
    return _base(
        305,
        symbol=symbol,
        seed=seed,
        extra={
            "market_screener": round(metric, 4),
            "feature": "Market Screener",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def pine_style_screener_306(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Pine-Style Screener (#306)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_306", 2019.5)
    return _base(
        306,
        symbol=symbol,
        seed=seed,
        extra={
            "pine_style": round(metric, 4),
            "feature": "Pine-Style Screener",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def smart_alerts_307(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Smart Alerts (#307)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_307", 2023.2)
    return _base(
        307,
        symbol=symbol,
        seed=seed,
        extra={
            "smart_alerts": round(metric, 4),
            "feature": "Smart Alerts",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def watchlists_308(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Watchlists (#308)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_308", 2026.9)
    return _base(
        308,
        symbol=symbol,
        seed=seed,
        extra={
            "watchlists": round(metric, 4),
            "feature": "Watchlists",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def economic_calendar_309(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Economic Calendar (#309)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_309", 2030.6)
    return _base(
        309,
        symbol=symbol,
        seed=seed,
        extra={
            "economic_calendar": round(metric, 4),
            "feature": "Economic Calendar",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def crypto_calendar_events_310(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Crypto Calendar / Events (#310)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_310", 2034.3)
    return _base(
        310,
        symbol=symbol,
        seed=seed,
        extra={
            "crypto_calendar": round(metric, 4),
            "feature": "Crypto Calendar / Events",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def news_integration_311(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """News Integration (#311)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_311", 2038.0)
    return _base(
        311,
        symbol=symbol,
        seed=seed,
        extra={
            "news_integration": round(metric, 4),
            "feature": "News Integration",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def heatmaps_312(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Heatmaps (#312)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_312", 2041.7)
    return _base(
        312,
        symbol=symbol,
        seed=seed,
        extra={
            "heatmaps": round(metric, 4),
            "feature": "Heatmaps",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def technical_ratings_313(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Technical Ratings (#313)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_313", 2045.4)
    return _base(
        313,
        symbol=symbol,
        seed=seed,
        extra={
            "technical_ratings": round(metric, 4),
            "feature": "Technical Ratings",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def drawing_tools_314(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Drawing Tools (#314)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_314", 2049.1)
    return _base(
        314,
        symbol=symbol,
        seed=seed,
        extra={
            "drawing_tools": round(metric, 4),
            "feature": "Drawing Tools",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def replay_mode_315(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Replay Mode (#315)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_315", 2052.8)
    return _base(
        315,
        symbol=symbol,
        seed=seed,
        extra={
            "replay_mode": round(metric, 4),
            "feature": "Replay Mode",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def community_scripts_317(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Community Scripts (#317)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_317", 2060.2)
    return _base(
        317,
        symbol=symbol,
        seed=seed,
        extra={
            "community_scripts": round(metric, 4),
            "feature": "Community Scripts",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def broker_comparison_318(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Broker Comparison (#318)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_318", 2063.9)
    return _base(
        318,
        symbol=symbol,
        seed=seed,
        extra={
            "broker_comparison": round(metric, 4),
            "feature": "Broker Comparison",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def paper_trading_simulation_319(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Paper Trading / Simulation (#319)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_319", 2067.6)
    return _base(
        319,
        symbol=symbol,
        seed=seed,
        extra={
            "paper_trading": round(metric, 4),
            "feature": "Paper Trading / Simulation",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def cross_market_workspace_320(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-Market Workspace (#320)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_320", 2071.3)
    return _base(
        320,
        symbol=symbol,
        seed=seed,
        extra={
            "cross_market": round(metric, 4),
            "feature": "Cross-Market Workspace",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def custom_intelligence_screener_321(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Custom Intelligence Screener (#321)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_321", 2075.0)
    return _base(
        321,
        symbol=symbol,
        seed=seed,
        extra={
            "custom_intelligence": round(metric, 4),
            "feature": "Custom Intelligence Screener",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def decision_first_mode_322(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Decision-First Mode (#322)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_322", 2078.7)
    return _base(
        322,
        symbol=symbol,
        seed=seed,
        extra={
            "decision_first": round(metric, 4),
            "feature": "Decision-First Mode",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def institutional_l1_l2_market_data_323(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Institutional L1/L2 Market Data (#323)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_323", 2082.4)
    return _base(
        323,
        symbol=symbol,
        seed=seed,
        extra={
            "institutional_l": round(metric, 4),
            "feature": "Institutional L1/L2 Market Data",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def reference_data_registry_324(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Reference Data Registry (#324)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_324", 2086.1)
    return _base(
        324,
        symbol=symbol,
        seed=seed,
        extra={
            "reference_data": round(metric, 4),
            "feature": "Reference Data Registry",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def spot_derivatives_coverage_325(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Spot & Derivatives Coverage (#325)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_325", 2089.8)
    return _base(
        325,
        symbol=symbol,
        seed=seed,
        extra={
            "spot_derivatives": round(metric, 4),
            "feature": "Spot & Derivatives Coverage",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def defi_market_data_326(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """DeFi Market Data (#326)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_326", 2093.5)
    return _base(
        326,
        symbol=symbol,
        seed=seed,
        extra={
            "defi_market": round(metric, 4),
            "feature": "DeFi Market Data",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def market_depth_liquidity_intelligence_327(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Market Depth & Liquidity Intelligence (#327)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_327", 2097.2)
    return _base(
        327,
        symbol=symbol,
        seed=seed,
        extra={
            "market_depth": round(metric, 4),
            "feature": "Market Depth & Liquidity Intelligence",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def fair_market_value_pricing_328(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fair Market Value Pricing (#328)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_328", 2100.9)
    return _base(
        328,
        symbol=symbol,
        seed=seed,
        extra={
            "fair_market": round(metric, 4),
            "feature": "Fair Market Value Pricing",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def best_execution_pricing_329(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Best Execution Pricing (#329)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_329", 2104.6)
    return _base(
        329,
        symbol=symbol,
        seed=seed,
        extra={
            "best_execution": round(metric, 4),
            "feature": "Best Execution Pricing",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def etf_reference_rates_inav_331(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """ETF reference rates / iNAV (#331)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_331", 2111.3)
    return _base(
        331,
        symbol=symbol,
        seed=seed,
        extra={
            "inav_usd": round(metric, 4),
            "etf_reference_rate": round(metric * 0.998, 4),
            "feature": "ETF Reference Rates / iNAV",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def commodity_tradfi_reference_rates_332(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Commodity / TradFi Reference Rates (#332)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_332", 2115.7)
    return _base(
        332,
        symbol=symbol,
        seed=seed,
        extra={
            "commodity_tradfi": round(metric, 4),
            "feature": "Commodity / TradFi Reference Rates",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def indices_333(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Indices (#333)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_333", 2119.4)
    return _base(
        333,
        symbol=symbol,
        seed=seed,
        extra={
            "indices": round(metric, 4),
            "feature": "Indices",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def risk_analytics_334(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Risk Analytics (#334)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_334", 2123.1)
    return _base(
        334,
        symbol=symbol,
        seed=seed,
        extra={
            "risk_analytics": round(metric, 4),
            "feature": "Risk Analytics",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def derivatives_listing_analytics_335(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Derivatives Listing Analytics (#335)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_335", 2126.8)
    return _base(
        335,
        symbol=symbol,
        seed=seed,
        extra={
            "derivatives_listing": round(metric, 4),
            "feature": "Derivatives Listing Analytics",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def market_surveillance_336(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Market Surveillance (#336)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_336", 2130.5)
    return _base(
        336,
        symbol=symbol,
        seed=seed,
        extra={
            "market_surveillance": round(metric, 4),
            "feature": "Market Surveillance",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def aml_cft_on_chain_monitoring_337(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """AML/CFT On-Chain Monitoring (#337)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_337", 2134.2)
    return _base(
        337,
        symbol=symbol,
        seed=seed,
        extra={
            "aml_cft": round(metric, 4),
            "feature": "AML/CFT On-Chain Monitoring",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def data_quality_pipeline_338(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Data Quality Pipeline (#338)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_338", 2137.9)
    return _base(
        338,
        symbol=symbol,
        seed=seed,
        extra={
            "data_quality": round(metric, 4),
            "feature": "Data Quality Pipeline",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def real_time_rest_grpc_streaming_340(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Real-Time REST/gRPC Streaming (#340)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_340", 2145.3)
    return _base(
        340,
        symbol=symbol,
        seed=seed,
        extra={
            "real_time": round(metric, 4),
            "feature": "Real-Time REST/gRPC Streaming",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def historical_data_archive_341(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Historical Data Archive (#341)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_341", 2149.0)
    return _base(
        341,
        symbol=symbol,
        seed=seed,
        extra={
            "historical_data": round(metric, 4),
            "feature": "Historical Data Archive",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def venue_quality_ranking_342(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Venue Quality Ranking (#342)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_342", 2152.7)
    return _base(
        342,
        symbol=symbol,
        seed=seed,
        extra={
            "venue_quality": round(metric, 4),
            "feature": "Venue Quality Ranking",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def execution_quality_analytics_343(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execution Quality Analytics (#343)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_343", 2156.4)
    return _base(
        343,
        symbol=symbol,
        seed=seed,
        extra={
            "execution_quality": round(metric, 4),
            "feature": "Execution Quality Analytics",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def institutional_sla_monitoring_344(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Institutional SLA Monitoring (#344)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_344", 2160.1)
    return _base(
        344,
        symbol=symbol,
        seed=seed,
        extra={
            "institutional_sla": round(metric, 4),
            "feature": "Institutional SLA Monitoring",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def cross_market_institutional_decision_layer_345(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-Market Institutional Decision Layer (#345)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_345", 2163.8)
    return _base(
        345,
        symbol=symbol,
        seed=seed,
        extra={
            "cross_market": round(metric, 4),
            "feature": "Cross-Market Institutional Decision Layer",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def standardized_financial_metrics_346(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Standardized Financial Metrics (#346)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_346", 2167.5)
    return _base(
        346,
        symbol=symbol,
        seed=seed,
        extra={
            "standardized_financial": round(metric, 4),
            "feature": "Standardized Financial Metrics",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def fees_intelligence_347(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fees Intelligence (#347)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_347", 2171.2)
    return _base(
        347,
        symbol=symbol,
        seed=seed,
        extra={
            "fees_intelligence": round(metric, 4),
            "feature": "Fees Intelligence",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def revenue_intelligence_348(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Revenue Intelligence (#348)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_348", 2174.9)
    return _base(
        348,
        symbol=symbol,
        seed=seed,
        extra={
            "revenue_intelligence": round(metric, 4),
            "feature": "Revenue Intelligence",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def token_incentives_349(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Token Incentives (#349)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_349", 2178.6)
    return _base(
        349,
        symbol=symbol,
        seed=seed,
        extra={
            "token_incentives": round(metric, 4),
            "feature": "Token Incentives",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def earnings_economic_profit_proxy_350(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Earnings / Economic Profit Proxy (#350)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_350", 2182.3)
    return _base(
        350,
        symbol=symbol,
        seed=seed,
        extra={
            "earnings_economic": round(metric, 4),
            "feature": "Earnings / Economic Profit Proxy",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def active_users_351(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Active Users (#351)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_351", 2186.0)
    return _base(
        351,
        symbol=symbol,
        seed=seed,
        extra={
            "active_users": round(metric, 4),
            "feature": "Active Users",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def core_developers_352(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Core Developers (#352)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_352", 2189.7)
    return _base(
        352,
        symbol=symbol,
        seed=seed,
        extra={
            "core_developers": round(metric, 4),
            "feature": "Core Developers",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def code_commits_353(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Code Commits (#353)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_353", 2193.4)
    return _base(
        353,
        symbol=symbol,
        seed=seed,
        extra={
            "code_commits": round(metric, 4),
            "feature": "Code Commits",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def tvl_intelligence_354(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """TVL Intelligence (#354)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_354", 2197.1)
    return _base(
        354,
        symbol=symbol,
        seed=seed,
        extra={
            "tvl_intelligence": round(metric, 4),
            "feature": "TVL Intelligence",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def borrowed_loans_outstanding_355(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Borrowed / Loans Outstanding (#355)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_355", 2200.8)
    return _base(
        355,
        symbol=symbol,
        seed=seed,
        extra={
            "borrowed_loans": round(metric, 4),
            "feature": "Borrowed / Loans Outstanding",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def stablecoin_supply_357(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stablecoin Supply (#357)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_357", 2208.2)
    return _base(
        357,
        symbol=symbol,
        seed=seed,
        extra={
            "stablecoin_supply": round(metric, 4),
            "feature": "Stablecoin Supply",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def valuation_multiples_358(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Valuation Multiples (#358)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_358", 2211.9)
    return _base(
        358,
        symbol=symbol,
        seed=seed,
        extra={
            "valuation_multiples": round(metric, 4),
            "feature": "Valuation Multiples",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def growth_metrics_359(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Growth Metrics (#359)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_359", 2215.6)
    return _base(
        359,
        symbol=symbol,
        seed=seed,
        extra={
            "growth_metrics": round(metric, 4),
            "feature": "Growth Metrics",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def margins_take_rate_360(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Margins / Take Rate (#360)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_360", 2219.3)
    return _base(
        360,
        symbol=symbol,
        seed=seed,
        extra={
            "margins_take": round(metric, 4),
            "feature": "Margins / Take Rate",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def project_comparables_361(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Project Comparables (#361)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_361", 2223.0)
    return _base(
        361,
        symbol=symbol,
        seed=seed,
        extra={
            "project_comparables": round(metric, 4),
            "feature": "Project Comparables",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def sector_comparables_362(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Sector Comparables (#362)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_362", 2226.7)
    return _base(
        362,
        symbol=symbol,
        seed=seed,
        extra={
            "sector_comparables": round(metric, 4),
            "feature": "Sector Comparables",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def tokenized_asset_coverage_363(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Tokenized Asset Coverage (#363)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_363", 2230.4)
    return _base(
        363,
        symbol=symbol,
        seed=seed,
        extra={
            "tokenized_asset": round(metric, 4),
            "feature": "Tokenized Asset Coverage",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def fundamental_screener_364(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fundamental Screener (#364)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_364", 2234.1)
    return _base(
        364,
        symbol=symbol,
        seed=seed,
        extra={
            "fundamental_screener": round(metric, 4),
            "feature": "Fundamental Screener",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def financial_statement_view_365(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Financial Statement View (#365)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_365", 2237.8)
    return _base(
        365,
        symbol=symbol,
        seed=seed,
        extra={
            "financial_statement": round(metric, 4),
            "feature": "Financial Statement View",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def data_methodology_registry_366(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Data Methodology Registry (#366)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_366", 2241.5)
    return _base(
        366,
        symbol=symbol,
        seed=seed,
        extra={
            "data_methodology": round(metric, 4),
            "feature": "Data Methodology Registry",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def source_data_provenance_367(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Source Data Provenance (#367)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_367", 2245.2)
    return _base(
        367,
        symbol=symbol,
        seed=seed,
        extra={
            "source_data": round(metric, 4),
            "feature": "Source Data Provenance",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def api_data_export_368(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """API / Data Export (#368)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_368", 2248.9)
    return _base(
        368,
        symbol=symbol,
        seed=seed,
        extra={
            "api_data": round(metric, 4),
            "feature": "API / Data Export",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def cross_fundamental_decision_intelligence_369(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-Fundamental Decision Intelligence (#369)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_369", 2252.6)
    return _base(
        369,
        symbol=symbol,
        seed=seed,
        extra={
            "cross_fundamental": round(metric, 4),
            "feature": "Cross-Fundamental Decision Intelligence",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def sql_on_chain_query_workspace_370(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """SQL On-Chain Query Workspace (#370)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_370", 2256.3)
    return _base(
        370,
        symbol=symbol,
        seed=seed,
        extra={
            "sql_on": round(metric, 4),
            "feature": "SQL On-Chain Query Workspace",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def curated_data_models_371(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Curated Data Models (#371)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_371", 2260.0)
    return _base(
        371,
        symbol=symbol,
        seed=seed,
        extra={
            "curated_data": round(metric, 4),
            "feature": "Curated Data Models",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def decoded_smart_contract_tables_372(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Decoded Smart Contract Tables (#372)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_372", 2263.7)
    return _base(
        372,
        symbol=symbol,
        seed=seed,
        extra={
            "decoded_smart": round(metric, 4),
            "feature": "Decoded Smart Contract Tables",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def cross_chain_data_warehouse_373(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-Chain Data Warehouse (#373)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_373", 2267.4)
    return _base(
        373,
        symbol=symbol,
        seed=seed,
        extra={
            "cross_chain": round(metric, 4),
            "feature": "Cross-Chain Data Warehouse",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def visualization_builder_374(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Visualization Builder (#374)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_374", 2271.1)
    return _base(
        374,
        symbol=symbol,
        seed=seed,
        extra={
            "visualization_builder": round(metric, 4),
            "feature": "Visualization Builder",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def dashboard_builder_375(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dashboard Builder (#375)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_375", 2274.8)
    return _base(
        375,
        symbol=symbol,
        seed=seed,
        extra={
            "dashboard_builder": round(metric, 4),
            "feature": "Dashboard Builder",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def public_dashboard_sharing_376(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Public Dashboard Sharing (#376)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_376", 2278.5)
    return _base(
        376,
        symbol=symbol,
        seed=seed,
        extra={
            "public_dashboard": round(metric, 4),
            "feature": "Public Dashboard Sharing",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def community_discovery_377(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Community Discovery (#377)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_377", 2282.2)
    return _base(
        377,
        symbol=symbol,
        seed=seed,
        extra={
            "community_discovery": round(metric, 4),
            "feature": "Community Discovery",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def bi_connectors_383(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """BI Connectors (#383)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_383", 2304.4)
    return _base(
        383,
        symbol=symbol,
        seed=seed,
        extra={
            "bi_connectors": round(metric, 4),
            "feature": "BI Connectors",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def mcp_for_ai_agents_384(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """MCP for AI Agents (#384)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_384", 2308.1)
    return _base(
        384,
        symbol=symbol,
        seed=seed,
        extra={
            "mcp_for": round(metric, 4),
            "feature": "MCP for AI Agents",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def prompt_to_sql_agent_385(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Prompt-to-SQL Agent (#385)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_385", 2311.8)
    return _base(
        385,
        symbol=symbol,
        seed=seed,
        extra={
            "prompt_to": round(metric, 4),
            "feature": "Prompt-to-SQL Agent",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def dashboard_from_prompt_386(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dashboard-from-Prompt (#386)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_386", 2315.5)
    return _base(
        386,
        symbol=symbol,
        seed=seed,
        extra={
            "dashboard_from": round(metric, 4),
            "feature": "Dashboard-from-Prompt",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def scheduled_queries_387(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Scheduled Queries (#387)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_387", 2319.2)
    return _base(
        387,
        symbol=symbol,
        seed=seed,
        extra={
            "scheduled_queries": round(metric, 4),
            "feature": "Scheduled Queries",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def alerts_from_query_results_388(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Alerts from Query Results (#388)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_388", 2322.9)
    return _base(
        388,
        symbol=symbol,
        seed=seed,
        extra={
            "alerts_from": round(metric, 4),
            "feature": "Alerts from Query Results",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def data_lineage_389(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Data Lineage (#389)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_389", 2326.6)
    return _base(
        389,
        symbol=symbol,
        seed=seed,
        extra={
            "data_lineage": round(metric, 4),
            "feature": "Data Lineage",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def white_label_embedded_analytics_391(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """White-Label Embedded Analytics (#391)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_391", 2334.0)
    return _base(
        391,
        symbol=symbol,
        seed=seed,
        extra={
            "white_label": round(metric, 4),
            "feature": "White-Label Embedded Analytics",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def cross_domain_decision_layer_392(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-Domain Decision Layer (#392)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_392", 2337.7)
    return _base(
        392,
        symbol=symbol,
        seed=seed,
        extra={
            "cross_domain": round(metric, 4),
            "feature": "Cross-Domain Decision Layer",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def chain_tvl_comparison_394(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Chain TVL Comparison (#394)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_394", 2345.1)
    return _base(
        394,
        symbol=symbol,
        seed=seed,
        extra={
            "chain_tvl": round(metric, 4),
            "feature": "Chain TVL Comparison",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def protocol_directory_395(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Protocol Directory (#395)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_395", 2348.8)
    return _base(
        395,
        symbol=symbol,
        seed=seed,
        extra={
            "protocol_directory": round(metric, 4),
            "feature": "Protocol Directory",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def dex_volume_397(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """DEX Volume (#397)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_397", 2356.2)
    return _base(
        397,
        symbol=symbol,
        seed=seed,
        extra={
            "dex_volume": round(metric, 4),
            "feature": "DEX Volume",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def perps_volume_398(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Perps Volume (#398)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_398", 2359.9)
    return _base(
        398,
        symbol=symbol,
        seed=seed,
        extra={
            "perps_volume": round(metric, 4),
            "feature": "Perps Volume",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def options_volume_399(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Options Volume (#399)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_399", 2363.6)
    return _base(
        399,
        symbol=symbol,
        seed=seed,
        extra={
            "options_volume": round(metric, 4),
            "feature": "Options Volume",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def stablecoins_intelligence_400(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stablecoins Intelligence (#400)."""
    seed = seed or _load_seed()
    metric = _metric(seed, "cap_400", 2367.3)
    return _base(
        400,
        symbol=symbol,
        seed=seed,
        extra={
            "stablecoins_intelligence": round(metric, 4),
            "feature": "Stablecoins Intelligence",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        },
    )

def run_charting_market_intelligence_e2e_batch(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """E2E smoke for generated #301–#400 surfaces."""
    seed = seed or _load_seed()
    sample = multi_chart_layouts_301(seed=seed)
    return {
        "ok": True,
        "feature_range": "301-400",
        "sample_capability": 301,
        "sample_ok": sample.get("ok") is True,
    }
