"""Launch-57 Batch H — visible remaining-path consumer surfaces (#31–#32, #34–#35, #37, #46, #50, #52–#57)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"


def _dash() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def _remaining_block() -> str:
    dash = _dash()
    start = dash.index("const LAUNCH57_GUEST_TRUST")
    end = dash.index("let lastVisibleTrust")
    return dash[start:end]


@pytest.fixture
def authed_client():
    from dashboard import app

    client = TestClient(app, base_url="http://127.0.0.1")
    client.cookies.set("bd_token", f"remaining-paths-batch-h-{uuid.uuid4().hex[:8]}")
    return client


def _allow_tier(monkeypatch, tier: str):
    monkeypatch.setattr(
        "launch57.tier_distribution.enforce_launch57_tier_access",
        lambda **kwargs: {"allowed": True, "effective_tier": tier, "minimum_tier": tier},
    )


def test_dashboard_wires_launch57_remaining_path_routes():
    block = _remaining_block()
    assert "LAUNCH57_GUEST_TRUST = '/api/launch57/guest-trust'" in block
    assert "LAUNCH57_MARKET_SCREENER = '/api/launch57/market-screener'" in block
    assert "LAUNCH57_WATCHLISTS = '/api/launch57/watchlists'" in block
    assert "LAUNCH57_SIGNAL_EXPLANATION = '/api/launch57/signal-explanation'" in block
    assert "LAUNCH57_PRICE_MOVE_EXPLANATION = '/api/launch57/price-move-explanation'" in block
    assert "LAUNCH57_CROSS_MARKET = '/api/launch57/cross-market'" in block
    assert "LAUNCH57_DISCIPLINE_MIRROR = '/api/launch57/discipline-mirror'" in block
    assert "LAUNCH57_CAPABILITY_LIBRARY = '/api/launch57/capability-library'" in block
    assert "LAUNCH57_WALLET_DD = '/api/launch57/wallet-due-diligence'" in block
    assert "LAUNCH57_TOKEN_DD = '/api/launch57/token-due-diligence'" in block
    assert "LAUNCH57_PUMP_DUMP_ALERTS = '/api/launch57/pump-dump-alerts'" in block
    assert "LAUNCH57_SUSPICIOUS_FLAGS = '/api/launch57/suspicious-flags'" in block
    assert "LAUNCH57_EXCHANGE_TRANSPARENCY = '/api/launch57/exchange-transparency'" in block
    assert "function loadLaunch57RemainingPaths" in _dash()
    assert 'id="launch57-remaining-paths"' in _dash()


def test_first_screen_guest_trust_link_wires_launch57_guest_trust():
    block = _dash().split("async function loadLaunch57FirstScreenGaps", 1)[1].split("function renderLaunch57RiskFlags", 1)[0]
    assert "LAUNCH57_GUEST_TRUST" in block
    assert "renderLaunch57GuestTrustLink" in block
    assert 'href="/status"' in _dash().split("function renderLaunch57GuestTrustLink", 1)[1].split("async function loadLaunch57FirstScreenGaps", 1)[0]


def test_wallet_and_token_dd_one_click_buttons():
    section = _dash().split('id="launch57-remaining-paths"', 1)[1].split('id="launch57-data-spine"', 1)[0]
    assert "runLaunch57WalletDd" in section
    assert "runLaunch57TokenDd" in section
    assert "LAUNCH57_WALLET_DD" in _dash().split("async function runLaunch57WalletDd", 1)[1].split("async function runLaunch57TokenDd", 1)[0]
    assert "LAUNCH57_TOKEN_DD" in _dash().split("async function runLaunch57TokenDd", 1)[1].split("async function prefetchShareProof", 1)[0]


def test_risk_flags_hidden_when_sources_fail():
    risk = _dash().split("function renderLaunch57RiskFlags", 1)[1].split("function renderLaunch57RemainingPaths", 1)[0]
    assert "el.hidden = true" in risk
    assert "launch_item_id) === 55" in risk
    assert "launch_item_id) === 56" in risk
    assert "launch_item_id) === 57" in risk


def test_market_screener_route_launch_31(authed_client, monkeypatch):
    _allow_tier(monkeypatch, "elite")
    res = authed_client.get("/api/launch57/market-screener", params={"symbol": "BTC", "tier": "elite"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 31


def test_broken_market_screener_handler_fails(monkeypatch):
    from dashboard import app

    _allow_tier(monkeypatch, "elite")

    async def broken(**kwargs):
        raise RuntimeError("market_screener_handler_removed")

    monkeypatch.setattr("launch57.derivatives_batch2.general_market_token_screener", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"batch-h-broken-31-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/market-screener", params={"symbol": "BTC", "tier": "elite"})
    assert res.status_code == 500


def test_watchlists_route_launch_32(authed_client, monkeypatch):
    _allow_tier(monkeypatch, "pro")
    res = authed_client.get("/api/launch57/watchlists", params={"symbol": "BTC", "tier": "pro"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 32


def test_broken_watchlists_handler_fails(monkeypatch):
    from dashboard import app

    _allow_tier(monkeypatch, "pro")

    async def broken(**kwargs):
        raise RuntimeError("watchlists_handler_removed")

    monkeypatch.setattr("launch57.derivatives_batch2.limited_watchlists", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"batch-h-broken-32-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/watchlists", params={"symbol": "BTC", "tier": "pro"})
    assert res.status_code == 500


def test_signal_explanation_route_launch_34(authed_client, monkeypatch):
    _allow_tier(monkeypatch, "pro")
    res = authed_client.get("/api/launch57/signal-explanation", params={"symbol": "BTC", "tier": "pro"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 34


def test_broken_signal_explanation_handler_fails(monkeypatch):
    from dashboard import app

    _allow_tier(monkeypatch, "pro")

    async def broken(**kwargs):
        raise RuntimeError("signal_explanation_handler_removed")

    monkeypatch.setattr("launch57.explanation_ai_batch1.signal_explanation_workflow", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"batch-h-broken-34-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/signal-explanation", params={"symbol": "BTC", "tier": "pro"})
    assert res.status_code == 500


def test_price_move_explanation_route_launch_35(authed_client, monkeypatch):
    _allow_tier(monkeypatch, "pro")
    res = authed_client.get("/api/launch57/price-move-explanation", params={"symbol": "BTC", "tier": "pro"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 35


def test_broken_price_move_explanation_handler_fails(monkeypatch):
    from dashboard import app

    _allow_tier(monkeypatch, "pro")

    async def broken(**kwargs):
        raise RuntimeError("price_move_explanation_handler_removed")

    monkeypatch.setattr("launch57.explanation_ai_batch1.price_move_explanation", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"batch-h-broken-35-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/price-move-explanation", params={"symbol": "BTC", "tier": "pro"})
    assert res.status_code == 500


def test_cross_market_route_launch_37(authed_client, monkeypatch):
    _allow_tier(monkeypatch, "quant")
    res = authed_client.get("/api/launch57/cross-market", params={"symbol": "BTC", "tier": "quant"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 37


def test_broken_cross_market_handler_fails(monkeypatch):
    from dashboard import app

    _allow_tier(monkeypatch, "quant")

    async def broken(**kwargs):
        raise RuntimeError("cross_market_handler_removed")

    monkeypatch.setattr("launch57.decision_batch2.cross_market_decision_engine", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"batch-h-broken-37-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/cross-market", params={"symbol": "BTC", "tier": "quant"})
    assert res.status_code == 500


def test_guest_trust_route_launch_46():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/guest-trust", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 46


def test_broken_guest_trust_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("guest_trust_handler_removed")

    monkeypatch.setattr("launch57.trust_batch2.guest_trust_surface", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/guest-trust", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_discipline_mirror_route_launch_50(authed_client, monkeypatch):
    _allow_tier(monkeypatch, "pro")
    res = authed_client.get("/api/launch57/discipline-mirror", params={"tier": "pro", "limit": 5})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 50


def test_broken_discipline_mirror_handler_fails(monkeypatch):
    from dashboard import app

    _allow_tier(monkeypatch, "pro")

    async def broken(**kwargs):
        raise RuntimeError("discipline_mirror_handler_removed")

    monkeypatch.setattr("launch57.edge_ui_batch1.discipline_mirror_light", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"batch-h-broken-50-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/discipline-mirror", params={"tier": "pro"})
    assert res.status_code == 500


def test_capability_library_route_launch_52():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/capability-library", params={"q": "oracle"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 52


def test_broken_capability_library_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("capability_library_handler_removed")

    monkeypatch.setattr("launch57.edge_ui_batch1.capability_library_search", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/capability-library", params={"q": "oracle"})
    assert res.status_code == 500


def test_wallet_dd_route_launch_53(authed_client, monkeypatch):
    _allow_tier(monkeypatch, "elite")
    res = authed_client.get(
        "/api/launch57/wallet-due-diligence",
        params={"symbol": "BTC", "address": "0x0000000000000000000000000000000000000000", "tier": "elite"},
    )
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 53


def test_broken_wallet_dd_handler_fails(monkeypatch):
    from dashboard import app

    _allow_tier(monkeypatch, "elite")

    async def broken(**kwargs):
        raise RuntimeError("wallet_dd_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch2.instant_wallet_due_diligence", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"batch-h-broken-53-{uuid.uuid4().hex[:8]}")
    res = client.get(
        "/api/launch57/wallet-due-diligence",
        params={"symbol": "BTC", "address": "0x0000000000000000000000000000000000000000", "tier": "elite"},
    )
    assert res.status_code == 500


def test_token_dd_route_launch_54(authed_client, monkeypatch):
    _allow_tier(monkeypatch, "elite")
    res = authed_client.get("/api/launch57/token-due-diligence", params={"symbol": "BTC", "tier": "elite"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 54


def test_broken_token_dd_handler_fails(monkeypatch):
    from dashboard import app

    _allow_tier(monkeypatch, "elite")

    async def broken(**kwargs):
        raise RuntimeError("token_dd_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch2.instant_token_due_diligence", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"batch-h-broken-54-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/token-due-diligence", params={"symbol": "BTC", "tier": "elite"})
    assert res.status_code == 500


def test_pump_dump_alerts_route_launch_55(authed_client, monkeypatch):
    _allow_tier(monkeypatch, "elite")
    res = authed_client.get("/api/launch57/pump-dump-alerts", params={"symbol": "BTC", "tier": "elite"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 55


def test_broken_pump_dump_alerts_handler_fails(monkeypatch):
    from dashboard import app

    _allow_tier(monkeypatch, "elite")

    async def broken(**kwargs):
        raise RuntimeError("pump_dump_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch3.pump_dump_manipulation_alerts", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"batch-h-broken-55-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/pump-dump-alerts", params={"symbol": "BTC", "tier": "elite"})
    assert res.status_code == 500


def test_suspicious_flags_route_launch_56(authed_client, monkeypatch):
    _allow_tier(monkeypatch, "quant")
    res = authed_client.get("/api/launch57/suspicious-flags", params={"symbol": "BTC", "tier": "quant"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 56


def test_broken_suspicious_flags_handler_fails(monkeypatch):
    from dashboard import app

    _allow_tier(monkeypatch, "quant")

    async def broken(**kwargs):
        raise RuntimeError("suspicious_flags_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch3.suspicious_activity_flags", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"batch-h-broken-56-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/suspicious-flags", params={"symbol": "BTC", "tier": "quant"})
    assert res.status_code == 500


def test_exchange_transparency_route_launch_57(authed_client, monkeypatch):
    _allow_tier(monkeypatch, "quant")
    res = authed_client.get("/api/launch57/exchange-transparency", params={"symbol": "BTC", "tier": "quant"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 57


def test_broken_exchange_transparency_handler_fails(monkeypatch):
    from dashboard import app

    _allow_tier(monkeypatch, "quant")

    async def broken(**kwargs):
        raise RuntimeError("exchange_transparency_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch3.exchange_transparency_risk_indicators", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"batch-h-broken-57-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/exchange-transparency", params={"symbol": "BTC", "tier": "quant"})
    assert res.status_code == 500
