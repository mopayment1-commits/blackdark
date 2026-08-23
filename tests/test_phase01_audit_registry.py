"""Phase 1 — Immutable audit log & decision registry tests."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def _isolated_sqlite(tmp_path, monkeypatch, name: str) -> None:
    import config
    import database

    db_path = tmp_path / name
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("AUDIT_SIGNING_KEY", "phase1-test-signing-key")
    asyncio.run(database.init_db())


def test_audit_log_signature_and_persistence(tmp_path, monkeypatch):
    _isolated_sqlite(tmp_path, monkeypatch, "audit-persist.db")
    from audit_registry import fetch_audit_logs, hash_payload, record_audit_log, verify_record_signature

    row = asyncio.run(
        record_audit_log(
            actor="tester@example.com",
            action="unit.test",
            payload_hash=hash_payload({"hello": "world"}),
            outcome="ok",
            request_method="POST",
            request_path="/api/test",
        )
    )
    assert row["signature"]
    assert verify_record_signature(row)
    rows = asyncio.run(fetch_audit_logs(actor="tester@example.com", limit=10))
    assert len(rows) >= 1
    assert rows[0]["signature_valid"] is True


def test_decision_versioning(tmp_path, monkeypatch):
    _isolated_sqlite(tmp_path, monkeypatch, "decision-version.db")
    from audit_registry import create_decision, create_decision_version, get_decision

    created = asyncio.run(
        create_decision(
            context={"symbol": "BTC", "regime": "risk_on"},
            prediction={"action": "bullish", "horizon": "24h"},
            confidence=0.82,
            actor="oracle",
        )
    )
    did = created["decision_id"]
    assert created["version"] == 1
    assert created["outcome"] == "pending"

    v2 = asyncio.run(
        create_decision_version(
            decision_id=did,
            outcome="verified",
            actor="oracle",
        )
    )
    assert v2 is not None
    assert v2["version"] == 2
    assert v2["outcome"] == "verified"

    latest = asyncio.run(get_decision(did))
    assert latest is not None
    assert latest["version"] == 2
    assert latest["version_count"] == 2
    assert latest["versions"] == [1, 2]


def test_decision_search_by_date_range(tmp_path, monkeypatch):
    _isolated_sqlite(tmp_path, monkeypatch, "decision-search.db")
    from audit_registry import create_decision, search_decisions

    asyncio.run(
        create_decision(
            context={"symbol": "ETH"},
            prediction={"action": "neutral"},
            confidence=0.55,
        )
    )
    start = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    end = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    items = asyncio.run(search_decisions(start=start, end=end, symbol="ETH"))
    assert len(items) >= 1
    assert items[0]["context"]["symbol"] == "ETH"


def test_api_middleware_writes_audit_on_existing_api(tmp_path, monkeypatch):
    _isolated_sqlite(tmp_path, monkeypatch, "audit-mw.db")
    from audit_registry import fetch_audit_logs
    from dashboard import app

    client = TestClient(app)
    resp = client.get("/api/trust-os")
    assert resp.status_code == 200

    rows = asyncio.run(fetch_audit_logs(action="api.get", limit=20))
    paths = [r.get("request_path") for r in rows]
    assert "/api/trust-os" in paths


def test_decision_api_create_get_search_export(tmp_path, monkeypatch):
    _isolated_sqlite(tmp_path, monkeypatch, "audit-api.db")
    from dashboard import app

    client = TestClient(app)
    now = datetime.now(UTC)
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    create = client.post(
        "/api/decisions",
        json={
            "context": {"symbol": "BTC", "source": "phase1-test"},
            "prediction": {"action": "long", "target_pct": 3.5},
            "confidence": 0.77,
        },
    )
    assert create.status_code == 200, create.text
    decision_id = create.json()["decision"]["decision_id"]

    fetched = client.get(f"/api/decisions/{decision_id}")
    assert fetched.status_code == 200
    body = fetched.json()["decision"]
    assert body["decision_id"] == decision_id
    assert body["version"] == 1
    assert body["signature_valid"] is True

    patched = client.patch(
        f"/api/decisions/{decision_id}",
        json={"outcome": "verified"},
    )
    assert patched.status_code == 200
    assert patched.json()["decision"]["version"] == 2

    search = client.get(
        "/api/decisions/search",
        params={"start": start, "end": end, "symbol": "BTC"},
    )
    assert search.status_code == 200
    assert search.json()["count"] >= 1

    manual = client.post(
        "/api/audit/log",
        json={
            "actor": "phase1@test",
            "action": "manual.evidence",
            "payload": {"note": "runtime proof"},
            "outcome": "logged",
        },
    )
    assert manual.status_code == 200

    export_json = client.get("/api/audit/export", params={"format": "json", "limit": 50})
    assert export_json.status_code == 200
    payload = json.loads(export_json.text)
    assert payload["count"] >= 1
    assert any(i.get("action") == "api.get" for i in payload["items"])

    export_csv = client.get("/api/audit/export", params={"format": "csv", "limit": 10})
    assert export_csv.status_code == 200
    assert "timestamp,actor,action" in export_csv.text.splitlines()[0]
