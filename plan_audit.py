"""
BLACKDARK — Plan audit vs Excel roadmap (خطوات التحقيق).

Maps the founder Excel spec to live modules/endpoints with honest status.
"""

from __future__ import annotations

from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any, Literal

# Sonar S1192: duplicated string literals
PATH_API_ARBITRAGE_OPPORTUNITIES = '/api/arbitrage/opportunities'
PATH_API_PORTFOLIO_ANALYZE = '/api/portfolio/analyze'
STR_COPY_XLSX = 'خطوات التحقيق - Copy.xlsx'

PlanStatus = Literal["complete", "partial", "planned"]

ROOT = Path(__file__).resolve().parent.parent

# category, title (English), status, module, endpoint, note
_PLAN_ROWS: tuple[tuple[Any, ...], ...] = (
    ("core", "Real-time price ingestion", "complete", "aggregator", "/api/ingestion/status", "Binance/OKX/Bybit + WS hub"),
    ("core", "Fast price updates (WebSocket)", "partial", "exchange_ws_hub", "/api/low-latency/status", "WS ~100–800ms — not microsecond HFT"),
    ("core", "100 exchanges — phase 1", "complete", "universe_rollout", "/api/universe/rollout", "100 fetchers + auto-activate manifest"),
    ("core", "Cross-exchange arbitrage", "complete", "arbitrage_engine", PATH_API_ARBITRAGE_OPPORTUNITIES, "cross_exchange live"),
    ("core", "Triangular arbitrage", "complete", "arbitrage_engine", PATH_API_ARBITRAGE_OPPORTUNITIES, "triangular live"),
    ("core", "Funding rate harvest", "complete", "arbitrage_engine", PATH_API_ARBITRAGE_OPPORTUNITIES, "funding harvest live"),
    ("core", "Spot vs Futures", "complete", "arbitrage_engine", PATH_API_ARBITRAGE_OPPORTUNITIES, "spot_futures live"),
    ("core", "CEX ↔ DEX", "complete", "bd_platform.cex_dex_executor", "/api/platform/arb/cex-dex/execute", "DexScreener scan + dry-run/live CEX leg"),
    ("core", "Execution risk scoring %", "complete", "risk_manager", "/api/risk/status", "slippage + poison price freeze"),
    ("core", "Risk management", "complete", "risk_manager", "/api/risk/freeze", "freeze/unfreeze + VaR in Research Lab"),
    ("core", "Liquidity filtering", "complete", "liquidity_discovery", None, "operational manifest hybrid filter"),
    ("core", "Auto execution via API keys", "complete", "execution_keys", "/api/execution/keys/status", "dry-run default + optional Binance live"),
    ("core", "77 arbitrage types catalog", "partial", "arbitrage_catalog", "/api/arbitrage/catalog", "Catalog live with proxy/planned honesty — see /api/arbitrage/catalog"),
    ("dash", "Live monitoring dashboard", "complete", "dashboard", "/dashboard", "Live dashboard + heatmap"),
    ("dash", "Telegram/Email/WhatsApp alerts", "partial", "alert_service", "/api/alerts/subscribe", "WhatsApp = wa.me link"),
    ("dash", "Opportunity duration tracking", "complete", "opportunity_tracker", "/api/arbitrage/durations", "duration tracking"),
    ("dash", "Net profit after fees", "complete", "arbitrage_service", PATH_API_ARBITRAGE_OPPORTUNITIES, "net profit after fees"),
    ("dash", "Why did this opportunity appear?", "complete", "ai_oracle", "/oracle/{symbol}/explain", "why + reasons + confidence"),
    ("features", "Heat map", "complete", "whale_tracker", "/api/market/sectors", "SII + sector heat"),
    ("features", "Trading Journal", "complete", "database", "/api/journal", "auth required"),
    ("features", "AI Reports / Weekly", "complete", "weekly_report", "/api/reports/weekly", "auto scheduler optional"),
    ("features", "Portfolio Analytics", "complete", "dashboard", PATH_API_PORTFOLIO_ANALYZE, "risk score 1–10"),
    ("features", "Risk Score", "complete", "dashboard", PATH_API_PORTFOLIO_ANALYZE, "beta-weighted risk"),
    ("features", "Profit Analytics", "complete", "market_intel", "/api/analytics/profit", "P&L analytics"),
    ("features", "AI Chat", "complete", "chat_service", "/api/chat", "LLM + context"),
    ("features", "AI Explanation", "complete", "ai_oracle", "/oracle/{symbol}", "single-sentence oracle"),
    ("features", "Trade Simulator", "complete", "trade_simulator", "/api/simulate/trade", "spot + arb sim"),
    ("features", "Execution Speed", "partial", "fast_scan_engine", "/api/low-latency/fast-scan", "millisecond warm path"),
    ("biz", "3 subscription tiers", "complete", "auth_service", "/api/billing/status", "free/pro/whale + Stripe"),
    ("ai", "AI Trading Engine RSI/MACD/EMA", "complete", "technical_analysis", "/api/forecast/{symbol}", "multi-indicator"),
    ("ai", "Whale Intelligence", "complete", "whale_tracker", "/api/whale-activity", "CVVD + why narrative"),
    ("ai", "Portfolio AI", "complete", "dashboard", PATH_API_PORTFOLIO_ANALYZE, "concentration + scenarios"),
    ("ai", "Market Radar — sectors", "complete", "dashboard", "/api/market/sectors", "Gaming/AI/RWA/Solana sectors"),
    ("ai", "Opportunity Score 0–100", "complete", "ai_oracle", "/api/oracle/data-hub", "scored opportunities"),
    ("inst", "Institutional B2B", "partial", "b2b_websocket_hub", "/b2b", "WS feed + proposal deck"),
    ("inst", "Research Lab", "complete", "research_lab", "/api/research/lab", "VaR/NVT/MVRV/SOPR proxies"),
    ("inst", "On-chain Intelligence", "partial", "onchain_tracker", "/api/onchain/overview", "flows matrix"),
    ("inst", "Whale Gravity Map", "complete", "market_intel", "/api/whale/gravity-map", "visualization API"),
    ("inst", "Panic Button", "complete", "execution_engine", "/api/execution/panic", "halt + disclaimer"),
    ("inst", "Voice Trading", "complete", "voice_service", "/api/voice/command", "analyze/scan/panic"),
    ("platform", "Platform Hub 40 features", "complete", "bd_platform", "/platform", "40/40 free tier"),
    ("platform", "GraphQL + REST API", "complete", "graphql_schema", "/graphql", "API-first"),
    ("platform", "Microservices", "complete", "microservices.lifecycle", "/api/services/status", "docker-compose + 4 workers"),
    ("mobile", "Web / Desktop / Mobile apps", "planned", None, None, "PWA web only — native planned"),
    ("data", "NLP Sentiment", "complete", "sentiment_engine", "/api/sentiment/overview", "Twitter/Reddit + VADER"),
    ("data", "SEC filings AI", "planned", None, None, "Not implemented — outside crypto core scope"),
)


