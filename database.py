"""
BLACKDARK — Async SQLite database layer (aiosqlite).

Tables
------
pricing_logs   — real-time price feeds (spot, cross, perpetual)
order_books    — depth snapshots (JSON-serialised levels)
funding_rates  — perpetual funding snapshots
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

import aiosqlite

import config
logger = logging.getLogger(__name__)


def _row_get(row: Any, index: int, name: str) -> Any:
    """Read a column from sqlite tuples or postgres/asyncpg mappings."""
    if row is None:
        return None
    if isinstance(row, dict):
        if name in row:
            return row[name]
        lowered = name.lower()
        if lowered in row:
            return row[lowered]
    try:
        return row[name]
    except (KeyError, TypeError):
        pass
    try:
        return row[index]
    except (KeyError, IndexError, TypeError):
        values = getattr(row, "values", None)
        if callable(values):
            vals = list(values())
            return vals[index] if index < len(vals) else None
    return None


def _first_cell(row: Any) -> Any:
    """SQLite tuples use [0]; Postgres dict rows use the first mapped value."""
    if row is None:
        return None
    if isinstance(row, dict):
        return next(iter(row.values()), None)
    try:
        return row[0]
    except (KeyError, IndexError, TypeError):
        values = getattr(row, "values", None)
        if callable(values):
            extracted = list(values())
            return extracted[0] if extracted else None
        return None

SCHEMA = """
CREATE TABLE IF NOT EXISTS pricing_logs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp         TEXT    NOT NULL,
    exchange          TEXT    NOT NULL,
    symbol            TEXT    NOT NULL,
    price             REAL    NOT NULL,
    volume            REAL,
    opportunity_score REAL,
    market_type       TEXT    NOT NULL DEFAULT 'spot'
);

CREATE INDEX IF NOT EXISTS idx_pricing_exchange_symbol_ts
    ON pricing_logs (exchange, symbol, timestamp);

CREATE TABLE IF NOT EXISTS order_books (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,
    exchange    TEXT    NOT NULL,
    symbol      TEXT    NOT NULL,
    bids        TEXT    NOT NULL,
    asks        TEXT    NOT NULL,
    market_type TEXT    NOT NULL DEFAULT 'spot'
);

CREATE INDEX IF NOT EXISTS idx_orderbook_exchange_symbol_ts
    ON order_books (exchange, symbol, timestamp);

CREATE TABLE IF NOT EXISTS funding_rates (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp         TEXT    NOT NULL,
    exchange          TEXT    NOT NULL,
    symbol            TEXT    NOT NULL,
    funding_rate      REAL    NOT NULL,
    next_funding_time TEXT
);

CREATE INDEX IF NOT EXISTS idx_funding_exchange_symbol_ts
    ON funding_rates (exchange, symbol, timestamp);

CREATE TABLE IF NOT EXISTS evaluated_opportunities (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT    NOT NULL,
    kind                TEXT    NOT NULL,
    asset               TEXT    NOT NULL,
    payload_json        TEXT    NOT NULL,
    opportunity_score   REAL    NOT NULL,
    net_profit_usdt     REAL    NOT NULL,
    oracle_verdict      TEXT    NOT NULL,
    oracle_sentence     TEXT    NOT NULL,
    explanation_json    TEXT    NOT NULL,
    confidence_percent  REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evaluated_asset_ts
    ON evaluated_opportunities (asset, timestamp);

CREATE TABLE IF NOT EXISTS institutional_flows (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT    NOT NULL,
    flow_type     TEXT    NOT NULL,
    exchange      TEXT,
    symbol        TEXT,
    asset         TEXT,
    sector        TEXT,
    side          TEXT,
    price         REAL,
    quantity      REAL,
    notional_usd  REAL,
    net_flow_usd  REAL,
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_institutional_flow_type_ts
    ON institutional_flows (flow_type, timestamp);

CREATE INDEX IF NOT EXISTS idx_institutional_sector_ts
    ON institutional_flows (sector, timestamp);

CREATE TABLE IF NOT EXISTS cloud_sync_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT    NOT NULL,
    local_path    TEXT    NOT NULL,
    s3_bucket     TEXT    NOT NULL,
    s3_key        TEXT    NOT NULL,
    etag          TEXT,
    size_bytes    INTEGER,
    status        TEXT    NOT NULL,
    local_deleted INTEGER NOT NULL DEFAULT 0,
    error         TEXT
);

CREATE INDEX IF NOT EXISTS idx_cloud_sync_local_path
    ON cloud_sync_logs (local_path, timestamp);

CREATE TABLE IF NOT EXISTS market_sentiment_logs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp         TEXT    NOT NULL,
    asset             TEXT    NOT NULL,
    sector            TEXT,
    source            TEXT    NOT NULL,
    raw_text          TEXT    NOT NULL,
    sentiment_score   REAL    NOT NULL,
    compound_momentum REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sentiment_asset_ts
    ON market_sentiment_logs (asset, timestamp);

CREATE INDEX IF NOT EXISTS idx_sentiment_sector_ts
    ON market_sentiment_logs (sector, timestamp);

CREATE TABLE IF NOT EXISTS macro_market_logs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp         TEXT    NOT NULL,
    dxy_score         REAL    NOT NULL,
    spx_score         REAL    NOT NULL,
    macro_regime      TEXT    NOT NULL,
    volatility_buffer REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_macro_market_ts
    ON macro_market_logs (timestamp);

CREATE TABLE IF NOT EXISTS waitlist (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    email     TEXT    NOT NULL UNIQUE,
    name      TEXT,
    joined_at TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_waitlist_joined_at
    ON waitlist (joined_at);

CREATE TABLE IF NOT EXISTS subscriptions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL,
    tier          TEXT    NOT NULL,
    stripe_sub_id TEXT,
    status        TEXT    NOT NULL DEFAULT 'active',
    created_at    TEXT    NOT NULL,
    trial_ends_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_email
    ON subscriptions (email);

CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_sub
    ON subscriptions (stripe_sub_id);

CREATE TABLE IF NOT EXISTS billing_webhook_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    provider     TEXT    NOT NULL,
    event_id     TEXT    NOT NULL,
    event_type   TEXT,
    received_at  TEXT    NOT NULL,
    UNIQUE(provider, event_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_webhook_received
    ON billing_webhook_events (received_at);

CREATE TABLE IF NOT EXISTS institutional_inquiries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    email        TEXT    NOT NULL,
    name         TEXT,
    company      TEXT,
    message      TEXT,
    budget_usd   TEXT,
    created_at   TEXT    NOT NULL,
    status       TEXT    NOT NULL DEFAULT 'new'
);

CREATE TABLE IF NOT EXISTS oracle_predictions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT    NOT NULL,
    asset               TEXT    NOT NULL,
    price_at_prediction REAL    NOT NULL,
    verdict             TEXT    NOT NULL,
    opportunity_score   INTEGER NOT NULL,
    confidence          INTEGER NOT NULL,
    resolved            INTEGER NOT NULL DEFAULT 0,
    price_after_24h     REAL,
    price_after_1h      REAL,
    price_after_4h      REAL,
    outcome             TEXT,
    accuracy_score      REAL,
    label               TEXT,
    direction_label     TEXT,
    features_json       TEXT,
    resolved_at         TEXT,
    kind                TEXT,
    source              TEXT DEFAULT 'oracle'
);

CREATE INDEX IF NOT EXISTS idx_oracle_predictions_asset_ts
    ON oracle_predictions (asset, timestamp);

CREATE INDEX IF NOT EXISTS idx_oracle_predictions_resolved
    ON oracle_predictions (resolved, timestamp);

CREATE TABLE IF NOT EXISTS arbitrage_alert_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT    NOT NULL,
    kind         TEXT    NOT NULL,
    title        TEXT    NOT NULL,
    payload_json TEXT    NOT NULL,
    delivered    INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_arbitrage_alert_ts
    ON arbitrage_alert_log (timestamp);

CREATE TABLE IF NOT EXISTS simulation_logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT    NOT NULL,
    kind         TEXT    NOT NULL,
    asset        TEXT    NOT NULL,
    payload_json TEXT    NOT NULL,
    pnl_usd      REAL
);

CREATE INDEX IF NOT EXISTS idx_simulation_ts
    ON simulation_logs (timestamp);

CREATE TABLE IF NOT EXISTS alert_subscriptions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    email             TEXT,
    telegram_chat_id  TEXT,
    whatsapp_phone    TEXT,
    min_profit_pct    REAL    NOT NULL DEFAULT 0.05,
    oracle_alerts     INTEGER NOT NULL DEFAULT 1,
    arbitrage_alerts  INTEGER NOT NULL DEFAULT 1,
    email_alerts      INTEGER NOT NULL DEFAULT 1,
    whatsapp_alerts   INTEGER NOT NULL DEFAULT 1,
    enabled           INTEGER NOT NULL DEFAULT 1,
    created_at        TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS alert_delivery_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT    NOT NULL,
    title        TEXT    NOT NULL,
    payload_json TEXT,
    results_json TEXT
);

