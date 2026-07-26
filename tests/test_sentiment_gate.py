"""Tests for sentiment gate."""

from sentiment_gate import sentiment_allows_execution


def test_sentiment_allows_neutral():
    assert sentiment_allows_execution("BTC", compound_score=0.0) is True


def test_sentiment_blocks_extreme_fear():
    assert sentiment_allows_execution("BTC", compound_score=-0.9) is False


def test_sentiment_allows_greed():
    assert sentiment_allows_execution("ETH", compound_score=0.8) is True
