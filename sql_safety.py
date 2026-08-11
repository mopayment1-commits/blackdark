"""SQL identifier allowlists and static query catalogs for Bandit B608 closure."""

from __future__ import annotations

import re

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Operational SQLite tables that may appear in dynamic maintenance SQL.
ALLOWED_SQLITE_TABLES: frozenset[str] = frozenset(
    {
        "pricing_logs",
        "order_books",
        "market_sentiment_logs",
        "institutional_flows",
        "oracle_predictions",
        "evaluated_opportunities",
        "funding_rates",
        "ingestion_snapshots",
    }
)

_TABLE_COUNT_SQL: dict[str, str] = {
    "pricing_logs": "SELECT COUNT(*) FROM pricing_logs",
    "order_books": "SELECT COUNT(*) FROM order_books",
    "market_sentiment_logs": "SELECT COUNT(*) FROM market_sentiment_logs",
    "institutional_flows": "SELECT COUNT(*) FROM institutional_flows",
    "oracle_predictions": "SELECT COUNT(*) FROM oracle_predictions",
    "evaluated_opportunities": "SELECT COUNT(*) FROM evaluated_opportunities",
    "funding_rates": "SELECT COUNT(*) FROM funding_rates",
    "ingestion_snapshots": "SELECT COUNT(*) FROM ingestion_snapshots",
}

_DELETE_ALL_SQL: dict[str, str] = {
    "pricing_logs": "DELETE FROM pricing_logs",
    "order_books": "DELETE FROM order_books",
}

_DELETE_BEFORE_SQL: dict[str, str] = {
    "pricing_logs": "DELETE FROM pricing_logs WHERE timestamp < ?",
    "order_books": "DELETE FROM order_books WHERE timestamp < ?",
}

PLATFORM_METRIC_INCREMENT_SQL: dict[str, str] = {
    "page_views": (
        "UPDATE platform_analytics SET page_views = page_views + 1, updated_at = ? WHERE id = 1"
    ),
    "dashboard_views": (
        "UPDATE platform_analytics SET dashboard_views = dashboard_views + 1, updated_at = ? WHERE id = 1"
    ),
    "landing_views": (
        "UPDATE platform_analytics SET landing_views = landing_views + 1, updated_at = ? WHERE id = 1"
    ),
    "voice_commands": (
        "UPDATE platform_analytics SET voice_commands = voice_commands + 1, updated_at = ? WHERE id = 1"
    ),
}

# Oracle integrity: live rows exclude synthetic historical_seed backfill.
LIVE_ORACLE_SOURCE_SQL = "(source IS NULL OR source NOT IN ('historical_seed'))"

LIVE_ORACLE_COUNT_SQL = (
    "SELECT COUNT(*) FROM oracle_predictions "
    "WHERE (source IS NULL OR source NOT IN ('historical_seed'))"
)
LIVE_ORACLE_RESOLVED_COUNT_SQL = (
    "SELECT COUNT(*) FROM oracle_predictions "
    "WHERE resolved = 1 AND (source IS NULL OR source NOT IN ('historical_seed'))"
)
LIVE_ORACLE_AVG_ACCURACY_SQL = """
SELECT AVG(accuracy_score)
FROM oracle_predictions
WHERE resolved = 1
  AND accuracy_score IS NOT NULL
  AND (source IS NULL OR source NOT IN ('historical_seed'))
"""
LIVE_ORACLE_RECENT_SQL = """
SELECT *
FROM oracle_predictions
WHERE (source IS NULL OR source NOT IN ('historical_seed'))
ORDER BY timestamp DESC, id DESC
LIMIT ?
"""
LIVE_ORACLE_LABELED_SQL = """
SELECT *
FROM oracle_predictions
WHERE resolved = 1
  AND price_after_24h IS NOT NULL
  AND label IS NOT NULL
  AND (source IS NULL OR source NOT IN ('historical_seed'))
ORDER BY timestamp ASC
LIMIT ?
"""
ALL_ORACLE_LABELED_SQL = """
SELECT *
FROM oracle_predictions
WHERE resolved = 1
  AND price_after_24h IS NOT NULL
  AND label IS NOT NULL
ORDER BY timestamp ASC
LIMIT ?
"""
LIVE_ORACLE_FEATURES_COUNT_SQL = """
SELECT COUNT(*) FROM oracle_predictions
WHERE (source IS NULL OR source NOT IN ('historical_seed'))
  AND features_json IS NOT NULL AND TRIM(features_json) != ''
"""
LIVE_ORACLE_LABELED_COUNT_SQL = """
SELECT COUNT(*) FROM oracle_predictions
WHERE (source IS NULL OR source NOT IN ('historical_seed'))
  AND resolved = 1 AND label IS NOT NULL
"""
LIVE_ORACLE_RESOLVED_ONLY_COUNT_SQL = (
    "SELECT COUNT(*) FROM oracle_predictions "
    "WHERE (source IS NULL OR source NOT IN ('historical_seed')) AND resolved = 1"
)

