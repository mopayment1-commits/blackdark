"""Tests for overfitting / look-ahead bias remediation."""

from __future__ import annotations

import pandas as pd
import pytest

import oracle_audit_chain as chain
import oracle_track_record as tr
from ml.training_utils import FEATURE_COLUMNS, temporal_train_test_split
from oracle_integrity import filter_live_predictions, is_synthetic_prediction, live_source_sql


@pytest.fixture
def clean_chain(tmp_path, monkeypatch):
    path = tmp_path / "chain.jsonl"
    monkeypatch.setattr(chain, "CHAIN_PATH", path)
    return path


def test_feature_columns_exclude_rule_engine_outputs():
    assert "opportunity_score" not in FEATURE_COLUMNS
    assert "confidence" not in FEATURE_COLUMNS


def test_is_synthetic_prediction():
    assert is_synthetic_prediction({"source": "historical_seed"}) is True
    assert is_synthetic_prediction({"source": "oracle"}) is False
    assert is_synthetic_prediction({}) is False


def test_filter_live_predictions():
    rows = [
        {"source": "oracle", "id": 1},
        {"source": "historical_seed", "id": 2},
        {"id": 3},
    ]
    live = filter_live_predictions(rows)
    assert len(live) == 2
    assert all(not is_synthetic_prediction(r) for r in live)


def test_live_source_sql_excludes_seed():
    clause = live_source_sql()
    assert "historical_seed" in clause
    assert "NOT IN" in clause


def test_temporal_split_no_shuffle():
    frame = pd.DataFrame(
        {
            "timestamp": [f"2026-01-{day:02d}T00:00:00+00:00" for day in range(1, 21)],
            **{col: [float(day) for day in range(1, 21)] for col in FEATURE_COLUMNS},
            "direction_label": ["up", "down"] * 10,
        }
    )
    split = temporal_train_test_split(frame, test_fraction=0.2, min_train=10, min_test=4)
    assert split is not None
    x_train, x_test, _, _ = split
    assert len(x_train) == 16
    assert len(x_test) == 4
    assert float(x_test.iloc[0][FEATURE_COLUMNS[0]]) > float(x_train.iloc[-1][FEATURE_COLUMNS[0]])


def test_temporal_split_insufficient_data():
    frame = pd.DataFrame(
        {
            "timestamp": ["2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00"],
            **{col: 1.0 for col in FEATURE_COLUMNS},
            "direction_label": ["up", "down"],
        }
    )
    assert temporal_train_test_split(frame) is None


def test_public_track_record_excludes_synthetic(clean_chain, monkeypatch):
    tr.on_prediction_created(
        10, asset="BTC", price_at_prediction=50000, verdict="BUY", source="oracle"
    )
    tr.on_prediction_resolved(
        10,
        asset="BTC",
        verdict="BUY",
        price_at_prediction=50000,
        price_after=52000,
        outcome="correct",
        accuracy_score=90,
        label="correct",
    )

    records = tr._read_all_records()
    records.append(
        {
            "event": "prediction_resolved",
            "prediction_id": 11,
            "source": "historical_seed",
            "label": "correct",
            "resolved": True,
        }
    )
    monkeypatch.setattr(tr, "_read_all_records", lambda: records)

    stats = tr.public_track_record()
    assert stats["cumulative"]["resolved_predictions"] == 1
    assert stats["synthetic_demo_data"]["resolved_predictions"] == 1
    assert stats["cumulative"]["metrics_scope"] == "live_only"