CREATE TABLE IF NOT EXISTS execution_state (
    id                     INTEGER PRIMARY KEY CHECK (id = 1),
    panic_active           INTEGER NOT NULL DEFAULT 0,
    auto_execution_enabled INTEGER NOT NULL DEFAULT 0,
    updated_at             TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS execution_logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT    NOT NULL,
    side         TEXT    NOT NULL,
    asset        TEXT    NOT NULL,
    payload_json TEXT    NOT NULL,
    live_mode    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS weekly_reports (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    generated_at TEXT    NOT NULL,
    narrative    TEXT    NOT NULL,
    payload_json TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_weekly_reports_ts
    ON weekly_reports (generated_at DESC);

CREATE TABLE IF NOT EXISTS maintenance_runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at   TEXT    NOT NULL,
    finished_at  TEXT,
    payload_json TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS platform_analytics (
    id                 INTEGER PRIMARY KEY CHECK (id = 1),
    page_views         INTEGER NOT NULL DEFAULT 0,
    dashboard_views    INTEGER NOT NULL DEFAULT 0,
    landing_views      INTEGER NOT NULL DEFAULT 0,
    voice_commands     INTEGER NOT NULL DEFAULT 0,
    waitlist_count     INTEGER NOT NULL DEFAULT 0,
    subscriber_count   INTEGER NOT NULL DEFAULT 0,
    updated_at         TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    name          TEXT,
    created_at    TEXT    NOT NULL,
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    token      TEXT    NOT NULL UNIQUE,
    expires_at TEXT    NOT NULL,
    created_at TEXT    NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_token
    ON user_sessions (token);

CREATE TABLE IF NOT EXISTS oracle_usage_daily (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email      TEXT    NOT NULL,
    usage_date TEXT    NOT NULL,
    count      INTEGER NOT NULL DEFAULT 0,
    UNIQUE(email, usage_date)
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email     TEXT    NOT NULL,
    timestamp      TEXT    NOT NULL,
    asset          TEXT    NOT NULL,
    action         TEXT    NOT NULL,
    notes          TEXT,
    oracle_verdict TEXT,
    entry_price    REAL,
    exit_price     REAL,
    pnl_usd        REAL,
    status         TEXT    NOT NULL DEFAULT 'open'
);

CREATE INDEX IF NOT EXISTS idx_journal_user_ts
    ON journal_entries (user_email, timestamp);

CREATE TABLE IF NOT EXISTS behavior_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type   TEXT    NOT NULL,
    user_email   TEXT,
    tier         TEXT,
    asset        TEXT,
    session_id   TEXT,
    payload_json TEXT    NOT NULL DEFAULT '{}',
    created_at   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_behavior_type_ts
    ON behavior_events (event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_behavior_user_ts
    ON behavior_events (user_email, created_at DESC);

CREATE TABLE IF NOT EXISTS audit_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    NOT NULL,
    actor           TEXT    NOT NULL,
    action          TEXT    NOT NULL,
    payload_hash    TEXT    NOT NULL,
    outcome         TEXT    NOT NULL,
    signature       TEXT    NOT NULL,
    request_method  TEXT,
    request_path    TEXT,
    metadata_json   TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_ts
    ON audit_logs (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_actor
    ON audit_logs (actor, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action
    ON audit_logs (action, timestamp DESC);

CREATE TABLE IF NOT EXISTS decisions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id     TEXT    NOT NULL,
    context         TEXT    NOT NULL,
    prediction      TEXT    NOT NULL,
    confidence      REAL    NOT NULL,
    timestamp       TEXT    NOT NULL,
    outcome         TEXT    NOT NULL DEFAULT 'pending',
    version         INTEGER NOT NULL DEFAULT 1,
    signature       TEXT    NOT NULL,
    UNIQUE(decision_id, version)
);

CREATE INDEX IF NOT EXISTS idx_decisions_id
    ON decisions (decision_id, version DESC);

CREATE INDEX IF NOT EXISTS idx_decisions_ts
    ON decisions (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_decisions_outcome
    ON decisions (outcome, timestamp DESC);

CREATE TABLE IF NOT EXISTS kg_nodes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id         TEXT    NOT NULL UNIQUE,
    node_type       TEXT    NOT NULL,
    label           TEXT,
    properties_json TEXT    NOT NULL DEFAULT '{}',
    timestamp       TEXT    NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    signature       TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_kg_nodes_type_ts
    ON kg_nodes (node_type, timestamp DESC);

CREATE TABLE IF NOT EXISTS kg_edges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    edge_id         TEXT    NOT NULL UNIQUE,
    source_node_id  TEXT    NOT NULL,
    target_node_id  TEXT    NOT NULL,
    edge_type       TEXT    NOT NULL,
    properties_json TEXT    NOT NULL DEFAULT '{}',
    timestamp       TEXT    NOT NULL,
    signature       TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_kg_edges_source
    ON kg_edges (source_node_id, edge_type);

CREATE INDEX IF NOT EXISTS idx_kg_edges_target
    ON kg_edges (target_node_id, edge_type);

CREATE TABLE IF NOT EXISTS market_signals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id       TEXT    NOT NULL,
    symbol          TEXT    NOT NULL,
    signal_type     TEXT    NOT NULL,
    value_json      TEXT    NOT NULL,
    confidence      REAL    NOT NULL,
    source          TEXT    NOT NULL,
    timestamp       TEXT    NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    payload_hash    TEXT    NOT NULL,
    signature       TEXT    NOT NULL,
    UNIQUE(signal_id, version)
);

CREATE INDEX IF NOT EXISTS idx_market_signals_symbol_ts
    ON market_signals (symbol, timestamp DESC);

CREATE TABLE IF NOT EXISTS learning_predictions (
    prediction_id       TEXT PRIMARY KEY,
    symbol                TEXT    NOT NULL,
    action                TEXT    NOT NULL,
    confidence            REAL    NOT NULL,
    timestamp             TEXT    NOT NULL,
    expiry                TEXT,
    oracle_prediction_id  INTEGER,
    context_json          TEXT    NOT NULL DEFAULT '{}',
    signature             TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS learning_outcomes (
    outcome_id        TEXT PRIMARY KEY,
    prediction_id     TEXT    NOT NULL,
    actual_result     TEXT    NOT NULL,
    accuracy_score    REAL,
    verified_at       TEXT    NOT NULL,
    counterfactual_json TEXT,
    signature         TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_learning_outcomes_pred
    ON learning_outcomes (prediction_id);

CREATE TABLE IF NOT EXISTS counterfactual_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    cf_id             TEXT    NOT NULL UNIQUE,
    prediction_id     TEXT    NOT NULL,
    scenario          TEXT    NOT NULL,
    alternate_action  TEXT    NOT NULL,
    projected_outcome TEXT    NOT NULL,
    timestamp         TEXT    NOT NULL,
    signature         TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS trust_evidence (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id     TEXT    NOT NULL UNIQUE,
    evidence_type   TEXT    NOT NULL,
    payload_json    TEXT    NOT NULL,
    payload_hash    TEXT    NOT NULL,
    timestamp       TEXT    NOT NULL,
    signature       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS proof_certificates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    certificate_id  TEXT    NOT NULL UNIQUE,
    subject         TEXT    NOT NULL,
    payload_hash    TEXT    NOT NULL,
    timestamp       TEXT    NOT NULL,
    signature       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_events (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type        TEXT    NOT NULL,
    user_id           INTEGER,
    session_id        TEXT,
    source            TEXT,
    attribution_json  TEXT    NOT NULL DEFAULT '{}',
    payload_json      TEXT    NOT NULL DEFAULT '{}',
    created_at        TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_analytics_events_type_ts
    ON analytics_events (event_type, created_at DESC);

CREATE TABLE IF NOT EXISTS ip_registry (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id          TEXT    NOT NULL UNIQUE,
    asset_type        TEXT    NOT NULL,
    title             TEXT    NOT NULL,
    description       TEXT,
    rights_json       TEXT    NOT NULL DEFAULT '{}',
    documentation_ref TEXT,
    created_at        TEXT    NOT NULL,
    updated_at        TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS corporate_dd_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id        TEXT    NOT NULL UNIQUE,
    inquiry_id      INTEGER,
    evidence_type   TEXT    NOT NULL,
    payload_json    TEXT    NOT NULL,
    created_at      TEXT    NOT NULL
);
"""


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


async def _configure_connection(db: aiosqlite.Connection) -> None:
    """Apply WAL mode and busy timeout immediately after connection setup."""
    if config.DB_WAL_MODE:
        await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute(f"PRAGMA busy_timeout={config.DB_BUSY_TIMEOUT_MS};")
    await db.execute("PRAGMA foreign_keys=ON;")


@asynccontextmanager
async def get_connection() -> AsyncIterator[Any]:
    """Yield PostgreSQL or SQLite connection depending on DATABASE_URL."""
    from postgres_backend import pg_connection, use_postgres

    if use_postgres():
        async with pg_connection() as db:
            yield db
        return

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(
        str(config.DB_PATH),
        timeout=config.DB_BUSY_TIMEOUT_MS / 1000.0,
    )
    db.row_factory = aiosqlite.Row

    try:
        await _configure_connection(db)
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("Database transaction failed; rolled back.")
        raise
    finally:
        await db.close()


async def init_db() -> None:
    """Create or connect to the database and ensure schema exists."""
    try:
        from postgres_backend import init_postgres, use_postgres

        if use_postgres():
            await init_postgres()
            async with get_connection() as db:
                await _apply_migrations(db)
            logger.info("Database initialised | engine=postgresql")
            return

        async with get_connection() as db:
            await db.executescript(SCHEMA)
            await _apply_migrations(db)
        logger.info("Database initialised at %s", config.DB_PATH)
    except Exception:
        logger.exception("Failed to initialise database")
        raise


async def _table_columns(db: Any, table: str) -> set[str]:
    """Dialect-aware column listing for SQLite and Postgres."""
    from postgres_backend import use_postgres

    if use_postgres():
        rows = await (
            await db.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = ?
                """,
                (table,),
            )
        ).fetchall()
        names: set[str] = set()
        for row in rows:
            if isinstance(row, dict):
                names.add(str(row.get("column_name") or "").lower())
            else:
                names.add(str(row[0]).lower())
        return {n for n in names if n}

    rows = await (await db.execute(f"PRAGMA table_info({table})")).fetchall()
    names = set()
    for row in rows:
        if isinstance(row, dict):
            names.add(str(row.get("name") or ""))
        else:
            names.add(str(row[1]))
    return names


async def _ensure_market_type_columns(db: Any) -> None:
    for table in ("pricing_logs", "order_books"):
        columns = await _table_columns(db, table)
        if "market_type" not in columns:
            await db.execute(
                f"ALTER TABLE {table} ADD COLUMN market_type TEXT NOT NULL DEFAULT 'spot'"
            )


async def _ensure_timestamp_indexes(db: Any) -> None:
    for table, index_name in (
        ("pricing_logs", "idx_pricing_timestamp"),
        ("order_books", "idx_orderbook_timestamp"),
        ("market_sentiment_logs", "idx_sentiment_timestamp"),
    ):
        await db.execute(
            f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} (timestamp)"
        )


async def _ensure_missing_columns(
    db: Any,
    table: str,
    columns: tuple[tuple[str, str], ...],
) -> None:
    existing = await _table_columns(db, table)
    for column, ddl in columns:
        if column not in existing:
            await db.execute(ddl)


async def _ensure_subscription_columns(db: Any) -> None:
    await _ensure_missing_columns(
        db,
        "subscriptions",
        (
            ("trial_ends_at", "ALTER TABLE subscriptions ADD COLUMN trial_ends_at TEXT"),
            ("past_due_at", "ALTER TABLE subscriptions ADD COLUMN past_due_at TEXT"),
            ("access_bonus_until", "ALTER TABLE subscriptions ADD COLUMN access_bonus_until TEXT"),
        ),
    )


async def _ensure_billing_subscription_tables(db: Any) -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS subscription_accounts (
            id                       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                  INTEGER NOT NULL UNIQUE,
            email                    TEXT    NOT NULL,
            plan                     TEXT    NOT NULL DEFAULT 'free',
            subscription_status      TEXT    NOT NULL DEFAULT 'active',
            payment_status           TEXT    NOT NULL DEFAULT 'none',
            start_date               TEXT,
            current_period_start     TEXT,
            current_period_end       TEXT,
            renewal_date             TEXT,
            cancel_at_period_end     INTEGER NOT NULL DEFAULT 0,
            auto_renew_consent_at    TEXT,
            auto_renew_enabled       INTEGER NOT NULL DEFAULT 0,
            provider                 TEXT,
            provider_subscription_id TEXT,
            provider_customer_id     TEXT,
            pending_plan             TEXT,
            entitlements_version     INTEGER NOT NULL DEFAULT 1,
            grace_period_end         TEXT,
            trial_ends_at            TEXT,
            created_at               TEXT    NOT NULL,
            updated_at               TEXT    NOT NULL
        )
        """
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_sub_accounts_email ON subscription_accounts (email)"
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sub_accounts_provider_sub
            ON subscription_accounts (provider_subscription_id)
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sub_accounts_period_end
            ON subscription_accounts (current_period_end)
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS billing_payment_events (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER,
            email               TEXT    NOT NULL,
            provider            TEXT    NOT NULL,
            provider_event_id   TEXT    NOT NULL,
            provider_invoice_id TEXT,
            event_type          TEXT    NOT NULL,
            amount_cents        INTEGER,
            currency            TEXT    NOT NULL DEFAULT 'usd',
            status              TEXT    NOT NULL,
            plan                TEXT,
            idempotency_key     TEXT    NOT NULL UNIQUE,
            raw_event_type      TEXT,
            created_at          TEXT    NOT NULL
        )
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS billing_audit_ledger (
            id                       INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp                TEXT    NOT NULL,
            actor                    TEXT    NOT NULL,
            action                   TEXT    NOT NULL,
            user_id                  INTEGER,
            email                    TEXT,
            old_plan                 TEXT,
            new_plan                 TEXT,
            old_status               TEXT,
            new_status               TEXT,
            amount_cents             INTEGER,
            currency                 TEXT,
            payment_event_id         INTEGER,
            provider_subscription_id TEXT,
            reason                   TEXT,
            entitlements_version     INTEGER,
            metadata_json            TEXT
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_billing_audit_user
            ON billing_audit_ledger (user_id, timestamp DESC)
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_meters (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            capability_key  TEXT    NOT NULL,
            period_key      TEXT    NOT NULL,
            count           INTEGER NOT NULL DEFAULT 0,
            limit_value     INTEGER,
            updated_at      TEXT    NOT NULL,
            UNIQUE(user_id, capability_key, period_key)
        )
        """
    )


async def _ensure_user_profile_columns(db: Any) -> None:
    await _ensure_missing_columns(
        db,
        "users",
        (
            ("stripe_customer_id", "ALTER TABLE users ADD COLUMN stripe_customer_id TEXT"),
            ("telegram_chat_id", "ALTER TABLE users ADD COLUMN telegram_chat_id TEXT"),
            ("mfa_enabled", "ALTER TABLE users ADD COLUMN mfa_enabled INTEGER NOT NULL DEFAULT 0"),
            ("mfa_secret_enc", "ALTER TABLE users ADD COLUMN mfa_secret_enc TEXT"),
            ("mfa_pending_secret_enc", "ALTER TABLE users ADD COLUMN mfa_pending_secret_enc TEXT"),
            ("mfa_recovery_hashes", "ALTER TABLE users ADD COLUMN mfa_recovery_hashes TEXT"),
            ("oauth_provider", "ALTER TABLE users ADD COLUMN oauth_provider TEXT"),
            ("oauth_subject", "ALTER TABLE users ADD COLUMN oauth_subject TEXT"),
            ("username", "ALTER TABLE users ADD COLUMN username TEXT"),
            ("email_verified_at", "ALTER TABLE users ADD COLUMN email_verified_at TEXT"),
            ("avatar_url", "ALTER TABLE users ADD COLUMN avatar_url TEXT"),
            ("ui_lang", "ALTER TABLE users ADD COLUMN ui_lang TEXT NOT NULL DEFAULT 'en'"),
            ("ux_mode_pref", "ALTER TABLE users ADD COLUMN ux_mode_pref TEXT NOT NULL DEFAULT 'beginner'"),
            ("timezone", "ALTER TABLE users ADD COLUMN timezone TEXT NOT NULL DEFAULT 'UTC'"),
            ("password_is_set", "ALTER TABLE users ADD COLUMN password_is_set INTEGER NOT NULL DEFAULT 1"),
        ),
    )


async def _ensure_oracle_prediction_columns(db: Any) -> None:
    await _ensure_missing_columns(
        db,
        "oracle_predictions",
        (
            ("price_after_1h", "ALTER TABLE oracle_predictions ADD COLUMN price_after_1h REAL"),
            ("price_after_4h", "ALTER TABLE oracle_predictions ADD COLUMN price_after_4h REAL"),
            ("label", "ALTER TABLE oracle_predictions ADD COLUMN label TEXT"),
            ("direction_label", "ALTER TABLE oracle_predictions ADD COLUMN direction_label TEXT"),
            ("features_json", "ALTER TABLE oracle_predictions ADD COLUMN features_json TEXT"),
            ("resolved_at", "ALTER TABLE oracle_predictions ADD COLUMN resolved_at TEXT"),
            ("kind", "ALTER TABLE oracle_predictions ADD COLUMN kind TEXT"),
            ("source", "ALTER TABLE oracle_predictions ADD COLUMN source TEXT DEFAULT 'oracle'"),
            ("market_regime", "ALTER TABLE oracle_predictions ADD COLUMN market_regime TEXT"),
        ),
    )


async def _apply_migrations(db: Any) -> None:
    """Apply lightweight schema migrations for existing databases (SQLite + Postgres)."""

    await _ensure_market_type_columns(db)
    await _ensure_timestamp_indexes(db)

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS platform_analytics (
            id                 INTEGER PRIMARY KEY CHECK (id = 1),
            page_views         INTEGER NOT NULL DEFAULT 0,
            dashboard_views    INTEGER NOT NULL DEFAULT 0,
            landing_views      INTEGER NOT NULL DEFAULT 0,
            voice_commands     INTEGER NOT NULL DEFAULT 0,
            waitlist_count     INTEGER NOT NULL DEFAULT 0,
            subscriber_count   INTEGER NOT NULL DEFAULT 0,
            updated_at         TEXT    NOT NULL
        )
        """
    )
    await db.execute(
        """
        INSERT OR IGNORE INTO platform_analytics
            (id, page_views, dashboard_views, landing_views, voice_commands,
             waitlist_count, subscriber_count, updated_at)
        VALUES (1, 0, 0, 0, 0, 0, 0, ?)
        """,
        (_utcnow_iso(),),
    )

    for ddl in (
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            name          TEXT,
            created_at    TEXT    NOT NULL,
            last_login_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            token      TEXT    NOT NULL UNIQUE,
            expires_at TEXT    NOT NULL,
            created_at TEXT    NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_user_sessions_token
            ON user_sessions (token)
        """,
        """
        CREATE TABLE IF NOT EXISTS oracle_usage_daily (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT    NOT NULL,
            usage_date TEXT    NOT NULL,
            count      INTEGER NOT NULL DEFAULT 0,
            UNIQUE(email, usage_date)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS journal_entries (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email     TEXT    NOT NULL,
            timestamp      TEXT    NOT NULL,
            asset          TEXT    NOT NULL,
            action         TEXT    NOT NULL,
            notes          TEXT,
            oracle_verdict TEXT,
            entry_price    REAL,
            exit_price     REAL,
            pnl_usd        REAL,
            status         TEXT    NOT NULL DEFAULT 'open'
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_journal_user_ts
            ON journal_entries (user_email, timestamp)
        """,
    ):
        await db.execute(ddl)

    await _ensure_subscription_columns(db)

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS billing_webhook_events (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            provider     TEXT    NOT NULL,
            event_id     TEXT    NOT NULL,
            event_type   TEXT,
            received_at  TEXT    NOT NULL,
            UNIQUE(provider, event_id)
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_billing_webhook_received
            ON billing_webhook_events (received_at)
        """
    )
    await _ensure_billing_subscription_tables(db)
    from org_tenant_store import ensure_org_tables

    await ensure_org_tables(db)
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS institutional_inquiries (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            email        TEXT    NOT NULL,
            name         TEXT,
            company      TEXT,
            message      TEXT,
            budget_usd   TEXT,
            created_at   TEXT    NOT NULL,
            status       TEXT    NOT NULL DEFAULT 'new'
        )
        """
    )


    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS auth_tokens (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            token_type  TEXT    NOT NULL,
            token_hash  TEXT    NOT NULL UNIQUE,
            expires_at  TEXT    NOT NULL,
            used_at     TEXT,
            created_at  TEXT    NOT NULL
        )
        """
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_type ON auth_tokens (user_id, token_type)"
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS oauth_states (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            provider    TEXT    NOT NULL,
            state       TEXT    NOT NULL UNIQUE,
            expires_at  TEXT    NOT NULL,
            created_at  TEXT    NOT NULL
        )
        """
    )

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS retention_grants (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT    NOT NULL,
            grant_type TEXT    NOT NULL,
            granted_at TEXT    NOT NULL,
            days       INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_retention_grants_email_type
            ON retention_grants (email, grant_type, granted_at DESC)
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS behavior_events (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type   TEXT    NOT NULL,
            user_email   TEXT,
            tier         TEXT,
            asset        TEXT,
            session_id   TEXT,
            payload_json TEXT    NOT NULL DEFAULT '{}',
            created_at   TEXT    NOT NULL
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_behavior_type_ts
            ON behavior_events (event_type, created_at DESC)
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_behavior_user_ts
            ON behavior_events (user_email, created_at DESC)
        """
    )

    await _ensure_user_profile_columns(db)
    await db.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users (username) WHERE username IS NOT NULL AND username != ''"
    )

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_snapshots (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id    TEXT    NOT NULL,
            category     TEXT    NOT NULL,
            payload_json TEXT    NOT NULL,
            fetched_at   TEXT    NOT NULL,
            status       TEXT    NOT NULL DEFAULT 'ok'
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ingestion_category_ts
            ON ingestion_snapshots (category, fetched_at DESC)
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ingestion_source_ts
            ON ingestion_snapshots (source_id, fetched_at DESC)
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_source_health (
            source_id       TEXT PRIMARY KEY,
            category        TEXT    NOT NULL,
            last_ok_at      TEXT,
            last_error_at   TEXT,
            last_error      TEXT,
            success_count   INTEGER NOT NULL DEFAULT 0,
            error_count     INTEGER NOT NULL DEFAULT 0,
            updated_at      TEXT    NOT NULL
        )
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS forecast_logs (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp           TEXT    NOT NULL,
            asset               TEXT    NOT NULL,
            horizon_hours       INTEGER NOT NULL,
            price_at            REAL    NOT NULL,
            price_forecast      REAL    NOT NULL,
            price_actual        REAL,
            direction_predicted TEXT,
            direction_actual    TEXT,
            confidence          REAL,
            model               TEXT,
            resolved            INTEGER NOT NULL DEFAULT 0,
            accuracy_score      REAL
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_forecast_asset_ts
            ON forecast_logs (asset, timestamp DESC)
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_forecast_resolved
            ON forecast_logs (resolved, timestamp)
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS weekly_reports (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            generated_at   TEXT    NOT NULL,
            narrative      TEXT    NOT NULL,
            payload_json   TEXT    NOT NULL
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_weekly_reports_ts
            ON weekly_reports (generated_at DESC)
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS maintenance_runs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at   TEXT    NOT NULL,
            finished_at  TEXT,
            payload_json TEXT    NOT NULL
        )
        """
    )

    await _ensure_oracle_prediction_columns(db)

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS ml_model_runs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at      TEXT    NOT NULL,
            finished_at     TEXT,
            model_name      TEXT    NOT NULL,
            model_version   TEXT    NOT NULL,
            samples_used    INTEGER NOT NULL DEFAULT 0,
            metrics_json    TEXT    NOT NULL,
            model_path      TEXT,
            status          TEXT    NOT NULL DEFAULT 'completed'
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ml_model_runs_started
            ON ml_model_runs (started_at DESC)
        """
    )

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS telegram_free_subscribers (
            chat_id       TEXT PRIMARY KEY,
            username      TEXT,
            subscribed_at TEXT NOT NULL,
            enabled       INTEGER NOT NULL DEFAULT 1,
            alerts_today  INTEGER NOT NULL DEFAULT 0,
            usage_date    TEXT NOT NULL
        )
        """
    )

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS user_api_keys (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER NOT NULL,
            exchange            TEXT    NOT NULL,
            api_key_encrypted   TEXT    NOT NULL,
            api_secret_encrypted TEXT   NOT NULL,
            label               TEXT,
            created_at          TEXT    NOT NULL,
            updated_at          TEXT    NOT NULL,
            UNIQUE(user_id, exchange)
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_user_api_keys_user
            ON user_api_keys (user_id)
        """
    )

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS risk_freeze_state (
            id         INTEGER PRIMARY KEY CHECK (id = 1),
            frozen     INTEGER NOT NULL DEFAULT 0,
            reason     TEXT,
            until_ts   REAL,
            updated_at TEXT    NOT NULL
        )
        """
    )
    await db.execute(
        """
        INSERT OR IGNORE INTO risk_freeze_state (id, frozen, reason, until_ts, updated_at)
        VALUES (1, 0, '', 0, ?)
        """,
        (_utcnow_iso(),),
    )

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS user_risk_settings (
            user_id              INTEGER PRIMARY KEY,
            max_slippage_bps     REAL    NOT NULL DEFAULT 80,
            max_risk_score       REAL    NOT NULL DEFAULT 70,
            max_daily_loss_usd   REAL    NOT NULL DEFAULT 500,
            updated_at           TEXT    NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT    NOT NULL,
            actor           TEXT    NOT NULL,
            action          TEXT    NOT NULL,
            payload_hash    TEXT    NOT NULL,
            outcome         TEXT    NOT NULL,
            signature       TEXT    NOT NULL,
            request_method  TEXT,
            request_path    TEXT,
            metadata_json   TEXT
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_logs_ts
            ON audit_logs (timestamp DESC)
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_logs_actor
            ON audit_logs (actor, timestamp DESC)
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_logs_action
            ON audit_logs (action, timestamp DESC)
        """
    )

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS decisions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id     TEXT    NOT NULL,
            context         TEXT    NOT NULL,
            prediction      TEXT    NOT NULL,
            confidence      REAL    NOT NULL,
            timestamp       TEXT    NOT NULL,
            outcome         TEXT    NOT NULL DEFAULT 'pending',
            version         INTEGER NOT NULL DEFAULT 1,
            signature       TEXT    NOT NULL,
            UNIQUE(decision_id, version)
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_decisions_id
            ON decisions (decision_id, version DESC)
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_decisions_ts
            ON decisions (timestamp DESC)
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_decisions_outcome
            ON decisions (outcome, timestamp DESC)
        """
    )

    await _ensure_compounding_tables(db)

    from blackdark.canonical.store import ensure_canonical_schema

    await ensure_canonical_schema(db)


async def _ensure_compounding_tables(db: Any) -> None:
    """Phases 2–7 institutional compounding tables."""
    statements = [
        """
        CREATE TABLE IF NOT EXISTS kg_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL UNIQUE,
            node_type TEXT NOT NULL,
            label TEXT,
            properties_json TEXT NOT NULL DEFAULT '{}',
            timestamp TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            signature TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_kg_nodes_type_ts ON kg_nodes (node_type, timestamp DESC)",
        """
        CREATE TABLE IF NOT EXISTS kg_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            edge_id TEXT NOT NULL UNIQUE,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            properties_json TEXT NOT NULL DEFAULT '{}',
            timestamp TEXT NOT NULL,
            signature TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_kg_edges_source ON kg_edges (source_node_id, edge_type)",
        "CREATE INDEX IF NOT EXISTS idx_kg_edges_target ON kg_edges (target_node_id, edge_type)",
        """
        CREATE TABLE IF NOT EXISTS market_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            value_json TEXT NOT NULL,
            confidence REAL NOT NULL,
            source TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            payload_hash TEXT NOT NULL,
            signature TEXT NOT NULL,
            UNIQUE(signal_id, version)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_market_signals_symbol_ts ON market_signals (symbol, timestamp DESC)",
        """
        CREATE TABLE IF NOT EXISTS learning_predictions (
            prediction_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp TEXT NOT NULL,
            expiry TEXT,
            oracle_prediction_id INTEGER,
            context_json TEXT NOT NULL DEFAULT '{}',
            signature TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_outcomes (
            outcome_id TEXT PRIMARY KEY,
            prediction_id TEXT NOT NULL,
            actual_result TEXT NOT NULL,
            accuracy_score REAL,
            verified_at TEXT NOT NULL,
            counterfactual_json TEXT,
            signature TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_learning_outcomes_pred ON learning_outcomes (prediction_id)",
        """
        CREATE TABLE IF NOT EXISTS counterfactual_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cf_id TEXT NOT NULL UNIQUE,
            prediction_id TEXT NOT NULL,
            scenario TEXT NOT NULL,
            alternate_action TEXT NOT NULL,
            projected_outcome TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            signature TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS trust_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT NOT NULL UNIQUE,
            evidence_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            signature TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS proof_certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            certificate_id TEXT NOT NULL UNIQUE,
            subject TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            signature TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id INTEGER,
            session_id TEXT,
            source TEXT,
            attribution_json TEXT NOT NULL DEFAULT '{}',
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_type_ts ON analytics_events (event_type, created_at DESC)",
        """
        CREATE TABLE IF NOT EXISTS ip_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT NOT NULL UNIQUE,
            asset_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            rights_json TEXT NOT NULL DEFAULT '{}',
            documentation_ref TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS corporate_dd_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id TEXT NOT NULL UNIQUE,
            inquiry_id INTEGER,
            evidence_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
    ]
    for stmt in statements:
        await db.execute(stmt)


def compaction_cutoff_iso(hours: int | None = None) -> str:
    age_hours = hours if hours is not None else config.COMPACTION_MIN_AGE_HOURS
    return (datetime.now(UTC) - timedelta(hours=age_hours)).isoformat()


def _parse_row_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


async def fetch_archivable_pricing_logs(
    cutoff_iso: str,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    batch_limit = limit or config.COMPACTION_SQLITE_BATCH_SIZE
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT *
                FROM pricing_logs
                WHERE timestamp < ?
                ORDER BY timestamp ASC, id ASC
                LIMIT ?
                """,
                (cutoff_iso, batch_limit),
            )
            result = await rows.fetchall()
        return [dict(row) for row in result]
    except Exception:
        logger.exception("Unable to fetch archivable pricing logs")
        return []


async def fetch_archivable_order_books(
    cutoff_iso: str,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    batch_limit = limit or config.COMPACTION_SQLITE_BATCH_SIZE
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT *
                FROM order_books
                WHERE timestamp < ?
                ORDER BY timestamp ASC, id ASC
                LIMIT ?
                """,
                (cutoff_iso, batch_limit),
            )
            result = await rows.fetchall()
        return [dict(row) for row in result]
    except Exception:
        logger.exception("Unable to fetch archivable order books")
        return []


async def fetch_archivable_sentiment_logs(
    cutoff_iso: str,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    batch_limit = limit or config.COMPACTION_SQLITE_BATCH_SIZE
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT *
                FROM market_sentiment_logs
                WHERE timestamp < ?
                ORDER BY timestamp ASC, id ASC
                LIMIT ?
                """,
                (cutoff_iso, batch_limit),
            )
            result = await rows.fetchall()
        return [dict(row) for row in result]
    except Exception:
        logger.exception("Unable to fetch archivable sentiment logs")
        return []


async def delete_pricing_logs_by_ids(row_ids: Sequence[int]) -> int:
    if not row_ids:
        return 0
    total = 0
    try:
        async with get_connection() as db:
            for i in range(0, len(row_ids), 500):
                batch = row_ids[i:i + 500]
                placeholders = ",".join("?" for _ in batch)
                cursor = await db.execute(
                    f"DELETE FROM pricing_logs WHERE id IN ({placeholders})",
                    tuple(int(item) for item in batch),
                )
                total += cursor.rowcount
        return total
    except Exception:
        logger.exception("Unable to purge archived pricing logs")
        return 0


async def delete_order_books_by_ids(row_ids: Sequence[int]) -> int:
    if not row_ids:
        return 0
    total = 0
    try:
        async with get_connection() as db:
            for i in range(0, len(row_ids), 500):
                batch = row_ids[i:i + 500]
                placeholders = ",".join("?" for _ in batch)
                cursor = await db.execute(
                    f"DELETE FROM order_books WHERE id IN ({placeholders})",
                    tuple(int(item) for item in batch),
                )
                total += cursor.rowcount
        return total
    except Exception:
        logger.exception("Unable to purge archived order books")
        return 0


async def delete_sentiment_logs_by_ids(row_ids: Sequence[int]) -> int:
    if not row_ids:
        return 0
    total = 0
    try:
        async with get_connection() as db:
            for i in range(0, len(row_ids), 500):
                batch = row_ids[i:i + 500]
                placeholders = ",".join("?" for _ in batch)
                cursor = await db.execute(
                    f"DELETE FROM market_sentiment_logs WHERE id IN ({placeholders})",
                    tuple(int(item) for item in batch),
                )
                total += cursor.rowcount
        return total
    except Exception:
        logger.exception("Unable to purge archived sentiment logs")
        return 0


async def insert_pricing_log(
    exchange: str,
    symbol: str,
    price: float,
    volume: float | None = None,
    opportunity_score: float | None = None,
    timestamp: str | None = None,
    market_type: str = "spot",
) -> int:
    """Insert one pricing log row and return its autoincrement id."""
    ts = timestamp or _utcnow_iso()
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO pricing_logs (
                timestamp, exchange, symbol, price, volume, opportunity_score, market_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (ts, exchange, symbol, price, volume, opportunity_score, market_type),
        )
        return cursor.lastrowid


async def insert_pricing_logs(
    rows: Sequence[tuple[str, str, str, float, float | None, float | None, str]],
) -> None:
    """
    Batch-insert pricing logs efficiently.

    Each row tuple is:
    (timestamp, exchange, symbol, price, volume, opportunity_score, market_type)
    """
    if not rows:
        return

    async with get_connection() as db:
        await db.executemany(
            """
            INSERT INTO pricing_logs (
                timestamp, exchange, symbol, price, volume, opportunity_score, market_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


async def insert_order_book(
    exchange: str,
    symbol: str,
    bids: Sequence[Sequence[float]],
    asks: Sequence[Sequence[float]],
    timestamp: str | None = None,
    market_type: str = "spot",
) -> int:
    """Insert one order book snapshot and return its autoincrement id."""
    ts = timestamp or _utcnow_iso()
    bids_json = json.dumps(list(bids), separators=(",", ":"))
    asks_json = json.dumps(list(asks), separators=(",", ":"))

    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO order_books (
                timestamp, exchange, symbol, bids, asks, market_type
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (ts, exchange, symbol, bids_json, asks_json, market_type),
        )
        return cursor.lastrowid


async def insert_order_books(
    rows: Sequence[tuple[str, str, str, str, str, str]],
) -> None:
    """
    Batch-insert order book snapshots efficiently.

    Each row tuple is:
    (timestamp, exchange, symbol, bids_json, asks_json, market_type)
    """
    if not rows:
        return

    async with get_connection() as db:
        await db.executemany(
            """
            INSERT INTO order_books (
                timestamp, exchange, symbol, bids, asks, market_type
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


async def insert_funding_rate(
    exchange: str,
    symbol: str,
    funding_rate: float,
    next_funding_time: str | None = None,
    timestamp: str | None = None,
) -> int:
    ts = timestamp or _utcnow_iso()
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO funding_rates (
                timestamp, exchange, symbol, funding_rate, next_funding_time
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (ts, exchange, symbol, funding_rate, next_funding_time),
        )
        return cursor.lastrowid


def _book_storage_key(symbol: str, market_type: str) -> str:
    if market_type == "perpetual":
        return f"{symbol}@perpetual"
    return symbol


async def fetch_latest_order_books(
    market_type: str | None = None,
) -> dict[str, dict[str, dict[str, Any]]]:
    """
    Return the most recent order book snapshot per exchange/symbol.

    Perpetual books are keyed as `{symbol}@perpetual` to avoid spot collisions.
    """
    books: dict[str, dict[str, dict[str, Any]]] = {}
    params: list[Any] = []
    market_filter = ""
    if market_type is not None:
        market_filter = "WHERE o.market_type = ?"
        params.append(market_type)

    query = f"""
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
        {market_filter}
    """

    async with get_connection() as db:
        rows = await db.execute(query, params)
        result = await rows.fetchall()

    for row in result:
        exchange = str(row["exchange"])
        symbol = str(row["symbol"])
        row_market_type = str(row["market_type"])
        storage_key = _book_storage_key(symbol, row_market_type)
        books.setdefault(exchange, {})[storage_key] = {
            "bids": json.loads(row["bids"]),
            "asks": json.loads(row["asks"]),
            "timestamp": str(row["timestamp"]),
            "market_type": row_market_type,
            "symbol": symbol,
        }

    return books


async def fetch_latest_funding_rates() -> dict[str, dict[str, dict[str, Any]]]:
    """
    Return the latest funding rate per exchange/symbol.

    Structure: {exchange: {symbol: {"funding_rate": float, "next_funding_time": str, "timestamp": str}}}
    """
    rates: dict[str, dict[str, dict[str, Any]]] = {}

    async with get_connection() as db:
        rows = await db.execute(
            """
            SELECT f.exchange, f.symbol, f.funding_rate, f.next_funding_time, f.timestamp
            FROM funding_rates f
            INNER JOIN (
                SELECT exchange, symbol, MAX(timestamp) AS max_ts
                FROM funding_rates
                GROUP BY exchange, symbol
            ) latest
                ON f.exchange = latest.exchange
               AND f.symbol = latest.symbol
               AND f.timestamp = latest.max_ts
            """
        )
        result = await rows.fetchall()

    for row in result:
        exchange = str(row["exchange"])
        symbol = str(row["symbol"])
        rates.setdefault(exchange, {})[symbol] = {
            "funding_rate": float(row["funding_rate"]),
            "next_funding_time": row["next_funding_time"],
            "timestamp": str(row["timestamp"]),
        }

    return rates


async def insert_evaluated_opportunity(
    kind: str,
    asset: str,
    payload_json: str,
    opportunity_score: float,
    net_profit_usdt: float,
    oracle_verdict: str,
    oracle_sentence: str,
    explanation_json: str,
    confidence_percent: float,
    timestamp: str | None = None,
) -> int:
    ts = timestamp or _utcnow_iso()
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO evaluated_opportunities (
                timestamp, kind, asset, payload_json, opportunity_score,
                net_profit_usdt, oracle_verdict, oracle_sentence,
                explanation_json, confidence_percent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                kind,
                asset,
                payload_json,
                opportunity_score,
                net_profit_usdt,
                oracle_verdict,
                oracle_sentence,
                explanation_json,
                confidence_percent,
            ),
        )
        return cursor.lastrowid


async def fetch_evaluated_opportunities(limit: int = 250) -> list[dict[str, Any]]:
    """Return recent evaluated opportunities newest-first."""
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT
                    id, timestamp, kind, asset, payload_json, opportunity_score,
                    net_profit_usdt, oracle_verdict, oracle_sentence,
                    explanation_json, confidence_percent
                FROM evaluated_opportunities
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            )
            result = await rows.fetchall()
        return [dict(row) for row in result]
    except Exception:
        logger.exception("Unable to read evaluated_opportunities; returning empty list")
        return []


async def _safe_table_count(db: aiosqlite.Connection, table_name: str) -> int:
    """Return row count for a table, or 0 if the table is unavailable."""
    try:
        row = await (await db.execute(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
        return int(row[0] or 0)
    except Exception:
        logger.debug("Unable to count rows for table=%s", str(table_name).replace("\r", " ").replace("\n", " "))
        return 0


async def fetch_system_telemetry() -> dict[str, Any]:
    """Aggregate database and pipeline health metrics for the dashboard."""
    try:
        async with get_connection() as db:
            evaluated_count = (
                await (await db.execute("SELECT COUNT(*) FROM evaluated_opportunities")).fetchone()
            )[0]
            pricing_count = (
                await (await db.execute("SELECT COUNT(*) FROM pricing_logs")).fetchone()
            )[0]
            orderbook_count = (
                await (await db.execute("SELECT COUNT(*) FROM order_books")).fetchone()
            )[0]
            funding_count = (
                await (await db.execute("SELECT COUNT(*) FROM funding_rates")).fetchone()
            )[0]
            latest_eval = (
                await (
                    await db.execute("SELECT MAX(timestamp) FROM evaluated_opportunities")
                ).fetchone()
            )[0]
            latest_pricing = (
                await (await db.execute("SELECT MAX(timestamp) FROM pricing_logs")).fetchone()
            )[0]
            institutional_flows_count = await _safe_table_count(db, "institutional_flows")
            market_sentiment_count = await _safe_table_count(db, "market_sentiment_logs")
            institutional_count = institutional_flows_count + market_sentiment_count
    except Exception:
        logger.exception("Unable to read telemetry tables; returning safe defaults")
        evaluated_count = pricing_count = orderbook_count = funding_count = 0
        institutional_count = 0
        institutional_flows_count = 0
        market_sentiment_count = 0
        latest_eval = latest_pricing = None

    db_exists = config.DB_PATH.exists()
    db_size_bytes = config.DB_PATH.stat().st_size if db_exists else 0

    return {
        "evaluated_count": int(evaluated_count or 0),
        "pricing_count": int(pricing_count or 0),
        "orderbook_count": int(orderbook_count or 0),
        "funding_count": int(funding_count or 0),
        "institutional_flow_count": int(institutional_count or 0),
        "institutional_flows_count": int(institutional_flows_count or 0),
        "market_sentiment_log_count": int(market_sentiment_count or 0),
        "latest_evaluated_at": latest_eval,
        "latest_pricing_at": latest_pricing,
        "database_path": str(config.DB_PATH),
        "database_size_bytes": db_size_bytes,
        "database_online": db_exists,
        "poll_interval_seconds": config.POLL_INTERVAL_SECONDS,
    }


async def insert_institutional_flow(
    flow_type: str,
    exchange: str | None = None,
    symbol: str | None = None,
    asset: str | None = None,
    sector: str | None = None,
    side: str | None = None,
    price: float | None = None,
    quantity: float | None = None,
    notional_usd: float | None = None,
    net_flow_usd: float | None = None,
    metadata_json: str | None = None,
    timestamp: str | None = None,
) -> int:
    ts = timestamp or _utcnow_iso()
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO institutional_flows (
                timestamp, flow_type, exchange, symbol, asset, sector, side,
                price, quantity, notional_usd, net_flow_usd, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                flow_type,
                exchange,
                symbol,
                asset,
                sector,
                side,
                price,
                quantity,
                notional_usd,
                net_flow_usd,
                metadata_json,
            ),
        )
        return cursor.lastrowid


async def insert_institutional_flows(
    rows: Sequence[tuple[Any, ...]],
) -> None:
    if not rows:
        return
    async with get_connection() as db:
        await db.executemany(
            """
            INSERT INTO institutional_flows (
                timestamp, flow_type, exchange, symbol, asset, sector, side,
                price, quantity, notional_usd, net_flow_usd, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


async def fetch_latest_whale_alerts(limit: int = 50) -> list[dict[str, Any]]:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT *
                FROM institutional_flows
                WHERE flow_type IN ('manipulation_alert', 'whale_alert')
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            )
            result = await rows.fetchall()
        return [dict(row) for row in result]
    except Exception:
        logger.exception("Unable to read manipulation alerts; returning empty list")
        return []


async def fetch_latest_sector_flows(limit: int = 20) -> list[dict[str, Any]]:
    """Return the latest sector inflow index snapshot per sector."""
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT s.*
                FROM institutional_flows s
                INNER JOIN (
                    SELECT sector, MAX(timestamp) AS max_ts
                    FROM institutional_flows
                    WHERE flow_type IN ('sector_inflow_index', 'sector_rotation')
                    GROUP BY sector
                ) latest
                    ON s.sector = latest.sector
                   AND s.timestamp = latest.max_ts
                ORDER BY s.timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            result = await rows.fetchall()
        return [dict(row) for row in result]
    except Exception:
        logger.exception("Unable to read sector inflow index; returning empty list")
        return []


async def fetch_institutional_feed_rows(
    *,
    limit: int = 250,
    flow_types: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Return recent institutional flow rows for B2B export packaging."""
    allowed = flow_types or (
        "manipulation_alert",
        "sector_inflow_index",
        "whale_alert",
        "sector_rotation",
    )
    placeholders = ", ".join("?" for _ in allowed)
    try:
        async with get_connection() as db:
            rows = await db.execute(
                f"""
                SELECT *
                FROM institutional_flows
                WHERE flow_type IN ({placeholders})
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (*allowed, limit),
            )
            result = await rows.fetchall()
        return [dict(row) for row in result]
    except Exception:
        logger.exception("Unable to read institutional feed rows")
        return []


async def fetch_institutional_flow_count() -> int:
    """Return combined institutional + sentiment log count for telemetry."""
    try:
        async with get_connection() as db:
            flows = await _safe_table_count(db, "institutional_flows")
            sentiment = await _safe_table_count(db, "market_sentiment_logs")
        return flows + sentiment
    except Exception:
        return 0


async def insert_cloud_sync_log(
    *,
    local_path: str,
    s3_bucket: str,
    s3_key: str,
    status: str,
    etag: str | None = None,
    size_bytes: int | None = None,
    local_deleted: bool = False,
    error: str | None = None,
    timestamp: str | None = None,
) -> int:
    ts = timestamp or _utcnow_iso()
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO cloud_sync_logs (
                timestamp, local_path, s3_bucket, s3_key, etag, size_bytes,
                status, local_deleted, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                local_path,
                s3_bucket,
                s3_key,
                etag,
                size_bytes,
                status,
                1 if local_deleted else 0,
                error,
            ),
        )
        return cursor.lastrowid


async def fetch_latest_cloud_sync_log(local_path: str) -> dict[str, Any] | None:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT *
                FROM cloud_sync_logs
                WHERE local_path = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT 1
                """,
                (local_path,),
            )
            row = await rows.fetchone()
        return dict(row) if row else None
    except Exception:
        logger.exception(
            "Unable to read cloud sync log for %s",
            str(local_path).replace("\r", " ").replace("\n", " "),
        )
        return None


async def insert_market_sentiment_log(
    asset: str,
    source: str,
    raw_text: str,
    sentiment_score: float,
    compound_momentum: float,
    *,
    sector: str | None = None,
    timestamp: str | None = None,
) -> int:
    ts = timestamp or _utcnow_iso()
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO market_sentiment_logs (
                timestamp, asset, sector, source, raw_text,
                sentiment_score, compound_momentum
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                asset,
                sector,
                source,
                raw_text,
                sentiment_score,
                compound_momentum,
            ),
        )
        return cursor.lastrowid


async def insert_market_sentiment_logs(
    rows: Sequence[tuple[Any, ...]],
) -> None:
    if not rows:
        return
    async with get_connection() as db:
        await db.executemany(
            """
            INSERT INTO market_sentiment_logs (
                timestamp, asset, sector, source, raw_text,
                sentiment_score, compound_momentum
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


async def fetch_sentiment_logs_for_asset(
    asset: str,
    *,
    window_seconds: int = 300,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """Return sentiment rows for an asset within the rolling window."""
    try:
        cutoff = (
            datetime.now(UTC).timestamp() - window_seconds
        )
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT *
                FROM market_sentiment_logs
                WHERE asset = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (asset, limit),
            )
            result = await rows.fetchall()

        filtered: list[dict[str, Any]] = []
        for row in result:
            item = dict(row)
            try:
                ts = datetime.fromisoformat(str(item["timestamp"]))
                if ts.timestamp() >= cutoff:
                    filtered.append(item)
            except ValueError:
                filtered.append(item)
        return filtered
    except Exception:
        logger.exception("Unable to read sentiment logs for asset=%s", str(asset).replace("\r", " ").replace("\n", " "))
        return []


async def fetch_rolling_compound_sentiment_index(
    asset: str,
    *,
    window_seconds: int = 300,
) -> float:
    """
    Compute the rolling compound sentiment index for one asset.

    Uses time-decayed averaging of sentiment_score over the window.
    Returns 0.0 when no data is available.
    """
    rows = await fetch_sentiment_logs_for_asset(
        asset,
        window_seconds=window_seconds,
    )
    if not rows:
        return 0.0

    now_ts = datetime.now(UTC).timestamp()
    weighted_sum = 0.0
    weight_total = 0.0
    for row in rows:
        try:
            ts = datetime.fromisoformat(str(row["timestamp"])).timestamp()
            age = max(0.0, now_ts - ts)
            weight = max(0.05, 1.0 - (age / max(window_seconds, 1)))
        except ValueError:
            weight = 1.0
        score = float(row.get("sentiment_score") or 0.0)
        weighted_sum += score * weight
        weight_total += weight

    if weight_total <= 0:
        return 0.0
    return round(max(-1.0, min(1.0, weighted_sum / weight_total)), 4)


async def fetch_all_rolling_compound_sentiment_indices(
    assets: Sequence[str] | None = None,
    *,
    window_seconds: int = 300,
) -> dict[str, float]:
    """Return rolling compound sentiment indices keyed by asset."""
    target_assets = list(assets or config.WHITELIST_ASSETS)
    indices: dict[str, float] = {}
    for asset in target_assets:
        indices[asset] = await fetch_rolling_compound_sentiment_index(
            asset,
            window_seconds=window_seconds,
        )
    return indices


async def insert_macro_market_log(
    dxy_score: float,
    spx_score: float,
    macro_regime: str,
    volatility_buffer: float,
    *,
    timestamp: str | None = None,
) -> int:
    ts = timestamp or _utcnow_iso()
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO macro_market_logs (
                timestamp, dxy_score, spx_score, macro_regime, volatility_buffer
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (ts, dxy_score, spx_score, macro_regime, volatility_buffer),
        )
        return cursor.lastrowid


async def fetch_latest_macro_market_log() -> dict[str, Any] | None:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT *
                FROM macro_market_logs
                ORDER BY timestamp DESC, id DESC
                LIMIT 1
                """
            )
            row = await rows.fetchone()
        return dict(row) if row else None
    except Exception:
        logger.exception("Unable to read latest macro market log")
        return None


async def insert_waitlist_signup(email: str, name: str = "") -> dict[str, Any]:
    """Register an email on the pre-launch waitlist."""
    normalized_email = email.strip().lower()
    async with get_connection() as db:
        try:
            cursor = await db.execute(
                """
                INSERT INTO waitlist (email, name, joined_at)
                VALUES (?, ?, ?)
                """,
                (normalized_email, name.strip(), _utcnow_iso()),
            )
            return {"success": True, "position": int(cursor.lastrowid or 0)}
        except aiosqlite.IntegrityError:
            return {"success": False, "duplicate": True}


async def insert_subscription(
    email: str,
    tier: str,
    stripe_sub_id: str | None,
    *,
    status: str = "active",
    trial_ends_at: str | None = None,
) -> int:
    """Persist an activated Stripe subscription or trial."""
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO subscriptions (email, tier, stripe_sub_id, status, created_at, trial_ends_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                email.strip().lower(),
                tier.strip().lower(),
                stripe_sub_id,
                status,
                _utcnow_iso(),
                trial_ends_at,
            ),
        )
        return int(cursor.lastrowid or 0)


async def insert_pro_trial(email: str, days: int | None = None) -> dict[str, Any]:
    """Grant a Pro trial to a new or returning user."""
    import config

    await init_db()
    trial_days = days if days is not None else config.PRO_TRIAL_DAYS
    ends_at = (datetime.now(UTC) + timedelta(days=trial_days)).isoformat()
    sub_id = await insert_subscription(
        email,
        "pro",
        None,
        status="trial",
        trial_ends_at=ends_at,
    )
    return {"subscription_id": sub_id, "tier": "pro", "trial_ends_at": ends_at, "days": trial_days}


async def extend_pro_trial(email: str, extra_days: int) -> dict[str, Any]:
    """Extend an active trial or start a new one."""
    email = email.strip().lower()
    sub = await fetch_active_subscription_for_email(email)
    now = datetime.now(UTC)
    if sub and sub.get("status") == "trial" and sub.get("trial_ends_at"):
        try:
            current_end = datetime.fromisoformat(str(sub["trial_ends_at"]))
            base = max(now, current_end)
        except ValueError:
            base = now
    else:
        base = now
    ends_at = (base + timedelta(days=extra_days)).isoformat()
    if sub and sub.get("status") == "trial":
        async with get_connection() as db:
            await db.execute(
                "UPDATE subscriptions SET trial_ends_at = ? WHERE id = ?",
                (ends_at, sub["id"]),
            )
        return {"tier": "pro", "trial_ends_at": ends_at, "extended": True}
    return await insert_pro_trial(email, extra_days)


async def expire_subscription(subscription_id: int) -> None:
    async with get_connection() as db:
        await db.execute(
            "UPDATE subscriptions SET status = 'expired' WHERE id = ?",
            (subscription_id,),
        )


async def insert_oracle_prediction(
    asset: str,
    price_at_prediction: float,
    verdict: str,
    opportunity_score: int,
    confidence: int,
    *,
    timestamp: str | None = None,
    kind: str | None = None,
    features_json: str | None = None,
    source: str = "oracle",
    market_regime: str | None = None,
) -> int:
    from data_moat_guard import validate_prediction_insert

    ok, reason = validate_prediction_insert(source=source, features_json=features_json)
    if not ok:
        logger.warning(
            "Oracle prediction insert blocked | asset=%s source=%s reason=%s",
            str(asset).replace("\r", " ").replace("\n", " "),
            str(source).replace("\r", " ").replace("\n", " "),
            str(reason).replace("\r", " ").replace("\n", " "),
        )
        return 0

    ts = timestamp or _utcnow_iso()
    regime = (market_regime or "neutral").strip().lower() or "neutral"
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO oracle_predictions (
                timestamp, asset, price_at_prediction, verdict,
                opportunity_score, confidence, resolved, kind, features_json, source,
                market_regime
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            (
                ts,
                asset.upper(),
                price_at_prediction,
                verdict.upper(),
                opportunity_score,
                confidence,
                kind,
                features_json,
                source,
                regime,
            ),
        )
        row_id = int(cursor.lastrowid or 0)
    if row_id:
        try:
            from oracle_track_record import on_prediction_created

            on_prediction_created(
                row_id,
                asset=asset,
                price_at_prediction=price_at_prediction,
                verdict=verdict,
                opportunity_score=opportunity_score,
                confidence=confidence,
                source=source,
                kind=kind,
            )
        except Exception:
            logger.debug("Track record append skipped on insert", exc_info=True)
    return row_id


async def fetch_unresolved_oracle_predictions(limit: int = 100) -> list[dict[str, Any]]:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT *
                FROM oracle_predictions
                WHERE resolved = 0
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (limit,),
            )
            result = await rows.fetchall()
        return [dict(row) for row in result]
    except Exception:
        logger.exception("Unable to read unresolved oracle predictions")
        return []


async def update_oracle_prediction_horizons(
    prediction_id: int,
    *,
    price_after_1h: float | None = None,
    price_after_4h: float | None = None,
) -> None:
    async with get_connection() as db:
        await db.execute(
            """
            UPDATE oracle_predictions
            SET price_after_1h = COALESCE(?, price_after_1h),
                price_after_4h = COALESCE(?, price_after_4h)
            WHERE id = ?
            """,
            (price_after_1h, price_after_4h, prediction_id),
        )


async def resolve_oracle_prediction(
    prediction_id: int,
    price_after: float,
    outcome: str,
    accuracy_score: float,
    *,
    price_after_1h: float | None = None,
    price_after_4h: float | None = None,
    label: str | None = None,
    direction_label: str | None = None,
    resolved_at: str | None = None,
) -> None:
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT asset, verdict, price_at_prediction FROM oracle_predictions WHERE id = ?",
                (prediction_id,),
            )
        ).fetchone()
        await db.execute(
            """
            UPDATE oracle_predictions
            SET resolved = 1,
                price_after_24h = ?,
                price_after_1h = COALESCE(?, price_after_1h),
                price_after_4h = COALESCE(?, price_after_4h),
                outcome = ?,
                accuracy_score = ?,
                label = COALESCE(?, label),
                direction_label = COALESCE(?, direction_label),
                resolved_at = COALESCE(?, resolved_at)
            WHERE id = ?
            """,
            (
                price_after,
                price_after_1h,
                price_after_4h,
                outcome,
                accuracy_score,
                label,
                direction_label,
                resolved_at or _utcnow_iso(),
                prediction_id,
            ),
        )
    if row:
        try:
            from oracle_track_record import on_prediction_resolved

            on_prediction_resolved(
                prediction_id,
                asset=str(row[0] or ""),
                verdict=str(row[1] or ""),
                price_at_prediction=float(row[2] or 0),
                price_after=price_after,
                outcome=outcome,
                accuracy_score=accuracy_score,
                label=label,
                direction_label=direction_label,
            )
        except Exception:
            logger.debug("Track record append skipped on resolve", exc_info=True)


def _empty_oracle_audit_stats() -> dict[str, Any]:
    return {
        "total_predictions": 0,
        "resolved_predictions": 0,
        "pending_predictions": 0,
        "average_accuracy_percent": 0.0,
        "recent": [],
        "live": {
            "total_predictions": 0,
            "resolved_predictions": 0,
            "pending_predictions": 0,
            "average_accuracy_percent": 0.0,
        },
        "synthetic": {
            "total_predictions": 0,
            "resolved_predictions": 0,
            "pending_predictions": 0,
            "average_accuracy_percent": 0.0,
        },
        "integrity": {
            "synthetic_excluded_by_default": True,
            "synthetic_source_ids": ["historical_seed"],
        },
    }


async def _fetch_audit_core_rows(
    db: Any,
    limit: int,
    live_clause: str,
    include_synthetic: bool,
) -> tuple[Any, Any, Any, Any]:
    if include_synthetic:
        total_sql = "SELECT COUNT(*) FROM oracle_predictions"
        resolved_sql = "SELECT COUNT(*) FROM oracle_predictions WHERE resolved = 1"
        avg_sql = """
            SELECT AVG(accuracy_score)
            FROM oracle_predictions
            WHERE resolved = 1 AND accuracy_score IS NOT NULL
        """
        recent_sql = """
            SELECT *
            FROM oracle_predictions
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
        """
    else:
        total_sql = f"SELECT COUNT(*) FROM oracle_predictions WHERE {live_clause}"
        resolved_sql = f"SELECT COUNT(*) FROM oracle_predictions WHERE resolved = 1 AND {live_clause}"
        avg_sql = f"""
            SELECT AVG(accuracy_score)
            FROM oracle_predictions
            WHERE resolved = 1
              AND accuracy_score IS NOT NULL
              AND {live_clause}
        """
        recent_sql = f"""
            SELECT *
            FROM oracle_predictions
            WHERE {live_clause}
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
        """
    total_row = await (await db.execute(total_sql)).fetchone()
    resolved_row = await (await db.execute(resolved_sql)).fetchone()
    avg_row = await (await db.execute(avg_sql)).fetchone()
    recent_rows = await (await db.execute(recent_sql, (limit,))).fetchall()
    return total_row, resolved_row, avg_row, recent_rows


async def _fetch_synthetic_audit_rows(db: Any) -> tuple[Any, Any, Any]:
    synth_total_row = await (
        await db.execute(
            """
            SELECT COUNT(*) FROM oracle_predictions
            WHERE source = 'historical_seed'
            """
        )
    ).fetchone()
    synth_resolved_row = await (
        await db.execute(
            """
            SELECT COUNT(*) FROM oracle_predictions
            WHERE source = 'historical_seed' AND resolved = 1
            """
        )
    ).fetchone()
    synth_avg_row = await (
        await db.execute(
            """
            SELECT AVG(accuracy_score)
            FROM oracle_predictions
            WHERE source = 'historical_seed'
              AND resolved = 1
              AND accuracy_score IS NOT NULL
            """
        )
    ).fetchone()
    return synth_total_row, synth_resolved_row, synth_avg_row


def _live_audit_average(
    recent: list[dict[str, Any]],
    include_synthetic: bool,
    live_resolved: int,
    avg_accuracy: float,
) -> float:
    if not include_synthetic:
        return avg_accuracy
    if live_resolved <= 0:
        return 0.0
    from oracle_integrity import is_synthetic_prediction

    live_rows = [row for row in recent if not is_synthetic_prediction(row)]
    live_resolved_recent = sum(1 for row in live_rows if row.get("resolved"))
    if not live_resolved_recent:
        return 0.0
    return round(
        sum(float(row.get("accuracy_score") or 0) for row in live_rows if row.get("resolved"))
        / max(live_resolved_recent, 1),
        2,
    )


def _oracle_audit_payload(
    *,
    total: int,
    resolved: int,
    avg_accuracy: float,
    recent: list[dict[str, Any]],
    synth_total: int,
    synth_resolved: int,
    synth_avg: float,
    include_synthetic: bool,
) -> dict[str, Any]:
    live_total = total if not include_synthetic else max(0, total - synth_total)
    live_resolved = resolved if not include_synthetic else max(0, resolved - synth_resolved)
    live_avg = _live_audit_average(recent, include_synthetic, live_resolved, avg_accuracy)
    live_block = {
        "total_predictions": live_total,
        "resolved_predictions": live_resolved,
        "pending_predictions": max(0, live_total - live_resolved),
        "average_accuracy_percent": round(live_avg, 2) if not include_synthetic else live_avg,
    }
    return {
        "total_predictions": live_total,
        "resolved_predictions": live_resolved,
        "pending_predictions": max(0, live_total - live_resolved),
        "average_accuracy_percent": round(live_avg, 2) if isinstance(live_avg, float) else live_avg,
        "recent": recent,
        "live": live_block,
        "synthetic": {
            "total_predictions": synth_total,
            "resolved_predictions": synth_resolved,
            "pending_predictions": max(0, synth_total - synth_resolved),
            "average_accuracy_percent": round(synth_avg, 2),
            "note": (
                "Demo/due-diligence backfill only — excluded from training and public hit rate."
            ),
        },
        "integrity": {
            "synthetic_excluded_by_default": not include_synthetic,
            "synthetic_source_ids": ["historical_seed"],
        },
    }


async def fetch_oracle_audit_stats(
    limit: int = 500,
    *,
    include_synthetic: bool = False,
) -> dict[str, Any]:
    from oracle_integrity import live_source_sql

    empty = _empty_oracle_audit_stats()
    try:
        live_clause = live_source_sql()
        async with get_connection() as db:
            total_row, resolved_row, avg_row, recent_rows = await _fetch_audit_core_rows(
                db,
                limit,
                live_clause,
                include_synthetic,
            )
            synth_total_row, synth_resolved_row, synth_avg_row = await _fetch_synthetic_audit_rows(db)

        total = int(total_row[0] or 0)
        resolved = int(resolved_row[0] or 0)
        avg_accuracy = float(avg_row[0] or 0.0)
        recent = [dict(row) for row in recent_rows]

        synth_total = int(synth_total_row[0] or 0)
        synth_resolved = int(synth_resolved_row[0] or 0)
        synth_avg = float(synth_avg_row[0] or 0.0)

        return _oracle_audit_payload(
            total=total,
            resolved=resolved,
            avg_accuracy=avg_accuracy,
            recent=recent,
            synth_total=synth_total,
            synth_resolved=synth_resolved,
            synth_avg=synth_avg,
            include_synthetic=include_synthetic,
        )
    except Exception:
        logger.exception("Unable to compute oracle audit stats")
        return empty


async def fetch_labeled_oracle_predictions(
    limit: int = 5000,
    *,
    include_synthetic: bool = False,
) -> list[dict[str, Any]]:
    from oracle_integrity import live_source_sql

    try:
        source_clause = "" if include_synthetic else f"AND {live_source_sql()}"
        async with get_connection() as db:
            rows = await (
                await db.execute(
                    f"""
                    SELECT *
                    FROM oracle_predictions
                    WHERE resolved = 1
                      AND price_after_24h IS NOT NULL
                      AND label IS NOT NULL
                      {source_clause}
                    ORDER BY timestamp ASC
                    LIMIT ?
                    """,
                    (limit,),
                )
            ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        logger.exception("Unable to fetch labeled oracle predictions")
        return []


async def insert_ml_model_run(
    *,
    model_name: str,
    model_version: str,
    samples_used: int,
    metrics_json: str,
    model_path: str | None = None,
    status: str = "completed",
    started_at: str | None = None,
    finished_at: str | None = None,
) -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO ml_model_runs (
                started_at, finished_at, model_name, model_version,
                samples_used, metrics_json, model_path, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                started_at or _utcnow_iso(),
                finished_at or _utcnow_iso(),
                model_name,
                model_version,
                samples_used,
                metrics_json,
                model_path,
                status,
            ),
        )
        return int(cursor.lastrowid or 0)


async def fetch_latest_ml_model_run(model_name: str = "oracle_direction") -> dict[str, Any] | None:
    try:
        async with get_connection() as db:
            row = await (
                await db.execute(
                    """
                    SELECT *
                    FROM ml_model_runs
                    WHERE model_name = ?
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (model_name,),
                )
            ).fetchone()
        return dict(row) if row else None
    except Exception:
        logger.exception("Unable to fetch latest ML model run")
        return None


async def insert_arbitrage_alert_log(
    kind: str,
    title: str,
    payload_json: str,
    *,
    delivered: bool = False,
) -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO arbitrage_alert_log (timestamp, kind, title, payload_json, delivered)
            VALUES (?, ?, ?, ?, ?)
            """,
            (_utcnow_iso(), kind, title, payload_json, 1 if delivered else 0),
        )
        return int(cursor.lastrowid or 0)


async def fetch_arbitrage_alert_log(limit: int = 30) -> list[dict[str, Any]]:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT id, timestamp, kind, title, payload_json, delivered
                FROM arbitrage_alert_log
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            )
            result = await rows.fetchall()
        return [dict(row) for row in result]
    except Exception:
        logger.exception("Unable to read arbitrage alert log")
        return []


async def insert_simulation_log(kind: str, asset: str, payload_json: str, pnl_usd: float) -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO simulation_logs (timestamp, kind, asset, payload_json, pnl_usd)
            VALUES (?, ?, ?, ?, ?)
            """,
            (_utcnow_iso(), kind, asset.upper(), payload_json, pnl_usd),
        )
        return int(cursor.lastrowid or 0)


async def fetch_simulation_logs(limit: int = 20) -> list[dict[str, Any]]:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT * FROM simulation_logs
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            )
            result = await rows.fetchall()
        return [dict(row) for row in result]
    except Exception:
        logger.exception("Unable to read simulation logs")
        return []


async def insert_alert_subscription(
    *,
    email: str | None,
    telegram_chat_id: str | None,
    whatsapp_phone: str | None,
    min_profit_pct: float,
    oracle_alerts: bool,
    arbitrage_alerts: bool,
) -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO alert_subscriptions (
                email, telegram_chat_id, whatsapp_phone,
                min_profit_pct, oracle_alerts, arbitrage_alerts, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email,
                telegram_chat_id,
                whatsapp_phone,
                min_profit_pct,
                1 if oracle_alerts else 0,
                1 if arbitrage_alerts else 0,
                _utcnow_iso(),
            ),
        )
        return int(cursor.lastrowid or 0)


async def fetch_active_alert_subscriptions() -> list[dict[str, Any]]:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT * FROM alert_subscriptions
                WHERE enabled = 1
                ORDER BY id DESC
                """
            )
            result = await rows.fetchall()
        return [dict(row) for row in result]
    except Exception:
        logger.exception("Unable to read alert subscriptions")
        return []


async def insert_alert_delivery_log(
    title: str,
    payload_json: str,
    results_json: str,
) -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO alert_delivery_log (timestamp, title, payload_json, results_json)
            VALUES (?, ?, ?, ?)
            """,
            (_utcnow_iso(), title, payload_json, results_json),
        )
        return int(cursor.lastrowid or 0)


async def fetch_execution_state() -> dict[str, Any]:
    try:
        async with get_connection() as db:
            row = await (
                await db.execute("SELECT * FROM execution_state WHERE id = 1")
            ).fetchone()
            if row is None:
                ts = _utcnow_iso()
                await db.execute(
                    """
                    INSERT OR IGNORE INTO execution_state (id, panic_active, auto_execution_enabled, updated_at)
                    VALUES (1, 0, 0, ?)
                    """,
                    (ts,),
                )
                row = await (
                    await db.execute("SELECT * FROM execution_state WHERE id = 1")
                ).fetchone()
        return dict(row) if row else {"panic_active": 0, "auto_execution_enabled": 0}
    except Exception:
        logger.exception("Unable to read execution state")
        return {"panic_active": 0, "auto_execution_enabled": 0}


async def set_execution_state(
    *,
    panic_active: bool | None = None,
    auto_execution_enabled: bool | None = None,
) -> None:
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT panic_active, auto_execution_enabled FROM execution_state WHERE id = 1"
            )
        ).fetchone()
        if row is None:
            panic = int(bool(panic_active))
            auto_exec = int(bool(auto_execution_enabled))
        else:
            panic = int(
                panic_active if panic_active is not None else bool(row["panic_active"])
            )
            auto_exec = int(
                auto_execution_enabled
                if auto_execution_enabled is not None
                else bool(row["auto_execution_enabled"])
            )
        await db.execute(
            """
            INSERT INTO execution_state (id, panic_active, auto_execution_enabled, updated_at)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                panic_active = excluded.panic_active,
                auto_execution_enabled = excluded.auto_execution_enabled,
                updated_at = excluded.updated_at
            """,
            (panic, auto_exec, _utcnow_iso()),
        )


