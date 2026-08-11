"""
BLACKDARK — Master registry for 40-point platform roadmap.
Each entry: id, title, status, module, endpoint, env_keys, references.
"""

from __future__ import annotations

from typing import Any

# Sonar S1192: duplicated string literals
KEY_BD_PLATFORM_ONCHAIN_HUB = 'bd_platform.onchain_hub'

FEATURE_MATRIX: list[dict[str, Any]] = [
    {"id": 1, "key": "ml_trulens", "title": "Real ML + TruLens explainability", "module": "bd_platform.trulens_eval", "endpoint": "/api/platform/ml/explain", "refs": ["TruLens", "scikit-learn"]},
    {"id": 2, "key": "ws_execution_risk", "title": "WebSocket + manual/auto execution + risk", "module": "execution_engine", "endpoint": "/api/execution/status", "refs": ["Hummingbot", "3Commas", "Bitsgap", "Hyperliquid SDK", "Finnhub"]},
    {"id": 3, "key": "microservices_postgres", "title": "Microservices + PostgreSQL", "module": "postgres_backend", "endpoint": "/api/services/status", "refs": ["HaasCloud"]},
    {"id": 4, "key": "b2b_api", "title": "API-First B2B REST", "module": "dashboard", "endpoint": "/api/b2b/feed", "refs": []},
    {"id": 5, "key": "sentiment_nlp", "title": "Social Sentiment NLP", "module": "sentiment_engine", "endpoint": "/api/sentiment/overview", "refs": ["Telegram", "Reddit", "X"]},
    {"id": 6, "key": "test_coverage", "title": "Code coverage measurement", "module": "bd_platform.coverage_report", "endpoint": "/api/platform/coverage", "refs": []},
    {"id": 7, "key": "derivatives_coinglass", "title": "Derivatives / CoinGlass", "module": "bd_platform.derivatives_hub", "endpoint": "/api/platform/derivatives/overview", "refs": ["CoinGlass", "Apex Trader"]},
    {"id": 8, "key": "security", "title": "Security vault + pip-audit", "module": "secrets_vault", "endpoint": "/api/security/status", "refs": []},
    {"id": 9, "key": "cex_dex_arb", "title": "Cross-Boundary CEX↔DEX arbitrage", "module": "bd_platform.cex_dex_arbitrage", "endpoint": "/api/platform/arb/cex-dex", "refs": ["Jupiter", "Uniswap", "GMX", "1inch"]},
    {"id": 10, "key": "liquidation_frontrun", "title": "Predictive liquidation radar", "module": "bd_platform.liquidation_radar", "endpoint": "/api/platform/liquidations/radar", "refs": ["Insilico Terminal", "CoinGlass"]},
    {"id": 11, "key": "telegram_ai_agent", "title": "Autonomous Telegram AI agent", "module": "bd_platform.telegram_agent", "endpoint": "/api/platform/agent/telegram", "refs": []},
    {"id": 12, "key": "anti_spoofing", "title": "Anti-spoofing & poisoning shield", "module": "whale_tracker", "endpoint": "/api/whale/scan", "refs": []},
    {"id": 13, "key": "public_proof", "title": "Public cryptographic proof ledger", "module": "bd_platform.public_proof", "endpoint": "/api/platform/proof/public", "refs": []},
    {"id": 14, "key": "cmc_rankings", "title": "CoinMarketCap-style rankings", "module": "bd_platform.market_rankings", "endpoint": "/api/platform/market/rankings", "refs": []},
    {"id": 15, "key": "onchain_extended", "title": "Extended on-chain (DexScreener+Gecko)", "module": KEY_BD_PLATFORM_ONCHAIN_HUB, "endpoint": "/api/platform/onchain/pairs", "refs": ["DexScreener", "GeckoTerminal", "Dune", "Arkham", "Santiment"]},
    {"id": 16, "key": "token_unlocks", "title": "Token unlocks tracking", "module": "bd_platform.token_unlocks", "endpoint": "/api/platform/unlocks/calendar", "refs": ["TokenUnlocks", "CryptoRank"]},
    {"id": 17, "key": "lunarcrush", "title": "LunarCrush social metrics", "module": KEY_BD_PLATFORM_ONCHAIN_HUB, "endpoint": "/api/platform/social/lunarcrush", "refs": ["LunarCrush", "socialtickers"], "env_keys": ["LUNARCRUSH_API_KEY"], "free_tier": "socialtickers.com (no key)"},
    {"id": 18, "key": "coinmarketcal", "title": "Crowdsourced event calendar", "module": KEY_BD_PLATFORM_ONCHAIN_HUB, "endpoint": "/api/platform/events/calendar", "refs": ["CoinMarketCal", "DeFiLlama"], "env_keys": ["COINMARKETCAL_API_KEY"], "free_tier": "free key at developers.coinmarketcal.com"},
    {"id": 19, "key": "debank_wallet", "title": "Multi-EVM wallet dashboard", "module": KEY_BD_PLATFORM_ONCHAIN_HUB, "endpoint": "/api/platform/wallet/debank", "refs": ["DeBank", "Tracely", "Zerion"], "env_keys": ["DEBANK_API_KEY", "ZERION_API_KEY"], "free_tier": "tracely.live portfolio (no key)"},
    {"id": 20, "key": "bubblemaps", "title": "Wallet cluster visualization", "module": KEY_BD_PLATFORM_ONCHAIN_HUB, "endpoint": "/api/platform/wallet/clusters", "refs": ["Bubblemaps", "Tracely"], "env_keys": ["BUBBLEMAPS_API_KEY"], "free_tier": "tracely.live graph clusters (no key)"},
    {"id": 21, "key": "geckoterminal", "title": "GeckoTerminal pairs", "module": KEY_BD_PLATFORM_ONCHAIN_HUB, "endpoint": "/api/platform/defi/geckoterminal", "refs": ["GeckoTerminal"]},
    {"id": 22, "key": "tradingview_charts", "title": "TradingView Lightweight Charts", "module": "bd_platform.tradingview_bridge", "endpoint": "/api/platform/charts/config", "refs": ["TradingView"]},
    {"id": 23, "key": "footprint", "title": "Footprint / order-flow analytics", "module": "bd_platform.footprint_analytics", "endpoint": "/api/platform/analytics/footprint", "refs": []},
    {"id": 24, "key": "scopescan", "title": "0xScope / Scopescan labels", "module": KEY_BD_PLATFORM_ONCHAIN_HUB, "endpoint": "/api/platform/wallet/scopescan", "refs": ["0xScope", "Scopescan", "eth-labels"], "env_keys": ["SCOPESCAN_API_KEY"], "free_tier": "tracely + eth-labels.com (no key)"},
    {"id": 25, "key": "whale_storytelling", "title": "Whale movement storytelling", "module": "bd_platform.whale_story", "endpoint": "/api/platform/whale/narrative", "refs": []},
    {"id": 26, "key": "coindesk_research", "title": "CoinDesk deep research feed", "module": "bd_platform.news_classifier", "endpoint": "/api/platform/news/coindesk", "refs": ["CoinDesk"]},
    {"id": 27, "key": "defillama_raises", "title": "DeFiLlama raises / funding", "module": KEY_BD_PLATFORM_ONCHAIN_HUB, "endpoint": "/api/platform/defi/raises", "refs": ["DeFiLlama", "The Block Pro"]},
    {"id": 28, "key": "lookintobitcoin", "title": "Bitcoin macro cycle indicators", "module": KEY_BD_PLATFORM_ONCHAIN_HUB, "endpoint": "/api/platform/macro/bitcoin", "refs": ["LookIntoBitcoin"]},
    {"id": 29, "key": "news_classifier", "title": "News classification engine", "module": "bd_platform.news_classifier", "endpoint": "/api/platform/news/classify", "refs": ["CryptoPanic"]},
    {"id": 30, "key": "l2beat", "title": "L2Beat security metrics", "module": KEY_BD_PLATFORM_ONCHAIN_HUB, "endpoint": "/api/platform/l2/security", "refs": ["L2Beat"]},
    {"id": 31, "key": "cex_dex_derivatives_ui", "title": "CEX vs DEX derivatives comparison", "module": "bd_platform.derivatives_hub", "endpoint": "/api/platform/derivatives/cex-dex-compare", "refs": []},
    {"id": 32, "key": "blockpour", "title": "Blockpour cross-chain flows", "module": KEY_BD_PLATFORM_ONCHAIN_HUB, "endpoint": "/api/platform/flows/cross-chain", "refs": ["Blockpour", "DeFiLlama"], "env_keys": ["BLOCKPOUR_API_KEY"], "free_tier": "defillama bridges OR free key at app.blockpour.com"},
    {"id": 33, "key": "intotheblock", "title": "IntoTheBlock holder profitability", "module": KEY_BD_PLATFORM_ONCHAIN_HUB, "endpoint": "/api/platform/analytics/intotheblock", "refs": ["IntoTheBlock", "CoinGecko", "Binance"], "env_keys": [], "free_tier": "CoinGecko + Binance (ITB API discontinued)"},
    {"id": 34, "key": "grid_bot", "title": "Grid trading bot", "module": "bd_platform.grid_bot", "endpoint": "/api/platform/bots/grid", "refs": []},
    {"id": 35, "key": "strategy_marketplace", "title": "Strategy marketplace", "module": "bd_platform.strategy_marketplace", "endpoint": "/api/platform/marketplace/strategies", "refs": []},
    {"id": 36, "key": "institutional_linking", "title": "Institutional account linking", "module": "user_keys_service", "endpoint": "/api/user/exchange-keys", "refs": ["Quadency", "Tealstreet"]},
    {"id": 37, "key": "haas_script", "title": "Custom strategy scripting", "module": "bd_platform.script_sandbox", "endpoint": "/api/platform/scripts/run", "refs": ["HaasScript"]},
    {"id": 38, "key": "ifttt_rules", "title": "Simple IFTTT rule builder", "module": "bd_platform.ifttt_rules", "endpoint": "/api/platform/rules", "refs": []},
    {"id": 39, "key": "portfolio_rebalance", "title": "Portfolio rebalancing", "module": "bd_platform.portfolio_rebalancer", "endpoint": "/api/platform/portfolio/rebalance", "refs": []},
    {"id": 40, "key": "tradingview_bridge", "title": "TradingView signal execution bridge", "module": "bd_platform.tradingview_bridge", "endpoint": "/api/platform/tradingview/webhook", "refs": ["TradingView"]},
]


def feature_summary() -> dict[str, Any]:
    import importlib

    live = 0
    rows: list[dict[str, Any]] = []
    for feat in FEATURE_MATRIX:
        mod_path = feat.get("module", "")
        ok = False
        try:
            importlib.import_module(mod_path)
            ok = True
            live += 1
        except ImportError:
            ok = False
        rows.append({**feat, "module_loaded": ok})
    return {
        "total_features": len(FEATURE_MATRIX),
        "modules_loaded": live,
        "coverage_percent": round(live / len(FEATURE_MATRIX) * 100, 1),
        "features": rows,
    }
