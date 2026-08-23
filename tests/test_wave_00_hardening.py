"""Wave 0 — Security & Performance Hardening tests."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient


def _db(tmp_path, monkeypatch, name: str) -> None:
    import config
    import database

    db_path = tmp_path / name
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("AUDIT_SIGNING_KEY", "wave0-test-key")
    asyncio.run(database.init_db())


def test_wave_00_status_endpoint(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch, "w0-status.db")
    from dashboard import app

    c = TestClient(app)
    r = c.get("/api/security/wave-00")
    assert r.status_code == 200
    body = r.json()
    assert body["wave"] == 0
    assert body["ok"] is True
    assert body["version"]


def test_response_timing_headers(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch, "w0-timing.db")
    from dashboard import app

    c = TestClient(app)
    r = c.get("/health/live")
    assert r.status_code == 200
    assert r.headers.get("X-Response-Time", "").endswith("ms")
    assert r.headers.get("X-Wave-00")


def test_verify_cache_control(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch, "w0-cache.db")
    from dashboard import app

    c = TestClient(app)
    r = c.get("/api/compounding/_verify")
    assert r.status_code == 200
    cc = r.headers.get("cache-control", "")
    assert "max-age=" in cc


def test_institutional_write_body_too_large(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch, "w0-413.db")
    from dashboard import app

    c = TestClient(app)
    huge = "x" * 70000
    r = c.post(
        "/api/audit/log",
        json={"actor": "test", "action": "big", "payload": {"data": huge}},
    )
    assert r.status_code == 413
    assert r.json()["error"] == "payload_too_large"


def test_corp_header_present():
    from starlette.requests import Request

    from security_middleware import security_headers_for

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 123),
        "server": ("test", 443),
    }
    headers = security_headers_for(Request(scope))
    assert headers.get("Cross-Origin-Resource-Policy") == "same-site"


def test_viral_path_class_audit_export():
    from viral_capacity import _path_class, _limits_for

    assert _path_class("/api/audit/export", "GET") == "audit_export"
    assert _limits_for("audit_export")[0] == 20


def test_viral_path_class_institutional_write_post_only():
    from viral_capacity import _path_class

    assert _path_class("/api/decisions", "POST") == "institutional_write"
    assert _path_class("/api/decisions/search", "GET") == "api"
    assert _path_class("/api/signals/correlate", "GET") == "api"