async def fetch_risk_freeze_state() -> dict[str, Any]:
    try:
        async with get_connection() as db:
            row = await (
                await db.execute("SELECT * FROM risk_freeze_state WHERE id = 1")
            ).fetchone()
        return dict(row) if row else {"frozen": 0, "reason": "", "until_ts": 0.0}
    except Exception:
        logger.exception("Unable to read risk freeze state")
        return {"frozen": 0, "reason": "", "until_ts": 0.0}


async def set_risk_freeze_state(
    *,
    frozen: bool,
    reason: str = "",
    until_ts: float = 0.0,
) -> None:
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO risk_freeze_state (id, frozen, reason, until_ts, updated_at)
            VALUES (1, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                frozen = excluded.frozen,
                reason = excluded.reason,
                until_ts = excluded.until_ts,
                updated_at = excluded.updated_at
            """,
            (int(frozen), reason, float(until_ts), _utcnow_iso()),
        )


async def fetch_user_risk_settings(user_id: int) -> dict[str, Any]:
    defaults = {
        "user_id": user_id,
        "max_slippage_bps": float(os.getenv("RISK_MAX_SLIPPAGE_BPS", "80")),
        "max_risk_score": float(os.getenv("USER_DEFAULT_MAX_RISK_SCORE", "70")),
        "max_daily_loss_usd": float(os.getenv("USER_DEFAULT_MAX_DAILY_LOSS_USD", "500")),
    }
    try:
        async with get_connection() as db:
            row = await (
                await db.execute(
                    "SELECT * FROM user_risk_settings WHERE user_id = ?",
                    (user_id,),
                )
            ).fetchone()
        if row:
            return dict(row)
    except Exception:
        logger.exception(
            "Unable to read user risk settings | user_id=%s",
            str(user_id).replace("\r", " ").replace("\n", " "),
        )
    return defaults


async def upsert_user_risk_settings(
    user_id: int,
    *,
    max_slippage_bps: float | None = None,
    max_risk_score: float | None = None,
    max_daily_loss_usd: float | None = None,
) -> dict[str, Any]:
    current = await fetch_user_risk_settings(user_id)
    payload = {
        "max_slippage_bps": max_slippage_bps if max_slippage_bps is not None else current["max_slippage_bps"],
        "max_risk_score": max_risk_score if max_risk_score is not None else current["max_risk_score"],
        "max_daily_loss_usd": max_daily_loss_usd if max_daily_loss_usd is not None else current["max_daily_loss_usd"],
    }
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO user_risk_settings
                (user_id, max_slippage_bps, max_risk_score, max_daily_loss_usd, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                max_slippage_bps = excluded.max_slippage_bps,
                max_risk_score = excluded.max_risk_score,
                max_daily_loss_usd = excluded.max_daily_loss_usd,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                payload["max_slippage_bps"],
                payload["max_risk_score"],
                payload["max_daily_loss_usd"],
                _utcnow_iso(),
            ),
        )
    return {"user_id": user_id, **payload}


async def insert_execution_log(side: str, asset: str, payload_json: str, *, live: bool) -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO execution_logs (timestamp, side, asset, payload_json, live_mode)
            VALUES (?, ?, ?, ?, ?)
            """,
            (_utcnow_iso(), side, asset.upper(), payload_json, 1 if live else 0),
        )
        return int(cursor.lastrowid or 0)


