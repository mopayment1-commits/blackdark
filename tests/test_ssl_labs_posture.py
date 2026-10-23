"""SSL Labs / HSTS header contract (application layer)."""

from __future__ import annotations

from pathlib import Path


def test_hsts_includes_preload_directive():
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
    hsts = security_headers_for(Request(scope))["Strict-Transport-Security"]
    assert hsts == "max-age=31536000; includeSubDomains; preload"


def test_ssl_labs_docs_and_caa_runbook_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "deploy/tls/SSL_LABS_REMEDIATION.md").is_file()
    assert (root / "deploy/dns/caa-blackdark-io.md").is_file()
    assert (root / "scripts/check_ssl_labs_posture.py").is_file()
