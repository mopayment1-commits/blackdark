"""P0 authorization hardening — fail-closed admin / institutional / universe."""

from __future__ import annotations

import os

import pytest
from fastapi import HTTPException
from starlette.requests import Request


def _request(client_host: str = "127.0.0.1") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": (client_host, 12345),
        "server": ("test", 80),
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_loopback_never_grants_admin_outside_key(monkeypatch):
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    from security_auth import require_admin, require_admin_dev

    with pytest.raises(HTTPException) as exc:
        await require_admin(user=None, x_admin_key=None, x_admin_totp=None)
    assert exc.value.status_code == 403

    with pytest.raises(HTTPException) as exc2:
        await require_admin_dev(
            request=_request("127.0.0.1"),
            user=None,
            x_admin_key=None,
            x_admin_totp=None,
        )
    assert exc2.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_key_still_works_with_mfa_disabled(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key-please-rotate")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    from security_auth import require_admin

    user = await require_admin(
        user=None,
        x_admin_key="test-admin-key-please-rotate",
        x_admin_totp=None,
    )
    assert user["is_admin"] is True


@pytest.mark.asyncio
async def test_admin_mfa_enforced_on_require_admin(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key-please-rotate")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "true")
    monkeypatch.setenv("ADMIN_TOTP_SECRET", "JBSWY3DPEHPK3PXP")
    from security_auth import require_admin

    with pytest.raises(HTTPException) as exc:
        await require_admin(
            user=None,
            x_admin_key="test-admin-key-please-rotate",
            x_admin_totp="000000",
        )
    assert exc.value.status_code == 403

    import pyotp

    code = pyotp.TOTP("JBSWY3DPEHPK3PXP").now()
    user = await require_admin(
        user=None,
        x_admin_key="test-admin-key-please-rotate",
        x_admin_totp=code,
    )
    assert user["is_admin"] is True


def test_platform_keys_save_rejects_loopback_without_admin(monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    from platform_api import _local_or_admin

    with pytest.raises(HTTPException) as exc:
        _local_or_admin(_request("127.0.0.1"), x_admin_key=None)
    assert exc.value.status_code == 403


def test_institutional_router_requires_auth_dependency():
    from api.routers.institutional import router

    dep_names = []
    for dep in router.dependencies:
        call = getattr(dep, "dependency", None) or dep
        dep_names.append(getattr(call, "__name__", str(call)))
    assert "require_institutional_principal" in dep_names


def test_universe_activate_requires_admin_dependency():
    import ast
    from pathlib import Path

    src = Path("dashboard.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    found = False
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "universe_activate_full":
            args = [a.arg for a in node.args.args]
            assert "_admin" in args
            found = True
    assert found


def test_b2b_page_masks_demo_key_by_default(monkeypatch):
    monkeypatch.delenv("EXPOSE_B2B_DEMO_KEY", raising=False)
    monkeypatch.setenv("BLACKDARK_B2B_DEMO_KEY", "should-not-leak")
    # Re-import config pick-up is env-based at call time in dashboard
    import config

    monkeypatch.setattr(config, "B2B_DEMO_API_KEY", "should-not-leak", raising=False)
    src = open("dashboard.py", encoding="utf-8").read()
    assert "EXPOSE_B2B_DEMO_KEY" in src
    assert 'else "contact-sales"' in src