async def fetch_execution_logs(limit: int = 20) -> list[dict[str, Any]]:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT * FROM execution_logs
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            )
            result = await rows.fetchall()
        return [dict(row) for row in result]
    except Exception:
        logger.exception("Unable to read execution logs")
        return []


async def db_count_waitlist() -> int:
    try:
        async with get_connection() as db:
            rows = await db.execute("SELECT COUNT(*) AS c FROM waitlist")
            row = await rows.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


async def db_count_subscribers() -> int:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                "SELECT COUNT(*) AS c FROM subscriptions WHERE status = 'active'"
            )
            row = await rows.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


async def fetch_platform_analytics() -> dict[str, Any]:
    try:
        async with get_connection() as db:
            rows = await db.execute("SELECT * FROM platform_analytics WHERE id = 1")
            result = await rows.fetchone()
        if not result:
            return {
                "page_views": 0,
                "dashboard_views": 0,
                "landing_views": 0,
                "voice_commands": 0,
                "waitlist_count": 0,
                "subscriber_count": 0,
            }
        data = dict(result)
        data["waitlist_count"] = await db_count_waitlist()
        data["subscriber_count"] = await db_count_subscribers()
        return data
    except Exception:
        logger.exception("Unable to read platform analytics")
        return {}


async def increment_platform_metric(metric: str) -> dict[str, Any]:
    allowed = {"page_views", "dashboard_views", "landing_views", "voice_commands"}
    if metric not in allowed:
        raise ValueError(f"Unknown metric: {metric}")
    try:
        async with get_connection() as db:
            await db.execute(
                f"""
                UPDATE platform_analytics
                SET {metric} = {metric} + 1, updated_at = ?
                WHERE id = 1
                """,
                (_utcnow_iso(),),
            )
        return await fetch_platform_analytics()
    except Exception:
        logger.exception(
            "Unable to increment platform metric | metric=%s",
            str(metric).replace("\r", " ").replace("\n", " "),
        )
        return {}


