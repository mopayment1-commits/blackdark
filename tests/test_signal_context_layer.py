"""Tests — #330-REV Signal Context Layer."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from bd_platform import signal_context_layer as scl


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "signal_context_seed.json"
    seed.write_text(
        json.dumps({
            "panel_version": "1.0",
            "engine_version": "1.0",
            "methodology": "Rule-Based",
            "last_updated": "2026-08-25",
            "tier": "pro",
            "min_reasons": 3,
            "generation_sla_ms": 500,
            "weights": {
                "data_alignment": 0.30,
                "cvd_context": 0.20,
                "funding_context": 0.15,
                "liquidity_context": 0.15,
                "exchange_risk": 0.10,
                "fee_impact": 0.10,
            },
            "weights_version": "1.0",
            "assets": {
                "BTC": {
                    "data_freshness_seconds": 45,
                    "inputs": {
                        "cvd": {
                            "trend": "rising",
                            "pct_vs_baseline": 12.3,
                            "freshness_ms": 120,
                            "timestamp": "2026-08-25T20:56:00+00:00",
                            "source": "CVD Module #232",
                            "agree": True,
                        },
                        "funding": {
                            "rate_pct": -0.008,
                            "z_score": -1.8,
                            "regime": "negative",
                            "freshness_ms": 200,
                            "timestamp": "2026-08-25T20:55:00+00:00",
                            "source": "Funding Feed",
                            "agree": True,
                        },
                        "liquidity": {
                            "depth_change_pct": 8.5,
                            "spread_bps": 2.1,
                            "freshness_ms": 80,
                            "timestamp": "2026-08-25T20:56:30+00:00",
                            "source": "Liquidity Analytics",
                            "agree": True,
                        },
                        "exchange_quality": {
                            "score": 8.2,
                            "exchange": "binance",
                            "freshness_ms": 500,
                            "timestamp": "2026-08-25T20:56:00+00:00",
                            "source": "Exchange Quality #132",
                            "agree": True,
                        },
                        "onchain": {
                            "mvrv_proxy": 1.85,
                            "netflow_direction": "inflow",
                            "freshness_ms": 1500,
                            "timestamp": "2026-08-25T20:54:00+00:00",
                            "source": "On-Chain Metrics",
                            "agree": True,
                        },
                        "social": {
                            "freshness_ms": 360000,
                            "timestamp": "2026-08-25T12:00:00+00:00",
                            "source": "Social Feed",
                            "agree": False,
                            "stale": True,
                        },
                        "bot_activity": {
                            "spoofing_detected": False,
                            "freshness_ms": 300,
                            "timestamp": "2026-08-25T20:56:00+00:00",
                            "source": "Bot Activity #721",
                            "agree": True,
                        },
                    },
                    "fee_impact": {
                        "gas_estimate_usd": 2.40,
                        "funding_1h_usd": -0.80,
                        "slippage_estimate_pct": 0.12,
                        "net_after_fees_pct": 0.68,
                        "fee_db_version": "1.3",
                    },
                },
                "ETH": {
                    "data_freshness_seconds": 60,
                    "inputs": {
                        "cvd": {
                            "trend": "flat",
                            "pct_vs_baseline": 1.2,
                            "freshness_ms": 150,
                            "timestamp": "2026-08-25T20:56:00+00:00",
                            "source": "CVD Module #232",
                            "agree": True,
                        },
                        "funding": {
                            "rate_pct": 0.002,
                            "z_score": 0.3,
                            "regime": "neutral",
                            "freshness_ms": 220,
                            "timestamp": "2026-08-25T20:55:00+00:00",
                            "source": "Funding Feed",
                            "agree": True,
                        },
                    },
                    "fee_impact": {
                        "gas_estimate_usd": 1.80,
                        "funding_1h_usd": 0.10,
                        "slippage_estimate_pct": 0.18,
                        "net_after_fees_pct": -0.05,
                        "fee_db_version": "1.3",
                        "negative_fee_context": True,
                    },
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(scl, "_SEED_PATH", seed)
    return seed


@pytest.mark.asyncio
async def test_rule_based_documented(isolated_seed):
    panel = await scl.build_context_panel("BTC")
    assert panel["ok"] is True
    assert "Rule-based" in panel["signal_strength"]["methodology"]
    assert "Weights documented" in panel["signal_strength"]["methodology"]
    assert "Context Panel v1.0" in panel["panel_version_display"]


@pytest.mark.asyncio
async def test_data_alignment_score(isolated_seed):
    panel = await scl.build_context_panel("BTC")
    align = panel["data_alignment"]
    assert "%" in align["score"]
    assert "/" in align["sources_agree"]
    assert len(align["sources"]) >= 3


@pytest.mark.asyncio
async def test_three_reasons_with_source_timestamp_confidence(isolated_seed):
    panel = await scl.build_context_panel("BTC")
    reasons = panel["three_reasons"]
    assert len(reasons) >= 3
    for r in reasons:
        assert r.get("source")
        assert r.get("timestamp")
        assert r.get("confidence") in ("high", "medium", "low")


@pytest.mark.asyncio
async def test_insufficient_data_context(isolated_seed):
    panel = await scl.build_context_panel("ETH")
    assert panel["insufficient_data_context"] is True
    assert "Insufficient Data Context" in panel["insufficient_display"]
    assert "2/3" in panel["insufficient_display"] or "1/3" in panel["insufficient_display"]


@pytest.mark.asyncio
async def test_risk_flags_numeric(isolated_seed):
    panel = await scl.build_context_panel("BTC")
    flags = panel["risk_flags"]
    assert "/10" in flags["total_score"]
    assert len(flags["flags"]) >= 3
    assert any(f["label"] == "Spoofing Detected" for f in flags["flags"])


@pytest.mark.asyncio
async def test_fee_db_impact(isolated_seed):
    panel = await scl.build_context_panel("BTC")
    fee = panel["fee_impact"]
    assert fee["fee_db_feature_id"] == 130
    assert "net_after_fees" in fee
    assert "Fee estimates are approximate" in fee["disclaimer"]


@pytest.mark.asyncio
async def test_negative_fee_context(isolated_seed):
    panel = await scl.build_context_panel("ETH")
    assert panel["fee_impact"]["negative_fee_context"] is True
    assert "High Cost Environment" in panel["fee_impact"]["context_note"]


@pytest.mark.asyncio
async def test_not_recommendation(isolated_seed):
    panel = await scl.build_context_panel("BTC")
    assert panel["not_a_recommendation"] is True
    assert panel["not_buy_sell_signal"] is True
    assert "Buy" not in str(panel)
    assert "investment advice" in panel["disclaimer"]["text"].lower()


@pytest.mark.asyncio
async def test_disclaimer_non_hideable(isolated_seed):
    panel = await scl.build_context_panel("BTC")
    assert panel["disclaimer"]["collapsible"] is False
    assert panel["disclaimer"]["hideable"] is False
    assert panel["disclaimer_top"] == panel["disclaimer_bottom"]


@pytest.mark.asyncio
async def test_no_look_ahead(isolated_seed):
    panel = await scl.build_context_panel("BTC")
    assert panel["no_look_ahead"] is True


@pytest.mark.asyncio
async def test_generation_sla(isolated_seed):
    panel = await scl.build_context_panel("BTC")
    assert panel["sla_met"] is True
    assert panel["latency_ms"] <= 500


@pytest.mark.asyncio
async def test_not_standalone(isolated_seed):
    status = scl.signal_context_layer_status()
    assert status["standalone"] is False
    assert status["feature_id"] == 330
    assert "Market Radar" in status["integrated_surfaces"]


@pytest.mark.asyncio
async def test_portfolio_surface(isolated_seed):
    panel = await scl.build_portfolio_context_panel("BTC", portfolio_id="pf-1")
    assert panel["surface"] == "portfolio_ai"
    assert panel["portfolio_id"] == "pf-1"


@pytest.mark.asyncio
async def test_api_routes(isolated_seed, monkeypatch):
    monkeypatch.setattr(
        "bd_platform.free_market_data.binance_futures_snapshot",
        AsyncMock(return_value={"funding_rate_pct": -0.01, "timestamp": "2026-08-25T20:56:00+00:00"}),
    )
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/signal-context/status").status_code == 200
    status = c.get("/api/platform/market-radar/signal-context/status").json()
    assert status["feature_id"] == 330
    panel = c.get("/api/platform/market-radar/signal-context?asset=BTC")
    assert panel.status_code == 200
    assert panel.json()["signal_strength"]["score"].endswith("/10")
    assert c.get("/api/platform/portfolio/signal-context?asset=BTC").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/signal_context_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 330
    assert seed["standalone"] is False
    assert "BTC" in seed["assets"]
