"""Prove Starlette TestClient uses httpx2 — no deprecation fallback to httpx."""

from __future__ import annotations

import warnings

import httpx2
from starlette.exceptions import StarletteDeprecationWarning


def test_httpx2_is_installed_and_importable():
    assert httpx2.__version__.startswith("2.12.")


def test_starlette_testclient_imports_httpx2_without_deprecation():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", StarletteDeprecationWarning)
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        client = TestClient(app)
        response = client.get("/docs")

    starlette_httpx_warnings = [
        w
        for w in caught
        if issubclass(w.category, StarletteDeprecationWarning)
        and "httpx" in str(w.message).lower()
    ]
    assert starlette_httpx_warnings == []
    assert response.status_code == 200
    import starlette.testclient as tc

    assert tc.httpx.__name__ == "httpx2"


def test_legacy_httpx_runtime_clients_remain_importable():
    """Production modules keep httpx; installing httpx2 must not remove it."""
    import httpx

    assert httpx.__version__.startswith("0.28.")
    assert httpx.__name__ == "httpx"
