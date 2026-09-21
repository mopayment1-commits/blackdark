"""Break tests — live failure HTTP wiring on dashboard (handlers, correlation, maintenance)."""

from __future__ import annotations

import json

import pytest
from fastapi import HTTPException
from starlette.testclient import TestClient


@pytest.fixture()
def client():
    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_failure_handlers_registered_on_dashboard():
    from dashboard import app
    from failure.handlers import handlers_registered

    assert handlers_registered(app) is True


def test_http_error_includes_request_id_and_correlation(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password-15xx"},
        headers={"Origin": "https://testserver"},
    )
    assert res.status_code == 401
    body = res.json()
    assert body.get("error_code") == "BD-AUTH-001"
    assert body.get("correlation_id")
    assert body.get("request_id") == body.get("correlation_id")
    assert res.headers.get("X-Request-ID")
    assert res.headers.get("X-Correlation-ID")


def test_correlation_middleware_propagates_incoming_request_id(client):
    incoming = "bd-clientprovided01"
    res = client.get("/health/live", headers={"X-Correlation-ID": incoming})
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == incoming
    assert res.headers.get("X-Correlation-ID") == incoming


def test_http_error_has_no_technical_leak(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password-15xx"},
        headers={"Origin": "https://testserver"},
    )
    blob = json.dumps(res.json()).lower()
    assert "traceback" not in blob
    assert "/workspace" not in blob
    assert "file \"" not in blob


def test_maintenance_mode_returns_503_bd_maint(client, monkeypatch):
    monkeypatch.setenv("BLACKDARK_MAINTENANCE_MODE", "true")
    res = client.get("/api/status")
    assert res.status_code == 503
    body = res.json()
    assert body["error_code"] == "BD-MAINT-001"
    assert body.get("request_id")
    assert body.get("failure_origin") == "platform"


def test_maintenance_bypass_health_live(client, monkeypatch):
    monkeypatch.setenv("BLACKDARK_MAINTENANCE_MODE", "true")
    res = client.get("/health/live")
    assert res.status_code == 200


def test_login_error_uses_bd_auth_envelope(client, tmp_path, monkeypatch):
    import database
    from auth_service import hash_password

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "auth_err.db"))

    async def _setup():
        await database.init_db()
        await database.create_user(
            "fail@example.com",
            hash_password("valid-password-15chars"),
            "Fail",
        )

    import asyncio

    asyncio.run(_setup())
    res = client.post(
        "/api/auth/login",
        json={"email": "fail@example.com", "password": "wrong-password-15xx"},
        headers={"Origin": "https://testserver"},
    )
    assert res.status_code == 401
    body = res.json()
    assert body["error_code"] == "BD-AUTH-001"
    assert body.get("message_key")
    assert body.get("request_id")


def test_rate_limit_uses_bd_rate_envelope(client):
    from security_auth import _LOGIN_MAX_ATTEMPTS, check_login_rate_limit

    ip = "203.0.113.77"
    for _ in range(_LOGIN_MAX_ATTEMPTS):
        check_login_rate_limit(f"ip:{ip}")

    res = client.post(
        "/api/auth/login",
        json={"email": "ratelimit@example.com", "password": "wrong-password-15xx"},
        headers={"Origin": "https://testserver", "X-Forwarded-For": ip},
    )
    assert res.status_code == 429
    body = res.json()
    assert body["error_code"] == "BD-RATE-001"
    assert body.get("user_retry_max") == 1
    assert body.get("failure_origin") == "platform"
    assert body.get("request_id")


def test_user_retry_max_one_for_safe_user_retry():
    from failure.handlers import _finalize_problem
    from failure.problem import ProblemDetail
    from failure.registry import get_error_spec

    spec = get_error_spec("BD-RATE-001")
    assert spec is not None
    problem = ProblemDetail(
        type="t",
        title="t",
        status=429,
        detail="x",
        error_code="BD-RATE-001",
        correlation_id="bd-abc",
        retry_policy=spec.retry_policy.value,
        retryable=True,
    )
    _finalize_problem(problem, spec)
    assert problem.user_retry_max == 1


def test_upstream_error_marked_source_origin():
    from failure.handlers import _infer_failure_origin
    from failure.registry import get_error_spec

    spec = get_error_spec("BD-UP-502")
    assert spec is not None
    assert _infer_failure_origin("BD-UP-502", spec) == "source"


def test_break_unregistered_handler_no_problem_envelope():
    from fastapi import FastAPI, HTTPException
    from starlette.testclient import TestClient

    app = FastAPI()

    @app.get("/err")
    def err():
        raise HTTPException(status_code=500, detail="traceback /workspace/secret")

    with TestClient(app, raise_server_exceptions=False) as bare:
        res = bare.get("/err")
    body = res.json()
    assert "error_code" not in body
    assert "/workspace" in body.get("detail", "")


def test_break_without_correlation_middleware_no_request_id_header():
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    from failure.handlers import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    with TestClient(app, raise_server_exceptions=False) as bare:
        res = bare.get("/ok", headers={"X-Correlation-ID": "bd-clientprovided01"})
    assert res.headers.get("X-Request-ID") is None


def test_break_user_retry_max_never_above_one():
    from failure.dimensions import RetryPolicy
    from failure.handlers import _finalize_problem
    from failure.problem import ProblemDetail
    from failure.registry import list_error_specs

    for spec in list_error_specs():
        problem = ProblemDetail(
            type="t",
            title=spec.title,
            status=spec.http_status,
            detail="x",
            error_code=spec.error_code,
            correlation_id="bd-test",
            retry_policy=spec.retry_policy.value,
            retryable=spec.retry_policy
            in {RetryPolicy.SAFE_USER_RETRY, RetryPolicy.SAFE_AUTO_RETRY},
        )
        _finalize_problem(problem, spec)
        if spec.retry_policy in {RetryPolicy.SAFE_USER_RETRY, RetryPolicy.SAFE_AUTO_RETRY}:
            assert problem.user_retry_max == 1
        else:
            assert problem.user_retry_max is None

