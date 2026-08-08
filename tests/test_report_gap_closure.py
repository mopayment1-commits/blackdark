"""Tests for remaining binding-report product gaps (non-human)."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime

import pytest


def test_regime_artifact_loader_exists():
    from ml.regime_models import load_regime_predictor, predict_with_regime_artifact

    assert callable(load_regime_predictor)
    assert callable(predict_with_regime_artifact)


def test_regime_router_prefers_artifact_path():
    import ml.regime_router as rr

    src = inspect.getsource(rr.predict_direction_regime_aware)
    assert "predict_with_regime_artifact" in src
    assert "per_regime_artifact" in src or "inference_path" in src


def test_whale_enrich_wires_derivatives():
    import whale_signal_classifier as w

    src = inspect.getsource(w._derivatives_for_asset) + inspect.getsource(w.enrich_whale_narratives)
    assert "fetch_onchain_derivatives_mesh" in src
    assert "headline" in src


def test_locked_auto_seal_exists():
    from locked_predictions import maybe_auto_seal_from_oracle

    assert callable(maybe_auto_seal_from_oracle)


def test_startup_has_glass_box_cadence():
    import startup_orchestrator as so

    src = inspect.getsource(so.run_background_startup)
    assert "maybe_auto_seal_from_oracle" in src
    assert "glass_box_task" in inspect.getsource(so.RuntimeState)


@pytest.mark.asyncio
async def test_monthly_losing_groups_by_month(monkeypatch):
    import monthly_losing_report as mlr

    async def fake_rows(limit=800, include_synthetic=False):
        return [
            {"id": 1, "label": "incorrect", "asset": "BTC", "timestamp": "2026-08-01T00:00:00+00:00"},
            {"id": 2, "label": "partial", "asset": "ETH", "timestamp": "2026-07-15T00:00:00+00:00"},
            {"id": 3, "label": "correct", "asset": "SOL", "timestamp": "2026-08-02T00:00:00+00:00"},
        ]

    monkeypatch.setattr(
        "database.fetch_labeled_oracle_predictions",
        fake_rows,
        raising=False,
    )
    import database

    monkeypatch.setattr(database, "fetch_labeled_oracle_predictions", fake_rows)
    report = await mlr.build_monthly_losing_report(limit=10)
    assert "months" in report
    assert report["month"] == datetime.now(UTC).strftime("%Y-%m")
    assert report["total_labeled_misses_in_window"] == 2


def test_chat_and_oracle_attach_compliance():
    import ai_oracle
    import chat_service

    assert "compliance_footer" in inspect.getsource(chat_service.process_chat)
    assert "compliance_footer" in inspect.getsource(ai_oracle.evaluate_opportunity)


def test_voice_attaches_compliance():
    import voice_service

    src = inspect.getsource(voice_service.process_voice_command)
    assert "compliance_footer" in src
