"""Didit KYC webhook and configuration tests."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest


def _sign_v2(body: dict, secret: str, ts: str) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()


def test_verify_webhook_signature_v2():
    from didit_kyc import verify_webhook_signature

    secret = "test-webhook-secret"
    body = {
        "event_id": "evt-1",
        "webhook_type": "status.updated",
        "timestamp": int(time.time()),
        "session_id": "sess-1",
        "status": "Approved",
    }
    ts = str(body["timestamp"])
    sig = _sign_v2(body, secret, ts)
    assert verify_webhook_signature(body, signature_v2=sig, signature_simple=None, timestamp=ts, secret=secret)


def test_process_webhook_updates_case(tmp_path, monkeypatch):
    monkeypatch.setattr("institutional_commerce._ROOT", tmp_path / "commerce", raising=False)
    monkeypatch.setattr("institutional_commerce._INVOICES", tmp_path / "commerce" / "invoices.jsonl", raising=False)
    monkeypatch.setattr("institutional_commerce._KYC", tmp_path / "commerce" / "kyc_cases.jsonl", raising=False)
    monkeypatch.setattr("institutional_commerce._PAID", tmp_path / "commerce" / "paid.jsonl", raising=False)
    monkeypatch.setattr("institutional_commerce._DATA_BASE", tmp_path, raising=False)

    from institutional_commerce import open_kyc_case
    from didit_kyc import process_webhook_event

    case = open_kyc_case(email="buyer@example.com", legal_name="Buyer LLC", country="US", provider="didit")
    body = {
        "event_id": "evt-approve-1",
        "webhook_type": "status.updated",
        "timestamp": int(time.time()),
        "session_id": "didit-session-123",
        "status": "Approved",
        "vendor_data": case["case_id"],
        "metadata": {"case_id": case["case_id"], "email": "buyer@example.com"},
        "environment": "live",
    }
    out = process_webhook_event(body)
    assert out["ok"] is True
    assert out["decision"] == "approved"


def test_public_didit_webhook_route(monkeypatch):
    monkeypatch.setenv("DIDIT_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    health = client.get("/api/webhooks/didit")
    assert health.status_code == 200
    assert health.json()["url"].endswith("/api/webhooks/didit")

    body = {
        "event_id": "evt-dup",
        "webhook_type": "status.updated",
        "timestamp": int(time.time()),
        "session_id": "sess-x",
        "status": "Approved",
        "metadata": {"email": "kyc@example.com", "legal_name": "KYC User", "country": "US"},
        "environment": "live",
    }
    ts = str(body["timestamp"])
    sig = _sign_v2(body, "whsec_test", ts)
    resp = client.post(
        "/api/webhooks/didit",
        json=body,
        headers={"X-Signature-V2": sig, "X-Timestamp": ts},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
