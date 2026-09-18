"""Launch-57 Phase 7 Adaptive Batch A — builder verification tests (#43→#38→#49→#50→#52)."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.edge_ui_batch1 import (
    capability_library_search,
    discipline_mirror_light,
    mvrv_mvrv_z_score_suite,
    personal_decision_history,
    spot_perp_arbitrage_scanner,
)
from launch57.trust_batch1 import net_edge_truth_score


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 1.0,
        "data_spine": {},
    }


@pytest.mark.asyncio
async def test_entry_gate_capability_5_net_edge_pass_engineering():
    out = await net_edge_truth_score(
        symbol="BTC",
        params={
            "opportunity": {
                "net_profit_usdt": 5.0,
                "quote_amount": 1000.0,
                "total_slippage_bps": 2,
                "withdrawal_fee_usdt": 0.1,
                "trading_fees_usdt": 0.2,
                "quote_age_ms": 100,
                "estimated_recipients": 1,
            }
        },
    )
    assert out["launch_item_id"] == 5
    assert out["success"] is True
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 5
    assert out["net_edge_safety_floor"]["gross_edge_not_actionable_without_cost_treatment"] is True


@pytest.mark.asyncio
async def test_capability_43_gross_spread_not_executable_without_net_edge(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_scan(**kwargs):
        return {
            "opportunities": [{"kind": "spot_futures", "net_profit_usdt": 10.0, "id": "gross-1"}],
            "counts": {"spot_futures": 1},
            "data_source": "test",
            "data_age_sec": 1.0,
            "executable_count": 1,
        }

    monkeypatch.setattr("launch57.edge_ui_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("arbitrage_service.scan_arbitrage_opportunities", fake_scan)

    out = await spot_perp_arbitrage_scanner(symbol="BTC", params={})
    row = out["spot_perp_arbitrage"]["opportunities"][0]
    assert out["launch_item_id"] == 43
    assert row["gross_spread_only"] is True
    assert row["executable"] is False
    assert row["presented_as_actionable"] is False
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "GROSS_SPREAD_NOT_EXECUTABLE"
    assert out["adaptive_disclosure"]["spot_perp_net_edge_disclosure"]["gross_spread_not_executable_without_net_edge"] is True


@pytest.mark.asyncio
async def test_capability_38_mvrv_blocked_external_without_licensed_source(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_mvrv(symbol):
        return {"ok": True, "z_score": 1.2, "regime": "neutral"}

    async def fake_macro():
        return {"indicators": [{"id": "mvrv", "url": "https://example.com/mvrv"}]}

    monkeypatch.setattr("launch57.edge_ui_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.mvrv_realignment.compute_mvrv_realignment", fake_mvrv)
    monkeypatch.setattr("bd_platform.onchain_hub.lookintobitcoin_macro", fake_macro)

    out = await mvrv_mvrv_z_score_suite(symbol="BTC", params={})
    status = out["mvrv_z_score_suite"]["source_status"]["BTC"]
    assert out["launch_item_id"] == 38
    assert status["blocker"] == "BLOCKED_EXTERNAL"
    assert status["presented_as_live"] is False
    assert status["reference_only"] is True
    assert out["presented_as_live"] is False
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "BLOCKED_EXTERNAL_NO_LICENSED_SOURCE"


@pytest.mark.asyncio
async def test_capability_49_history_only_rejects_behavioral_learning(monkeypatch):
    monkeypatch.setattr(
        "launch57.edge_ui_common.read_decision_history_rows",
        lambda **kwargs: [{"decision_id": "d1"}],
    )

    out = await personal_decision_history(symbol="BTC", params={"behavioral_learning": True})
    assert out["launch_item_id"] == 49
    assert out["success"] is False
    assert out["personal_decision_history"]["decisions"] == []
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "UNSUPPORTED_LEARNING_SCOPE_REJECTED"
    assert out["personal_decision_history"]["history_only"] is True


@pytest.mark.asyncio
async def test_capability_50_mirror_reflective_not_market_evidence(monkeypatch):
    monkeypatch.setattr(
        "discipline_mirror.personal_mirror",
        lambda user_key, limit=20: {
            "private": True,
            "total_answers": 1,
            "hero_deepening": "portfolio_ai",
        },
    )

    out = await discipline_mirror_light(symbol="BTC", params={"user_key": "u1"})
    mirror = out["discipline_mirror"]
    assert out["launch_item_id"] == 50
    assert mirror["reflective_only"] is True
    assert mirror["market_evidence"] is False
    assert mirror["financial_truth"] is False
    assert "hero_deepening" not in mirror
    assert out["adaptive_disclosure"]["discipline_mirror_disclosure"]["reflective_only"] is True


@pytest.mark.asyncio
async def test_capability_52_rejects_parked_registry_injection(monkeypatch):
    monkeypatch.setattr(
        "launch57.edge_ui_common.launch57_library_entries",
        lambda **kwargs: [{"launch_number": 99, "engineering_status": "PASS_ENGINEERING", "launch_name": "bad"}],
    )

    out = await capability_library_search(symbol="BTC", params={"include_parked": True})
    assert out["launch_item_id"] == 52
    assert out["success"] is False
    assert out["capability_library"]["results"] == []
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "UNSUPPORTED_REGISTRY_SCOPE_REJECTED"
    assert out["capability_library"]["no_second_registry"] is True
