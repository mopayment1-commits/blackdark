"""Tests for data sources registry — 100+ sources."""

from data_sources_registry import DATA_SOURCES, registry_summary, source_by_id


def test_total_sources_at_least_100():
    assert len(DATA_SOURCES) >= 100


def test_registry_summary():
    summary = registry_summary()
    assert summary["total_sources"] >= 100
    assert "prices" in summary["by_category"]


def test_source_lookup():
    spec = source_by_id("binance_spot")
    assert spec is not None
    assert spec.category == "prices"


def test_no_duplicate_source_ids():
    ids = [s.source_id for s in DATA_SOURCES]
    assert len(ids) == len(set(ids))