async def fetch_user_count() -> int:
    try:
        async with get_connection() as db:
            row = await (await db.execute("SELECT COUNT(*) FROM users")).fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


async def insert_behavior_event(
    event_type: str,
    *,
    user_email: str | None = None,
    tier: str | None = None,
    asset: str | None = None,
    session_id: str | None = None,
    payload_json: str = "{}",
) -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO behavior_events (
                event_type, user_email, tier, asset, session_id, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_type.strip().lower(),
                (user_email or "").strip().lower() or None,
                tier,
                asset.upper() if asset else None,
                session_id,
                payload_json or "{}",
                _utcnow_iso(),
            ),
        )
        return int(cursor.lastrowid or 0)


async def fetch_behavior_event_stats(*, days: int = 30) -> dict[str, Any]:
    since = (datetime.now(UTC) - timedelta(days=days)).isoformat()
    empty = {
        "window_days": days,
        "total_events": 0,
        "unique_emails": 0,
        "unique_anonymous_sessions": 0,
        "unique_actor_count": 0,
        "top_event_types": [],
    }
    try:
        async with get_connection() as db:
            total_row = await (
                await db.execute(
                    "SELECT COUNT(*) FROM behavior_events WHERE created_at >= ?",
                    (since,),
                )
            ).fetchone()
            email_row = await (
                await db.execute(
                    """
                    SELECT COUNT(DISTINCT user_email) FROM behavior_events
                    WHERE created_at >= ? AND user_email IS NOT NULL AND user_email != ''
                    """,
                    (since,),
                )
            ).fetchone()
            session_row = await (
                await db.execute(
                    """
                    SELECT COUNT(DISTINCT session_id) FROM behavior_events
                    WHERE created_at >= ? AND session_id IS NOT NULL AND session_id != ''
                    """,
                    (since,),
                )
            ).fetchone()
            type_rows = await (
                await db.execute(
                    """
                    SELECT event_type, COUNT(*) AS c
                    FROM behavior_events
                    WHERE created_at >= ?
                    GROUP BY event_type
                    ORDER BY c DESC
                    LIMIT 12
                    """,
                    (since,),
                )
            ).fetchall()

        unique_emails = int(email_row[0]) if email_row else 0
        unique_sessions = int(session_row[0]) if session_row else 0
        return {
            "window_days": days,
            "total_events": int(total_row[0]) if total_row else 0,
            "unique_emails": unique_emails,
            "unique_anonymous_sessions": unique_sessions,
            "unique_actor_count": unique_emails + unique_sessions,
            "top_event_types": [{"event_type": r[0], "count": int(r[1])} for r in type_rows],
        }
    except Exception:
        logger.exception("Unable to read behavior event stats")
        return empty


