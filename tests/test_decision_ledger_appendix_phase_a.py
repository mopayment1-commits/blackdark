"""Launch-57 Phase A — decision ledger recommendation appendix."""

from __future__ import annotations

from typing import Any

import pytest

import decision_ledger_appendix as appendix


def test_appendix_recommendation_row_default_horizon_and_empty_outcome(monkeypatch):
    persisted: list[dict] = []

    def _capture(row: dict) -> None:
        persisted.append(dict(row))

    monkeypatch.setattr(appendix, "_persist", _capture)

    row = appendix.recommendation_row_from_oracle_enrichment(
        {"symbol": "BTC", "verdict": "WAIT", "opportunity_score": 72},
        asset="BTC",
        verdict="WAIT",
        decision_id="dec_test_phase_a_001",
        user_id="user-ref-42",
        tier="pro",
        event_time="2026-10-04T18:00:00+00:00",
    )

    assert row["outcome_horizon"] == "24h"
    assert row["actual_outcome"] == ""
    assert row["label"] == ""

    assert len(persisted) == 1
    assert persisted[0]["outcome_horizon"] == "24h"
    assert persisted[0]["actual_outcome"] == ""


@pytest.mark.asyncio
async def test_resolve_appendix_outcome_empty_when_no_horizon_candle():
    async def _empty_query(*_args: Any, **_kwargs: Any) -> list[dict[str, Any]]:
        return []

    row = {
        "decision_id": "dec_horizon_miss",
        "asset": "BTC",
        "event_time": "2026-10-04T12:00:00+00:00",
        "outcome_horizon": "24h",
        "recommendation": "BUY",
        "actual_outcome": "",
        "label": "",
    }
    resolved = await appendix.resolve_appendix_outcome_from_ohlcv(
        row,
        session=None,
        query_ohlcv=_empty_query,
    )
    assert resolved["actual_outcome"] == ""
    assert resolved["label"] == ""


@pytest.mark.asyncio
async def test_resolve_appendix_outcome_fills_close_and_label_after_24h():
    event_time = "2026-10-04T12:00:00+00:00"
    horizon_time = "2026-10-05T12:00:00+00:00"

    async def _query(
        _session: Any,
        *,
        symbol: str,
        interval: str,
        start_time: Any = None,
        end_time: Any = None,
        limit: int = 100,
        source_slug: str | None = None,
    ) -> list[dict[str, Any]]:
        assert symbol == "BTC"
        assert interval == "1h"
        if end_time is not None:
            return [{"open_time": event_time, "close": "100.0"}]
        if start_time is not None:
            return [{"open_time": horizon_time, "close": "105.0"}]
        return []

    row = {
        "decision_id": "dec_horizon_hit",
        "asset": "BTC",
        "event_time": event_time,
        "outcome_horizon": "24h",
        "recommendation": "BUY",
        "actual_outcome": "",
        "label": "",
    }
    resolved = await appendix.resolve_appendix_outcome_from_ohlcv(
        row,
        session=None,
        query_ohlcv=_query,
    )
    assert resolved["actual_outcome"] == "105.0"
    assert resolved["label"] == "correct"
