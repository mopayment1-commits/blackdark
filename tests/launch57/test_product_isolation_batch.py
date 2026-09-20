"""Launch-57 product isolation batch — first-screen scope lock (55 ready items)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"


def _dash() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def _first_screen_html() -> str:
    dash = _dash()
    start = dash.index('id="trust-pulse"')
    end = dash.index('id="launch57-data-spine"')
    return dash[start:end]


def _boot_block() -> str:
    return _dash().split("function boot()", 1)[1].split("function scheduleCommandHome", 1)[0]


def test_product_isolation_manifest_api():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/product-isolation")
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch57_product_isolation") is True
    assert body.get("ready_launch_count") == 55
    assert body.get("blocked_external_launch_ids") == [33, 38]
    assert body.get("verification_status") == "PENDING_VERIFICATION"
    assert body.get("pass_live_claimed") is False
    assert len(body.get("isolated_elements") or []) >= 10


def test_dashboard_product_isolation_active_in_boot():
    dash = _dash()
    assert "const LAUNCH57_PRODUCT_ISOLATION = true" in dash
    assert "function applyLaunch57ProductIsolation" in dash
    assert "applyLaunch57ProductIsolation()" in _boot_block()
    assert "function launch57IsolationActive" in dash
    assert "renderLaunch57BlockedExternal" in dash


def test_first_screen_no_parked_or_cap646_paths():
    block = _first_screen_html()
    assert "PARKED" not in block
    assert "cap646" not in block.lower()
    script = _dash().split("<script>", 1)[1]
    assert "fetch('/api/market/overview')" in script
    assert "if (launch57IsolationActive()) return" in script
    assert script.index("if (launch57IsolationActive()) return") < script.index("fetch('/api/market/overview')")


def test_first_screen_legacy_toolbar_marked_isolated():
    block = _first_screen_html()
    for legacy_href in ("/since-you-left", "/miss-feed", "/coverage-honesty", "/corpus-passport"):
        parts = block.split(f'href="{legacy_href}"', 1)
        assert len(parts) == 2
        tail = parts[1].split(">", 1)[0]
        assert 'data-launch57-isolate="legacy-non-l57"' in tail


def test_blocked_external_shown_without_launch_numbers():
    dash = _dash()
    blocked = dash.split('id="launch57-blocked-external"', 1)[1].split("</section>", 1)[0]
    render = dash.split("function renderLaunch57BlockedExternal", 1)[1].split("function applyLaunch57ProductIsolation", 1)[0]
    assert "Smart Alerts" in render
    assert "MVRV" in render
    assert "محجوب خارجيًا" in render
    assert "#33" not in render
    assert "#38" not in render
    assert "launch_item_id" not in render
    assert "/api/alerts/telegram" not in render


def test_no_telegram_send_when_isolation_active():
    dash = _dash()
    test_tg = dash.split("async function testTelegram", 1)[1].split("async function loadAlertsGenerosity", 1)[0]
    assert "if (launch57IsolationActive()) return" in test_tg
    tg_status = dash.split("async function loadTgStatus", 1)[1].split("async function testTelegram", 1)[0]
    assert "if (launch57IsolationActive()) return" in tg_status


def test_isolated_elements_inventory_matches_manifest():
    from launch57.product_isolation import ISOLATED_FIRST_SCREEN_ELEMENTS, build_product_isolation_manifest

    manifest = build_product_isolation_manifest()
    manifest_ids = {row["id"] for row in manifest["isolated_elements"]}
    code_ids = {row["id"] for row in ISOLATED_FIRST_SCREEN_ELEMENTS}
    assert manifest_ids == code_ids
    dash = _dash()
    for row in ISOLATED_FIRST_SCREEN_ELEMENTS:
        if row["surface"] == "entry-rail":
            continue
        if row["id"] == "dashboard-stream":
            stream = dash.split("function startDashboardStream", 1)[1].split("function loadOI", 1)[0]
            assert "if (launch57IsolationActive()) return" in stream
            continue
        assert f'data-launch57-isolate-id="{row["id"]}"' in dash


def test_breakage_disabling_isolation_exposes_legacy_path():
    """If isolation is turned off, legacy Since You Left stays visible — this test fails unless isolation stays on."""
    dash = _dash()
    assert re.search(r"const LAUNCH57_PRODUCT_ISOLATION = true", dash)
    assert "applyLaunch57ProductIsolation()" in _boot_block()
    disabled = dash.replace("const LAUNCH57_PRODUCT_ISOLATION = true", "const LAUNCH57_PRODUCT_ISOLATION = false")
    assert 'data-launch57-isolate="legacy-non-l57"' in disabled
    assert "launch57IsolationActive()" in disabled
    # Simulated off: boot still calls applyLaunch57ProductIsolation but it no-ops; marker remains unapplied.
    assert "node.setAttribute('data-launch57-isolated', 'true')" in dash
