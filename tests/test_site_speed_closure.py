"""Sitewide interactive latency budgets (engineering SLOs, local TestClient)."""

from __future__ import annotations

import statistics
import time

import pytest
from fastapi.testclient import TestClient


# Aligned with common SaaS / Core Web Vitals companion API targets (p95).
_BUDGETS_MS = {
    "/": 250,
    "/oracle/BTC/quick": 500,
    "/api/analytics/stats": 500,
    "/api/trust-pulse": 500,
    "/oracle-accuracy": 400,
}


def _p95(samples: list[float]) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    idx = max(0, int(len(ordered) * 0.95) - 1)
    return ordered[idx]


@pytest.fixture()
def client():
    from dashboard import app

    return TestClient(app)


def _warm(client: TestClient, path: str, headers: dict | None = None) -> None:
    client.get(path, headers=headers or {})


@pytest.mark.parametrize("path,budget_ms", list(_BUDGETS_MS.items()))
def test_public_surface_p95_latency(client: TestClient, path: str, budget_ms: int):
    headers = {"Accept": "text/html"} if path == "/" or path.startswith("/oracle-accuracy") else {"Accept": "application/json"}
    query = ""
    if path == "/oracle/BTC/quick":
        query = "?ux_mode=beginner&lang=en"
    elif path == "/api/trust-pulse":
        query = "?symbol=BTC&ux_mode=beginner&lang=en"
    url = path + query
    _warm(client, url, headers)
    samples = []
    for _ in range(8):
        t0 = time.perf_counter()
        res = client.get(url, headers=headers)
        samples.append((time.perf_counter() - t0) * 1000)
        assert res.status_code == 200, res.text[:200]
    p95 = _p95(samples)
    assert p95 <= budget_ms, f"{url} p95={p95:.1f}ms budget={budget_ms}ms samples={samples}"


def test_landing_html_includes_pulse_prefetch_and_csp_binder(client: TestClient):
    res = client.get("/", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert "/oracle/BTC/quick" in res.text
    assert "csp_events.js" in res.text
    assert "loadLandingTrustPulse" in res.text


def test_landing_critical_button_handlers_wired():
    from pathlib import Path

    boot = Path("static/js/landing_boot.js").read_text(encoding="utf-8")
    assert 'window.consultOracle = forward("consultOracle")' in boot
    assert "warmMain();" in boot
    landing = Path("templates/landing.html").read_text(encoding="utf-8")
    assert 'data-bd-call="consultOracle"' in landing
    assert 'data-bd-call="tryOracleFree"' in landing
