"""
BLACKDARK — ML training integrity utilities.

Temporal validation split and leak-free feature schema (no rule-engine outputs).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from oracle_integrity import filter_live_predictions

# Rule-engine outputs excluded — they leak the label being predicted.
FEATURE_COLUMNS: tuple[str, ...] = (
    "price",
    "ret_1h",
    "ret_4h",
    "ret_24h",
    "volatility",
    "sentiment_score",
    "sentiment_momentum",
    "obi_score",
    "obi_imbalance",
    "macro_weight",
)

LEAKAGE_GUARD_NOTE = (
    "Features exclude opportunity_score and confidence (rule-engine outputs). "
    "Training uses live predictions only; synthetic historical_seed rows excluded."
)


def temporal_train_test_split(
    frame: pd.DataFrame,
    *,
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS,
    label_column: str = "direction_label",
    test_fraction: float = 0.2,
    min_train: int = 10,
    min_test: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series] | None:
    """Chronological hold-out: train on past, test on future (no random shuffle)."""
    if "timestamp" not in frame.columns or len(frame) < min_train + min_test:
        return None

    ordered = frame.sort_values("timestamp").reset_index(drop=True)
    test_count = max(min_test, int(len(ordered) * test_fraction))
    train_count = len(ordered) - test_count
    if train_count < min_train:
        return None

    train = ordered.iloc[:train_count]
    test = ordered.iloc[train_count:]
    x_train = train[list(feature_columns)]
    y_train = train[label_column]
    x_test = test[list(feature_columns)]
    y_test = test[label_column]
    return x_train, x_test, y_train, y_test


def prepare_live_training_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return filter_live_predictions(rows)
