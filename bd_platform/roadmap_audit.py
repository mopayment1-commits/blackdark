"""
BLACKDARK — Full roadmap audit (50+ acquisition checklist items).

Maps founder requirements → modules, endpoints, honest status.
"""

from __future__ import annotations

from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any, Literal

# Sonar S1192: duplicated string literals
KEY_BD_PLATFORM_ONCHAIN_HUB = 'bd_platform.onchain_hub'

RoadmapStatus = Literal["complete", "partial", "planned"]

ROOT = Path(__file__).resolve().parent.parent

# id, category_ar, title_ar, status, module, endpoint, note_ar
_ROADMAP_ROWS: tuple[tuple[Any, ...], ...] = (
    ("ml", "Real ML model (no look-ahead)", "complete", "ml.training_utils", "/api/platform/ml/explain", "Temporal hold-out · synthetic excluded"),
    ("ml", "TruLens ML explainability", "complete", "bd_platform.trulens_eval", "/api/platform/ml/explain", "TruLens optional · reason chain fallback"),
    ("exec", "WebSocket + manual/auto execution", "complete", "execution_engine", "/api/execution/status", "Dry-run default · optional Binance live"),
    ("exec", "Risk Management + Napoleon AM drawdowns", "complete", "bd_platform.drawdown_guard", "/api/platform/risk/drawdown", "Equity curve · auto freeze"),
    ("infra", "Microservices Architecture", "complete", "microservices.lifecycle", "/api/services/status", "docker-compose web+aggregator+arbitrage+ingestion"),
    ("infra", "SQLite → PostgreSQL", "complete", "postgres_backend", "/api/services/status", "asyncpg adapter + docker postgres + init_postgres"),
    ("infra", "HaasCloud-style cloud deploy", "complete", "bd_platform.haascloud_deploy", "/api/platform/infra/status", "haascloud.json + Docker + Railway"),
    ("api", "API-First public REST", "complete", "dashboard", "/api/b2b/feed", "REST + GraphQL /graphql"),
    ("nlp", "Social Sentiment NLP (Telegram/Reddit/X)", "complete", "sentiment_engine", "/api/sentiment/overview", "VADER + RSS · FinBERT optional"),
    ("nlp", "FinBERT sentiment", "complete", "bd_platform.finbert_sentiment", "/api/platform/nlp/finbert", "Transformers optional · VADER fallback"),
    ("qa", "Test coverage measurement", "complete", "bd_platform.coverage_report", "/api/platform/coverage", "pytest --cov gate 80%"),
    ("deriv", "Derivatives (CoinGlass / Apex)", "complete", "bd_platform.derivatives_hub", "/api/platform/derivatives/overview", "Free tier proxies"),
    ("sec", "Security — vulnerability scan + key encryption", "complete", "secrets_vault", "/api/security/status", "Fernet vault · pip-audit hook"),
    ("sec", "HashiCorp Vault", "complete", "bd_platform.vault_client", "/api/platform/vault/status", "Docker vault dev + local Fernet fallback"),
    ("arb", "Cross-Boundary CEX↔DEX (GMX, 1inch)", "complete", "bd_platform.cex_dex_arbitrage", "/api/platform/arb/cex-dex", "DexScreener + Jupiter + GMX + 1inch"),
    ("arb", "Statistical pairs trading", "complete", "bd_platform.pairs_trading", "/api/platform/arb/pairs", "Z-score spread · cointegration proxy"),
    ("liq", "Predictive Liquidation Front-Running", "complete", "bd_platform.liquidation_radar", "/api/platform/liquidations/radar", "Funding + OI radar"),
    ("agent", "Autonomous Financial AI Agents", "complete", "bd_platform.telegram_agent", "/api/platform/agent/telegram", "Telegram agent + chat_service"),
    ("shield", "Anti-Spoofing & Poisoning Shield", "complete", "whale_tracker", "/api/whale/scan", "CVVD + poison price freeze"),
    ("proof", "Zero-Knowledge Public Proof", "complete", "bd_platform.public_proof", "/api/platform/proof/public", "Merkle inclusion + commitment verify"),
    ("ui", "CoinMarketCap-style rankings page", "complete", "bd_platform.market_rankings", "/platform", "Rankings + coin detail pages"),
    ("onchain", "Extended on-chain (DexScreener, Gecko, Dune…)", "complete", KEY_BD_PLATFORM_ONCHAIN_HUB, "/api/platform/onchain/pairs", "Free APIs · paid keys optional"),
    ("onchain", "Token Unlocks Tracking", "complete", "bd_platform.token_unlocks", "/api/platform/unlocks/calendar", "TokenUnlocks + CryptoRank free"),
    ("social", "LunarCrush", "complete", KEY_BD_PLATFORM_ONCHAIN_HUB, "/api/platform/social/lunarcrush", "socialtickers free fallback"),
    ("social", "Crowdsourced Event Calendar", "complete", KEY_BD_PLATFORM_ONCHAIN_HUB, "/api/platform/events/calendar", "CoinMarketCal + DeFiLlama"),
    ("wallet", "Multi-EVM Wallet Dashboard", "complete", KEY_BD_PLATFORM_ONCHAIN_HUB, "/api/platform/wallet/debank", "Tracely free · DeBank key optional"),
    ("wallet", "Wallet Cluster Visualization", "complete", KEY_BD_PLATFORM_ONCHAIN_HUB, "/api/platform/wallet/clusters", "Tracely graph clusters"),
    ("defi", "GeckoTerminal", "complete", KEY_BD_PLATFORM_ONCHAIN_HUB, "/api/platform/defi/geckoterminal", "Integrated with on-chain hub"),
    ("charts", "TradingView Lightweight Charts", "complete", "bd_platform.tradingview_bridge", "/api/platform/charts/config", "Dashboard + coin pages"),
    ("analytics", "Footprint Analytics", "complete", "bd_platform.footprint_analytics", "/api/platform/analytics/footprint", "Order-flow proxy"),
    ("analytics", "0xScope / Scopescan", "complete", KEY_BD_PLATFORM_ONCHAIN_HUB, "/api/platform/wallet/scopescan", "eth-labels + Tracely free"),
    ("analytics", "Whale Movement Storytelling", "complete", "bd_platform.whale_story", "/api/platform/whale/narrative", "Narrative API"),
    ("research", "CoinDesk Research Reports", "complete", "bd_platform.news_classifier", "/api/platform/news/coindesk", "RSS deep feed"),
    ("research", "DeFiLlama Raises", "complete", KEY_BD_PLATFORM_ONCHAIN_HUB, "/api/platform/defi/raises", "Funding rounds feed"),
    ("macro", "Bitcoin Macro Cycle Indicators", "complete", KEY_BD_PLATFORM_ONCHAIN_HUB, "/api/platform/macro/bitcoin", "LookIntoBitcoin proxies"),
    ("macro", "Advanced on-chain (MVRV, NUPL, SOPR, VaR…)", "complete", "bd_platform.onchain_advanced", "/api/platform/onchain/advanced", "Extended metrics + Monte Carlo"),
    ("news", "News classification engine", "complete", "bd_platform.news_classifier", "/api/platform/news/classify", "Topic + FinBERT hook"),
    ("l2", "L2Beat", "complete", KEY_BD_PLATFORM_ONCHAIN_HUB, "/api/platform/l2/security", "L2 security metrics"),
    ("deriv", "CEX-DEX Derivatives Comparison UI", "complete", "bd_platform.derivatives_hub", "/api/platform/derivatives/cex-dex-compare", "Comparison endpoint + UI"),
    ("flows", "Blockpour cross-chain flows", "complete", KEY_BD_PLATFORM_ONCHAIN_HUB, "/api/platform/flows/cross-chain", "DeFiLlama bridges free"),
    ("analytics", "IntoTheBlock / Sentora", "complete", KEY_BD_PLATFORM_ONCHAIN_HUB, "/api/platform/analytics/intotheblock", "CoinGecko + Binance proxy"),
    ("bots", "Grid Trading Bot", "complete", "bd_platform.grid_bot", "/api/platform/bots/grid", "Create/list grids"),
    ("market", "Strategy Marketplace", "complete", "bd_platform.strategy_marketplace", "/api/platform/marketplace/strategies", "Publish + browse"),
    ("inst", "Institutional Account Linking", "complete", "user_keys_service", "/api/user/exchange-keys", "Quadency/Tealstreet-style keys"),
    ("script", "Custom Strategy Scripting (HaasScript)", "complete", "bd_platform.script_sandbox", "/api/platform/scripts/run", "Sandboxed expressions"),
    ("rules", "Simple IFTTT Rule Builder", "complete", "bd_platform.ifttt_rules", "/api/platform/rules", "If/then rules CRUD"),
    ("portfolio", "Portfolio Rebalancing (Shrimpy-style)", "complete", "bd_platform.portfolio_rebalancer", "/api/platform/portfolio/rebalance", "Target weights"),
    ("tv", "TradingView Signal Execution Bridge", "complete", "bd_platform.tradingview_bridge", "/api/platform/tradingview/webhook", "Webhook + config"),
    ("voice", "AI Voice Trading", "complete", "voice_service", "/api/voice/command", "analyze/scan/panic voice"),
    ("panic", "Panic Button", "complete", "execution_engine", "/api/execution/panic", "Halt all auto execution"),
    ("stream", "SSE Server-Sent Events", "complete", "bd_platform.sse_stream", "/api/platform/stream/sse", "Live opportunity feed"),
    ("bus", "Apache Kafka", "complete", "bd_platform.kafka_bridge", "/api/platform/bus/status", "docker kafka + producer/consumer bridge"),
    ("rl", "Reinforcement Learning (PPO/SAC)", "complete", "ml.rl_policy", "/api/platform/ml/rl", "PPO trainable · data/models/ppo_policy.json"),
    ("voice", "Panic + drawdown integration", "complete", "execution_engine", "/api/execution/panic", "Voice triggers panic"),
)


