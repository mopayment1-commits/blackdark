"""Institutional compounding phases 2–8 integration tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def _db(tmp_path, monkeypatch, name: str) -> None:
    import config
    import database

    db_path = tmp_path / name
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("AUDIT_SIGNING_KEY", "compounding-test-key")
    asyncio.run(database.init_db())


def test_phase2_knowledge_graph(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch, "p2.db")
    from dashboard import app

    c = TestClient(app)
    n1 = c.post("/api/kg/node", json={"node_type": "Asset", "label": "BTC", "properties": {"symbol": "BTC"}})
    n2 = c.post("/api/kg/node", json={"node_type": "Decision", "label": "dec_test", "properties": {"symbol": "BTC"}})
    assert n1.status_code == 200 and n2.status_code == 200
    e = c.post(
        "/api/kg/edge",
        json={
            "source_node_id": n2.json()["node"]["node_id"],
            "target_node_id": n1.json()["node"]["node_id"],
            "edge_type": "predicted",
        },
    )
    assert e.status_code == 200
    q = c.get("/api/kg/query", params={"symbol": "BTC", "days": 30})
    assert q.status_code == 200
    assert q.json()["node_count"] >= 2


def test_phase2_decision_auto_ingest(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch, "p2-ingest.db")
    from dashboard import app

    c = TestClient(app)
    dec = c.post(
        "/api/decisions",
        json={"context": {"symbol": "ETH"}, "prediction": {"action": "long"}, "confidence": 0.7},
    )
    did = dec.json()["decision"]["decision_id"]
    q = c.get("/api/kg/query", params={"decision_id": did})
    assert q.status_code == 200
    assert q.json()["node_count"] >= 1


def test_phase3_signals_version_diff_correlate(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch, "p3.db")
    from dashboard import app

    c = TestClient(app)
    t0 = datetime.now(UTC).isoformat()
    c.post("/api/signals", json={"symbol": "BTC", "signal_type": "oracle_direction", "value": 0.5, "confidence": 0.5, "source": "test", "signal_id": "sig_test_btc"})
    c.post("/api/signals", json={"symbol": "BTC", "signal_type": "oracle_direction", "value": 0.8, "confidence": 0.8, "source": "test", "signal_id": "sig_test_btc"})
    c.post("/api/signals", json={"symbol": "ETH", "signal_type": "oracle_direction", "value": 0.6, "confidence": 0.6, "source": "test"})
    hist = c.get("/api/signals/BTC/history")
    assert hist.status_code == 200
    assert len(hist.json()["items"]) >= 2
    t1 = (datetime.now(UTC) + timedelta(seconds=2)).isoformat()
    diff = c.get("/api/signals/BTC/diff", params={"from": t0, "to": t1})
    assert diff.status_code == 200
    corr = c.get("/api/signals/correlate", params={"symbols": "BTC,ETH"})
    assert corr.status_code == 200
    assert "correlations" in corr.json()


def test_phase4_learning_outcomes_and_missed(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch, "p4.db")
    from dashboard import app

    c = TestClient(app)
    pred = c.post("/api/learning/predictions", json={"symbol": "BTC", "action": "long", "confidence": 0.66})
    pid = pred.json()["prediction"]["prediction_id"]
    out = c.post("/api/learning/outcomes", json={"prediction_id": pid, "actual_result": "correct", "accuracy_score": 0.9})
    assert out.status_code == 200
    acc = c.get("/api/oracle/accuracy")
    assert acc.status_code == 200
    assert "oracle" in acc.json()
    missed = c.get("/api/opportunities/missed")
    assert missed.status_code == 200
    cf = c.post(
        "/api/learning/counterfactuals",
        json={"prediction_id": pid, "scenario": "held_cash", "alternate_action": "flat", "projected_outcome": "neutral"},
    )
    assert cf.status_code == 200


def test_phase5_trust_evidence_and_certificate(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch, "p5.db")
    from dashboard import app

    c = TestClient(app)
    trust = c.get("/api/trust-os")
    assert trust.status_code == 200
    assert "historical_evidence" in trust.json()
    pack = c.get("/api/trust/evidence-pack")
    assert pack.status_code == 200
    cert = c.get("/api/proof-arena/certificate")
    assert cert.status_code == 200
    assert cert.json().get("certificate", {}).get("signature")


def test_phase6_analytics_events(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch, "p6.db")
    from dashboard import app

    c = TestClient(app)
    c.post("/api/analytics/event", json={"event_type": "signup", "payload": {"plan": "free"}, "source": "test"})
    c.post("/api/analytics/share", json={"object_type": "certificate", "object_id": "x", "channel": "x"})
    seo = c.get("/api/analytics/seo")
    assert seo.status_code == 200
    dash = c.get("/api/analytics/institutional-dashboard")
    assert dash.status_code == 200


def test_phase7_corporate_data_room(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch, "p7.db")
    from dashboard import app

    c = TestClient(app)
    comp = c.get("/api/compliance/status")
    assert comp.status_code == 200
    assert "external_dependencies" in comp.json()
    room = c.get("/api/corporate/data-room")
    assert room.status_code == 200
    assert "live_metrics" in room.json()
    ip = c.get("/api/corporate/ip-registry")
    assert ip.status_code == 200
    assert ip.json()["count"] >= 1


def test_phase8_verify_all_phases(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch, "p8.db")
    from dashboard import app

    c = TestClient(app)
    for phase in range(1, 9):
        r = c.get(f"/api/compounding/_verify/phase/{phase}")
        assert r.status_code == 200
        assert r.json().get("ok") is True, f"phase {phase} failed: {r.text}"
    all_v = c.get("/api/compounding/_verify")
    assert all_v.status_code == 200
    assert all_v.json()["ok"] is True
    alerts = c.get("/api/observability/alerts")
    assert alerts.status_code == 200
