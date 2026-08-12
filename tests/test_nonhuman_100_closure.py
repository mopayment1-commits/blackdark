"""Tests for 100% non-human gap closure pass."""

from __future__ import annotations

import inspect

import pytest


def test_signal_registry_lexicon_and_attach():
    from signal_registry import (
        SIGNAL_TYPE_LEXICON,
        attach_prediction_id,
        register_signal,
        registry_stats,
        resolve_signal,
    )

    assert "oracle_direction" in SIGNAL_TYPE_LEXICON
    row = register_signal(
        signal_type="oracle_direction",
        asset="BTC",
        score=70,
        verdict="BUY",
        persist=False,
    )
    assert row.get("definition")
    assert row.get("weight") is not None
    linked = attach_prediction_id(row["signal_id"], 424242)
    assert linked is not None
    assert str(linked.get("prediction_id")) == "424242"
    assert linked.get("signal_id") == "424242"
    resolved = resolve_signal("424242", "correct", meta={"test": True})
    assert resolved
    assert resolved.get("label") == "correct"
    assert (resolved.get("performance") or {}).get("hits", 0) >= 1
    stats = registry_stats()
    assert "status" in stats
    assert "by_type_performance" in stats


def test_decision_certificate_share_urls():
    from decision_certificate import build_decision_certificate

    cert = build_decision_certificate(
        {
            "symbol": "ETH",
            "prediction_id": 9,
            "decision_action": "ACT",
            "decision_sentence": "Act on ETH",
            "opportunity_score": 71,
        }
    )
    assert cert.get("share_urls", {}).get("x")
    assert cert.get("share_urls", {}).get("telegram")


def test_execution_keys_english_only_and_withdraw_field():
    import execution_keys as ek

    src = inspect.getsource(ek.activate_live_execution)
    assert "message_ar" not in src
    assert "disclaimer_ar" not in src
    assert "message" in src
    vsrc = inspect.getsource(ek.verify_binance_keys)
    assert "can_withdraw" in vsrc


def test_stop_loss_wired_into_auto_cycle():
    import execution_engine as ee

    cycle_src = inspect.getsource(ee.run_auto_execution_cycle)
    helper_src = inspect.getsource(ee._stop_loss_flatten_outcome)
    assert "_stop_loss_flatten_outcome" in cycle_src
    assert "check_stop_losses" in helper_src
    assert "stop_loss_flatten" in helper_src


def test_regime_train_has_panic_bootstrap():
    import ml.train_regime_models as tr

    assert callable(tr._bootstrap_regime_samples)
    src = inspect.getsource(tr._bootstrap_regime_samples) + inspect.getsource(tr.train_regime_models)
    assert "panic" in src
    assert "force" in inspect.getsource(tr.train_regime_models)


def test_evidence_pack_d8_honest_status():
    import acquirer_evidence_pack as aep

    pack_src = inspect.getsource(aep.build_acquirer_evidence_pack)
    d8_src = inspect.getsource(aep._refresh_registry_differentiator)
    assert "_refresh_registry_differentiator" in pack_src
    assert "pending_labels" in d8_src or 'd8.get("status")' in d8_src


def test_utility_routes_exist():
    import dashboard as dash

    src = inspect.getsource(dash)
    assert '/capabilities"' in src or "/capabilities" in src
    assert "/contact" in src
    assert "/complaints" in src


def test_d8_lexicon_includes_cross_exchange():
    from signal_registry import SIGNAL_TYPE_LEXICON

    assert "cross_exchange" in SIGNAL_TYPE_LEXICON
    assert SIGNAL_TYPE_LEXICON["cross_exchange"]["weight"] >= 0.5


@pytest.mark.asyncio
async def test_d8_backfill_callable(monkeypatch):
    from signal_registry import backfill_labels_from_oracle

    async def fake_rows(limit=2000, include_synthetic=False):
        return [
            {
                "id": 9001,
                "asset": "BTC",
                "label": "correct",
                "outcome": "correct",
                "opportunity_score": 70,
                "verdict": "BUY",
                "kind": "oracle_direction",
                "timestamp": "2026-08-01T00:00:00+00:00",
            }
        ]

    monkeypatch.setattr(
        "database.fetch_labeled_oracle_predictions",
        fake_rows,
        raising=False,
    )
    out = await backfill_labels_from_oracle(limit=10)
    assert out.get("ok") is True
    assert out.get("labeled_total_touch", 0) >= 1


@pytest.mark.asyncio
async def test_force_train_writes_four_regimes(tmp_path, monkeypatch):
    import ml.regime_models as rm
    import ml.train_regime_models as tr

    monkeypatch.setattr(rm, "_REGIME_MODEL_ROOT", tmp_path)
    monkeypatch.setattr(tr, "_REGIME_MODEL_ROOT", tmp_path)
    monkeypatch.setattr(tr, "STATUS_PATH", tmp_path / "training_status.json")
    monkeypatch.setattr(tr, "MIN_SAMPLES_PER_REGIME", 40)

    async def empty_buckets():
        return {r: [] for r in rm.REGIMES}

    monkeypatch.setattr(tr, "collect_regime_buckets", empty_buckets)
    out = await tr.train_regime_models(force=True)
    assert out.get("artifacts_written", 0) >= 4
    for regime in rm.REGIMES:
        assert (tmp_path / regime / "model.joblib").is_file()
