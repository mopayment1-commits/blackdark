"""
Cross-Chain Data Warehouse (#43) — canonical schema + chain-specific semantics.

Backend infrastructure for On-Chain Module (#29 Canonical + #16 Asset Metadata).
NOT a user-facing UI — warehouse access for explorers, indexers, and analytics.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from blackdark.canonical.cross_chain_schema import (
    NormalizedAssetBalance,
    NormalizedTransaction,
)
from blackdark.canonical.resolver import resolve_asset
from bd_platform.transaction_index import append_transactions, query_index
from path_safety import ensure_under, safe_data_file

logger = logging.getLogger("BLACKDARK.CrossChainWarehouse")

_DATA_BASE = Path(__file__).resolve().parent.parent / "data"
_DB_PATH = safe_data_file("warehouse", "cross_chain_warehouse.db")
_LOCK = threading.Lock()

# Chain semantics — documented for warehouse consumers (acceptance: chain semantics documented)
CHAIN_SEMANTICS: dict[str, dict[str, Any]] = {
    "ethereum": {
        "chain_id": 1,
        "address_format": "evm_hex_0x",
        "native_symbol": "ETH",
        "native_decimals": 18,
        "finality_blocks": 12,
        "block_time_sec": 12,
        "semantics": "account_nonce_sequential_evm",
        "tx_id_field": "tx_hash",
        "value_field": "value_native_wei",
    },
    "bsc": {
        "chain_id": 56,
        "address_format": "evm_hex_0x",
        "native_symbol": "BNB",
        "native_decimals": 18,
        "finality_blocks": 15,
        "block_time_sec": 3,
        "semantics": "account_nonce_sequential_evm",
        "tx_id_field": "tx_hash",
        "value_field": "value_native_wei",
    },
    "arbitrum": {
        "chain_id": 42161,
        "address_format": "evm_hex_0x",
        "native_symbol": "ETH",
        "native_decimals": 18,
        "finality_blocks": 20,
        "block_time_sec": 0.25,
        "semantics": "rollup_sequencer_evm",
        "tx_id_field": "tx_hash",
        "value_field": "value_native_wei",
    },
    "polygon": {
        "chain_id": 137,
        "address_format": "evm_hex_0x",
        "native_symbol": "MATIC",
        "native_decimals": 18,
        "finality_blocks": 128,
        "block_time_sec": 2,
        "semantics": "pos_checkpoint_evm",
        "tx_id_field": "tx_hash",
        "value_field": "value_native_wei",
    },
    "solana": {
        "chain_id": "solana",
        "address_format": "base58_pubkey",
        "native_symbol": "SOL",
        "native_decimals": 9,
        "finality_blocks": 32,
        "block_time_sec": 0.4,
        "semantics": "slot_based_signatures",
        "tx_id_field": "signature",
        "value_field": "lamports",
    },
    "tron": {
        "chain_id": "tron",
        "address_format": "base58_tron_T",
        "native_symbol": "TRX",
        "native_decimals": 6,
        "finality_blocks": 19,
        "block_time_sec": 3,
        "semantics": "account_resource_model",
        "tx_id_field": "tx_id",
        "value_field": "sun",
    },
    "avalanche": {
        "chain_id": 43114,
        "address_format": "evm_hex_0x",
        "native_symbol": "AVAX",
        "native_decimals": 18,
        "finality_blocks": 20,
        "block_time_sec": 2,
        "semantics": "snowman_consensus_evm",
        "tx_id_field": "tx_hash",
        "value_field": "value_native_wei",
    },
    "optimism": {
        "chain_id": 10,
        "address_format": "evm_hex_0x",
        "native_symbol": "ETH",
        "native_decimals": 18,
        "finality_blocks": 20,
        "block_time_sec": 2,
        "semantics": "rollup_sequencer_evm",
        "tx_id_field": "tx_hash",
        "value_field": "value_native_wei",
    },
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _db_path() -> Path:
    path = ensure_under(_DB_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS warehouse_chains (
            chain TEXT PRIMARY KEY,
            chain_id TEXT NOT NULL,
            semantics_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS warehouse_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_hash TEXT NOT NULL,
            chain TEXT NOT NULL,
            chain_id TEXT,
            canonical_asset_id TEXT,
            from_address TEXT,
            to_address TEXT,
            value_native REAL,
            value_usd REAL,
            token_symbol TEXT,
            timestamp INTEGER,
            action_type TEXT,
            source TEXT,
            semantics TEXT,
            payload_json TEXT,
            UNIQUE(chain, tx_hash)
        );
        CREATE TABLE IF NOT EXISTS warehouse_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain TEXT NOT NULL,
            address TEXT NOT NULL,
            canonical_asset_id TEXT,
            symbol TEXT,
            balance REAL,
            balance_usd REAL,
            source TEXT,
            updated_at TEXT NOT NULL,
            UNIQUE(chain, address, symbol)
        );
        CREATE INDEX IF NOT EXISTS idx_wtx_chain_ts ON warehouse_transactions(chain, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_wtx_address ON warehouse_transactions(from_address, to_address);
        """
    )
    conn.commit()


