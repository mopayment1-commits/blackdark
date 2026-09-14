"""Temporal P0 API runtime contract tests."""

from __future__ import annotations

import os
import socket
import uuid

import pytest
from fastapi import HTTPException


POSTGRES_URL = os.getenv(
    "BLACKDARK_TEST_DATABASE_URL",
    "postgresql://blackdark:blackdark@127.0.0.1:5432/blackdark_clean",
)


def _postgres_reachable() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 5432), timeout=1.5):
            return True
    except OSError:
        return False


async def _prepare_engine(monkeypatch) -> None:
    import config
    import blackdark.data.db as db_module
    from blackdark.data.db import init_data_engine

    monkeypatch.setattr(config, "DATABASE_URL", POSTGRES_URL)
    os.environ["DATABASE_URL"] = POSTGRES_URL
    db_module._engine = None
    db_module._session_factory = None
    db_module._schema_ready = False
    db_module._bootstrapped = False
    await init_data_engine()


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres unavailable")
async def test_walk_forward_contamination_returns_422_not_500(monkeypatch) -> None:
    from api.routers.temporal import WalkForwardRequest, evaluate_walk_forward

    await _prepare_engine(monkeypatch)
    body = WalkForwardRequest(
        dataset_id=f"ds-api-contam-{uuid.uuid4().hex[:8]}",
        samples=[{"event_time": "2026-01-15T00:30:00Z", "value": 1}],
        series_start="2026-01-15T00:00:00Z",
        series_end="2026-01-15T08:00:00Z",
        train_duration_seconds=7200,
        eval_duration_seconds=3600,
        step_seconds=3600,
    )
    first = await evaluate_walk_forward(body)
    assert first["fold_count"] >= 1

    with pytest.raises(HTTPException) as exc:
        await evaluate_walk_forward(body)
    assert exc.value.status_code == 422
    detail = exc.value.detail
    assert detail["error_code"] == "EVALUATION_CONTAMINATION_REJECTED"


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres unavailable")
async def test_walk_forward_multi_fold_api_returns_200(monkeypatch) -> None:
    from api.routers.temporal import WalkForwardRequest, evaluate_walk_forward

    await _prepare_engine(monkeypatch)
    body = WalkForwardRequest(
        dataset_id=f"ds-api-wf-{uuid.uuid4().hex[:8]}",
        samples=[
            {"event_time": "2026-01-20T00:30:00Z", "value": 1},
            {"event_time": "2026-01-20T01:30:00Z", "value": 2},
            {"event_time": "2026-01-20T02:30:00Z", "value": 3},
            {"event_time": "2026-01-20T03:30:00Z", "value": 4},
            {"event_time": "2026-01-20T04:30:00Z", "value": 5},
            {"event_time": "2026-01-20T05:30:00Z", "value": 6},
        ],
        series_start="2026-01-20T00:00:00Z",
        series_end="2026-01-20T08:00:00Z",
        train_duration_seconds=7200,
        eval_duration_seconds=3600,
        step_seconds=3600,
    )
    result = await evaluate_walk_forward(body)
    assert result["fold_count"] >= 2


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres unavailable")
async def test_temporal_metrics_endpoint_exposes_counters(monkeypatch) -> None:
    from api.routers.temporal import temporal_metrics

    await _prepare_engine(monkeypatch)
    payload = await temporal_metrics()
    assert "temporal_spine_runs_total" in payload
    assert "temporal_api_requests_total" in payload
