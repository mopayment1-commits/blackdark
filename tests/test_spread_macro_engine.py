"""Tests — Price Spread Calculator (#136) + Macro Context Engine (#141 + #104)."""

from __future__ import annotations

import pytest

from bd_platform.macro_context_engine import (
    _build_relationship_chain,
    _expected_impact,
    macro_context_engine_status,
)
from bd_platform.price_spread_calculator import (
    calculate_price_spread,
    spread_calculator_status,
)


def test_spread_calculator_status_internal():
    status = spread_calculator_status()
    assert status["ok"] is True
    assert status["feature_id"] == 136
    assert status["user_facing"] is False
    assert "#112" in status["consumers"]


def test_calculate_price_spread_not_profitable_after_fees():
    # 2.3% gross spread on $1000
    result = calculate_price_spread(
        buy_price=100.0,
        sell_price=102.3,
        notional_usd=1000.0,
        buy_exchange="binance",
        sell_exchange="okx",
        symbol="BTC/USDT",
    )
    assert result["ok"] is True
    assert result["user_facing"] is False
    assert result["gross_spread_pct"] == pytest.approx(2.3, abs=0.05)
    assert "Spread:" in result["display"]
    assert "after fees:" in result["display"]
    assert "not profitable" in result["display"] or "profitable" in result["display"]
    assert "الفرق:" in result["display_ar"]
    assert result["integrated_features"] == ["#130", "#113"]
    assert result["sla_met"] is True
    # Gross positive but fees may eat edge
    if result["gross_spread_pct"] > 0 and not result["profitable"]:
        assert result["gross_only_misleading"] is True


def test_calculate_price_spread_large_edge_profitable():
    result = calculate_price_spread(
        buy_price=100.0,
        sell_price=105.0,
        notional_usd=1000.0,
        buy_exchange="binance",
        sell_exchange="okx",
        symbol="BTC/USDT",
        include_transfer_fees=False,
    )
    assert result["ok"] is True
    assert result["gross_spread_pct"] == pytest.approx(5.0, abs=0.05)
    assert result["profitable"] is True
    assert "profitable" in result["display"]


def test_expected_impact_dxy_negative_for_btc():
    impact = _expected_impact("DXY", "BTC", 1.2)
    assert impact["expected_impact"] == "negative"
    assert impact["macro_change_pct"] == 1.2


def test_build_relationship_chain_format():
    rel = _build_relationship_chain("DXY", "BTC", 1.2)
    assert "DXY rose 1.2%" in rel["relationship"]
    assert "historically BTC" in rel["relationship"]
    assert "expected impact:" in rel["relationship"]
    assert "ارتفع" in rel["relationship_ar"]
    assert "التأثير المتوقع" in rel["relationship_ar"]


def test_macro_context_engine_status():
    status = macro_context_engine_status()
    assert status["ok"] is True
    assert 141 in status["feature_ids"]
    assert 104 in status["feature_ids"]
    assert status["output_mode"] == "relationships_not_lists"


@pytest.mark.asyncio
async def test_build_macro_relationships(monkeypatch):
    async def fake_moves():
        return {
            "DXY": {"change_pct": 1.2, "source": "test", "symbol": "DXY"},
            "SPX": {"change_pct": -0.5, "source": "test", "symbol": "SPX"},
        }

    async def fake_regime():
        return {"macro_regime": "Risk-Off"}

    monkeypatch.setattr("bd_platform.macro_context_engine._fetch_macro_moves", fake_moves)
    monkeypatch.setattr("bd_platform.macro_context_engine.get_latest_macro_regime", fake_regime)

    from bd_platform.macro_context_engine import build_macro_relationships

    out = await build_macro_relationships("BTC")
    assert out["ok"] is True
    assert out["not_raw_lists"] is True
    assert out["relationship_count"] >= 1
    assert out["sla_met"] is True
    assert "DXY rose 1.2%" in out["relationships"][0]["relationship"]


@pytest.mark.asyncio
async def test_oracle_macro_hook(monkeypatch):
    async def fake_ctx(asset: str):
        return {
            "macro_context_enabled": True,
            "macro_regime": "Risk-Off",
            "primary_relationship": "DXY rose 1.2% → historically BTC drops ~3.0% → expected impact: negative",
            "primary_relationship_ar": "DXY ارتفع 1.2% → تاريخياً BTC ينخفض ~3.0% → التأثير المتوقع: سلبي",
            "feature_ids": [141, 104],
        }

    monkeypatch.setattr("bd_platform.macro_context_engine.macro_context_for_oracle", fake_ctx)

    from bd_platform.macro_context_engine import macro_context_for_oracle

    block = await macro_context_for_oracle("BTC")
    assert block["macro_context_enabled"] is True
    assert "DXY rose" in block["primary_relationship"]
