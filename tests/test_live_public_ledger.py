"""Live public ledger query_ok and postgres-safe resolved predicates."""

from __future__ import annotations

from fastapi.testclient import TestClient

from oracle_integrity import resolved_true_sql


def test_public_accuracy_live_ledger_query_ok():
    from dashboard import app

    client = TestClient(app)
    payload = client.get("/api/oracle/accuracy/public").json()
    live = payload.get("live_ledger") or {}
    assert live.get("query_ok") is True
    assert isinstance(live.get("miss_sample"), list)


def test_resolved_true_sql_sqlite_uses_integer_compare():
    assert resolved_true_sql() == "resolved = 1"