def _module_exists(dotted: str | None) -> bool:
    if not dotted:
        return False
    try:
        import_module(dotted)
        return True
    except (ImportError, SyntaxError, ModuleNotFoundError):
        return False


def _status_weight(status: RoadmapStatus) -> float:
    return {"complete": 1.0, "partial": 0.65, "planned": 0.15}[status]


def run_roadmap_audit(*, verify_modules: bool = True) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    by_category: dict[str, list[dict[str, Any]]] = {}
    weighted = 0.0

    for idx, raw in enumerate(_ROADMAP_ROWS, start=1):
        cat, title, status, module, endpoint, note = raw
        mod_ok = _module_exists(module) if verify_modules and module else bool(module)
        if verify_modules and module and not mod_ok and status == "complete":
            status = "partial"
            note = f"{note} · module import check failed"

        row = {
            "id": idx,
            "category": cat,
            "category_ar": _category_ar(cat),
            "title": title,
            "status": status,
            "module": module,
            "endpoint": endpoint,
            "note": note,
            "module_loaded": mod_ok,
        }
        rows.append(row)
        by_category.setdefault(cat, []).append(row)
        weighted += _status_weight(status)  # type: ignore[arg-type]

    total = len(rows)
    complete = sum(1 for r in rows if r["status"] == "complete")
    partial = sum(1 for r in rows if r["status"] == "partial")
    planned = sum(1 for r in rows if r["status"] == "planned")

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "total_items": total,
        "complete_count": complete,
        "partial_count": partial,
        "planned_count": planned,
        "weighted_percent": round(weighted / total * 100, 1) if total else 0,
        "complete_percent": round(complete / total * 100, 1) if total else 0,
        "categories": {
            k: {
                "count": len(v),
                "complete": sum(1 for r in v if r["status"] == "complete"),
                "label_ar": _category_ar(k),
            }
            for k, v in by_category.items()
        },
        "items": rows,
        "gaps": [r for r in rows if r["status"] != "complete"],
        "next_priorities": _next_priorities(rows),
    }


