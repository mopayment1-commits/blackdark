"""Tests — #896 Ingestion Pipeline + #899 Multi-Tenant Isolation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_engine_architecture as arch
from bd_platform import data_engine_ingestion_pipeline as pipe


@pytest.fixture
def pipe_seed() -> dict:
    return json.loads(Path("data/data_engine_ingestion_pipeline_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def arch_seed() -> dict:
    return json.loads(Path("data/data_engine_architecture_seed.json").read_text(encoding="utf-8"))


# --- #896 ---


def test_896_status(pipe_seed):
    status = pipe.ingestion_pipeline_status_896(seed=pipe_seed)
    assert status["standalone_rejected"] is True
    assert status["no_scraping"] is True
    assert status["smart_branding_rejected"] is True
    assert status["official_apis_only"] is True
    assert status["sources"] == ["coingecko", "binance", "fred"]


def test_896_normalize():
    rec = pipe.normalize_market_record_896(
        {"symbol": "btc", "price": 64800, "volume": 1e9, "market_cap": 1.2e12},
        "coingecko",
    )
    assert rec["symbol"] == "BTC"
    assert rec["rule_based"] is True


def test_896_fetch_and_cache(pipe_seed):
    pipe._CACHE.clear()
    first = pipe.fetch_from_source_896("coingecko", "BTC", seed=pipe_seed)
    second = pipe.fetch_from_source_896("coingecko", "BTC", seed=pipe_seed)
    assert first["ok"] is True
    assert second["cache_hit"] is True
    assert first["no_scraping"] is True


def test_896_fallback(pipe_seed):
    fb = pipe.fetch_from_source_896("coingecko", "BTC", seed=pipe_seed, force_primary_fail=True)
    assert fb["fallback_used"] is True


def test_896_aggregate(pipe_seed):
    snap = pipe.aggregate_market_snapshot_896("BTC", seed=pipe_seed)
    assert snap["ok"] is True
    assert snap["rule_based_only"] is True
    assert snap["aggregated"]["sources_count"] >= 2


def test_896_rate_limit(pipe_seed):
    rate = pipe.run_rate_limit_handling_test_896(seed=pipe_seed)
    assert rate["cache_enabled"] is True
    assert rate["cache_ttl_min_sec"] >= 3600


def test_896_e2e(pipe_seed):
    e2e = pipe.run_ingestion_pipeline_e2e_896(seed=pipe_seed)
    assert e2e["all_passed"] is True


# --- #899 ---


def test_899_status(arch_seed):
    status = arch.multi_tenant_isolation_status_899(seed=arch_seed)
    assert status["isolation_method"] == "row_level_security"
    assert status["no_shared_data"] is True
    assert status["accuracy_target_pct"] >= 99.99
    assert status["query_target_ms"] <= 1000
    assert status["retention_years_min"] >= 2


def test_899_tenant_scope(arch_seed):
    scope = arch.enforce_tenant_scope_899("tenant_alpha", {"table": "market_data"}, seed=arch_seed)
    assert scope["rls_enforced"] is True
    assert scope["scoped_query"]["tenant_id"] == "tenant_alpha"


def test_899_cross_tenant_blocked(arch_seed):
    cross = arch.enforce_tenant_scope_899(
        "tenant_alpha",
        {"tenant_id": "tenant_beta", "table": "market_data"},
        seed=arch_seed,
    )
    assert cross["ok"] is False
    assert cross["cross_tenant_leakage_prevented"] is True


def test_899_leakage_test(arch_seed):
    test = arch.run_cross_tenant_leakage_test_899(seed=arch_seed)
    assert test["cross_tenant_blocked"] is True


def test_899_pen_test(arch_seed):
    pen = arch.run_quarterly_pen_test_899(seed=arch_seed)
    assert pen["last_passed"] is True
    assert pen["rls_verified"] is True


def test_899_e2e(arch_seed):
    e2e = arch.run_multi_tenant_e2e_899(seed=arch_seed)
    assert e2e["all_passed"] is True
