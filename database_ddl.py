"""SSOT DDL for tables duplicated across SCHEMA bootstrap and migrations."""

from __future__ import annotations

_TABLE_DDL: dict[str, str] = {
    "platform_analytics": """CREATE TABLE IF NOT EXISTS platform_analytics (
    id                 INTEGER PRIMARY KEY CHECK (id = 1),
    page_views         INTEGER NOT NULL DEFAULT 0,
    dashboard_views    INTEGER NOT NULL DEFAULT 0,
    landing_views      INTEGER NOT NULL DEFAULT 0,
    voice_commands     INTEGER NOT NULL DEFAULT 0,
    waitlist_count     INTEGER NOT NULL DEFAULT 0,
    subscriber_count   INTEGER NOT NULL DEFAULT 0,
    updated_at         TEXT    NOT NULL
);""",
    "journal_entries": """CREATE TABLE IF NOT EXISTS journal_entries (
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
)""",
    "audit_logs": """CREATE TABLE IF NOT EXISTS audit_logs (
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
)""",
    "decisions": """CREATE TABLE IF NOT EXISTS decisions (
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
)""",
    "kg_nodes": """CREATE TABLE IF NOT EXISTS kg_nodes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id         TEXT    NOT NULL UNIQUE,
    node_type       TEXT    NOT NULL,
    label           TEXT,
    properties_json TEXT    NOT NULL DEFAULT '{}',
    timestamp       TEXT    NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    signature       TEXT    NOT NULL
)""",
    "kg_edges": """CREATE TABLE IF NOT EXISTS kg_edges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    edge_id         TEXT    NOT NULL UNIQUE,
    source_node_id  TEXT    NOT NULL,
    target_node_id  TEXT    NOT NULL,
    edge_type       TEXT    NOT NULL,
    properties_json TEXT    NOT NULL DEFAULT '{}',
    timestamp       TEXT    NOT NULL,
    signature       TEXT    NOT NULL
)""",
    "market_signals": """CREATE TABLE IF NOT EXISTS market_signals (
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
)""",
    "learning_predictions": """CREATE TABLE IF NOT EXISTS learning_predictions (
    prediction_id       TEXT PRIMARY KEY,
    symbol                TEXT    NOT NULL,
    action                TEXT    NOT NULL,
    confidence            REAL    NOT NULL,
    timestamp             TEXT    NOT NULL,
    expiry                TEXT,
    oracle_prediction_id  INTEGER,
    context_json          TEXT    NOT NULL DEFAULT '{}',
    signature             TEXT    NOT NULL
)""",
    "ip_registry": """CREATE TABLE IF NOT EXISTS ip_registry (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id          TEXT    NOT NULL UNIQUE,
    asset_type        TEXT    NOT NULL,
    title             TEXT    NOT NULL,
    description       TEXT,
    rights_json       TEXT    NOT NULL DEFAULT '{}',
    documentation_ref TEXT,
    created_at        TEXT    NOT NULL,
    updated_at        TEXT    NOT NULL
)""",
}


def table_schema(name: str) -> str:
    """Return canonical CREATE TABLE DDL for a migration-duplicated table."""
    try:
        ddl = _TABLE_DDL[name].rstrip()
    except KeyError as exc:
        raise KeyError(f"unknown SSOT table schema: {name}") from exc
    if not ddl.endswith(";"):
        ddl += ";"
    return ddl