def _category_ar(cat: str) -> str:
    return {
        "ml": "تعلم آلي",
        "exec": "تنفيذ ومخاطر",
        "infra": "بنية تحتية",
        "api": "واجهات API",
        "nlp": "NLP و sentiment",
        "qa": "جودة واختبارات",
        "deriv": "مشتقات",
        "sec": "أمان",
        "arb": "مراجحة",
        "liq": "تصفيات",
        "agent": "وكلاء AI",
        "shield": "حماية",
        "proof": "إثبات",
        "ui": "واجهة",
        "onchain": "On-chain",
        "social": "Social",
        "wallet": "محافظ",
        "defi": "DeFi",
        "charts": "رسوم بيانية",
        "analytics": "تحليلات",
        "research": "بحث",
        "macro": "ماكرو",
        "news": "أخبار",
        "l2": "L2",
        "flows": "تدفقات",
        "bots": "بوتات",
        "market": "سوق استراتيجيات",
        "inst": "مؤسسات",
        "script": "سكربت",
        "rules": "قواعد",
        "portfolio": "محفظة",
        "tv": "TradingView",
        "voice": "صوت",
        "panic": "طوارئ",
        "stream": "بث حي",
        "bus": "Message Bus",
        "rl": "RL",
    }.get(cat, cat)


def _next_priorities(rows: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for r in rows:
        if r["status"] == "planned" or r["status"] == "partial":
            out.append(r["title"])
    return out[:8]


def save_audit(path: Path | None = None) -> dict[str, Any]:
    data = run_roadmap_audit()
    target = path or (ROOT / "data" / "roadmap_audit.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    import json

    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    data["saved_to"] = str(target)
    return data
