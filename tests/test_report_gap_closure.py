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

    router_src = inspect.getsource(rr.predict_direction_regime_aware)
    artifact_src = inspect.getsource(rr._artifact_prediction)
    assert "_artifact_prediction" in router_src
    assert "predict_with_regime_artifact" in artifact_src
    assert "per_regime_artifact" in router_src or "inference_path" in router_src


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

    startup_src = inspect.getsource(so.run_background_startup)
    loop_src = inspect.getsource(so._glass_box_seal_loop)
    assert "_start_glass_box" in startup_src
    assert "maybe_auto_seal_from_oracle" in loop_src
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
    eval_src = inspect.getsource(ai_oracle.evaluate_opportunity)
    helper_src = inspect.getsource(ai_oracle._attach_evaluation_compliance)
    assert "_attach_evaluation_compliance" in eval_src
    assert "compliance_footer" in helper_src


def test_voice_attaches_compliance():
    import voice_service

    cmd_src = inspect.getsource(voice_service.process_voice_command)
    out_src = inspect.getsource(voice_service._out)
    assert "_out(" in cmd_src or "return _out" in cmd_src or "_out({" in inspect.getsource(voice_service)
    assert "compliance_footer" in out_src
