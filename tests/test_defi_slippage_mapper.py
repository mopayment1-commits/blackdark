"""Tests — #228 DeFi Slippage Mapper."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import defi_slippage_mapper as dsm


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "defi_slippage_mapper_seed.json"
    seed.write_text(
        json.dumps({
            "feature_id": 228,
            "last_updated_utc": "2026-08-25T22:00:00+00:00",
            "wash_noise_policy": {
                "minimum_volume_usd": 1000,
                "bot_filtered": True,
                "display": "Excludes: Wash trades | Threshold: $1,000 minimum volume | Bot-filtered: Yes",
            },
            "methodology": {
                "version": "1.2",
                "calculation": "AMM formula",
                "source": "On-chain events",
                "last_revised": "2026-08-25",
                "display": "Slippage Methodology v1.2 | Calculation: AMM formula | Source: On-chain events | Last Updated: 2026-08-25",
            },
            "protocols": {
                "uniswap-v3": {
                    "id": "uniswap-v3", "name": "Uniswap v3", "type": "AMM", "chain": "ethereum",
                    "assets": ["ETH"], "tvl_usd": 4200000000,
                    "slippage_by_size": {"$1K": 0.1, "$10K": 0.5, "$100K": 2.3, "$1M": 8.5},
                    "fee_impact": {"gross_apy_pct": 8.5, "gas_cost_pct": 0.4, "slippage_10k_pct": 0.3, "impermanent_loss_30d_pct": -1.2},
                    "risk_flags": {"score": 3, "max_score": 10, "impermanent_loss_risk": "Medium", "smart_contract_risk": "Low"},
                    "data_context": {"liquidity_depth": "Sufficient", "slippage_assessment": "Acceptable", "max_comfortable_size_usd": 50000},
                    "historical": {"avg_slippage_1y_pct": 0.3, "volatility_pct": 12.5, "history_days": 400},
                },
                "curve": {
                    "id": "curve", "name": "Curve", "type": "AMM", "chain": "ethereum",
                    "assets": ["ETH"], "tvl_usd": 3800000000,
                    "slippage_by_size": {"$1K": 0.05, "$10K": 0.2, "$100K": 0.8, "$1M": 3.2},
                    "fee_impact": {"gross_apy_pct": 5.8, "gas_cost_pct": 0.5, "slippage_10k_pct": 0.15, "impermanent_loss_30d_pct": -0.5},
                    "risk_flags": {"score": 2, "max_score": 10, "impermanent_loss_risk": "Low", "smart_contract_risk": "Low"},
                    "data_context": {"liquidity_depth": "Sufficient", "slippage_assessment": "Low", "max_comfortable_size_usd": 500000},
                    "historical": {"avg_slippage_1y_pct": 0.2, "volatility_pct": 8.1, "history_days": 520},
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(dsm, "_SEED_PATH", seed)
    return seed


def test_wash_noise_policy(isolated_seed):
    policy = dsm.build_wash_noise_policy(json.loads(isolated_seed.read_text()))
    assert "Wash trades" in policy["display"]
    assert policy["minimum_volume_usd"] == 1000
    assert policy["bot_filtered"] is True


def test_slippage_per_trade_size(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    proto = seed["protocols"]["uniswap-v3"]
    result = dsm.build_slippage_by_size(proto)
    assert "For $1K: 0.1%" in result["display"]
    assert "For $10K: 0.5%" in result["display"]
    assert "For $100K: 2.3%" in result["display"]
    assert "For $1M: 8.5%" in result["display"]


def test_slippage_insufficient_liquidity(isolated_seed):
    result = dsm.build_slippage_by_size({"slippage_by_size": {"$1M": None}})
    assert "N/A (insufficient liquidity)" in result["display"]


def test_fee_impact_with_fee_db(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    fee = dsm.build_fee_impact(seed["protocols"]["uniswap-v3"])
    assert fee["fee_db_integrated"] is True
    assert "Gross APY:" in fee["display"]
    assert "Net after fees:" in fee["display"]
    assert fee["net_after_fees_pct"] == pytest.approx(6.6, abs=0.1)


def test_risk_flags_not_vague(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    flags = dsm.build_risk_flags(seed["protocols"]["uniswap-v3"])
    assert "Risk Flags:" in flags["display"]
    assert "Impermanent Loss Risk:" in flags["display"]
    assert "Smart Contract Risk:" in flags["display"]
    assert "low risk" not in flags["display"].lower()
    assert flags["no_vague_risk_label"] is True


def test_data_context_not_opportunity(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    ctx = dsm.build_data_context(seed["protocols"]["uniswap-v3"])
    assert "Liquidity Depth:" in ctx["display"]
    assert ctx["not_investment_opportunity"] is True
    assert "opportunity" not in ctx["display"].lower() or "not_investment" in dir(ctx)


def test_historical_1_year(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    hist = dsm.build_historical_trend(seed["protocols"]["curve"])
    assert hist["history_meets_1y"] is True
    assert "Slippage trend (1Y):" in hist["display"]
    assert "Volatility:" in hist["display"]


def test_no_best_opportunity_language(isolated_seed):
    dash = dsm.build_defi_slippage_dashboard("ETH")
    text = json.dumps(dash)
    assert "best opportunity" not in text.lower()
    assert "ادخل" not in text
    assert dash["no_best_opportunity_language"] is True
    assert "Protocol Comparison:" in dash["comparison"]["display"]


def test_update_schedule_15_min(isolated_seed):
    dash = dsm.build_defi_slippage_dashboard("ETH")
    sched = dash["update_schedule"]
    assert sched["interval_minutes"] == 15
    assert "Last Updated:" in sched["display"]
    assert "Next Update:" in sched["display"]
    assert sched["no_real_time_claim"] is True


def test_disclaimer_non_hideable(isolated_seed):
    dash = dsm.build_defi_slippage_dashboard("ETH")
    assert dash["disclaimer_hideable"] is False
    assert "Not investment advice" in dash["disclaimer"]


def test_methodology_versioned(isolated_seed):
    dash = dsm.build_defi_slippage_dashboard("ETH")
    assert "Slippage Methodology v1.2" in dash["methodology"]["display"]
    assert dash["methodology"]["accuracy_tolerance_pct"] == 0.1


def test_data_alerts_not_yield_opportunities(isolated_seed):
    protocols = [
        {"id": "test", "name": "Test Protocol", "slippage_by_size": {"$100K": 6.5}},
    ]
    alerts = dsm.build_data_alerts(protocols, threshold_pct=5.0)
    assert len(alerts) == 1
    assert "Slippage on Test Protocol exceeded" in alerts[0]["display"]
    assert alerts[0]["not_yield_opportunity"] is True
    assert "yield opportunity" not in alerts[0]["display"].lower()


def test_protocol_coverage():
    full = json.loads(Path("data/defi_slippage_mapper_seed.json").read_text(encoding="utf-8"))
    assert len(full["protocols"]) >= 10


def test_get_protocol_slippage(isolated_seed):
    result = dsm.get_protocol_slippage("uniswap-v3")
    assert result is not None
    assert result["name"] == "Uniswap v3"
    assert dsm.get_protocol_slippage("unknown") is None


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/defi/slippage-mapper/status").status_code == 200
    dash = c.get("/api/platform/market-radar/defi/slippage-mapper/dashboard?asset=ETH")
    assert dash.status_code == 200
    assert dash.json()["feature_id"] == 228
    proto = c.get("/api/platform/market-radar/defi/slippage-mapper/protocol/uniswap-v3")
    assert proto.status_code == 200
    assert c.get("/api/platform/market-radar/defi/slippage-mapper/protocol/fake").status_code == 404
