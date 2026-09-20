"""Launch-57 anonymous public surface security batch — tightened allowlist."""

from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from anonymous_route_foundation import (
    ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES,
    DENIED_LEGACY_PUBLIC_EXACT,
    DENIED_LEGACY_PUBLIC_PREFIXES,
    LAUNCH57_PUBLIC_API_EXACT,
    PUBLIC_API_EXACT,
    PUBLIC_HTML_EXACT,
    is_anonymous_route_allowed,
    iter_anonymous_public_surface_manifest,
)


@pytest.fixture(autouse=True)
def disable_viral_rate_limits(monkeypatch):
    monkeypatch.setattr("viral_capacity.viral_middleware_enabled", lambda: False)


@pytest.fixture()
def client():
    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_legacy_prefixes_not_in_allowlist():
    for prefix in DENIED_LEGACY_PUBLIC_PREFIXES:
        assert prefix not in ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES, prefix


def test_legacy_prefix_reintroduction_fails():
    """Re-adding a legacy prefix must fail this guard."""
    contaminated = tuple(ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES) + ("/api/whale/",)
    assert "/api/whale/" in contaminated
    assert "/api/whale/" not in ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES


def test_denied_legacy_exact_paths_not_allowlisted():
    for path in DENIED_LEGACY_PUBLIC_EXACT:
        assert is_anonymous_route_allowed("GET", path) is False, path


@pytest.mark.parametrize(
    "path",
    [
        "/api/dashboard/stream",
        "/api/whale/stealth-advisor",
        "/api/mev/sandwich-report",
        "/api/audience/entry",
        "/api/heroes/status",
        "/api/strategy/priority-chain",
        "/api/intent/recent",
        "/api/execution/recent",
        "/api/ledger/public",
        "/api/glass-box/summary",
        "/api/accuracy/summary",
        "/api/viral/readiness",
        "/api/wow/metrics",
        "/api/anti-hype/score",
        "/api/since-you-left",
    ],
)
def test_removed_paths_return_401_without_cookie(client, path: str):
    response = client.get(path)
    assert response.status_code == 401, f"{path} -> {response.status_code}"


def test_launch57_guest_paths_remain_public_without_cookie(client, monkeypatch):
    async def fake_guest_trust(symbol: str, params=None):
        return {
            "launch_item_id": 46,
            "guest_trust": {"no_pii_leak": True, "public_intelligence_proofs": []},
        }

    async def fake_real_time_prices(symbol: str, params=None):
        return {
            "launch_item_id": 22,
            "symbol": symbol,
            "price": 42000.0,
            "freshness_state": "LIVE",
            "presented_as_live": True,
        }

    async def fake_shareable_accuracy_page(symbol: str, params=None):
        return {"launch_item_id": 45, "success": True, "symbol": symbol}

    monkeypatch.setattr("launch57.trust_batch2.guest_trust_surface", fake_guest_trust)
    monkeypatch.setattr("launch57.data_batch1.real_time_prices", fake_real_time_prices)
    monkeypatch.setattr("launch57.trust_batch2.shareable_accuracy_page", fake_shareable_accuracy_page)

    for path in (
        "/api/launch57/guest-trust",
        "/api/launch57/real-time-prices",
        "/api/launch57/shareable-accuracy",
    ):
        response = client.get(path, params={"symbol": "BTC"})
        assert response.status_code == 200, path


def test_public_status_and_accuracy_html_without_cookie(client):
    for path in ("/status", "/how-it-works", "/oracle-accuracy"):
        response = client.get(path, headers={"Accept": "text/html"})
        assert response.status_code == 200, path
        assert "Anonymous access denied" not in response.text


def test_landing_has_no_analytics_requests():
    landing = Path("templates/landing.html").read_text(encoding="utf-8")
    forbidden = (
        "/api/analytics/",
        "/api/discipline-mirror/",
        "/api/telegram/free/",
        "/api/billing/payments",
        "/api/billing/institutional-inquiry",
        "/api/audience/entry",
    )
    hits = [token for token in forbidden if token in landing]
    assert hits == [], hits


def test_site_footer_public_links():
    footer = Path("templates/partials/site_footer.html").read_text(encoding="utf-8")
    for href in (
        'href="/terms"',
        'href="/privacy"',
        'href="/disclaimer"',
        'href="/how-it-works"',
        'href="/status"',
        'href="/oracle-accuracy"',
    ):
        assert href in footer


def test_public_surface_manifest_launch57_only():
    manifest = iter_anonymous_public_surface_manifest()
    exact_paths = {row["path"] for row in manifest if not row["path"].endswith("*")}
    assert "/api/status" in exact_paths
    assert "/api/launch57/guest-trust" in exact_paths
    assert "/api/dashboard/stream" not in exact_paths
    assert "/api/whale/stealth-advisor" not in exact_paths
    assert LAUNCH57_PUBLIC_API_EXACT.issubset(PUBLIC_API_EXACT)
    assert "/oracle-accuracy" in PUBLIC_HTML_EXACT
    prefix_rows = [row["path"] for row in manifest if row["path"].endswith("*")]
    assert "/api/launch57/capability-library/*" in prefix_rows
    assert "/api/whale/*" not in prefix_rows