def bootstrap_chain_registry() -> dict[str, Any]:
    """Sync CHAIN_SEMANTICS into warehouse_chains table."""
    with _LOCK:
        conn = _connect()
        _init_schema(conn)
        count = 0
        for chain, sem in CHAIN_SEMANTICS.items():
            conn.execute(
                """
                INSERT INTO warehouse_chains(chain, chain_id, semantics_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(chain) DO UPDATE SET
                    chain_id=excluded.chain_id,
                    semantics_json=excluded.semantics_json,
                    updated_at=excluded.updated_at
                """,
                (chain, str(sem.get("chain_id")), json.dumps(sem), _utcnow()),
            )
            count += 1
        conn.commit()
        conn.close()
    return {"ok": True, "chains_registered": count, "timestamp": _utcnow()}


def get_chain_semantics(chain: str) -> dict[str, Any] | None:
    key = (chain or "").strip().lower()
    return CHAIN_SEMANTICS.get(key)


def _canonical_id_for_symbol(symbol: str | None) -> str | None:
    if not symbol:
        return None
    resolved = resolve_asset(symbol)
    return resolved.canonical_id if resolved.found else None


def ingest_transactions(
    rows: list[NormalizedTransaction | dict[str, Any]],
    *,
    mirror_to_index: bool = True,
) -> dict[str, Any]:
    """Persist normalized txs to warehouse + optional JSONL index."""
    dict_rows: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, NormalizedTransaction):
            d = row.to_dict()
        else:
            d = dict(row)
        d["canonical_asset_id"] = _canonical_id_for_symbol(d.get("token_symbol"))
        dict_rows.append(d)

    written = 0
    with _LOCK:
        conn = _connect()
        _init_schema(conn)
        for d in dict_rows:
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO warehouse_transactions(
                        tx_hash, chain, chain_id, canonical_asset_id,
                        from_address, to_address, value_native, value_usd,
                        token_symbol, timestamp, action_type, source, semantics, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        d.get("tx_hash"),
                        d.get("chain"),
                        str(d.get("chain_id")),
                        d.get("canonical_asset_id"),
                        d.get("from_address"),
                        d.get("to_address"),
                        d.get("value_native"),
                        d.get("value_usd"),
                        d.get("token_symbol"),
                        int(d.get("timestamp") or 0),
                        d.get("action_type"),
                        d.get("source"),
                        d.get("semantics", "point_in_time"),
                        json.dumps(d, default=str),
                    ),
                )
                if conn.total_changes:
                    written += 1
            except sqlite3.Error as exc:
                logger.debug("warehouse tx insert skip: %s", exc)
        conn.commit()
        conn.close()

    indexed = 0
    if mirror_to_index and dict_rows:
        indexed = append_transactions(dict_rows)

    return {
        "ok": True,
        "feature": "#43",
        "written_sql": written,
        "indexed_jsonl": indexed,
        "timestamp": _utcnow(),
    }


