"""Tests for live collect + market-replay bootstrap flywheel path."""

from __future__ import annotations

from ml.market_replay_bootstrap import SOURCE, _feature_vector_from_closes, _verdict_from_past
from ml.training_utils import FEATURE_COLUMNS


def test_market_replay_source_is_trainable():
    from oracle_integrity import SYNTHETIC_PREDICTION_SOURCES, is_synthetic_prediction

    assert SOURCE == "market_replay_v1"
    assert SOURCE not in SYNTHETIC_PREDICTION_SOURCES
    assert is_synthetic_prediction({"source": SOURCE}) is False


def test_feature_vector_covers_training_columns():
    closes = [100 + i * 0.2 for i in range(40)]
    feats = _feature_vector_from_closes("BTC", closes)
    for col in FEATURE_COLUMNS:
        assert col in feats


def test_verdict_from_past_is_public_taxonomy():
    up = [100 + i for i in range(30)]
    down = [200 - i for i in range(30)]
    flat = [100.0] * 30
    assert "BULLISH" in _verdict_from_past(up) or _verdict_from_past(up) == "BULLISH_ANALYTICS"
    assert "BEARISH" in _verdict_from_past(down) or _verdict_from_past(down) == "BEARISH_ANALYTICS"
    assert "NEUTRAL" in _verdict_from_past(flat) or _verdict_from_past(flat) == "NEUTRAL_OBSERVE"


def test_flywheel_cycle_signature_supports_bootstrap_flags():
    import inspect

    from ml.labeling_pipeline import run_labeling_flywheel_cycle

    sig = inspect.signature(run_labeling_flywheel_cycle)
    assert "bootstrap_if_needed" in sig.parameters
    assert "collect_live" in sig.parameters
