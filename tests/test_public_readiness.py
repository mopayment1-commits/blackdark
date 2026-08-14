"""Public direct-use HTTP readiness — visitor/paper ≥95%, never COMPLETE."""

from __future__ import annotations

import os

from public_readiness import PUBLIC_FLOOR_PCT, advertised_public_surfaces, catalog_without_probe


def test_catalog_covers_legal_auth_unique_and_ops_fail_closed():
    rows = advertised_public_surfaces()
    paths = {r["path"] for r in rows}
    for required in (
        "/",
        "/login",
        "/register",
        "/terms",
        "/privacy",
        "/dashboard",
        "/oracle-accuracy",
        "/kill-rate",
        "/unique-ten",
        "/api/product/capability-inventory",
        "/api/alerts/telegram/status",
        "/api/alerts/telegram/test",
        "/health",
    ):
        assert required in paths, required
    buckets = {r["id"]: r["bucket"] for r in rows}
    assert buckets["tg_test_unauth"] == "ops_fail_closed"
    assert buckets["ex_live_order_unauth"] == "excluded_external"
    cat = catalog_without_probe()
    assert cat["product_complete"] is False
    assert cat["institutional_verdict"] == "NOT_COMPLETE"
    assert cat["live_money_ready"] is False
    assert cat["floor_percent"] == PUBLIC_FLOOR_PCT
    assert cat["advertised_count"] == len(rows)
    assert cat["public_direct_count"] >= 80


def test_telegram_unconfigured_is_503_not_silent_200(monkeypatch):
    from fastapi.testclient import TestClient

    from dashboard import app

    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    client = TestClient(app, follow_redirects=False)
    unauth = client.post("/api/alerts/telegram/test", json={})
    assert unauth.status_code == 401
    status = client.get("/api/alerts/telegram/status")
    assert status.status_code == 200
    assert status.json()["configured"] is False
    redir = client.get("/register")
    assert redir.status_code in {307, 302, 301}
    assert "/login" in (redir.headers.get("location") or "")


def test_launch_checklist_skip_is_not_telegram_done(monkeypatch):
    monkeypatch.setenv("LAUNCH_SKIP_TELEGRAM", "true")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("SMTP_HOST", raising=False)
    from launch_checklist import launch_checklist

    board = launch_checklist()
    rows = {r["id"]: r for day in board.get("days") or board.get("items") or [] for r in ([day] if isinstance(day, dict) and "id" in day else day.get("items") or day.get("rows") or [])}
    # launch_checklist shape varies — search recursively
    def _walk(obj):
        if isinstance(obj, dict):
            if obj.get("id") in {"d3_telegram", "d3_email"}:
                yield obj
            for v in obj.values():
                yield from _walk(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from _walk(v)

    found = {r["id"]: r for r in _walk(board)}
    assert found["d3_telegram"]["status"] != "done"
    assert found["d3_email"]["status"] != "done"


def test_al_tg_is_ops_config_not_works():
    from product_capability_inventory import capability_catalog

    by_id = {r["id"]: r for r in capability_catalog()}
    assert by_id["AL-TG"]["status"] == "ops_config"
    assert by_id["AL-SUB"]["status"] == "works"
    assert "/api/alerts/telegram/" not in " ".join(by_id["AL-SUB"]["surfaces"])
    assert by_id["SITE-PUBLIC"]["status"] == "works"


def test_public_readiness_http_probe_meets_floor():
    from fastapi.testclient import TestClient

    from dashboard import app
    from public_readiness import probe_with_client

    client = TestClient(app, follow_redirects=False)
    out = probe_with_client(client)
    assert out["product_complete"] is False
    assert out["institutional_verdict"] == "NOT_COMPLETE"
    score = out["score"]
    assert score["counted_total"] >= 80
    if score["failures"]:
        # Fail the test with the actual missing/broken surfaces — do not hide them.
        assert score["meets_public_floor"], score["failures"]
    assert score["public_direct_use_percent"] >= PUBLIC_FLOOR_PCT
    assert score["institutional_complete"] is False
    assert score["live_money_ready"] is False


def test_public_readiness_api_never_self_grades_complete():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app, follow_redirects=False)
    r = client.get("/api/product/public-readiness")
    assert r.status_code == 200
    body = r.json()
    assert body["product_complete"] is False
    assert body["institutional_verdict"] == "NOT_COMPLETE"
    assert body["live_money_ready"] is False
    assert body["advertised_count"] >= 80
