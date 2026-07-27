"""
BLACKDARK — Central configuration.
All runtime parameters live here to prevent context drift across modules.
"""

from pathlib import Path
import os

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "blackdark.db"
ML_TRAINING_DIR = DATA_DIR / "training"
ML_MODELS_DIR = DATA_DIR / "models"

# ── ML flywheel (AI model training pipeline) ─────────────────────────────────
ML_FLYWHEEL_ENABLED = os.getenv("ML_FLYWHEEL_ENABLED", "true").lower() in {"1", "true", "yes"}
ML_FLYWHEEL_INTERVAL_SEC = int(os.getenv("ML_FLYWHEEL_INTERVAL_SEC", "3600"))
ML_MIN_TRAIN_SAMPLES = int(os.getenv("ML_MIN_TRAIN_SAMPLES", "50"))
ML_AUTO_TRAIN = os.getenv("ML_AUTO_TRAIN", "true").lower() in {"1", "true", "yes"}

# Data moat — live-only oracle dataset for acquisition defensibility
DATA_MOAT_GUARD_ENABLED = os.getenv("DATA_MOAT_GUARD_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}
DATA_MOAT_LIVE_ONLY = os.getenv("DATA_MOAT_LIVE_ONLY", "true").lower() in {"1", "true", "yes"}
DATA_MOAT_BLOCK_SYNTHETIC_SEED = os.getenv("DATA_MOAT_BLOCK_SYNTHETIC_SEED", "true").lower() in {
    "1",
    "true",
    "yes",
}
DATA_MOAT_REQUIRE_FEATURES_JSON = os.getenv("DATA_MOAT_REQUIRE_FEATURES_JSON", "true").lower() in {
    "1",
    "true",
    "yes",
}

# Behavior data asset — non-code acquisition moat (usage patterns, funnel, retention)
BEHAVIOR_DATA_ENABLED = os.getenv("BEHAVIOR_DATA_ENABLED", "true").lower() in {"1", "true", "yes"}
BEHAVIOR_DATA_RETENTION_DAYS = int(os.getenv("BEHAVIOR_DATA_RETENTION_DAYS", "365"))
FEATURE_FREEZE_ENABLED = os.getenv("FEATURE_FREEZE_ENABLED", "false").lower() in {"1", "true", "yes"}

# ── Instant alerts (sub-minute market pulse) ───────────────────────────────
INSTANT_ALERTS_ENABLED = os.getenv("INSTANT_ALERTS_ENABLED", "true").lower() in {"1", "true", "yes"}
INSTANT_ALERT_INTERVAL_SEC = float(os.getenv("INSTANT_ALERT_INTERVAL_SEC", "1"))
INSTANT_ALERT_COOLDOWN_SEC = float(os.getenv("INSTANT_ALERT_COOLDOWN_SEC", "45"))
INSTANT_ALERT_MIN_PROFIT_USDT = float(os.getenv("INSTANT_ALERT_MIN_PROFIT_USDT", "0.15"))
TELEGRAM_ALERT_INTERVAL_SECONDS = float(os.getenv("TELEGRAM_ALERT_INTERVAL_SECONDS", "5"))

# ── Aggregator ─────────────────────────────────────────────────────────────
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "3"))
ORDER_BOOK_DEPTH = 20
QUOTE_BASE = "USDT"

# ── Market cache / scan performance (due-diligence latency fixes) ────────────
MARKET_CACHE_TTL_SEC = float(os.getenv("MARKET_CACHE_TTL_SEC", "2"))
SCAN_CACHE_TTL_SEC = float(os.getenv("SCAN_CACHE_TTL_SEC", "0.5"))
LIVE_FETCH_STALE_THRESHOLD_SEC = float(os.getenv("LIVE_FETCH_STALE_THRESHOLD_SEC", "8"))
ARBITRAGE_PREFER_LIVE = os.getenv("ARBITRAGE_PREFER_LIVE", "false").lower() in {"1", "true", "yes"}
LIVE_FETCH_TIMEOUT_SEC = float(os.getenv("LIVE_FETCH_TIMEOUT_SEC", "3"))
LIVE_FETCH_FAST_DEADLINE_SEC = float(os.getenv("LIVE_FETCH_FAST_DEADLINE_SEC", "1.5"))
INSTITUTIONAL_CONTEXT_CACHE_SEC = float(os.getenv("INSTITUTIONAL_CONTEXT_CACHE_SEC", "2"))
FAST_LIVE_EXCHANGES: frozenset[str] = frozenset(
    ex.strip().lower()
    for ex in os.getenv("FAST_LIVE_EXCHANGES", "binance,okx,bybit,kraken,coinbase").split(",")
    if ex.strip()
)

# ── Price Feed Engine (WS-only strict mode) ──────────────────────────────────
PRICE_FEED_WS_ONLY = os.getenv("PRICE_FEED_WS_ONLY", "true").lower() in {"1", "true", "yes"}
WS_PRICE_VENUES: frozenset[str] = frozenset({"binance", "okx", "bybit"})
# Deferred until Docker/Redis/Kafka infra is available (see DEFERRED_STEPS.md)
REDIS_REQUIRED = os.getenv("REDIS_REQUIRED", "false").lower() in {"1", "true", "yes"}
KAFKA_REQUIRED = os.getenv("KAFKA_REQUIRED", "false").lower() in {"1", "true", "yes"}

# Local dev: skip Redis/Kafka unless explicitly required or enabled
_redis_cache_env = os.getenv("REDIS_PRICE_CACHE_ENABLED")
if _redis_cache_env is None:
    REDIS_PRICE_CACHE_ENABLED = REDIS_REQUIRED
else:
    REDIS_PRICE_CACHE_ENABLED = _redis_cache_env.lower() in {"1", "true", "yes"}

_kafka_stream_env = os.getenv("KAFKA_PRICE_STREAM_ENABLED")
if _kafka_stream_env is None:
    KAFKA_PRICE_STREAM_ENABLED = KAFKA_REQUIRED
else:
    KAFKA_PRICE_STREAM_ENABLED = _kafka_stream_env.lower() in {"1", "true", "yes"}
REDIS_PRICE_TTL_SEC = int(os.getenv("REDIS_PRICE_TTL_SEC", "5"))
PRICE_STREAM_TOPIC = os.getenv("PRICE_STREAM_TOPIC", "blackdark.price.ticks")
REDIS_CLUSTER_NODES = os.getenv("REDIS_CLUSTER_NODES", "").strip()
KAFKA_BROKERS_DEFAULT = os.getenv("KAFKA_BROKERS_DEFAULT", "localhost:9092")
PRICE_STREAM_INLINE_PROCESS = os.getenv("PRICE_STREAM_INLINE_PROCESS", "true").lower() in {"1", "true", "yes"}
GAS_ORACLE_REFRESH_SEC = float(os.getenv("GAS_ORACLE_REFRESH_SEC", "12"))
FEE_MATRIX_REFRESH_SEC = int(os.getenv("FEE_MATRIX_REFRESH_SEC", "3600"))

