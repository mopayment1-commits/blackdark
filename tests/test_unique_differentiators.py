"""Unique differentiators: Net-Edge Truth, Half-Life, Signal Registry, Personas, Evidence Pack."""

from __future__ import annotations

import pytest


def test_net_edge_truth_rejects_stale_thin_edge():
    from net_edge_truth import compute_net_edge_truth

    truth = compute_net_edge_truth(
        {
            "net_profit_usdt": 0.01,
            "quote_amount": 1000,
            "total_slippage_bps": 40,
            "withdrawal_fee_usdt": 1.0,
            "quote_age_ms": 5000,
            "estimated_recipients": 40,
        }
    )
    assert truth["enabled"] is True
    assert truth["reject"] is True
    assert truth["truth_score"] < 55
    assert "residual_edge_below_threshold" in truth["reasons"] or "stale_quote_latency" in truth["reasons"]


def test_net_edge_truth_passes_fresh_executable():
    from net_edge_truth import apply_truth_gate_to_score, compute_net_edge_truth

    truth = compute_net_edge_truth(
        {
            "net_profit_usdt": 2.5,
            "quote_amount": 500,
            "total_slippage_bps": 3,
            "withdrawal_fee_usdt": 0.05,
            "trading_fees_usdt": 0.2,
            "quote_age_ms": 120,
            "estimated_recipients": 2,
            "flywheel_net_after_crowd_usd": 2.1,
        }
    )
    assert truth["pass"] is True
    assert truth["truth_score"] >= 55
    assert apply_truth_gate_to_score(80.0, truth) == 80.0


def test_opportunity_half_life_model():
    from opportunity_tracker import estimate_opportunity_half_life, expected_half_life_seconds

    half = expected_half_life_seconds("cross_exchange", "BTC")
    assert half > 0
    est = estimate_opportunity_half_life(
        {"kind": "cross_exchange", "asset": "BTC"},
        live_duration_seconds=half * 0.5,
    )
    assert est["remaining_seconds"] > 0
    assert 0 <= est["disappearance_probability"] <= 1
    assert est["urgency"] in {"critical", "high", "normal"}


def test_signal_registry_roundtrip(tmp_path, monkeypatch):
    import signal_registry as sr

    monkeypatch.setattr(sr, "_PATH", tmp_path / "signals.jsonl")
    monkeypatch.setattr(sr, "_SIGNALS", {})

    row = sr.register_signal(
        signal_type="cross_exchange",
        asset="ETH",
        features={"score": 71, "truth": 66},
        score=71,
        verdict="Buy Now",
        label="pending",
    )
    assert row["signal_id"]
    assert row["features_hash"]
    got = sr.get_signal(row["signal_id"])
    assert got["asset"] == "ETH"
    resolved = sr.resolve_signal(row["signal_id"], "correct")
    assert resolved["label"] == "correct"
    stats = sr.registry_stats()
    assert stats["total_in_memory"] >= 1
    assert stats["moat_claim"] == "sovereign_labeled_signal_lexicon"


def test_persona_clarity_all_segments():
    from persona_clarity import build_persona_clarity

    card = build_persona_clarity(
        asset="BTC",
        score=68,
        verdict="Do Not Touch",
        payload={
            "market_regime": "panic",
            "net_edge_truth": {"truth_score": 40, "reject": True},
            "opportunity_half_life": {
                "expected_half_life_seconds": 12,
                "remaining_seconds": 3,
                "disappearance_probability": 0.8,
            },
            "dimension_conflict": {"veto": False},
        },
        net_profit_usdt=0.05,
    )
    assert card["action"] == "WAIT"
    for key in ("retail", "pro", "whale", "fund", "acquirer"):
        assert "ar" in card["personas"][key]
        assert "en" in card["personas"][key]


@pytest.mark.asyncio
async def test_evaluate_opportunity_attaches_differentiators():
    from types import SimpleNamespace

    from ai_oracle import evaluate_opportunity

    opp = SimpleNamespace(
        symbol="BTC/USDT",
        net_profit_usdt=1.25,
        net_profit_percent=0.25,
        total_slippage_bps=4.0,
        gross_spread_bps=18.0,
        quote_amount=500.0,
        buy_exchange="binance",
        sell_exchange="okx",
        withdrawal_fee_usdt=0.1,
        change_24h=1.2,
        price=65000.0,
    )
    evaluated = await evaluate_opportunity(opp, "cross_exchange")
    assert "net_edge_truth" in evaluated.payload
    assert "opportunity_half_life" in evaluated.payload
    assert "persona_clarity" in evaluated.payload
    assert evaluated.payload.get("signal_registry", {}).get("signal_id")


@pytest.mark.asyncio
async def test_acquirer_evidence_pack_shape():
    from acquirer_evidence_pack import build_acquirer_evidence_pack

    pack = await build_acquirer_evidence_pack()
    assert "differentiators" in pack
    assert len(pack["differentiators"]) >= 8
    assert "sections" in pack
    assert "public_accuracy" in pack["sections"]
    assert "signal_registry" in pack["sections"]
    assert "net_edge_truth" in pack["sections"]
    assert pack["committee_checklist"]