async def insert_journal_entry(
    user_email: str,
    asset: str,
    action: str,
    *,
    notes: str = "",
    oracle_verdict: str = "",
    entry_price: float | None = None,
) -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO journal_entries
                (user_email, timestamp, asset, action, notes, oracle_verdict, entry_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'open')
            """,
            (
                user_email.strip().lower(),
                _utcnow_iso(),
                asset.upper(),
                action.lower(),
                notes or None,
                oracle_verdict or None,
                entry_price,
            ),
        )
        return int(cursor.lastrowid or 0)


async def fetch_journal_entries(user_email: str, limit: int = 50) -> list[dict[str, Any]]:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT * FROM journal_entries
                WHERE user_email = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (user_email.strip().lower(), limit),
            )
            result = await rows.fetchall()
        return [dict(r) for r in result]
    except Exception:
        logger.exception("Unable to read journal entries")
        return []


async def update_journal_entry(
    entry_id: int,
    user_email: str,
    *,
    exit_price: float | None = None,
    pnl_usd: float | None = None,
    notes: str | None = None,
    status: str = "closed",
) -> bool:
    async with get_connection() as db:
        cursor = await db.execute(
            """
            UPDATE journal_entries
            SET exit_price = COALESCE(?, exit_price),
                pnl_usd = COALESCE(?, pnl_usd),
                notes = COALESCE(?, notes),
                status = ?
            WHERE id = ? AND user_email = ?
            """,
            (exit_price, pnl_usd, notes, status, entry_id, user_email.strip().lower()),
        )
        return cursor.rowcount > 0


async def delete_journal_entry(entry_id: int, user_email: str) -> bool:
    async with get_connection() as db:
        cursor = await db.execute(
            "DELETE FROM journal_entries WHERE id = ? AND user_email = ?",
            (entry_id, user_email.strip().lower()),
        )
        return cursor.rowcount > 0


async def activate_paid_subscription(
    email: str,
    tier: str,
    stripe_sub_id: str,
    *,
    stripe_customer_id: str | None = None,
) -> int:
    """Activate Stripe subscription — expires trials and prior active rows."""
    email = email.strip().lower()
    async with get_connection() as db:
        await db.execute(
            """
            UPDATE subscriptions
            SET status = 'expired'
            WHERE email = ? AND status IN ('trial', 'active', 'past_due')
            """,
            (email,),
        )
        cursor = await db.execute(
            """
            INSERT INTO subscriptions (email, tier, stripe_sub_id, status, created_at, trial_ends_at)
            VALUES (?, ?, ?, 'active', ?, NULL)
            """,
            (email, tier.strip().lower(), stripe_sub_id, _utcnow_iso()),
        )
        if stripe_customer_id:
            await db.execute(
                "UPDATE users SET stripe_customer_id = ? WHERE email = ?",
                (stripe_customer_id, email),
            )
        return int(cursor.lastrowid or 0)


async def upsert_subscription_by_stripe_id(
    stripe_sub_id: str,
    *,
    tier: str | None = None,
    status: str | None = None,
    email: str | None = None,
) -> None:
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT id FROM subscriptions WHERE stripe_sub_id = ? ORDER BY id DESC LIMIT 1",
                (stripe_sub_id,),
            )
        ).fetchone()
        if row:
            updates: list[str] = []
            params: list[Any] = []
            if tier is not None:
                updates.append("tier = ?")
                params.append(tier.strip().lower())
            if status is not None:
                updates.append("status = ?")
                params.append(status)
                if status == "past_due":
                    updates.append("past_due_at = COALESCE(past_due_at, ?)")
                    params.append(_utcnow_iso())
                elif status == "active":
                    updates.append("past_due_at = NULL")
            if updates:
                params.append(int(row[0]))
                await db.execute(
                    f"UPDATE subscriptions SET {', '.join(updates)} WHERE id = ?",
                    params,
                )
            return
        if email and tier and status:
            await db.execute(
                """
                INSERT INTO subscriptions (email, tier, stripe_sub_id, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (email.strip().lower(), tier.strip().lower(), stripe_sub_id, status, _utcnow_iso()),
            )


async def cancel_subscription_by_stripe_id(stripe_sub_id: str) -> None:
    async with get_connection() as db:
        await db.execute(
            "UPDATE subscriptions SET status = 'expired' WHERE stripe_sub_id = ?",
            (stripe_sub_id,),
        )


async def claim_billing_webhook_event(
    *,
    provider: str,
    event_id: str,
    event_type: str | None = None,
) -> bool:
    """Return True if this event is new (claimed); False if duplicate."""
    provider = (provider or "").strip().lower()
    event_id = (event_id or "").strip()
    if not provider or not event_id:
        return True
    async with get_connection() as db:
        try:
            await db.execute(
                """
                INSERT INTO billing_webhook_events (provider, event_id, event_type, received_at)
                VALUES (?, ?, ?, ?)
                """,
                (provider, event_id, (event_type or "")[:120], _utcnow_iso()),
            )
            return True
        except Exception:
            # Unique violation → already processed
            return False


async def insert_institutional_inquiry(
    *,
    email: str,
    name: str = "",
    company: str = "",
    message: str = "",
    budget_usd: str = "",
) -> int:
    email = email.strip().lower()
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO institutional_inquiries
                (email, name, company, message, budget_usd, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, 'new')
            """,
            (
                email,
                (name or "")[:120],
                (company or "")[:160],
                (message or "")[:4000],
                (budget_usd or "")[:40],
                _utcnow_iso(),
            ),
        )
        return int(cursor.lastrowid or 0)


async def update_user_telegram_chat_id(email: str, telegram_chat_id: str | None) -> None:
    async with get_connection() as db:
        await db.execute(
            "UPDATE users SET telegram_chat_id = ? WHERE email = ?",
            (telegram_chat_id.strip() if telegram_chat_id else None, email.strip().lower()),
        )


async def fetch_user_stripe_customer_id(email: str) -> str | None:
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT stripe_customer_id FROM users WHERE email = ?",
                (email.strip().lower(),),
            )
        ).fetchone()
    if row and row[0]:
        return str(row[0])
    return None


async def fetch_user_profile(email: str) -> dict[str, Any] | None:
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT id, email, name, username, created_at, last_login_at,
                       stripe_customer_id, telegram_chat_id,
                       email_verified_at, avatar_url, ui_lang, ux_mode_pref,
                       timezone, password_is_set, oauth_provider, mfa_enabled
                FROM users WHERE email = ?
                """,
                (email.strip().lower(),),
            )
        ).fetchone()
    return dict(row) if row else None


async def fetch_users_with_telegram() -> list[dict[str, Any]]:
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT email, telegram_chat_id
                FROM users
                WHERE telegram_chat_id IS NOT NULL AND telegram_chat_id != ''
                """
            )
        ).fetchall()
    return [dict(row) for row in rows]


async def upsert_telegram_free_subscriber(
    chat_id: str,
    *,
    username: str | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO telegram_free_subscribers (
                chat_id, username, subscribed_at, enabled, alerts_today, usage_date
            ) VALUES (?, ?, ?, ?, 0, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                username = excluded.username,
                enabled = excluded.enabled,
                subscribed_at = COALESCE(telegram_free_subscribers.subscribed_at, excluded.subscribed_at)
            """,
            (chat_id, username, _utcnow_iso(), 1 if enabled else 0, today),
        )
        row = await (
            await db.execute(
                "SELECT * FROM telegram_free_subscribers WHERE chat_id = ?",
                (chat_id,),
            )
        ).fetchone()
    return dict(row) if row else {"chat_id": chat_id}


async def set_telegram_free_subscriber_enabled(chat_id: str, *, enabled: bool) -> None:
    async with get_connection() as db:
        await db.execute(
            "UPDATE telegram_free_subscribers SET enabled = ? WHERE chat_id = ?",
            (1 if enabled else 0, chat_id),
        )


async def fetch_telegram_free_subscriber(chat_id: str) -> dict[str, Any] | None:
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT * FROM telegram_free_subscribers WHERE chat_id = ?",
                (chat_id,),
            )
        ).fetchone()
    return dict(row) if row else None