def ingest_balances(rows: list[NormalizedAssetBalance | dict[str, Any]]) -> dict[str, Any]:
    written = 0
    with _LOCK:
        conn = _connect()
        _init_schema(conn)
        for row in rows:
            d = row.to_dict() if isinstance(row, NormalizedAssetBalance) else dict(row)
            cid = _canonical_id_for_symbol(d.get("symbol"))
            try:
                conn.execute(
                    """
                    INSERT INTO warehouse_balances(
                        chain, address, canonical_asset_id, symbol,
                        balance, balance_usd, source, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(chain, address, symbol) DO UPDATE SET
                        balance=excluded.balance,
                        balance_usd=excluded.balance_usd,
                        canonical_asset_id=excluded.canonical_asset_id,
                        source=excluded.source,
                        updated_at=excluded.updated_at
                    """,
                    (
                        d.get("chain"),
                        d.get("address"),
                        cid,
                        d.get("symbol"),
                        d.get("balance"),
                        d.get("balance_usd"),
                        d.get("source"),
                        _utcnow(),
                    ),
                )
                written += 1
            except sqlite3.Error as exc:
                logger.debug("warehouse balance skip: %s", exc)
        conn.commit()
        conn.close()
    return {"ok": True, "feature": "#43", "written": written, "timestamp": _utcnow()}


def query_warehouse_transactions(
    *,
    chain: str | None = None,
    address: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Warehouse access — SQL primary, JSONL index fallback."""
    clauses: list[str] = []
    params: list[Any] = []
    if chain:
        clauses.append("chain = ?")
        params.append(chain.lower())
    if address:
        addr = address.lower()
        clauses.append("(from_address = ? OR to_address = ?)")
        params.extend([addr, addr])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(max(1, min(limit, 200)))

    rows: list[dict[str, Any]] = []
    with _LOCK:
        conn = _connect()
        _init_schema(conn)
        cur = conn.execute(
            f"""
            SELECT tx_hash, chain, chain_id, canonical_asset_id, from_address, to_address,
                   value_native, value_usd, token_symbol, timestamp, action_type, source, semantics
            FROM warehouse_transactions {where}
            ORDER BY timestamp DESC LIMIT ?
            """,
            tuple(params),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

    if not rows and address:
        idx = query_index(address=address, chain=chain, limit=limit, cursor=cursor)
        return {
            "ok": True,
            "feature": "#43",
            "source": "jsonl_index_fallback",
            "transactions": idx.get("transactions") or [],
            "next_cursor": idx.get("next_cursor"),
            "timestamp": _utcnow(),
        }

    return {
        "ok": True,
        "feature": "#43",
        "source": "sqlite_warehouse",
        "transactions": rows,
        "count": len(rows),
        "timestamp": _utcnow(),
    }


def warehouse_status() -> dict[str, Any]:
    bootstrap_chain_registry()
    with _LOCK:
        conn = _connect()
        _init_schema(conn)
        tx_count = conn.execute("SELECT COUNT(*) AS c FROM warehouse_transactions").fetchone()["c"]
        bal_count = conn.execute("SELECT COUNT(*) AS c FROM warehouse_balances").fetchone()["c"]
        chains = conn.execute("SELECT chain FROM warehouse_chains ORDER BY chain").fetchall()
        conn.close()
    return {
        "ok": True,
        "feature": "#43",
        "surface": "cross_chain_data_warehouse",
        "chains_supported": len(CHAIN_SEMANTICS),
        "chains_registered": [r["chain"] for r in chains],
        "transaction_rows": tx_count,
        "balance_rows": bal_count,
        "canonical_integration": "#29+#16",
        "semantics_documented": True,
        "db_path": str(_db_path()),
        "access_modes": ["sqlite_warehouse", "jsonl_index_fallback"],
        "timestamp": _utcnow(),
    }


def list_chain_semantics() -> dict[str, Any]:
    return {
        "ok": True,
        "feature": "#43",
        "chains": CHAIN_SEMANTICS,
        "count": len(CHAIN_SEMANTICS),
        "timestamp": _utcnow(),
    }
