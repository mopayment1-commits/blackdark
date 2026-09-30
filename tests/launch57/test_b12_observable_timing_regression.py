"""Regression — B12 timing from observable-only suspicious activity flags (#56)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from launch57.temporal_common import to_rfc3339, utc_now


def _ts(offset_sec: float = 0) -> str:
    return to_rfc3339(utc_now() + timedelta(seconds=offset_sec))


async def _fake_spine(symbol, params):
    return {
        "symbol": symbol,
        "live_eligible": True,
        "freshness_state": "FRESH",
        "data_spine": {"timestamp": _ts(0)},
        "presented_as_live": True,
    }


@pytest.mark.asyncio
async def test_observable_only_flags_attach_b12_timing(monkeypatch):
    import bd_platform.derivatives_onchain_intelligence_layer as fraud_layer
    from launch57.smart_money_batch3 import suspicious_activity_flags

    monkeypatch.setattr("launch57.smart_money_batch3.load_decision_spine", _fake_spine)
    monkeypatch.setattr(
        fraud_layer,
        "fraud_suspicious_activity_297",
        lambda seed: {
            "flags": [{"id": "f1", "source_age_ms": 1000, "last_update_time": _ts(0)}],
        },
    )
    out = await suspicious_activity_flags(symbol="BTC", params={})
    assert out["due_diligence_risk_timing"]["last_update_time"]
    assert out["presented_as_current_only"] is True