def _module_exists(dotted: str | None) -> bool:
    if not dotted:
        return False
    try:
        import_module(dotted)
        return True
    except (ImportError, SyntaxError):
        return False


def _status_weight(status: PlanStatus) -> float:
    return {"complete": 1.0, "partial": 0.65, "planned": 0.15}[status]


def plan_audit(*, excel_path: str | None = None) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    by_category: dict[str, list[dict[str, Any]]] = {}
    weighted = 0.0

    for idx, row in enumerate(_PLAN_ROWS, start=1):
        category, title, status, module, endpoint, note = row
        live = _module_exists(module) if module else status != "planned"
        item = {
            "id": idx,
            "category": category,
            "title": title,
            "status": status,
            "module": module,
            "endpoint": endpoint,
            "note": note,
            "module_loaded": live,
        }
        items.append(item)
        by_category.setdefault(category, []).append(item)
        weighted += _status_weight(status)  # type: ignore[arg-type]

    total = len(_PLAN_ROWS)
    complete = sum(1 for i in items if i["status"] == "complete")
    partial = sum(1 for i in items if i["status"] == "partial")
    planned = sum(1 for i in items if i["status"] == "planned")

    categories_summary = []
    for cat, rows in by_category.items():
        cat_weight = sum(_status_weight(r["status"]) for r in rows)  # type: ignore[arg-type]
        categories_summary.append({
            "category": cat,
            "count": len(rows),
            "complete": sum(1 for r in rows if r["status"] == "complete"),
            "percent": round(cat_weight / len(rows) * 100, 1),
        })

    excel_file = Path(excel_path) if excel_path else ROOT.parent / STR_COPY_XLSX
    if not excel_file.exists():
        excel_file = ROOT / "excel_plan_review.json"

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "source_excel": str(excel_file),
        "source_found": excel_file.exists(),
        "total_items": total,
        "complete_count": complete,
        "partial_count": partial,
        "planned_count": planned,
        "overall_percent": round(weighted / total * 100, 1),
        "categories": sorted(categories_summary, key=lambda x: -x["percent"]),
        "items": items,
        "next_priority": [
            i for i in items if i["status"] in {"partial", "planned"}
        ][:8],
        "arbitrage_catalog": _catalog_stats(),
    }


def _catalog_stats() -> dict[str, Any]:
    try:
        from arbitrage_catalog import get_catalog

        data = get_catalog()
        return data.get("counts_by_status") or {}
    except ImportError:
        return {"live": 0, "proxy": 0, "planned": 0}


