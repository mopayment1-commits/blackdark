"""Readable /oracle-accuracy/json-api mirrors /api/oracle/accuracy/public counters."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_json_api_button_destination_is_readable_page():
    from dashboard import app

    client = TestClient(app)
    ledger = client.get("/oracle-accuracy")
    assert ledger.status_code == 200
    assert 'href="/oracle-accuracy/json-api"' in ledger.text
    assert 'href="/api/oracle/accuracy/public" target="_blank"' not in ledger.text


def test_readable_page_matches_public_json_live_ledger():
    from dashboard import app

    client = TestClient(app)
    api = client.get("/api/oracle/accuracy/public")
    assert api.status_code == 200
    live = api.json().get("live_ledger") or {}

    page = client.get("/oracle-accuracy/json-api")
    assert page.status_code == 200
    assert "<title>Public Accuracy API — BLACKDARK</title>" in page.text
    assert "Raw JSON" in page.text
    assert 'href="/api/oracle/accuracy/public"' in page.text

    for key in (
        "logged",
        "resolved",
        "pending",
        "accuracy_percent",
        "verified_errors",
        "partial_outcomes",
    ):
        val = live.get(key)
        assert f"<dt>{key}</dt>" in page.text
        assert f"<dd>{val}</dd>" in page.text
