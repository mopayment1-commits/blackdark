"""D-06 — institutional API: idempotency and tenant scope."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from api.idempotency import check_idempotency, idempotent_response, store_idempotency
from api.middleware.tenant_scope import assert_tenant_access, resolve_tenant_id


def _request(headers: dict[str, str]) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": ("127.0.0.1", 123),
        "server": ("test", 443),
    }
    return Request(scope)


def test_idempotency_dedup():
  from api import idempotency as mod

  mod._STORE.clear()
  store_idempotency("key-1", 201, {"ok": True, "id": "abc"})
  dup, cached = check_idempotency("key-1")
  assert dup is True
  assert cached["status_code"] == 201
  assert cached["body"]["id"] == "abc"


def test_idempotent_response_returns_cached():
  from api import idempotency as mod

  mod._STORE.clear()
  body = {"ok": True, "signal_id": "sig_test"}
  first = idempotent_response("idem-x", 201, body)
  assert first == body
  second = idempotent_response("idem-x", 201, {"ok": True, "signal_id": "other"})
  assert second.status_code == 201
  assert second.body == b'{"ok":true,"signal_id":"sig_test"}'


def test_tenant_isolation_denied(monkeypatch):
    monkeypatch.setenv("TENANT_SCOPE_ENFORCE", "true")
    req = _request({"X-Tenant-Id": "tenant-a"})
    with pytest.raises(HTTPException) as exc:
        assert_tenant_access(req, "tenant-b")
    assert exc.value.status_code == 403


def test_tenant_header_resolved():
    req = _request({"X-Tenant-Id": "org-42"})
    assert resolve_tenant_id(req) == "org-42"
