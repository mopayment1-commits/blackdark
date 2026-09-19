"""Launch-57 Phase 8 — governing E2E acceptance on real consumer paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from failure.freshness import FreshnessState

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 2.0,
        "data_spine": {"phase1": "ok"},
    }


@pytest.fixture(scope="module")
def e2e_journeys():
    from governance.launch57.generate_phase8_launch_coherence import generate

    generate(skip_tests=True)
    return json.loads((GOV / "PHASE8_E2E_JOURNEYS.json").read_text(encoding="utf-8"))


def test_all_e2e_journeys_pass(e2e_journeys):
    assert e2e_journeys["all_pass"] is True
    assert e2e_journeys["passed"] == e2e_journeys["total"]
    assert e2e_journeys["total"] >= 13
    for journey in e2e_journeys["journeys"]:
        assert journey["status"] == "PASS", journey.get("journey")


def test_home_command_grounded_journey(e2e_journeys):
    row = next(j for j in e2e_journeys["journeys"] if j["journey"] == "data_spine_trust_decision_command_home")
    assert row["answer_state"] == "COMMAND_HOME_GROUNDED"
    assert row["presented_as_live"] is True


def test_no_parked_home_journey(e2e_journeys):
    row = next(j for j in e2e_journeys["journeys"] if j["journey"] == "no_parked_home_reachability")
    assert row["eligible_empty"] is True


def test_stale_blocks_live_journey(e2e_journeys):
    row = next(j for j in e2e_journeys["journeys"] if j["journey"] == "stale_blocks_presented_as_live")
    assert row["presented_as_live"] is False


@pytest.mark.asyncio
async def test_net_edge_binds_spot_perp_without_opportunity(monkeypatch):
    from launch57.edge_ui_batch1 import spot_perp_arbitrage_scanner

    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.edge_ui_common.load_decision_spine", fake_spine)
    out = await spot_perp_arbitrage_scanner(symbol="BTC", params={"cost_claim": True})
    assert out.get("cost_claim_blocked") is True


@pytest.mark.asyncio
async def test_exchange_risk_only_not_solvency(monkeypatch):
    from launch57.smart_money_batch3 import exchange_transparency_risk_indicators

    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch3.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.institutional_b2b_layer.build_exchange_health_with_counterparty_92",
        lambda exchange="binance", withdrawal_latency_hours=12.0, seed=None: {
            "exchange": exchange,
            "health_score": 7.5,
            "counterparty_risk": {"withdrawal_latency_status": "green", "abnormal_flow_pattern": False},
        },
    )
    out = await exchange_transparency_risk_indicators(symbol="BTC", params={"exchange": "binance"})
    indicators = out["exchange_risk_indicators"]
    assert indicators["indicators_only"] is True
    assert indicators["solvency_certificate_claim"] == "FORBIDDEN"