# ── Microservices architecture ───────────────────────────────────────────────
SERVICE_MODE = os.getenv("SERVICE_MODE", "all").strip().lower()
if REDIS_PRICE_CACHE_ENABLED and PRICE_FEED_WS_ONLY and not os.getenv("REDIS_URL"):
    REDIS_URL = "redis://localhost:6379/0"
else:
    REDIS_URL = os.getenv("REDIS_URL", "").strip()
if KAFKA_PRICE_STREAM_ENABLED and PRICE_FEED_WS_ONLY and not os.getenv("KAFKA_BROKERS"):
    os.environ.setdefault("KAFKA_BROKERS", KAFKA_BROKERS_DEFAULT)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
PG_POOL_MAX = int(os.getenv("PG_POOL_MAX", "20"))
SERVICE_BUS_LOCAL = os.getenv("SERVICE_BUS_LOCAL", "true").lower() in {"1", "true", "yes"}

# ── Low Latency Engine (WebSocket order books) ───────────────────────────────
LOW_LATENCY_MODE = os.getenv("LOW_LATENCY_MODE", "true").lower() in {"1", "true", "yes"}
EXCHANGE_WS_ENABLED = os.getenv("EXCHANGE_WS_ENABLED", "true").lower() in {"1", "true", "yes"}
LIVE_BOOK_MAX_AGE_MS = float(os.getenv("LIVE_BOOK_MAX_AGE_MS", "300"))
EXECUTION_MAX_QUOTE_AGE_MS = float(os.getenv("EXECUTION_MAX_QUOTE_AGE_MS", "300"))
FAST_SCAN_MAX_QUOTE_AGE_MS = float(os.getenv("FAST_SCAN_MAX_QUOTE_AGE_MS", "300"))
STALE_PRICE_GUARD_ENABLED = os.getenv("STALE_PRICE_GUARD_ENABLED", "true").lower() in {"1", "true", "yes"}

# ── Exchange ingress (anti-DDoS / IP-ban) ────────────────────────────────────
INGRESS_GUARD_ENABLED = os.getenv("INGRESS_GUARD_ENABLED", "true").lower() in {"1", "true", "yes"}
MAX_CONCURRENT_EXCHANGE_POLLS = int(os.getenv("MAX_CONCURRENT_EXCHANGE_POLLS", "8"))
MAX_CONCURRENT_SYMBOL_POLLS_PER_EXCHANGE = int(os.getenv("MAX_CONCURRENT_SYMBOL_POLLS_PER_EXCHANGE", "4"))
EXCHANGE_POLL_STAGGER_MS = float(os.getenv("EXCHANGE_POLL_STAGGER_MS", "150"))
EXCHANGE_BAN_COOLDOWN_SEC = float(os.getenv("EXCHANGE_BAN_COOLDOWN_SEC", "3600"))
EXCHANGE_RATE_LIMIT_STRIKES = int(os.getenv("EXCHANGE_RATE_LIMIT_STRIKES", "3"))
ML_DRIFT_PSI_THRESHOLD = float(os.getenv("ML_DRIFT_PSI_THRESHOLD", "0.25"))
ML_OOD_REJECT_THRESHOLD = float(os.getenv("ML_OOD_REJECT_THRESHOLD", "0.65"))
ML_OOD_FAIL_CLOSED = os.getenv("ML_OOD_FAIL_CLOSED", "true").lower() in {"1", "true", "yes"}
ML_DRIFT_FREEZE_SEC = int(os.getenv("ML_DRIFT_FREEZE_SEC", "300"))
AUTO_EXECUTION_INTERVAL_SEC = int(os.getenv("AUTO_EXECUTION_INTERVAL_SEC", "1"))

# ── Immutable whitelist guards (NEVER dynamically excluded) ────────────────
WHITELIST_EXCHANGES: frozenset[str] = frozenset(
    {
        "binance",
        "okx",
        "bybit",
        "coinbase",
        "kraken",
        "kucoin",
        "gateio",
        "bitget",
        "mexc",
    }
)
WHITELIST_ASSETS: frozenset[str] = frozenset(
    {
        "BTC",
        "ETH",
        "SOL",
        "BNB",
        "XRP",
    }
)

# Phase-1 launch universe — full client blueprint (105 assets)
def _load_universe_symbols() -> frozenset[str]:
    import json

    registry_path = DATA_DIR / "universe_registry.json"
    if registry_path.exists():
        try:
            payload = json.loads(registry_path.read_text(encoding="utf-8"))
            symbols: set[str] = set()
            for row in payload.get("assets") or []:
                sym = str(row.get("symbol") or "").upper()
                if sym:
                    symbols.add(sym)
                for alias in row.get("aliases") or []:
                    if alias:
                        symbols.add(str(alias).upper())
            if symbols:
                return frozenset(symbols)
        except (json.JSONDecodeError, OSError):
            pass
    return frozenset(
        {
            "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LINK",
            "MATIC", "UNI", "ATOM", "LTC", "NEAR", "APT", "ARB", "OP", "INJ", "SUI",
            "SEI", "TIA", "PEPE", "WIF", "FIL",
        }
    )


UNIVERSE_ASSETS: frozenset[str] = _load_universe_symbols()

# Backward-compatible alias used across modules
EXTENDED_TRACKED_ASSETS: frozenset[str] = UNIVERSE_ASSETS

MARKET_RADAR_LIMIT = int(os.getenv("MARKET_RADAR_LIMIT", "105"))


def tracked_asset_list() -> list[str]:
    """Sorted list of the 105 blueprint assets."""
    return sorted(UNIVERSE_ASSETS)


# Exchanges with implemented REST fetchers (100-venue universe via market_fetcher_hub)
CCXT_SYMBOL_LIMIT = int(os.getenv("CCXT_SYMBOL_LIMIT", "25"))
COINGECKO_SYMBOL_LIMIT = int(os.getenv("COINGECKO_SYMBOL_LIMIT", "10"))
DEX_SYMBOL_LIMIT = int(os.getenv("DEX_SYMBOL_LIMIT", "15"))
PERP_DEX_SYMBOL_LIMIT = int(os.getenv("PERP_DEX_SYMBOL_LIMIT", "15"))