async def _fetch_sector_change(session: Any, asset: str) -> tuple[str, float] | None:
    import aiohttp

    import config

    pair = f"{asset}USDT"
    if not pair.isalnum():
        return None
    try:
        async with session.get(
            f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
        ) as resp:
            if resp.status != 200:
                return None
            row = await resp.json()
            sector = config.SECTOR_MAP.get(asset, "Other")
            return sector, float(row.get("priceChangePercent") or 0)
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


def _sector_heat(avg: float) -> str:
    if avg > 2:
        return "Hot"
    if avg < -2:
        return "Cool"
    return "Neutral"


def _sector_rows(sector_assets: dict[str, list[float]]) -> list[dict[str, Any]]:
    sectors: list[dict[str, Any]] = []
    for name, changes in sector_assets.items():
        if not changes:
            continue
        avg = sum(changes) / len(changes)
        sectors.append({
            "sector": name,
            "avg_change_24h": round(avg, 2),
            "asset_count": len(changes),
            "heat_label": _sector_heat(avg),
        })
    sectors.sort(key=lambda x: abs(x["avg_change_24h"]), reverse=True)
    return sectors


def _market_radar_bullets(sectors: list[dict[str, Any]]) -> list[str]:
    hot = [s for s in sectors if s["heat_label"] == "Hot"][:3]
    cool = [s for s in sectors if s["heat_label"] == "Cool"][:3]
    unusual = [s for s in sectors if s["heat_label"] == "Neutral" and abs(s["avg_change_24h"]) > 1][:2]
    bullets_en = [f"Strong activity in {s['sector']} (+{s['avg_change_24h']:.1f}%)" for s in hot]
    bullets_en.extend(f"Weakness in {s['sector']} ({s['avg_change_24h']:.1f}%)" for s in cool)
    bullets_en.extend(f"Unusual flow in {s['sector']}" for s in unusual)
    return bullets_en or ["Market balanced — no extreme sectors today"]


async def market_radar_narrative() -> dict[str, Any]:
    """Excel-style sector narrative: Gaming up, AI weak, etc."""
    import aiohttp

    import config

    sector_assets: dict[str, list[float]] = {}
    timeout = aiohttp.ClientTimeout(total=12)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for asset in config.tracked_asset_list()[:24]:
            result = await _fetch_sector_change(session, asset)
            if result is not None:
                sector, change = result
                sector_assets.setdefault(sector, []).append(change)

    sectors = _sector_rows(sector_assets)
    bullets_en = _market_radar_bullets(sectors)

    payload = {
        "summary": "Today's market: " + " · ".join(bullets_en[:5]),
        "bullets": bullets_en,
        "sectors": sectors,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    try:
        from bd_platform.large_liquidity_event_alert import enrich_market_radar as enrich_liq
        from bd_platform.large_liquidity_event_alert import scan_large_liquidity_events
        from bd_platform.listing_intelligence_engine import enrich_market_radar as enrich_listing
        from bd_platform.listing_intelligence_engine import scan_listing_intelligence
        from bd_platform.unusual_liquidity_alert_engine import enrich_market_radar as enrich_unusual
        from bd_platform.unusual_liquidity_alert_engine import scan_unusual_liquidity_events
        from bd_platform.order_flow_analytics import enrich_market_radar as enrich_order_flow
        from bd_platform.order_flow_analytics import scan_order_flow

        liquidity = await scan_large_liquidity_events(limit=5)
        listings = await scan_listing_intelligence(limit=5)
        unusual = await scan_unusual_liquidity_events(limit=5)
        order_flow = await scan_order_flow("BTC", limit=5)
        payload = enrich_liq(payload, liquidity)
        payload = enrich_listing(payload, listings)
        payload = enrich_unusual(payload, unusual)
        payload = enrich_order_flow(payload, order_flow)
    except Exception:
        pass

    return payload


async def execution_speed_snapshot() -> dict[str, Any]:
    """Execution speed panel — fast scan + WS freshness."""
    from fast_scan_engine import run_fast_scan

    scan = await run_fast_scan()
    try:
        from exchange_ws_hub import ws_hub_stats
        from live_book_hub import hub_stats

        ws = ws_hub_stats()
        books = hub_stats()
    except ImportError:
        ws, books = {}, {}

    tier = scan.get("latency_tier", "unknown")
    ms = float(scan.get("latency_ms") or 0)
    label_en = {
        "millisecond": "Ultra-fast (<50ms)",
        "sub_second": "Fast (<500ms)",
        "slow": "Slow",
    }.get(tier, tier)

    return {
        "latency_ms": ms,
        "latency_tier": tier,
        "label": label_en,
        "scan": scan,
        "websocket": ws,
        "live_books": books,
        "disclaimer": "Speed depends on exchange and network — not a fixed 3-second guarantee",
    }
