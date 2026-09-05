"""Prove Starlette TestClient uses httpx2 — no deprecation fallback to httpx."""

from __future__ import annotations

from pathlib import Path
import warnings

import httpx2
from starlette.exceptions import StarletteDeprecationWarning

ROOT = Path(__file__).resolve().parents[1]
HASHES = (ROOT / "requirements.hashes.txt").read_text(encoding="utf-8")
LOCK = (ROOT / "requirements.lock.txt").read_text(encoding="utf-8")

# Official PyPI sha256 digests (wheel + sdist) — must match requirements.hashes.txt.
HTTPX2_STACK_HASHES = {
    "httpx2==2.12.0": {
        "cc8b6eecb8661c146b8f89a60e97456ee086e91a784ed31ac450c3a9e613dd36",
        "7631fe9887a8a2275f4a2540e053aa670fcc50742864a9ae7c66e609fdcf12cf",
    },
    "httpcore2==2.12.0": {
        "7e04258ce01013d7d615e5b910a3b27fac937d7a95038227e79652b4ba3b4ceb",
        "9293522bba0aa7c4c8e9e3f040c16575bd8868e155a77fa30c7a9085a5eae648",
    },
    "truststore==0.10.4": {
        "adaeaecf1cbb5f4de3b1959b42d41f6fab57b2b1666adb59e89cb0b53361d981",
        "9d91bd436463ad5e4ee4aba766628dd6cd7010cf3e2461756b3303710eebc301",
    },
}


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


def test_httpx2_stack_pins_and_official_hashes():
    for pin, expected in HTTPX2_STACK_HASHES.items():
        assert pin in LOCK
        assert pin in HASHES
        for digest in expected:
            assert f"sha256:{digest}" in HASHES