def _load_universe_exchange_ids() -> frozenset[str]:
    path = DATA_DIR / "universe_registry.json"
    if path.exists():
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
        ids = {str(row["id"]) for row in payload.get("exchanges") or [] if row.get("id")}
        if ids:
            return frozenset(ids)
    return frozenset(
        {
            "binance",
            "okx",
            "bybit",
            "coinbase",
            "kraken",
            "kucoin",
            "gateio",
            "bitget",
            "mexc",
        }
    )


INGESTION_READY_EXCHANGES: frozenset[str] = _load_universe_exchange_ids()

# ── Dynamic liquidity discovery ────────────────────────────────────────────
LIQUIDITY_QUOTE_CURRENCIES = ("USDT", "USDC")
LIQUIDITY_MIN_TRUST_SCORE = int(os.getenv("LIQUIDITY_MIN_TRUST_SCORE", "7"))
LIQUIDITY_MIN_24H_VOLUME_USD = float(os.getenv("LIQUIDITY_MIN_24H_VOLUME_USD", "5000000"))
LIQUIDITY_MAX_DYNAMIC_EXCHANGES = int(os.getenv("LIQUIDITY_MAX_DYNAMIC_EXCHANGES", "100"))
LIQUIDITY_MAX_DYNAMIC_ASSETS = int(os.getenv("LIQUIDITY_MAX_DYNAMIC_ASSETS", "100"))
LIQUIDITY_DISCOVERY_TIMEOUT_SECONDS = int(os.getenv("LIQUIDITY_DISCOVERY_TIMEOUT_SECONDS", "30"))
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY", "")
COINMARKETCAP_ENABLED = bool(COINMARKETCAP_API_KEY)
COINMARKETCAP_LISTINGS_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
COINMARKETCAP_EXCHANGES_URL = "https://pro-api.coinmarketcap.com/v1/exchange/listings/latest"
OPERATIONAL_MANIFEST_PATH = DATA_DIR / "operational_manifest.json"
MANIFEST_AUTO_APPROVE = os.getenv("MANIFEST_AUTO_APPROVE", "false").lower() in {
    "1",
    "true",
    "yes",
}
MANIFEST_REQUIRE_REVIEW = os.getenv("MANIFEST_REQUIRE_REVIEW", "true").lower() in {
    "1",
    "true",
    "yes",
}

# ── Core symbols ───────────────────────────────────────────────────────────
CORE_COINS = sorted(WHITELIST_ASSETS)

# All blueprint USDT pairs for scanning (105 assets)
SYMBOLS = [f"{coin}/{QUOTE_BASE}" for coin in sorted(UNIVERSE_ASSETS)]

# Cross-pair anchors used for triangular loops (e.g. ETH/BTC, SOL/BTC).
CROSS_QUOTES = ["BTC", "ETH"]


def cross_pairs() -> list[str]:
    """Essential spot cross-pairs for triangular arbitrage."""
    pairs: set[str] = set()

    if "BTC" in CORE_COINS and "ETH" in CORE_COINS:
        pairs.add("ETH/BTC")

    for coin in CORE_COINS:
        if coin in CROSS_QUOTES:
            continue
        if "BTC" in CORE_COINS:
            pairs.add(f"{coin}/BTC")
        if "ETH" in CORE_COINS and coin != "ETH":
            pairs.add(f"{coin}/ETH")

    return sorted(pairs)


def all_spot_symbols() -> list[str]:
    """Stablecoin pairs plus cross-pairs required for 3-legged scans."""
    symbols = list(SYMBOLS)
    for pair in cross_pairs():
        if pair not in symbols:
            symbols.append(pair)
    return symbols


def perpetual_symbols() -> list[str]:
    """Linear perpetual symbols aligned to the core USDT spot pairs."""
    return list(SYMBOLS)


# ── Exchanges (CCXT ids) ───────────────────────────────────────────────────
EXCHANGES = {
    "binance": {
        "enabled": True,
        "rate_limit": True,
        "options": {"defaultType": "spot"},
    },
    "okx": {
        "enabled": True,
        "rate_limit": True,
        "options": {"defaultType": "spot"},
    },
    "bybit": {
        "enabled": True,
        "rate_limit": True,
        "options": {"defaultType": "spot"},
    },
    "coinbase": {
        "enabled": True,
        "rate_limit": True,
        "options": {"defaultType": "spot"},
    },
    "kraken": {
        "enabled": True,
        "rate_limit": True,
        "options": {"defaultType": "spot"},
    },
    "kucoin": {
        "enabled": True,
        "rate_limit": True,
        "options": {"defaultType": "spot"},
    },
    "gateio": {
        "enabled": True,
        "rate_limit": True,
        "options": {"defaultType": "spot"},
    },
}


def enabled_exchanges() -> dict:
    """Return enabled exchanges — native Tier-1 + CCXT Phase-B venues."""
    enabled = {
        exchange_id: settings
        for exchange_id, settings in EXCHANGES.items()
        if settings.get("enabled", False)
    }
    for exchange_id in INGESTION_READY_EXCHANGES:
        if exchange_id not in enabled:
            try:
                from market_fetcher_hub import provider_for_venue

                provider = provider_for_venue(exchange_id)
            except ImportError:
                provider = "native"
            enabled[exchange_id] = {
                "enabled": True,
                "rate_limit": True,
                "provider": provider,
            }
    return enabled


def is_whitelisted_exchange(exchange_id: str) -> bool:
    return exchange_id.strip().lower() in WHITELIST_EXCHANGES


def is_whitelisted_asset(asset: str) -> bool:
    return asset.strip().upper() in WHITELIST_ASSETS


def enforce_whitelist_guards(
    exchanges: list[str] | set[str],
    assets: list[str] | set[str],
) -> tuple[list[str], list[str]]:
    """Merge candidate lists with immutable whitelist baseline."""
    exchange_set = {item.strip().lower() for item in exchanges}
    asset_set = {item.strip().upper() for item in assets}
    exchange_set.update(WHITELIST_EXCHANGES)
    asset_set.update(WHITELIST_ASSETS)
    return sorted(exchange_set), sorted(asset_set)


# ── RSI defaults ───────────────────────────────────────────────────────────
TA_RSI_PERIOD = 14
TA_RSI_OVERSOLD = 30.0
TA_RSI_OVERBOUGHT = 70.0

# ── MACD defaults ──────────────────────────────────────────────────────────
TA_MACD_FAST = 12
TA_MACD_SLOW = 26
TA_MACD_SIGNAL = 9

# ── EMA defaults ───────────────────────────────────────────────────────────
TA_EMA_FAST = 12
TA_EMA_SLOW = 26
TA_EMA_TREND = 50

