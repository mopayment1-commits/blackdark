"""Tests for infra metrics."""

from infra_metrics import collect_infra_metrics, _cost_rating


def test_collect_infra_metrics():
    m = collect_infra_metrics()
    assert "timestamp" in m
    assert "service_mode" in m
    assert "data_sources" in m


def test_cost_rating_excellent():
    assert _cost_rating({"process": {"rss_mb": 100}}) == "excellent"


def test_cost_rating_heavy():
    assert _cost_rating({"process": {"rss_mb": 2000}}) == "heavy"
