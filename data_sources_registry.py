"""
BLACKDARK — Master registry of external data sources (100+ free-tier endpoints).

Architecture: schedulers pull → data_lake (SQLite + hot spool) → Oracle reads lake.
Never hit APIs directly from the AI model at request time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FetchKind = Literal["rest", "rss", "websocket", "subgraph", "internal"]

Category = Literal[
    "prices",
    "onchain",
    "defi",
    "news",
    "sentiment",
    "events",
    "whale",
    "research",
    "macro",
    "regulatory",
]


@dataclass(frozen=True)
class DataSourceSpec:
    source_id: str
    category: Category
    name: str
    fetch_kind: FetchKind
    url: str
    interval_seconds: int
    env_key: str | None = None
    notes: str = ""


# Default poll intervals per architecture doc
CATEGORY_INTERVALS: dict[Category, int] = {
    "prices": 5,
    "onchain": 60,
    "defi": 120,
    "news": 60,
    "sentiment": 120,
    "events": 3600,
    "whale": 30,
    "research": 3600,
    "macro": 300,
    "regulatory": 600,
}


DATA_SOURCES: tuple[DataSourceSpec, ...] = (
    # ── 1. Spot & Derivatives Price Data ─────────────────────────────────────
    DataSourceSpec("binance_spot", "prices", "Binance Spot", "rest",
                   "https://api.binance.com/api/v3/ticker/24hr", 5),
    DataSourceSpec("binance_futures", "prices", "Binance Futures", "rest",
                   "https://fapi.binance.com/fapi/v1/premiumIndex", 5),
    DataSourceSpec("coingecko_prices", "prices", "CoinGecko", "rest",
                   "https://api.coingecko.com/api/v3/simple/price", 60),
    DataSourceSpec("coinmarketcap", "prices", "CoinMarketCap", "rest",
                   "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest", 300,
                   env_key="COINMARKETCAP_API_KEY"),
    DataSourceSpec("cryptocompare_prices", "prices", "CryptoCompare", "rest",
                   "https://min-api.cryptocompare.com/data/pricemultifull", 60,
                   env_key="SENTIMENT_CRYPTOCOMPARE_API_KEY"),
    DataSourceSpec("coinapi", "prices", "CoinAPI", "rest",
                   "https://rest.coinapi.io/v1/exchangerate/BTC/USD", 3600,
                   env_key="COINAPI_KEY"),
    DataSourceSpec("kucoin_spot", "prices", "KuCoin", "rest",
                   "https://api.kucoin.com/api/v1/market/allTickers", 30),
    DataSourceSpec("bybit_spot", "prices", "Bybit Spot", "rest",
                   "https://api.bybit.com/v5/market/tickers", 15, notes="category=spot"),
    DataSourceSpec("bybit_linear", "prices", "Bybit Linear", "rest",
                   "https://api.bybit.com/v5/market/tickers", 15, notes="category=linear"),
    DataSourceSpec("okx_spot", "prices", "OKX Spot", "rest",
                   "https://www.okx.com/api/v5/market/tickers", 15, notes="instType=SPOT"),
    DataSourceSpec("okx_swap", "prices", "OKX Swap", "rest",
                   "https://www.okx.com/api/v5/market/tickers", 15, notes="instType=SWAP"),
    DataSourceSpec("gateio_spot", "prices", "Gate.io", "rest",
                   "https://api.gateio.ws/api/v4/spot/tickers", 30),
    DataSourceSpec("kraken_spot", "prices", "Kraken", "rest",
                   "https://api.kraken.com/0/public/Ticker", 30),
    DataSourceSpec("coinbase_spot", "prices", "Coinbase Advanced", "rest",
                   "https://api.exchange.coinbase.com/products", 15),
    DataSourceSpec("coincap", "prices", "CoinCap", "rest",
                   "https://api.coincap.io/v2/assets", 60),
    DataSourceSpec("binance_ws", "prices", "Binance WebSocket", "websocket",
                   "wss://stream.binance.com:9443/ws/btcusdt@trade", 0, notes="hot_spool"),
    # ── 2. On-Chain & Block Explorers ────────────────────────────────────────
    DataSourceSpec("etherscan", "onchain", "Etherscan", "rest",
                   "https://api.etherscan.io/api", 60, env_key="ETHERSCAN_API_KEY"),
    DataSourceSpec("bscscan", "onchain", "BscScan", "rest",
                   "https://api.bscscan.com/api", 60, env_key="BSCSCAN_API_KEY"),
    DataSourceSpec("polygonscan", "onchain", "Polygonscan", "rest",
                   "https://api.polygonscan.com/api", 60, env_key="POLYGONSCAN_API_KEY"),
    DataSourceSpec("arbiscan", "onchain", "Arbiscan", "rest",
                   "https://api.arbiscan.io/api", 60, env_key="ARBISCAN_API_KEY"),
    DataSourceSpec("optimistic_etherscan", "onchain", "Optimistic Etherscan", "rest",
                   "https://api-optimistic.etherscan.io/api", 60, env_key="OPTIMISM_ETHERSCAN_API_KEY"),
    DataSourceSpec("tronscan", "onchain", "Tronscan", "rest",
                   "https://apilist.tronscanapi.com/api/token/trc20", 120),
    DataSourceSpec("blockchain_com", "onchain", "Blockchain.com BTC", "rest",
                   "https://blockchain.info/stats?format=json", 60),
    DataSourceSpec("blockchair", "onchain", "Blockchair", "rest",
                   "https://api.blockchair.com/bitcoin/stats", 120, env_key="BLOCKCHAIR_API_KEY"),
    DataSourceSpec("solana_rpc", "onchain", "Solana Public RPC", "rest",
                   "https://api.mainnet-beta.solana.com", 60, notes="JSON-RPC"),
    DataSourceSpec("glassnode_free", "onchain", "Glassnode Free Tier", "rest",
                   "https://api.glassnode.com/v1/metrics/market/price_usd_close", 3600,
                   env_key="GLASSNODE_API_KEY"),
    # ── 3. DeFi & DEX Aggregators ────────────────────────────────────────────
    DataSourceSpec("defillama_tvl", "defi", "DeFiLlama TVL", "rest",
                   "https://api.llama.fi/v2/chains", 120),
    DataSourceSpec("defillama_protocols", "defi", "DeFiLlama Protocols", "rest",
                   "https://api.llama.fi/protocols", 300),
    DataSourceSpec("defillama_yields", "defi", "DeFiLlama Yields", "rest",
                   "https://yields.llama.fi/pools", 300),
    DataSourceSpec("geckoterminal", "defi", "GeckoTerminal", "rest",
                   "https://api.geckoterminal.com/api/v2/networks/eth/tokens/0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", 120),
    DataSourceSpec("dexscreener", "defi", "DexScreener", "rest",
                   "https://api.dexscreener.com/latest/dex/search", 60, notes="q=BTC"),
    DataSourceSpec("oneinch", "defi", "1inch Network", "rest",
                   "https://api.1inch.dev/swap/v6.0/1/quote", 300, env_key="ONEINCH_API_KEY"),
    DataSourceSpec("uniswap_subgraph", "defi", "Uniswap Subgraph", "subgraph",
                   "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3", 600),
    DataSourceSpec("aave_subgraph", "defi", "Aave Subgraph", "subgraph",
                   "https://api.thegraph.com/subgraphs/name/aave/protocol-v3", 600),
    # ── 4. News & RSS ────────────────────────────────────────────────────────
    DataSourceSpec("coindesk_rss", "news", "CoinDesk RSS", "rss",
                   "https://www.coindesk.com/arc/outboundfeeds/rss/", 60),
    DataSourceSpec("cointelegraph_rss", "news", "CoinTelegraph RSS", "rss",
                   "https://cointelegraph.com/rss", 60),
    DataSourceSpec("decrypt_rss", "news", "Decrypt RSS", "rss",
                   "https://decrypt.co/feed", 60),
    DataSourceSpec("blockworks_rss", "news", "Blockworks RSS", "rss",
                   "https://blockworks.co/feed", 120),
    DataSourceSpec("bitcoin_magazine_rss", "news", "Bitcoin Magazine RSS", "rss",
                   "https://bitcoinmagazine.com/.rss/full/", 120),
    DataSourceSpec("cryptoslate_rss", "news", "CryptoSlate RSS", "rss",
                   "https://cryptoslate.com/feed/", 120),
    DataSourceSpec("cryptopanic", "news", "CryptoPanic", "rest",
                   "https://cryptopanic.com/api/v1/posts/", 60, env_key="CRYPTOPANIC_API_KEY"),
    DataSourceSpec("newsapi", "news", "NewsAPI.org", "rest",
                   "https://newsapi.org/v2/everything", 300, env_key="NEWSAPI_KEY"),
    DataSourceSpec("bbc_world_rss", "news", "BBC World", "rss",
                   "https://feeds.bbci.co.uk/news/world/rss.xml", 60),
    DataSourceSpec("marketwatch_rss", "news", "MarketWatch", "rss",
                   "https://feeds.marketwatch.com/marketwatch/topstories/", 60),
    # ── 5. Sentiment & Social ─────────────────────────────────────────────────
    DataSourceSpec("fear_greed", "sentiment", "Alternative.me F&G", "rest",
                   "https://api.alternative.me/fng/", 300),
    DataSourceSpec("reddit_crypto", "sentiment", "Reddit r/CryptoCurrency", "rest",
                   "https://www.reddit.com/r/CryptoCurrency/hot.json", 120),
    DataSourceSpec("coingecko_trending", "sentiment", "CoinGecko Trending", "rest",
                   "https://api.coingecko.com/api/v3/search/trending", 120),
    DataSourceSpec("stocktwits_btc", "sentiment", "Stocktwits BTC", "rest",
                   "https://api.stocktwits.com/api/2/streams/symbol/BTC.X.json", 120),
    DataSourceSpec("lunarcrush", "sentiment", "LunarCrush", "rest",
                   "https://lunarcrush.com/api4/public/coins/list/v1", 300, env_key="LUNARCRUSH_API_KEY"),
    DataSourceSpec("twitter_api", "sentiment", "X/Twitter API", "rest",
                   "https://api.twitter.com/2/tweets/search/recent", 300, env_key="TWITTER_BEARER_TOKEN"),
    # ── 6. Events & Calendars ─────────────────────────────────────────────────
    DataSourceSpec("coinmarketcal", "events", "CoinMarketCal", "rest",
                   "https://developers.coinmarketcal.com/v1/events", 3600, env_key="COINMARKETCAL_API_KEY"),
    DataSourceSpec("coingecko_events", "events", "CoinGecko Events", "rest",
                   "https://api.coingecko.com/api/v3/events", 3600),
    DataSourceSpec("defillama_airdrops", "events", "DeFiLlama Airdrops", "rest",
                   "https://api.llama.fi/airdrops", 3600),
    # ── 7. Whale Tracking ─────────────────────────────────────────────────────
    DataSourceSpec("whale_alert", "whale", "Whale Alert", "rest",
                   "https://api.whale-alert.io/v1/transactions", 30, env_key="WHALE_ALERT_API_KEY"),
    DataSourceSpec("blockchain_com_ws", "whale", "Blockchain.com", "rest",
                   "https://blockchain.info/unconfirmed-transactions?format=json", 60),
    DataSourceSpec("debank", "whale", "DeBank", "rest",
                   "https://pro-openapi.debank.com/v1/user/total_balance", 300, env_key="DEBANK_API_KEY"),
    DataSourceSpec("cryptoquant_free", "whale", "CryptoQuant Free", "rest",
                   "https://api.cryptoquant.com/v1/btc/exchange-flows/inflow", 300, env_key="CRYPTOQUANT_API_KEY"),
    DataSourceSpec("internal_cvvd", "whale", "BLACKDARK CVVD", "internal", "whale_tracker", 30),
    # ── 8. Research & Institutional ───────────────────────────────────────────
    DataSourceSpec("binance_research_rss", "research", "Binance Research", "rss",
                   "https://research.binance.com/en/rss", 3600),
    DataSourceSpec("messari_rss", "research", "Messari", "rss",
                   "https://messari.io/rss", 3600),
    DataSourceSpec("coingecko_reports", "research", "CoinGecko Reports", "rest",
                   "https://api.coingecko.com/api/v3/global", 3600),
    # ── 9. Macro & Traditional Finance ────────────────────────────────────────
    DataSourceSpec("fred", "macro", "FRED (Fed)", "rest",
                   "https://api.stlouisfed.org/fred/series/observations", 3600, env_key="FRED_API_KEY"),
    DataSourceSpec("yahoo_finance", "macro", "Yahoo Finance", "rest",
                   "https://query1.finance.yahoo.com/v8/finance/chart/^GSPC", 300),
    DataSourceSpec("alpha_vantage", "macro", "Alpha Vantage", "rest",
                   "https://www.alphavantage.co/query", 3600, env_key="ALPHA_VANTAGE_API_KEY"),
    DataSourceSpec("open_exchange_rates", "macro", "Open Exchange Rates", "rest",
                   "https://openexchangerates.org/api/latest.json", 3600, env_key="OPENEXCHANGERATES_APP_ID"),
    DataSourceSpec("twelvedata", "macro", "Twelve Data", "rest",
                   "https://api.twelvedata.com/time_series", 3600, env_key="TWELVEDATA_API_KEY"),
    DataSourceSpec("investing_com_rss", "macro", "Investing.com Calendar", "rss",
                   "https://www.investing.com/rss/news_301.rss", 600),
    DataSourceSpec("polygon_io", "macro", "Polygon.io", "rest",
                   "https://api.polygon.io", 300, env_key="POLYGON_API_KEY"),
    # ── 10. Regulatory & Security ─────────────────────────────────────────────
    DataSourceSpec("sec_rss", "regulatory", "SEC RSS", "rss",
                   "https://www.sec.gov/news/pressreleases.rss", 600),
    DataSourceSpec("cftc_rss", "regulatory", "CFTC Press", "rss",
                   "https://www.cftc.gov/PressRoom/PressReleases/index.htm", 600, notes="html fallback"),
    DataSourceSpec("certik_skynet", "regulatory", "CertiK Skynet", "rest",
                   "https://skynet.certik.com/api/public/dashboard", 600),
    DataSourceSpec("defi_rekt", "regulatory", "DeFi Rekt Database", "rest",
                   "https://api.rekt.news/leaders", 3600),
    DataSourceSpec("slowmist_hacked", "regulatory", "SlowMist Hacked", "rss",
                   "https://hacked.slowmist.io/feed.xml", 600),
)

# Merge extended registry (100+ sources — Buyer Requirement #8)
try:
    from data_sources_extra import EXTRA_DATA_SOURCES

    DATA_SOURCES = DATA_SOURCES + EXTRA_DATA_SOURCES
except ImportError:
    pass


def sources_by_category(category: Category) -> list[DataSourceSpec]:
    return [s for s in DATA_SOURCES if s.category == category]


def source_by_id(source_id: str) -> DataSourceSpec | None:
    for spec in DATA_SOURCES:
        if spec.source_id == source_id:
            return spec
    return None


def registry_summary() -> dict[str, int]:
    counts: dict[str, int] = {}
    for spec in DATA_SOURCES:
        counts[spec.category] = counts.get(spec.category, 0) + 1
    unique_ids = {s.source_id for s in DATA_SOURCES}
    return {
        "total_sources": len(unique_ids),
        "registered_entries": len(DATA_SOURCES),
        "by_category": counts,
    }