# ── Database ───────────────────────────────────────────────────────────────
DB_WAL_MODE = True
DB_BUSY_TIMEOUT_MS = 5000

# ── Arbitrage ──────────────────────────────────────────────────────────────
DEFAULT_QUOTE_AMOUNT = 100.0
DEFAULT_TAKER_FEE = 0.001
DEFAULT_MAKER_FEE = 0.0002
TRIANGLE_ANCHOR = QUOTE_BASE
MIN_SPREAD_BPS = 0.0
SLIPPAGE_BUFFER_BPS = 5.0
DEFAULT_FUTURES_TAKER_FEE = 0.0005
MIN_FUNDING_SPREAD_BPS = 1.0
FUNDING_PERIODS_PER_DAY = 3

# ── AI Oracle ────────────────────────────────────────────────────────────────
AI_ORACLE_MIN_SCORE = 65.0
AI_ORACLE_MIN_CONFIDENCE = 60.0
AI_ORACLE_PROFIT_REFERENCE_PCT = 2.0
AI_ORACLE_SLIPPAGE_REFERENCE_BPS = 50.0
AI_ORACLE_PROVIDER = "rules"

# Dimension conflict guard — veto/abstain when TA vs NLP vs on-chain disagree
DIMENSION_CONFLICT_VETO_ENABLED = os.getenv("DIMENSION_CONFLICT_VETO_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}
DIMENSION_CONFLICT_SEVERE_SCORE_CAP = float(os.getenv("DIMENSION_CONFLICT_SEVERE_SCORE_CAP", "49"))
DIMENSION_CONFLICT_MILD_SCORE_CAP = float(os.getenv("DIMENSION_CONFLICT_MILD_SCORE_CAP", "59"))
DIMENSION_CONFLICT_BLOCK_MILD_EXECUTION = os.getenv(
    "DIMENSION_CONFLICT_BLOCK_MILD_EXECUTION", "true"
).lower() in {"1", "true", "yes"}
SENTIMENT_GATE_FAIL_CLOSED = os.getenv("SENTIMENT_GATE_FAIL_CLOSED", "true").lower() in {
    "1",
    "true",
    "yes",
}

# ── Institutional Manipulation & Sector Rotation ─────────────────────────────
SECTOR_FLOW_WINDOW_SECONDS = 60
SII_BUCKET_COUNT = 4

SECTOR_MAP: dict[str, str] = {
    "BTC": "Layer 1",
    "ETH": "Layer 1",
    "SOL": "Layer 1",
    "BNB": "DeFi",
    "XRP": "Payments",
    "ADA": "Layer 1",
    "DOGE": "Meme",
    "AVAX": "Layer 1",
    "DOT": "Layer 1",
    "LINK": "Oracle",
    "MATIC": "L2",
    "UNI": "DeFi",
    "ATOM": "Layer 1",
    "LTC": "Payments",
    "NEAR": "Layer 1",
    "APT": "Layer 1",
    "ARB": "L2",
    "OP": "L2",
    "INJ": "DeFi",
    "SUI": "Layer 1",
    "SEI": "Layer 1",
    "TIA": "Infrastructure",
    "PEPE": "Meme",
    "WIF": "Meme",
    "FIL": "Infrastructure",
}

# Cross-Venue Volume Discrepancy (CVVD) tuning
CVVD_VOLUME_SPIKE_RATIO = 2.2
CVVD_LIQUIDITY_DROP_RATIO = -0.12
CVVD_MIN_MANIPULATION_SCORE = 45.0
CVVD_ICEBERG_TRADE_COUNT = 8
CVVD_ICEBERG_SIZE_CV_MAX = 0.35
CVVD_BOOK_DEPTH_LEVELS = 10

# Sector Inflow Index (SII) tuning
SII_VELOCITY_SCALE_USD = 250_000.0
SII_ACCELERATION_SCALE_USD = 150_000.0

# Legacy scoring hook (used by ai_oracle)
WHALE_NOTIONAL_THRESHOLD_USD = 50_000.0
WHALE_SCORE_BOOST_MAX = 8.0
MANIPULATION_SCORE_BOOST_MAX = 8.0

# B2B data exporter
B2B_API_KEY_ENV = "BLACKDARK_B2B_API_KEY"
B2B_DEMO_API_KEY = os.getenv("BLACKDARK_B2B_DEMO_KEY", "bd_demo_launch_2026")
B2B_FEED_VERSION = "1.0.0"
B2B_DEFAULT_EXPORT_LIMIT = 250
B2B_DEMO_EXPORT_LIMIT = 15
B2B_WS_ENABLED = os.getenv("B2B_WS_ENABLED", "true").lower() in {"1", "true", "yes"}
B2B_WS_HEARTBEAT_SEC = int(os.getenv("B2B_WS_HEARTBEAT_SEC", "15"))
B2B_WS_EVENT_COOLDOWN_SEC = float(os.getenv("B2B_WS_EVENT_COOLDOWN_SEC", "3"))
B2B_WS_LATENCY_TARGET_MS = int(os.getenv("B2B_WS_LATENCY_TARGET_MS", "500"))
B2B_WS_MAX_CONNECTIONS = int(os.getenv("B2B_WS_MAX_CONNECTIONS", "50"))

# Launch — Pro trial on signup + Stripe checkout
PRO_TRIAL_DAYS = int(os.getenv("PRO_TRIAL_DAYS", "7"))
LAUNCH_PROMO_CODES: dict[str, int] = {
    "LAUNCHPRO": 14,
    "DARKSIDE": 7,
    "BLACKDARK": 7,
}

# ── Funding + Institutional Convergence ──────────────────────────────────────
FUNDING_SII_VELOCITY_WEIGHT = 0.60
FUNDING_SII_ACCELERATION_WEIGHT = 0.40
FUNDING_SII_CONVERGENCE_BPS = 8.0
FUNDING_SII_SCORE_BOOST_MAX = 12.0
FUNDING_CVVD_RISK_BUFFER_BPS = 25.0
FUNDING_CVVD_RISK_BUFFER_MAX_BPS = 150.0
FUNDING_CVVD_HIGH_RISK_PATTERNS = ("cross_venue_manipulation", "liquidity_spoof")

# ── Hot-Data Pipeline (Point 38) ─────────────────────────────────────────────
HOT_STORAGE_DIR = DATA_DIR / "hot_spool"
HOT_STORAGE_BUFFER_MAX = int(os.getenv("HOT_STORAGE_BUFFER_MAX", "10000"))
HOT_STORAGE_FLUSH_BATCH_SIZE = int(os.getenv("HOT_STORAGE_FLUSH_BATCH_SIZE", "500"))
HOT_STORAGE_FLUSH_INTERVAL_SECONDS = float(
    os.getenv("HOT_STORAGE_FLUSH_INTERVAL_SECONDS", "1.0")
)
# Production default: never mirror high-frequency ticks into SQLite (bloat risk).
HOT_STORAGE_MIRROR_SQLITE = os.getenv("HOT_STORAGE_MIRROR_SQLITE", "false").lower() in {
    "1",
    "true",
    "yes",
}
HOT_STORAGE_BACKEND = os.getenv("HOT_STORAGE_BACKEND", "local")
HOT_TIER_RETENTION_HOURS = int(os.getenv("HOT_TIER_RETENTION_HOURS", "48"))
# Cost guard — prevent terabyte hot-tier bloat at 100-exchange scale
STORAGE_COST_GUARD_ENABLED = os.getenv("STORAGE_COST_GUARD_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}
HOT_STORAGE_ARCHIVE_PRICING = os.getenv("HOT_STORAGE_ARCHIVE_PRICING", "true").lower() in {
    "1",
    "true",
    "yes",
}
HOT_STORAGE_ARCHIVE_ORDER_BOOKS = os.getenv("HOT_STORAGE_ARCHIVE_ORDER_BOOKS", "false").lower() in {
    "1",
    "true",
    "yes",
}
HOT_STORAGE_ARCHIVE_TICKS = os.getenv("HOT_STORAGE_ARCHIVE_TICKS", "false").lower() in {
    "1",
    "true",
    "yes",
}
HOT_STORAGE_ARCHIVE_FUNDING = os.getenv("HOT_STORAGE_ARCHIVE_FUNDING", "true").lower() in {
    "1",
    "true",
    "yes",
}
HOT_STORAGE_DAILY_MAX_MB = float(os.getenv("HOT_STORAGE_DAILY_MAX_MB", "2048"))
HOT_STORAGE_ORDER_BOOK_THROTTLE_MS = int(os.getenv("HOT_STORAGE_ORDER_BOOK_THROTTLE_MS", "60000"))
HOT_STORAGE_TICK_THROTTLE_MS = int(os.getenv("HOT_STORAGE_TICK_THROTTLE_MS", "0"))
HOT_STORAGE_FUNDING_THROTTLE_MS = int(os.getenv("HOT_STORAGE_FUNDING_THROTTLE_MS", "60000"))
HOT_STORAGE_ARCHIVE_WS_TICKS = os.getenv("HOT_STORAGE_ARCHIVE_WS_TICKS", "false").lower() in {
    "1",
    "true",
    "yes",
}
HOT_STORAGE_SYMBOL_THROTTLE_MS = int(os.getenv("HOT_STORAGE_SYMBOL_THROTTLE_MS", "1000"))
HOT_STORAGE_CLICKHOUSE_URL = os.getenv("HOT_STORAGE_CLICKHOUSE_URL", "")
HOT_STORAGE_CLICKHOUSE_DATABASE = os.getenv("HOT_STORAGE_CLICKHOUSE_DATABASE", "blackdark")
HOT_STORAGE_CLICKHOUSE_USER = os.getenv("HOT_STORAGE_CLICKHOUSE_USER", "default")
HOT_STORAGE_CLICKHOUSE_PASSWORD = os.getenv("HOT_STORAGE_CLICKHOUSE_PASSWORD", "")
HOT_STORAGE_TIMESCALE_DSN = os.getenv("HOT_STORAGE_TIMESCALE_DSN", "")
HOT_STORAGE_TIMESCALE_SCHEMA = os.getenv("HOT_STORAGE_TIMESCALE_SCHEMA", "public")

# ── Parquet Compaction (Point 39) ────────────────────────────────────────────
HISTORICAL_PARQUET_DIR = DATA_DIR / "historical_parquet"
PARQUET_COMPACTION_ARCHIVE_DIR = DATA_DIR / "hot_spool_archive"
PARQUET_COMPACTION_DISPOSITION = os.getenv("PARQUET_COMPACTION_DISPOSITION", "delete")
PARQUET_COMPACTION_HOUR_UTC = int(os.getenv("PARQUET_COMPACTION_HOUR_UTC", "0"))
PARQUET_COMPACTION_MINUTE_UTC = int(os.getenv("PARQUET_COMPACTION_MINUTE_UTC", "5"))
PARQUET_COMPACTION_ENABLED = os.getenv("PARQUET_COMPACTION_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}
HISTORY_PARQUET_DIR = DATA_DIR / "history"
COMPACTION_MIN_AGE_HOURS = int(os.getenv("COMPACTION_MIN_AGE_HOURS", "48"))
SQLITE_HISTORICAL_COMPACTION_ENABLED = os.getenv(
    "SQLITE_HISTORICAL_COMPACTION_ENABLED", "true"
).lower() in {"1", "true", "yes"}
COMPACTION_SQLITE_BATCH_SIZE = int(os.getenv("COMPACTION_SQLITE_BATCH_SIZE", "50000"))
COMPACTION_BACKGROUND_COOLDOWN_SECONDS = int(
    os.getenv("COMPACTION_BACKGROUND_COOLDOWN_SECONDS", "3600")
)

# ── Cloud Cold Storage Sync (Point 40) ───────────────────────────────────────
CLOUD_SYNC_ENABLED = os.getenv("CLOUD_SYNC_ENABLED", "false").lower() in {
    "1",
    "true",
    "yes",
}
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "")
AWS_S3_REGION = os.getenv("AWS_S3_REGION", "us-east-1")
AWS_S3_PREFIX = os.getenv("AWS_S3_PREFIX", "blackdark/historical")
CLOUD_SYNC_DELETE_LOCAL_AFTER_VERIFY = os.getenv(
    "CLOUD_SYNC_DELETE_LOCAL_AFTER_VERIFY", "true"
).lower() in {"1", "true", "yes"}
CLOUD_SYNC_UPLOAD_TIMEOUT_SECONDS = int(os.getenv("CLOUD_SYNC_UPLOAD_TIMEOUT_SECONDS", "120"))
CLOUD_SYNC_ALLOW_IAM_ROLE = os.getenv("CLOUD_SYNC_ALLOW_IAM_ROLE", "false").lower() in {
    "1",
    "true",
    "yes",
}
CLOUD_SYNC_INTERVAL_HOURS = int(os.getenv("CLOUD_SYNC_INTERVAL_HOURS", "6"))
AWS_S3_STORAGE_CLASS = os.getenv("AWS_S3_STORAGE_CLASS", "STANDARD_IA")
AWS_S3_GLACIER_TRANSITION_DAYS = int(os.getenv("AWS_S3_GLACIER_TRANSITION_DAYS", "90"))
AWS_S3_DEEP_ARCHIVE_TRANSITION_DAYS = int(
    os.getenv("AWS_S3_DEEP_ARCHIVE_TRANSITION_DAYS", "365")
)

# ── Multi-Tier Storage Orchestration ─────────────────────────────────────────
STORAGE_TIER_AUTO = os.getenv("STORAGE_TIER_AUTO", "true").lower() in {"1", "true", "yes"}
STORAGE_TIER_MAINTENANCE_INTERVAL_HOURS = int(
    os.getenv("STORAGE_TIER_MAINTENANCE_INTERVAL_HOURS", "1")
)
DB_MARKET_DATA_RETENTION_DAYS = int(os.getenv("DB_MARKET_DATA_RETENTION_DAYS", "2"))
WARM_PARQUET_LOCAL_RETENTION_DAYS = int(os.getenv("WARM_PARQUET_LOCAL_RETENTION_DAYS", "30"))
HOT_SPOOL_ARCHIVE_RETENTION_DAYS = int(os.getenv("HOT_SPOOL_ARCHIVE_RETENTION_DAYS", "2"))
ORACLE_RETRAIN_ENABLED = os.getenv("ORACLE_RETRAIN_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}

# ── Order Book Imbalance & Flash Crash Predictor (Point 41) ─────────────────
OBI_DEPTH_LEVELS = int(os.getenv("OBI_DEPTH_LEVELS", "10"))
OBI_WEIGHT_DECAY = float(os.getenv("OBI_WEIGHT_DECAY", "0.85"))
OBI_HISTORY_WINDOW = int(os.getenv("OBI_HISTORY_WINDOW", "20"))
OBI_MIN_HISTORY_POINTS = int(os.getenv("OBI_MIN_HISTORY_POINTS", "5"))
OBI_FLASH_CRASH_Z_THRESHOLD = float(os.getenv("OBI_FLASH_CRASH_Z_THRESHOLD", "2.5"))
OBI_LIQUIDITY_DROUGHT_THRESHOLD = float(os.getenv("OBI_LIQUIDITY_DROUGHT_THRESHOLD", "-0.65"))
OBI_LIQUIDITY_DROUGHT_DELTA = float(os.getenv("OBI_LIQUIDITY_DROUGHT_DELTA", "0.12"))
OBI_SCORE_BOOST_MAX = float(os.getenv("OBI_SCORE_BOOST_MAX", "6.0"))
OBI_FLASH_PENALTY_MAX = float(os.getenv("OBI_FLASH_PENALTY_MAX", "10.0"))

# ── On-Chain Whale Flow Matrix (Point 42) ─────────────────────────────────────
ONCHAIN_DATA_SOURCE = os.getenv("ONCHAIN_DATA_SOURCE", "simulated")
ONCHAIN_API_URL = os.getenv("ONCHAIN_API_URL", "")
ONCHAIN_API_KEY = os.getenv("ONCHAIN_API_KEY", "")
ONCHAIN_FETCH_TIMEOUT_SECONDS = int(os.getenv("ONCHAIN_FETCH_TIMEOUT_SECONDS", "8"))
ONCHAIN_HISTORY_WINDOW = int(os.getenv("ONCHAIN_HISTORY_WINDOW", "12"))
ONCHAIN_MIN_HISTORY_POINTS = int(os.getenv("ONCHAIN_MIN_HISTORY_POINTS", "4"))
ONCHAIN_SPIKE_Z_THRESHOLD = float(os.getenv("ONCHAIN_SPIKE_Z_THRESHOLD", "2.0"))
ONCHAIN_LARGE_FLOW_USD = float(os.getenv("ONCHAIN_LARGE_FLOW_USD", "1000000"))
ONCHAIN_MIN_STDEV_USD = float(os.getenv("ONCHAIN_MIN_STDEV_USD", "250000"))
ONCHAIN_NEUTRAL_BAND_USD = float(os.getenv("ONCHAIN_NEUTRAL_BAND_USD", "150000"))
ONCHAIN_SCORE_BOOST_MAX = float(os.getenv("ONCHAIN_SCORE_BOOST_MAX", "5.0"))
ONCHAIN_DISTRIBUTION_PENALTY_MAX = float(os.getenv("ONCHAIN_DISTRIBUTION_PENALTY_MAX", "8.0"))

# ── AI NLP Sentiment & News Radar (Phase 4) ───────────────────────────────────
SENTIMENT_POLL_INTERVAL_SECONDS = int(os.getenv("SENTIMENT_POLL_INTERVAL_SECONDS", "60"))
SENTIMENT_ROLLING_WINDOW_SECONDS = int(os.getenv("SENTIMENT_ROLLING_WINDOW_SECONDS", "300"))
SENTIMENT_FETCH_TIMEOUT_SECONDS = int(os.getenv("SENTIMENT_FETCH_TIMEOUT_SECONDS", "12"))
SENTIMENT_DATA_SOURCE = os.getenv("SENTIMENT_DATA_SOURCE", "mixed").lower()
SENTIMENT_CRYPTOCOMPARE_API_KEY = os.getenv("SENTIMENT_CRYPTOCOMPARE_API_KEY", "")
SENTIMENT_RSS_FEEDS = [
    feed.strip()
    for feed in os.getenv(
        "SENTIMENT_RSS_FEEDS",
        "https://www.coindesk.com/arc/outboundfeeds/rss/,"
        "https://cointelegraph.com/rss,"
        "https://decrypt.co/feed",
    ).split(",")
    if feed.strip()
]
SENTIMENT_TWITTER_MOCK_ENABLED = os.getenv("SENTIMENT_TWITTER_MOCK_ENABLED", "false").lower() in {
    "1",
    "true",
    "yes",
}
SENTIMENT_TELEGRAM_MOCK_ENABLED = os.getenv("SENTIMENT_TELEGRAM_MOCK_ENABLED", "false").lower() in {
    "1",
    "true",
    "yes",
}
SENTIMENT_LLM_FALLBACK = os.getenv("SENTIMENT_LLM_FALLBACK", "false").lower() in {
    "1",
    "true",
    "yes",
}
SENTIMENT_LLM_PROVIDER = os.getenv("SENTIMENT_LLM_PROVIDER", "openai")
SENTIMENT_OPENAI_MODEL = os.getenv("SENTIMENT_OPENAI_MODEL", "gpt-4o-mini")
SENTIMENT_SCORE_BOOST_MAX = float(os.getenv("SENTIMENT_SCORE_BOOST_MAX", "4.0"))
SENTIMENT_SCORE_PENALTY_MAX = float(os.getenv("SENTIMENT_SCORE_PENALTY_MAX", "4.0"))
SENTIMENT_NEUTRAL_BAND = float(os.getenv("SENTIMENT_NEUTRAL_BAND", "0.08"))
SENTIMENT_EXTREME_NEGATIVE_THRESHOLD = float(
    os.getenv("SENTIMENT_EXTREME_NEGATIVE_THRESHOLD", "-0.6")
)
SENTIMENT_EXTREME_POSITIVE_THRESHOLD = float(
    os.getenv("SENTIMENT_EXTREME_POSITIVE_THRESHOLD", "0.75")
)
SENTIMENT_PANIC_SCORE_PENALTY = float(os.getenv("SENTIMENT_PANIC_SCORE_PENALTY", "25"))
SENTIMENT_GREED_SCORE_PENALTY = float(os.getenv("SENTIMENT_GREED_SCORE_PENALTY", "20"))
SENTIMENT_PUMP_RISK_PENALTY = float(os.getenv("SENTIMENT_PUMP_RISK_PENALTY", "15"))
SENTIMENT_GREED_BLOCK_ENABLED = os.getenv("SENTIMENT_GREED_BLOCK_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}

# NLP manipulation guard — pump-dump / fake social sentiment resistance
SENTIMENT_MANIPULATION_GUARD_ENABLED = os.getenv(
    "SENTIMENT_MANIPULATION_GUARD_ENABLED", "true"
).lower() in {"1", "true", "yes"}
SENTIMENT_ALLOW_MOCK_IN_SCORING = os.getenv("SENTIMENT_ALLOW_MOCK_IN_SCORING", "false").lower() in {
    "1",
    "true",
    "yes",
}
SENTIMENT_TRUST_WEIGHT_RSS = float(os.getenv("SENTIMENT_TRUST_WEIGHT_RSS", "1.0"))
SENTIMENT_TRUST_WEIGHT_EDITORIAL = float(os.getenv("SENTIMENT_TRUST_WEIGHT_EDITORIAL", "1.0"))
SENTIMENT_TRUST_WEIGHT_TWITTER = float(os.getenv("SENTIMENT_TRUST_WEIGHT_TWITTER", "0.15"))
SENTIMENT_TRUST_WEIGHT_REDDIT = float(os.getenv("SENTIMENT_TRUST_WEIGHT_REDDIT", "0.20"))
SENTIMENT_TRUST_WEIGHT_MOCK = float(os.getenv("SENTIMENT_TRUST_WEIGHT_MOCK", "0.0"))
SENTIMENT_TRUST_WEIGHT_DEFAULT = float(os.getenv("SENTIMENT_TRUST_WEIGHT_DEFAULT", "0.5"))
SENTIMENT_BURST_WINDOW_SEC = float(os.getenv("SENTIMENT_BURST_WINDOW_SEC", "120"))
SENTIMENT_BURST_MAX_SIMILAR = int(os.getenv("SENTIMENT_BURST_MAX_SIMILAR", "3"))

# ── API key security (custody / regulatory) ───────────────────────────────────
API_KEY_SECURITY_GUARD_ENABLED = os.getenv("API_KEY_SECURITY_GUARD_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}
API_KEY_BLOCK_WITHDRAW_ENABLED = os.getenv("API_KEY_BLOCK_WITHDRAW_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}
API_KEY_REQUIRE_USER_VAULT_LIVE = os.getenv("API_KEY_REQUIRE_USER_VAULT_LIVE", "true").lower() in {
    "1",
    "true",
    "yes",
}
API_KEY_BLOCK_ENV_KEYS_IN_PRODUCTION = os.getenv(
    "API_KEY_BLOCK_ENV_KEYS_IN_PRODUCTION", "true"
).lower() in {"1", "true", "yes"}
WASH_TRADE_GUARD_ENABLED = os.getenv("WASH_TRADE_GUARD_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}
WASH_TRADE_WINDOW_SEC = float(os.getenv("WASH_TRADE_WINDOW_SEC", "300"))

# Regulatory compliance — oracle outputs are informational analytics, not investment advice
REGULATORY_COMPLIANCE_ENABLED = os.getenv("REGULATORY_COMPLIANCE_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}

# Subscriber retention — bear-market churn mitigation
RETENTION_GUARD_ENABLED = os.getenv("RETENTION_GUARD_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}
RETENTION_PAST_DUE_GRACE_DAYS = int(os.getenv("RETENTION_PAST_DUE_GRACE_DAYS", "7"))
RETENTION_LOW_ARB_PROFITABLE_MAX = int(os.getenv("RETENTION_LOW_ARB_PROFITABLE_MAX", "1"))
RETENTION_LOW_VOLATILITY_PCT = float(os.getenv("RETENTION_LOW_VOLATILITY_PCT", "3.0"))
RETENTION_AUTO_TRIAL_EXTENSION = os.getenv("RETENTION_AUTO_TRIAL_EXTENSION", "true").lower() in {
    "1",
    "true",
    "yes",
}
RETENTION_BEAR_TRIAL_EXTENSION_DAYS = int(os.getenv("RETENTION_BEAR_TRIAL_EXTENSION_DAYS", "7"))
RETENTION_GRANT_COOLDOWN_DAYS = int(os.getenv("RETENTION_GRANT_COOLDOWN_DAYS", "30"))

# Flywheel saturation — crowd liquidity depletion on mass arbitrage alerts
FLYWHEEL_SATURATION_GUARD_ENABLED = os.getenv("FLYWHEEL_SATURATION_GUARD_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}
FLYWHEEL_MAX_ALERT_RECIPIENTS = int(os.getenv("FLYWHEEL_MAX_ALERT_RECIPIENTS", "50"))
FLYWHEEL_MAX_EXECUTION_SLOTS_PER_OPP = int(os.getenv("FLYWHEEL_MAX_EXECUTION_SLOTS_PER_OPP", "5"))
FLYWHEEL_DEFAULT_COMPETING_NOTIONAL_USD = float(os.getenv("FLYWHEEL_DEFAULT_COMPETING_NOTIONAL_USD", "100"))
FLYWHEEL_ESTIMATED_ACTORS_PER_ALERT = int(os.getenv("FLYWHEEL_ESTIMATED_ACTORS_PER_ALERT", "10"))
FLYWHEEL_CROWD_STATE_TTL_SEC = float(os.getenv("FLYWHEEL_CROWD_STATE_TTL_SEC", "120"))
FLYWHEEL_MIN_PROFIT_AFTER_CROWD_USD = float(os.getenv("FLYWHEEL_MIN_PROFIT_AFTER_CROWD_USD", "0.05"))
FLYWHEEL_MAX_FREE_TELEGRAM_BATCH = int(os.getenv("FLYWHEEL_MAX_FREE_TELEGRAM_BATCH", "25"))

# ── Macro Liquidity & Traditional Markets Correlation (Phase 4) ───────────────
MACRO_DATA_SOURCE = os.getenv("MACRO_DATA_SOURCE", "mixed").lower()
MACRO_POLL_INTERVAL_SECONDS = int(os.getenv("MACRO_POLL_INTERVAL_SECONDS", "300"))
MACRO_FETCH_TIMEOUT_SECONDS = int(os.getenv("MACRO_FETCH_TIMEOUT_SECONDS", "12"))
MACRO_RISK_ON_DXY_THRESHOLD = float(os.getenv("MACRO_RISK_ON_DXY_THRESHOLD", "-0.15"))
MACRO_RISK_ON_SPX_THRESHOLD = float(os.getenv("MACRO_RISK_ON_SPX_THRESHOLD", "0.15"))
MACRO_RISK_OFF_DXY_THRESHOLD = float(os.getenv("MACRO_RISK_OFF_DXY_THRESHOLD", "0.25"))
MACRO_RISK_OFF_SPX_THRESHOLD = float(os.getenv("MACRO_RISK_OFF_SPX_THRESHOLD", "-0.25"))
MACRO_VOLATILITY_BUFFER_RISK_ON = float(os.getenv("MACRO_VOLATILITY_BUFFER_RISK_ON", "3.0"))
MACRO_VOLATILITY_BUFFER_NEUTRAL = float(os.getenv("MACRO_VOLATILITY_BUFFER_NEUTRAL", "5.0"))
MACRO_VOLATILITY_BUFFER_RISK_OFF = float(os.getenv("MACRO_VOLATILITY_BUFFER_RISK_OFF", "12.0"))
MACRO_SLIPPAGE_MULTIPLIER_RISK_ON = float(os.getenv("MACRO_SLIPPAGE_MULTIPLIER_RISK_ON", "0.85"))
MACRO_SLIPPAGE_MULTIPLIER_NEUTRAL = float(os.getenv("MACRO_SLIPPAGE_MULTIPLIER_NEUTRAL", "1.0"))
MACRO_SLIPPAGE_MULTIPLIER_RISK_OFF = float(os.getenv("MACRO_SLIPPAGE_MULTIPLIER_RISK_OFF", "1.35"))
MACRO_SCORE_WEIGHT_RISK_ON = float(os.getenv("MACRO_SCORE_WEIGHT_RISK_ON", "1.08"))
MACRO_SCORE_WEIGHT_NEUTRAL = float(os.getenv("MACRO_SCORE_WEIGHT_NEUTRAL", "1.0"))
MACRO_SCORE_WEIGHT_RISK_OFF = float(os.getenv("MACRO_SCORE_WEIGHT_RISK_OFF", "0.92"))
MACRO_YAHOO_DXY_SYMBOL = os.getenv("MACRO_YAHOO_DXY_SYMBOL", "DX-Y.NYB")
MACRO_YAHOO_SPX_SYMBOL = os.getenv("MACRO_YAHOO_SPX_SYMBOL", "^GSPC")
MACRO_YAHOO_BTC_SYMBOL = os.getenv("MACRO_YAHOO_BTC_SYMBOL", "BTC-USD")
MACRO_YAHOO_GOLD_SYMBOL = os.getenv("MACRO_YAHOO_GOLD_SYMBOL", "GC=F")

# ── Oracle Data Hub (free intelligence mesh) ────────────────────────────────
ORACLE_DATA_HUB_ENABLED = os.getenv("ORACLE_DATA_HUB_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}
ORACLE_HUB_CACHE_SECONDS = int(os.getenv("ORACLE_HUB_CACHE_SECONDS", "90"))
ORACLE_HUB_FETCH_TIMEOUT_SECONDS = int(os.getenv("ORACLE_HUB_FETCH_TIMEOUT_SECONDS", "15"))
ORACLE_MACRO_VIX_SYMBOL = os.getenv("ORACLE_MACRO_VIX_SYMBOL", "^VIX")
ORACLE_MACRO_US10Y_SYMBOL = os.getenv("ORACLE_MACRO_US10Y_SYMBOL", "^TNX")
ORACLE_MACRO_NASDAQ_SYMBOL = os.getenv("ORACLE_MACRO_NASDAQ_SYMBOL", "^IXIC")
ORACLE_MACRO_OIL_SYMBOL = os.getenv("ORACLE_MACRO_OIL_SYMBOL", "CL=F")
ORACLE_GEO_NEWS_RSS_FEEDS = [
    feed.strip()
    for feed in os.getenv(
        "ORACLE_GEO_NEWS_RSS_FEEDS",
        "https://feeds.bbci.co.uk/news/world/rss.xml,"
        "https://feeds.bbci.co.uk/news/business/rss.xml,"
        "https://www.aljazeera.com/xml/rss/all.xml,"
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114,"
        "https://feeds.marketwatch.com/marketwatch/topstories/",
    ).split(",")
    if feed.strip()
]
ORACLE_FREE_LLM_CHAIN = os.getenv("ORACLE_FREE_LLM_CHAIN", "groq,gemini,openrouter,ollama")

# ── Data Ingestion Architecture (Scheduler → Lake → Oracle) ─────────────────
INGESTION_ENABLED = os.getenv("INGESTION_ENABLED", "true").lower() in {"1", "true", "yes"}
INGESTION_BOOTSTRAP_ON_START = os.getenv("INGESTION_BOOTSTRAP_ON_START", "true").lower() in {
    "1",
    "true",
    "yes",
}
INGESTION_FETCH_TIMEOUT_SECONDS = int(os.getenv("INGESTION_FETCH_TIMEOUT_SECONDS", "20"))
INGESTION_LAKE_MAX_AGE_SECONDS = int(os.getenv("INGESTION_LAKE_MAX_AGE_SECONDS", "600"))
INGESTION_LAKE_MAX_ROWS = int(os.getenv("INGESTION_LAKE_MAX_ROWS", "50000"))
INGESTION_MAINTENANCE_INTERVAL_SECONDS = int(
    os.getenv("INGESTION_MAINTENANCE_INTERVAL_SECONDS", "3600")
)
BINANCE_WS_ENABLED = os.getenv("BINANCE_WS_ENABLED", "false").lower() in {"1", "true", "yes"}