ORDER_BOOKS_LATEST_SQL = """
SELECT o.exchange, o.symbol, o.bids, o.asks, o.timestamp, o.market_type
FROM order_books o
INNER JOIN (
    SELECT exchange, symbol, market_type, MAX(timestamp) AS max_ts
    FROM order_books
    GROUP BY exchange, symbol, market_type
) latest
    ON o.exchange = latest.exchange
   AND o.symbol = latest.symbol
   AND o.market_type = latest.market_type
   AND o.timestamp = latest.max_ts
"""
ORDER_BOOKS_LATEST_BY_MARKET_SQL = """
SELECT o.exchange, o.symbol, o.bids, o.asks, o.timestamp, o.market_type
FROM order_books o
INNER JOIN (
    SELECT exchange, symbol, market_type, MAX(timestamp) AS max_ts
    FROM order_books
    GROUP BY exchange, symbol, market_type
) latest
    ON o.exchange = latest.exchange
   AND o.symbol = latest.symbol
   AND o.market_type = latest.market_type
   AND o.timestamp = latest.max_ts
WHERE o.market_type = ?
"""

# Fixed verdict labels for elevated-risk oracle counts (values bound as parameters).
RISK_ORACLE_VERDICTS: tuple[str, ...] = ("Do Not Touch", "CAUTION", "ELEVATED_RISK", "AVOID")
RISK_ORACLE_COUNT_SQL = """
SELECT COUNT(*)
FROM oracle_predictions
WHERE timestamp >= ?
  AND verdict IN (?, ?, ?, ?)
"""

INSTITUTIONAL_FLOW_TYPES_DEFAULT: tuple[str, ...] = (
    "manipulation_alert",
    "sector_inflow_index",
    "whale_alert",
    "sector_rotation",
)
INSTITUTIONAL_FLOW_BY_TYPE_SQL = """
SELECT *
FROM institutional_flows
WHERE flow_type IN (?, ?, ?, ?)
ORDER BY timestamp DESC, id DESC
LIMIT ?
"""

# User profile columns allowlisted for UPDATE ... SET col = ?
USER_PROFILE_UPDATE_SQL: dict[str, str] = {
    "name": "UPDATE users SET name = ? WHERE id = ?",
    "username": "UPDATE users SET username = ? WHERE id = ?",
    "telegram_chat_id": "UPDATE users SET telegram_chat_id = ? WHERE id = ?",
    "avatar_url": "UPDATE users SET avatar_url = ? WHERE id = ?",
    "ui_lang": "UPDATE users SET ui_lang = ? WHERE id = ?",
    "ux_mode_pref": "UPDATE users SET ux_mode_pref = ? WHERE id = ?",
    "timezone": "UPDATE users SET timezone = ? WHERE id = ?",
    "email_verified_at": "UPDATE users SET email_verified_at = ? WHERE id = ?",
    "password_hash": "UPDATE users SET password_hash = ? WHERE id = ?",
    "password_is_set": "UPDATE users SET password_is_set = ? WHERE id = ?",
}


def require_sql_ident(name: str) -> str:
    cleaned = str(name).strip()
    if not _IDENT_RE.fullmatch(cleaned):
        raise ValueError(f"Unsafe SQL identifier: {name!r}")
    return cleaned


def require_sqlite_table(table_name: str) -> str:
    name = require_sql_ident(table_name)
    if name not in ALLOWED_SQLITE_TABLES:
        raise ValueError(f"Table not allowlisted: {table_name!r}")
    return name


def table_count_sql(table_name: str) -> str:
    name = require_sqlite_table(table_name)
    return _TABLE_COUNT_SQL[name]


def delete_all_sql(table_name: str) -> str:
    name = require_sql_ident(table_name)
    try:
        return _DELETE_ALL_SQL[name]
    except KeyError as exc:
        raise ValueError(f"Delete-all not allowlisted for table: {table_name!r}") from exc


def delete_before_sql(table_name: str) -> str:
    name = require_sql_ident(table_name)
    try:
        return _DELETE_BEFORE_SQL[name]
    except KeyError as exc:
        raise ValueError(f"Delete-before not allowlisted for table: {table_name!r}") from exc


def platform_metric_increment_sql(metric: str) -> str:
    try:
        return PLATFORM_METRIC_INCREMENT_SQL[metric]
    except KeyError as exc:
        raise ValueError(f"Unknown metric: {metric}") from exc


def require_schema_ident(schema: str) -> str:
    return require_sql_ident(schema)
