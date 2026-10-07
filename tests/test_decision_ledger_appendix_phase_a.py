"""Launch-57 Phase A — decision ledger recommendation appendix."""

from __future__ import annotations

import json
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


def test_appendix_ingestion_timestamp_distinct_from_event_time(monkeypatch):
    monkeypatch.setattr(appendix, "_persist", lambda _row: None)
    fixed_event = "2020-01-01T00:00:00+00:00"
    row = appendix.recommendation_row_from_oracle_enrichment(
        {"symbol": "BTC", "verdict": "WAIT"},
        asset="BTC",
        verdict="WAIT",
        decision_id="dec_ingest_ts",
        user_id="u1",
        tier="pro",
        event_time=fixed_event,
    )
    assert row["ingestion_timestamp"]
    assert row["ingestion_timestamp"] != fixed_event


def test_appendix_no_action_flag_for_wait_and_non_wait(monkeypatch):
    monkeypatch.setattr(appendix, "_persist", lambda _row: None)
    wait_row = appendix.recommendation_row_from_oracle_enrichment(
        {"symbol": "BTC", "verdict": "WAIT"},
        asset="BTC",
        verdict="WAIT",
        decision_id="dec_wait",
        user_id="u1",
        tier="pro",
        event_time="2026-10-04T18:00:00+00:00",
    )
    buy_row = appendix.recommendation_row_from_oracle_enrichment(
        {"symbol": "BTC", "verdict": "BUY", "decision_action": "BUY"},
        asset="BTC",
        verdict="BUY",
        decision_id="dec_buy",
        user_id="u1",
        tier="pro",
        event_time="2026-10-04T18:00:00+00:00",
    )
    assert wait_row["recommendation"] == "WAIT"
    assert wait_row["no_action"] is True
    assert buy_row["recommendation"] == "BUY"
    assert buy_row["no_action"] is False


@pytest.mark.asyncio
async def test_resolve_incorrect_sets_failure_reason_with_closes():
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
        if end_time is not None:
            return [{"open_time": event_time, "close": "100.0"}]
        if start_time is not None:
            return [{"open_time": horizon_time, "close": "80.0"}]
        return []

    row = {
        "decision_id": "dec_incorrect",
        "asset": "BTC",
        "event_time": event_time,
        "outcome_horizon": "24h",
        "recommendation": "BUY",
    }
    resolved = await appendix.resolve_appendix_outcome_from_ohlcv(
        row, session=None, query_ohlcv=_query
    )
    assert resolved["label"] == "incorrect"
    assert resolved["failure_reason"] == "score_verdict_accuracy|event_close=100.0|horizon_close=80.0"
    assert resolved["candle_source"] == "query_ohlcv"
    assert resolved["candle_interval"] == "1h"


@pytest.mark.asyncio
async def test_resolve_correct_keeps_failure_reason_empty():
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
        if end_time is not None:
            return [{"open_time": event_time, "close": "100.0"}]
        if start_time is not None:
            return [{"open_time": horizon_time, "close": "105.0"}]
        return []

    row = {
        "asset": "BTC",
        "event_time": event_time,
        "outcome_horizon": "24h",
        "recommendation": "BUY",
    }
    resolved = await appendix.resolve_appendix_outcome_from_ohlcv(
        row, session=None, query_ohlcv=_query
    )
    assert resolved["label"] == "correct"
    assert resolved["failure_reason"] == ""


@pytest.mark.asyncio
async def test_resolve_no_horizon_candle_keeps_candle_fields_empty():
    async def _empty_query(*_args: Any, **_kwargs: Any) -> list[dict[str, Any]]:
        return []

    row = {
        "asset": "BTC",
        "event_time": "2026-10-04T12:00:00+00:00",
        "outcome_horizon": "24h",
        "recommendation": "BUY",
        "candle_source": "",
        "candle_interval": "",
    }
    resolved = await appendix.resolve_appendix_outcome_from_ohlcv(
        row, session=None, query_ohlcv=_empty_query
    )
    assert resolved["candle_source"] == ""
    assert resolved["candle_interval"] == ""


def test_load_appendix_rows_returns_persisted_row(tmp_path, monkeypatch):
    target = tmp_path / "decision_ledger_recommendation_appendix.jsonl"
    monkeypatch.setattr(appendix, "appendix_write_path", lambda: target)

    def _persist(row: dict) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    monkeypatch.setattr(appendix, "_persist", _persist)

    appendix.recommendation_row_from_oracle_enrichment(
        {"symbol": "BTC", "verdict": "WAIT"},
        asset="BTC",
        verdict="WAIT",
        decision_id="dec_query_load",
        user_id="u1",
        tier="pro",
        event_time="2026-10-04T18:00:00+00:00",
    )
    rows = appendix.load_appendix_rows_with_outcomes()
    assert len(rows) == 1
    assert rows[0]["decision_id"] == "dec_query_load"
    assert rows[0]["actual_outcome"] == ""
    assert rows[0]["label"] == ""