async def fetch_enabled_telegram_free_subscribers() -> list[dict[str, Any]]:
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT * FROM telegram_free_subscribers
                WHERE enabled = 1
                ORDER BY subscribed_at DESC
                """
            )
        ).fetchall()
    return [dict(row) for row in rows]


async def increment_telegram_free_alert_usage(
    chat_id: str,
    usage_date: str,
    daily_limit: int,
) -> None:
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT alerts_today, usage_date FROM telegram_free_subscribers WHERE chat_id = ?",
                (chat_id,),
            )
        ).fetchone()
        if not row:
            return
        current_date = str(row["usage_date"] or "")
        count = int(row["alerts_today"] or 0)
        if current_date != usage_date:
            count = 0
        count = min(daily_limit, count + 1)
        await db.execute(
            """
            UPDATE telegram_free_subscribers
            SET alerts_today = ?, usage_date = ?
            WHERE chat_id = ?
            """,
            (count, usage_date, chat_id),
        )


async def count_telegram_free_subscribers() -> int:
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT COUNT(*) FROM telegram_free_subscribers WHERE enabled = 1"
            )
        ).fetchone()
    return int(_first_cell(row) or 0)


async def fetch_platform_user_stats() -> dict[str, Any]:
    async with get_connection() as db:
        users_row = await (await db.execute("SELECT COUNT(*) FROM users")).fetchone()
        subs_row = await (
            await db.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")
        ).fetchone()
        trial_row = await (
            await db.execute(
                """
                SELECT COUNT(*) FROM subscriptions
                WHERE status = 'trial' AND (trial_ends_at IS NULL OR trial_ends_at > ?)
                """,
                (_utcnow_iso(),),
            )
        ).fetchone()
        alert_row = await (
            await db.execute("SELECT COUNT(*) FROM alert_subscriptions WHERE enabled = 1")
        ).fetchone()
    return {
        "registered_users": int(_first_cell(users_row) or 0),
        "paid_subscribers": int(_first_cell(subs_row) or 0),
        "active_trials": int(_first_cell(trial_row) or 0),
        "alert_subscribers": int(_first_cell(alert_row) or 0),
    }


async def fetch_active_subscription_for_email(email: str) -> dict[str, Any] | None:
    try:
        from billing.subscription_engine import effective_plan, entitlement_allowed
        from billing.subscription_store import ensure_subscription_account, get_by_email

        email = email.strip().lower()
        user = await fetch_user_by_email(email)
        if user:
            sub_acc = await ensure_subscription_account(int(user["id"]), email)
            if entitlement_allowed(sub_acc) and effective_plan(sub_acc) != "free":
                plan = effective_plan(sub_acc)
                return {
                    "id": sub_acc["id"],
                    "email": email,
                    "tier": plan,
                    "plan": plan,
                    "status": sub_acc["subscription_status"],
                    "subscription_status": sub_acc["subscription_status"],
                    "payment_status": sub_acc["payment_status"],
                    "current_period_start": sub_acc.get("current_period_start"),
                    "current_period_end": sub_acc.get("current_period_end"),
                    "renewal_date": sub_acc.get("renewal_date"),
                    "cancel_at_period_end": sub_acc.get("cancel_at_period_end"),
                    "auto_renew_enabled": sub_acc.get("auto_renew_enabled"),
                    "trial_ends_at": sub_acc.get("trial_ends_at"),
                    "entitlements_version": sub_acc.get("entitlements_version"),
                    "provider": sub_acc.get("provider"),
                    "stripe_sub_id": sub_acc.get("provider_subscription_id"),
                    "grace_period_end": sub_acc.get("grace_period_end"),
                }
            sub_acc_only = await get_by_email(email)
            if sub_acc_only and sub_acc_only.get("subscription_status") == "trialing":
                plan = effective_plan(sub_acc_only)
                return {
                    "id": sub_acc_only["id"],
                    "email": email,
                    "tier": plan,
                    "plan": plan,
                    "status": "trial",
                    "subscription_status": "trialing",
                    "trial_ends_at": sub_acc_only.get("trial_ends_at"),
                }

        import config

        now_dt = datetime.now(UTC)
        now = now_dt.isoformat()
        grace_days = int(getattr(config, "RETENTION_PAST_DUE_GRACE_DAYS", 7))
        # Dialect-safe grace floor: past_due_at + grace_days > now
        # ⇔ past_due_at > now - grace_days (no SQLite datetime() — breaks Postgres).
        past_due_grace_floor = (now_dt - timedelta(days=grace_days)).isoformat()
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT * FROM subscriptions
                WHERE email = ?
                  AND (
                    status = 'active'
                    OR (status = 'trial' AND (trial_ends_at IS NULL OR trial_ends_at > ?))
                    OR (
                      status = 'past_due'
                      AND past_due_at IS NOT NULL
                      AND past_due_at > ?
                    )
                    OR (access_bonus_until IS NOT NULL AND access_bonus_until > ?)
                  )
                ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'past_due' THEN 1 ELSE 2 END, id DESC
                LIMIT 1
                """,
                (email.strip().lower(), now, past_due_grace_floor, now),
            )
            result = await rows.fetchone()
        if result is None:
            return None
        row = dict(result)
        if row.get("status") == "trial" and row.get("trial_ends_at") and row["trial_ends_at"] <= now:
            await expire_subscription(int(row["id"]))
            return None
        if row.get("status") == "past_due" and row.get("past_due_at"):
            try:
                past_due_at = datetime.fromisoformat(str(row["past_due_at"]))
                if now_dt > past_due_at + timedelta(days=grace_days):
                    await expire_subscription(int(row["id"]))
                    return None
            except ValueError:
                pass
        row["past_due_grace_days"] = grace_days
        return row
    except Exception:
        logger.exception("Unable to fetch subscription for email")
        return None




async def insert_auth_token(
    *,
    user_id: int,
    token_type: str,
    token_hash: str,
    expires_at: str,
) -> None:
    async with get_connection() as db:
        # Invalidate prior unused tokens of same type for this user
        await db.execute(
            """
            UPDATE auth_tokens SET used_at = ?
            WHERE user_id = ? AND token_type = ? AND used_at IS NULL
            """,
            (_utcnow_iso(), int(user_id), token_type),
        )
        await db.execute(
            """
            INSERT INTO auth_tokens (user_id, token_type, token_hash, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (int(user_id), token_type, token_hash, expires_at, _utcnow_iso()),
        )


async def consume_auth_token_row(token_hash: str, token_type: str) -> int | None:
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT id, user_id, expires_at, used_at
                FROM auth_tokens
                WHERE token_hash = ? AND token_type = ?
                ORDER BY id DESC LIMIT 1
                """,
                (token_hash, token_type),
            )
        ).fetchone()
        if not row:
            return None
        data = dict(row)
        if data.get("used_at"):
            return None
        try:
            exp = datetime.fromisoformat(str(data["expires_at"]))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=UTC)
            if datetime.now(UTC) > exp:
                return None
        except Exception:
            return None
        await db.execute(
            "UPDATE auth_tokens SET used_at = ? WHERE id = ?",
            (_utcnow_iso(), int(data["id"])),
        )
        return int(data["user_id"])


async def insert_oauth_state(*, provider: str, state: str, expires_at: str) -> None:
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO oauth_states (provider, state, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (provider.strip().lower(), state, expires_at, _utcnow_iso()),
        )


async def consume_oauth_state(*, provider: str, state: str) -> bool:
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT id, expires_at FROM oauth_states
                WHERE provider = ? AND state = ?
                ORDER BY id DESC LIMIT 1
                """,
                (provider.strip().lower(), state),
            )
        ).fetchone()
        if not row:
            return False
        data = dict(row)
        try:
            exp = datetime.fromisoformat(str(data["expires_at"]))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=UTC)
            if datetime.now(UTC) > exp:
                await db.execute("DELETE FROM oauth_states WHERE id = ?", (int(data["id"]),))
                return False
        except Exception:
            return False
        await db.execute("DELETE FROM oauth_states WHERE id = ?", (int(data["id"]),))
        return True


async def update_user_profile_fields(user_id: int, fields: dict[str, Any]) -> None:
    allowed = {
        "name",
        "username",
        "telegram_chat_id",
        "avatar_url",
        "ui_lang",
        "ux_mode_pref",
        "timezone",
        "email_verified_at",
        "password_hash",
        "password_is_set",
    }
    updates = []
    params: list[Any] = []
    for key, value in fields.items():
        if key not in allowed:
            continue
        updates.append(f"{key} = ?")
        params.append(value)
    if not updates:
        return
    params.append(int(user_id))
    async with get_connection() as db:
        await db.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
            params,
        )


async def fetch_user_by_username(username: str) -> dict[str, Any] | None:
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT * FROM users WHERE username = ?",
                (username.strip().lower(),),
            )
        ).fetchone()
    return dict(row) if row else None


async def fetch_user_by_id(user_id: int) -> dict[str, Any] | None:
    async with get_connection() as db:
        row = await (
            await db.execute("SELECT * FROM users WHERE id = ?", (int(user_id),))
        ).fetchone()
    return dict(row) if row else None


async def mark_email_verified(user_id: int) -> None:
    async with get_connection() as db:
        await db.execute(
            "UPDATE users SET email_verified_at = COALESCE(email_verified_at, ?) WHERE id = ?",
            (_utcnow_iso(), int(user_id)),
        )


async def create_user(email: str, password_hash: str, name: str = "") -> int:
    try:
        async with get_connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO users (
                    email, password_hash, name, created_at, password_is_set
                )
                VALUES (?, ?, ?, ?, 1)
                """,
                (email.strip().lower(), password_hash, name or None, _utcnow_iso()),
            )
            return int(cursor.lastrowid or 0)
    except Exception as exc:
        kind = type(exc).__name__
        msg = str(exc).lower()
        if "integrity" in kind.lower() or "unique" in kind.lower() or "unique" in msg:
            raise ValueError("Email already registered") from exc
        raise


async def fetch_user_by_email(email: str) -> dict[str, Any] | None:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                "SELECT * FROM users WHERE email = ?",
                (email.strip().lower(),),
            )
            result = await rows.fetchone()
        return dict(result) if result else None
    except Exception:
        logger.exception("Unable to fetch user")
        return None


async def erase_user_personal_data(email: str) -> dict[str, Any]:
    """GDPR Art. 17 — delete user account and linked personal rows."""
    normalized = email.strip().lower()
    user = await fetch_user_by_email(normalized)
    if not user:
        return {"found": False, "rows_deleted": 0}

    user_id = int(user["id"])
    deleted = 0
    try:
        async with get_connection() as db:
            for stmt, params in (
                ("DELETE FROM journal_entries WHERE user_email = ?", (normalized,)),
                ("DELETE FROM oracle_usage_daily WHERE email = ?", (normalized,)),
                ("DELETE FROM user_sessions WHERE user_id = ?", (user_id,)),
                ("DELETE FROM user_api_keys WHERE user_id = ?", (user_id,)),
                ("DELETE FROM user_risk_settings WHERE user_id = ?", (user_id,)),
                (
                    """
                    UPDATE behavior_events
                    SET user_email = NULL, session_id = NULL, payload_json = '{}'
                    WHERE user_email = ?
                    """,
                    (normalized,),
                ),
                ("DELETE FROM users WHERE id = ?", (user_id,)),
            ):
                cur = await db.execute(stmt, params)
                deleted += int(cur.rowcount or 0)
            await db.commit()
    except Exception:
        logger.exception("GDPR erasure failed | email=%s", str(normalized).replace("\r", " ").replace("\n", " "))
        raise

    return {"found": True, "rows_deleted": deleted, "user_id": user_id}


async def fetch_user_by_session(token: str) -> dict[str, Any] | None:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT u.* FROM users u
                JOIN user_sessions s ON s.user_id = u.id
                WHERE s.token = ? AND s.expires_at > ?
                """,
                (token, _utcnow_iso()),
            )
            result = await rows.fetchone()
        return dict(result) if result else None
    except Exception:
        logger.exception("Unable to fetch user by session")
        return None


async def insert_user_session(user_id: int, token: str, expires_at: str) -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO user_sessions (user_id, token, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, token, expires_at, _utcnow_iso()),
        )
        return int(cursor.lastrowid or 0)


async def delete_user_session(token: str) -> None:
    async with get_connection() as db:
        await db.execute("DELETE FROM user_sessions WHERE token = ?", (token,))


async def delete_user_sessions_for_user(user_id: int) -> int:
    """Revoke all sessions for a user (login fixation / stolen-token blast radius)."""
    async with get_connection() as db:
        cursor = await db.execute(
            "DELETE FROM user_sessions WHERE user_id = ?",
            (int(user_id),),
        )
        return int(cursor.rowcount or 0)


async def touch_user_login(user_id: int) -> None:
    async with get_connection() as db:
        await db.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (_utcnow_iso(), user_id),
        )


def _parse_recovery_hashes(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    try:
        data = json.loads(str(raw))
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception:
        pass
    return [x for x in str(raw).split(",") if x]


async def fetch_user_mfa_row(user_id: int) -> dict[str, Any] | None:
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT id, mfa_enabled, mfa_secret_enc, mfa_pending_secret_enc, mfa_recovery_hashes
                FROM users WHERE id = ?
                """,
                (user_id,),
            )
            result = await rows.fetchone()
        if not result:
            return None
        row = dict(result)
        hashes = _parse_recovery_hashes(row.get("mfa_recovery_hashes"))
        row["mfa_recovery_hashes"] = hashes
        row["mfa_recovery_remaining"] = len(hashes)
        row["mfa_enabled"] = bool(int(row.get("mfa_enabled") or 0))
        return row
    except Exception:
        logger.exception("Unable to fetch MFA row")
        return None


async def set_user_mfa_pending_secret(user_id: int, secret_enc: str) -> None:
    async with get_connection() as db:
        await db.execute(
            "UPDATE users SET mfa_pending_secret_enc = ? WHERE id = ?",
            (secret_enc, user_id),
        )


async def enable_user_mfa(user_id: int, secret_enc: str) -> None:
    async with get_connection() as db:
        await db.execute(
            """
            UPDATE users
            SET mfa_enabled = 1,
                mfa_secret_enc = ?,
                mfa_pending_secret_enc = NULL
            WHERE id = ?
            """,
            (secret_enc, user_id),
        )


async def set_user_mfa_recovery_hashes(user_id: int, hashes: list[str]) -> None:
    async with get_connection() as db:
        await db.execute(
            "UPDATE users SET mfa_recovery_hashes = ? WHERE id = ?",
            (json.dumps(hashes), user_id),
        )


async def consume_mfa_recovery_hash(user_id: int, matched_hash: str) -> None:
    row = await fetch_user_mfa_row(user_id)
    if not row:
        return
    remaining = [h for h in (row.get("mfa_recovery_hashes") or []) if h != matched_hash]
    await set_user_mfa_recovery_hashes(user_id, remaining)


async def clear_user_mfa(user_id: int) -> None:
    async with get_connection() as db:
        await db.execute(
            """
            UPDATE users
            SET mfa_enabled = 0,
                mfa_secret_enc = NULL,
                mfa_pending_secret_enc = NULL,
                mfa_recovery_hashes = NULL
            WHERE id = ?
            """,
            (user_id,),
        )


async def fetch_user_by_oauth(provider: str, subject: str) -> dict[str, Any] | None:
    if not provider or not subject:
        return None
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT * FROM users
                WHERE oauth_provider = ? AND oauth_subject = ?
                """,
                (provider.strip().lower(), subject.strip()),
            )
            result = await rows.fetchone()
        return dict(result) if result else None
    except Exception:
        logger.exception("Unable to fetch OAuth user")
        return None


async def link_user_oauth(user_id: int, provider: str, subject: str) -> None:
    async with get_connection() as db:
        await db.execute(
            """
            UPDATE users
            SET oauth_provider = ?, oauth_subject = ?
            WHERE id = ?
            """,
            (provider.strip().lower(), subject.strip(), user_id),
        )


async def create_oauth_user(email: str, name: str, provider: str, subject: str) -> int:
    """Create passwordless OAuth user with unusable password hash."""
    import secrets as _secrets

    from auth_service import hash_password

    unusable = hash_password(_secrets.token_urlsafe(48))
    now = _utcnow_iso()
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO users (
                email, password_hash, name, created_at,
                oauth_provider, oauth_subject,
                password_is_set, email_verified_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                email.strip().lower(),
                unusable,
                name or None,
                now,
                provider.strip().lower(),
                subject.strip(),
                now,
            ),
        )
        return int(cursor.lastrowid or 0)


async def fetch_oracle_usage_today(email: str) -> int:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT count FROM oracle_usage_daily
                WHERE email = ? AND usage_date = ?
                """,
                (email.strip().lower(), today),
            )
            row = await rows.fetchone()
        return int(_first_cell(row) or 0)
    except Exception:
        return 0


