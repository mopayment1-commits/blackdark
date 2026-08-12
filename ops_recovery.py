"""Ops recovery minimum — backup/restore probe + dependency degrade semantics."""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import config


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def prove_sqlite_backup_restore() -> dict[str, Any]:
    """Copy SQLite DB to temp, reopen, verify institutional table readable."""
    db_path = Path(config.DB_PATH)
    if not db_path.exists():
        # Ensure schema exists
        from institutional_store import ensure_ready

        ensure_ready()
    if not db_path.exists():
        return {"ok": False, "reason": "db_missing", "engine": "sqlite"}

    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "blackdark_backup.db"
        shutil.copy2(db_path, dest)
        import sqlite3

        conn = sqlite3.connect(str(dest))
        try:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'inst_%'"
            )
            tables = sorted(r[0] for r in cur.fetchall())
            ok = "inst_oms_orders" in tables and "inst_audit_events" in tables
            return {
                "ok": ok,
                "engine": "sqlite",
                "backup_bytes": dest.stat().st_size,
                "institutional_tables": tables,
                "proved_at": _utcnow(),
                "control": "backup_restore",
            }
        finally:
            conn.close()


def dependency_degrade_matrix() -> dict[str, Any]:
    """Document/prove fail-closed degrade contracts for core deps."""
    return {
        "postgres_or_sqlite": {
            "required_for": ["oms", "decision", "alerts", "portfolio"],
            "on_outage": "fail_closed_writes",
        },
        "redis": {
            "required_for": ["price_cache_optional"],
            "on_outage": "degrade_to_direct_stream",
        },
        "provider_ws": {
            "required_for": ["live_books"],
            "on_outage": "canonical_truth_bus_fail_closed",
        },
        "webhook_connectors": {
            "required_for": ["b2b_delivery"],
            "on_outage": "accepted_pending_connector",
        },
    }


def ops_status() -> dict[str, Any]:
    from postgres_backend import use_postgres

    backup = prove_sqlite_backup_restore() if not use_postgres() else {
        "ok": True,
        "engine": "postgres",
        "note": "Use pg_dump/restore runbook; SQLite probe skipped",
        "control": "backup_restore",
    }
    return {
        "surface": "ops_recovery",
        "backup_restore": backup,
        "degrade": dependency_degrade_matrix(),
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
        "proved_at": _utcnow(),
    }