async def fetch_oracle_usage_month(email: str) -> int:
    """Sum Oracle calls over the rolling last 30 days."""
    since = (datetime.now(UTC) - timedelta(days=30)).strftime("%Y-%m-%d")
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT COALESCE(SUM(count), 0)
                FROM oracle_usage_daily
                WHERE email = ? AND usage_date >= ?
                """,
                (email.strip().lower(), since),
            )
            row = await rows.fetchone()
        return int(_first_cell(row) or 0)
    except Exception:
        return 0


async def count_risk_oracle_predictions_month() -> int:
    """Platform-wide elevated-risk oracle outputs in the last 30 days."""
    since = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    risk_labels = ("Do Not Touch", "CAUTION", "ELEVATED_RISK", "AVOID")
    placeholders = ",".join("?" for _ in risk_labels)
    try:
        async with get_connection() as db:
            rows = await db.execute(
                f"""
                SELECT COUNT(*)
                FROM oracle_predictions
                WHERE timestamp >= ?
                  AND verdict IN ({placeholders})
                """,
                (since, *risk_labels),
            )
            row = await rows.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


async def record_retention_grant(email: str, grant_type: str, days: int) -> None:
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO retention_grants (email, grant_type, granted_at, days)
            VALUES (?, ?, ?, ?)
            """,
            (email.strip().lower(), grant_type, _utcnow_iso(), int(days)),
        )


async def retention_grant_recent(email: str, grant_type: str, *, within_days: int = 30) -> bool:
    since = (datetime.now(UTC) - timedelta(days=within_days)).isoformat()
    try:
        async with get_connection() as db:
            rows = await db.execute(
                """
                SELECT COUNT(*) FROM retention_grants
                WHERE email = ? AND grant_type = ? AND granted_at >= ?
                """,
                (email.strip().lower(), grant_type, since),
            )
            row = await rows.fetchone()
        return bool(row and int(row[0]) > 0)
    except Exception:
        return False


async def increment_oracle_usage(email: str) -> int:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    try:
        async with get_connection() as db:
            await db.execute(
                """
                INSERT INTO oracle_usage_daily (email, usage_date, count)
                VALUES (?, ?, 1)
                ON CONFLICT(email, usage_date) DO UPDATE SET count = count + 1
                """,
                (email.strip().lower(), today),
            )
            rows = await db.execute(
                "SELECT count FROM oracle_usage_daily WHERE email = ? AND usage_date = ?",
                (email.strip().lower(), today),
            )
            row = await rows.fetchone()
        return int(_first_cell(row) or 1)
    except Exception:
        logger.exception("increment_oracle_usage failed")
        return 0


def close_db() -> None:
    """
    Compatibility hook for graceful shutdown.

    Connections are opened per operation and closed by get_connection().
    """
    logger.debug("close_db called; no persistent pool to close.")


async def insert_ingestion_snapshot(
    source_id: str,
    category: str,
    payload: dict[str, Any] | list[Any],
    *,
    status: str = "ok",
) -> int:
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO ingestion_snapshots (source_id, category, payload_json, fetched_at, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (source_id, category, json.dumps(payload, separators=(",", ":")), _utcnow_iso(), status),
        )
        await db.commit()
        return int(cursor.lastrowid)


def _next_ingestion_counts(row: Any, ok: bool) -> tuple[int, int]:
    success_count = int(row[0]) + (1 if ok else 0)
    error_count = int(row[1]) + (0 if ok else 1)
    return success_count, error_count


async def _update_ingestion_health_row(
    db: Any,
    source_id: str,
    *,
    ok: bool,
    error: str | None,
    now: str,
    row: Any,
) -> None:
    success_count, error_count = _next_ingestion_counts(row, ok)
    await db.execute(
        """
        UPDATE ingestion_source_health
        SET last_ok_at = CASE WHEN ? THEN ? ELSE last_ok_at END,
            last_error_at = CASE WHEN ? THEN last_error_at ELSE ? END,
            last_error = CASE WHEN ? THEN last_error ELSE ? END,
            success_count = ?,
            error_count = ?,
            updated_at = ?
        WHERE source_id = ?
        """,
        (ok, now, ok, now, ok, error or "", success_count, error_count, now, source_id),
    )


async def _insert_ingestion_health_row(
    db: Any,
    source_id: str,
    category: str,
    *,
    ok: bool,
    error: str | None,
    now: str,
) -> None:
    await db.execute(
        """
        INSERT INTO ingestion_source_health
            (source_id, category, last_ok_at, last_error_at, last_error,
             success_count, error_count, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_id,
            category,
            now if ok else None,
            None if ok else now,
            None if ok else (error or "unknown"),
            1 if ok else 0,
            0 if ok else 1,
            now,
        ),
    )


async def upsert_ingestion_health(
    source_id: str,
    category: str,
    *,
    ok: bool,
    error: str | None = None,
) -> None:
    now = _utcnow_iso()
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT success_count, error_count FROM ingestion_source_health WHERE source_id = ?",
                (source_id,),
            )
        ).fetchone()
        if row:
            await _update_ingestion_health_row(
                db,
                source_id,
                ok=ok,
                error=error,
                now=now,
                row=row,
            )
        else:
            await _insert_ingestion_health_row(
                db,
                source_id,
                category,
                ok=ok,
                error=error,
                now=now,
            )
        await db.commit()


async def fetch_latest_ingestion_by_category(
    category: str,
    *,
    max_age_seconds: int = 600,
    limit: int = 50,
) -> list[dict[str, Any]]:
    cutoff = (datetime.now(UTC) - timedelta(seconds=max_age_seconds)).isoformat()
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT source_id, category, payload_json, fetched_at, status
                FROM ingestion_snapshots
                WHERE category = ? AND fetched_at >= ?
                ORDER BY fetched_at DESC
                LIMIT ?
                """,
                (category, cutoff, limit),
            )
        ).fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        try:
            payload = json.loads(row[2])
        except json.JSONDecodeError:
            payload = {}
        results.append(
            {
                "source_id": row[0],
                "category": row[1],
                "payload": payload,
                "fetched_at": row[3],
                "status": row[4],
            }
        )
    return results


async def fetch_ingestion_snapshots_for_export(*, limit: int = 500) -> list[dict[str, Any]]:
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT id, source_id, category, payload_json, fetched_at, status
                FROM ingestion_snapshots
                ORDER BY fetched_at DESC
                LIMIT ?
                """,
                (int(limit),),
            )
        ).fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        payload_raw = _row_get(row, 3, "payload_json")
        try:
            payload = json.loads(payload_raw)
        except (json.JSONDecodeError, TypeError):
            payload = {}
        results.append(
            {
                "id": int(_row_get(row, 0, "id") or 0),
                "source_id": _row_get(row, 1, "source_id"),
                "category": _row_get(row, 2, "category"),
                "payload": payload,
                "fetched_at": _row_get(row, 4, "fetched_at"),
                "status": _row_get(row, 5, "status"),
            }
        )
    return results


async def fetch_ingestion_health_summary() -> list[dict[str, Any]]:
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT source_id, category, last_ok_at, last_error_at, last_error,
                       success_count, error_count, updated_at
                FROM ingestion_source_health
                ORDER BY category, source_id
                """
            )
        ).fetchall()
    return [
        {
            "source_id": _row_get(row, 0, "source_id"),
            "category": _row_get(row, 1, "category"),
            "last_ok_at": _row_get(row, 2, "last_ok_at"),
            "last_error_at": _row_get(row, 3, "last_error_at"),
            "last_error": _row_get(row, 4, "last_error"),
            "success_count": _row_get(row, 5, "success_count"),
            "error_count": _row_get(row, 6, "error_count"),
            "updated_at": _row_get(row, 7, "updated_at"),
        }
        for row in rows
    ]


async def prune_ingestion_snapshots(max_rows: int = 50_000) -> int:
    async with get_connection() as db:
        count_row = await (await db.execute("SELECT COUNT(*) FROM ingestion_snapshots")).fetchone()
        total = int(count_row[0]) if count_row else 0
        if total <= max_rows:
            return 0
        to_delete = total - max_rows
        await db.execute(
            """
            DELETE FROM ingestion_snapshots
            WHERE id IN (
                SELECT id FROM ingestion_snapshots ORDER BY fetched_at ASC LIMIT ?
            )
            """,
            (to_delete,),
        )
        await db.commit()
        return to_delete


async def fetch_recent_pricing_for_symbol(symbol: str, limit: int = 200) -> list[dict[str, Any]]:
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT price, timestamp, exchange
                FROM pricing_logs
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (symbol, limit),
            )
        ).fetchall()
    return [{"price": row[0], "timestamp": row[1], "exchange": row[2]} for row in rows]


async def insert_forecast_logs(
    asset: str,
    price_at: float,
    forecast: dict[str, Any],
) -> None:
    ts = _utcnow_iso()
    model = str(forecast.get("model") or "ema_linear_trend_v1")
    confidence = float(forecast.get("confidence_percent") or 0)
    horizons = forecast.get("horizons") or {}
    rows: list[tuple[Any, ...]] = []
    for row in horizons.values():
        if not isinstance(row, dict):
            continue
        rows.append(
            (
                ts,
                asset.upper(),
                int(row.get("horizon_hours") or 0),
                price_at,
                float(row.get("price_forecast") or price_at),
                str(row.get("direction") or "neutral"),
                confidence,
                model,
            )
        )
    if not rows:
        return
    async with get_connection() as db:
        await db.executemany(
            """
            INSERT INTO forecast_logs (
                timestamp, asset, horizon_hours, price_at, price_forecast,
                direction_predicted, confidence, model, resolved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            rows,
        )
        await db.commit()


async def fetch_unresolved_forecast_logs(limit: int = 100) -> list[dict[str, Any]]:
    cutoff = (datetime.now(UTC) - timedelta(hours=23)).isoformat()
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT *
                FROM forecast_logs
                WHERE resolved = 0
                  AND timestamp <= ?
                  AND horizon_hours = 24
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (cutoff, limit),
            )
        ).fetchall()
    return [dict(row) for row in rows]


async def resolve_forecast_log(
    forecast_id: int,
    price_actual: float,
    direction_actual: str,
    accuracy_score: float,
) -> None:
    async with get_connection() as db:
        await db.execute(
            """
            UPDATE forecast_logs
            SET resolved = 1,
                price_actual = ?,
                direction_actual = ?,
                accuracy_score = ?
            WHERE id = ?
            """,
            (price_actual, direction_actual, accuracy_score, forecast_id),
        )
        await db.commit()


async def fetch_forecast_audit_stats(limit: int = 200) -> dict[str, Any]:
    async with get_connection() as db:
        total_row = await (await db.execute("SELECT COUNT(*) FROM forecast_logs")).fetchone()
        resolved_row = await (
            await db.execute("SELECT COUNT(*) FROM forecast_logs WHERE resolved = 1")
        ).fetchone()
        avg_row = await (
            await db.execute(
                """
                SELECT AVG(accuracy_score)
                FROM forecast_logs
                WHERE resolved = 1 AND accuracy_score IS NOT NULL
                """
            )
        ).fetchone()
        recent = await (
            await db.execute(
                """
                SELECT asset, timestamp, price_at, price_forecast, price_actual,
                       direction_predicted, direction_actual, accuracy_score, horizon_hours
                FROM forecast_logs
                WHERE resolved = 1
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
        ).fetchall()
    total = int(total_row[0]) if total_row else 0
    resolved = int(resolved_row[0]) if resolved_row else 0
    avg_acc = float(avg_row[0]) if avg_row and avg_row[0] is not None else 0.0
    return {
        "total_forecasts": total,
        "resolved_forecasts": resolved,
        "average_accuracy_percent": round(avg_acc, 2),
        "recent": [dict(row) for row in recent],
    }


async def insert_weekly_report(narrative: str, payload: dict[str, Any]) -> int:
    import json

    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO weekly_reports (generated_at, narrative, payload_json)
            VALUES (?, ?, ?)
            """,
            (_utcnow_iso(), narrative[:2000], json.dumps(payload, default=str)),
        )
        return int(cursor.lastrowid or 0)


async def fetch_weekly_reports(limit: int = 12) -> list[dict[str, Any]]:
    import json

    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT id, generated_at, narrative, payload_json
                FROM weekly_reports
                ORDER BY generated_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        try:
            item["payload"] = json.loads(item.pop("payload_json") or "{}")
        except json.JSONDecodeError:
            item["payload"] = {}
        out.append(item)
    return out


async def insert_maintenance_run(payload: dict[str, Any]) -> int:
    import json

    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO maintenance_runs (started_at, finished_at, payload_json)
            VALUES (?, ?, ?)
            """,
            (
                payload.get("started_at") or _utcnow_iso(),
                payload.get("finished_at"),
                json.dumps(payload),
            ),
        )
        return int(cursor.lastrowid or 0)


async def fetch_maintenance_runs(limit: int = 10) -> list[dict[str, Any]]:
    import json

    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT id, started_at, finished_at, payload_json
                FROM maintenance_runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        try:
            item["payload"] = json.loads(item.pop("payload_json") or "{}")
        except json.JSONDecodeError:
            item["payload"] = {}
        out.append(item)
    return out


async def upsert_user_api_key(
    user_id: int,
    exchange: str,
    api_key_encrypted: str,
    api_secret_encrypted: str,
    *,
    label: str = "",
) -> int:
    ts = _utcnow_iso()
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO user_api_keys
                (user_id, exchange, api_key_encrypted, api_secret_encrypted, label, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, exchange) DO UPDATE SET
                api_key_encrypted = excluded.api_key_encrypted,
                api_secret_encrypted = excluded.api_secret_encrypted,
                label = excluded.label,
                updated_at = excluded.updated_at
            """,
            (user_id, exchange.lower(), api_key_encrypted, api_secret_encrypted, label or None, ts, ts),
        )
        row = await (await db.execute("SELECT last_insert_rowid()")).fetchone()
        return int(row[0] or 0)


async def fetch_user_api_keys(user_id: int) -> list[dict[str, Any]]:
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT id, user_id, exchange, label, created_at, updated_at
                FROM user_api_keys WHERE user_id = ?
                ORDER BY exchange
                """,
                (user_id,),
            )
        ).fetchall()
    return [dict(r) for r in rows]


async def fetch_user_api_key_secrets(user_id: int, exchange: str) -> dict[str, Any] | None:
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT * FROM user_api_keys
                WHERE user_id = ? AND exchange = ?
                """,
                (user_id, exchange.lower()),
            )
        ).fetchone()
    return dict(row) if row else None


async def delete_user_api_key(user_id: int, exchange: str) -> bool:
    async with get_connection() as db:
        cursor = await db.execute(
            "DELETE FROM user_api_keys WHERE user_id = ? AND exchange = ?",
            (user_id, exchange.lower()),
        )
        return int(cursor.rowcount or 0) > 0


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def _main() -> None:
        await init_db()
        pricing_id = await insert_pricing_log(
            exchange="binance",
            symbol="BTC/USDT",
            price=67_250.5,
            volume=12.34,
            opportunity_score=72.5,
        )
        order_book_id = await insert_order_book(
            exchange="binance",
            symbol="BTC/USDT",
            bids=[[67250.0, 1.2], [67249.5, 0.8]],
            asks=[[67251.0, 0.5], [67252.0, 1.1]],
        )
        print(f"[database] pricing_log id={pricing_id}, order_book id={order_book_id}")

    asyncio.run(_main())
