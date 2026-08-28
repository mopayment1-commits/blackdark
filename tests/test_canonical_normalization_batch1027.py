"""Tests — Canonical Normalization Engine (#1027 Data Engine)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blackdark.data import canonical_normalization_engine as cne
from blackdark.data import multi_source_reconciliation as msr


@pytest.fixture
def cne_seed() -> dict:
    return json.loads(Path("data/canonical_normalization_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def msr_seed() -> dict:
    return json.loads(Path("data/multi_source_reconciliation_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    cne.reset_normalization_state()
    msr.reset_multi_source_state()
    yield
    cne.reset_normalization_state()
    msr.reset_multi_source_state()


def test_1027_status_no_standalone(cne_seed):
    status = cne.canonical_normalization_status_1027(seed=cne_seed)
    assert status["standalone_rejected"] is True
    assert status["merged_into"] == "Data Engine"
    assert status["policy"]["rule_based_only"] is True
    assert status["policy"]["pipeline_sequence"] == ["ingest", "normalize", "outlier_check", "serve"]


def test_symbol_canonicalization_btc(cne_seed):
    result = cne.canonicalize_symbol("Bitcoin", seed=cne_seed)
    assert result["canonical_symbol"] == "BTC"
    assert result["silent_remap"] is False


def test_symbol_canonicalization_btcusdt(cne_seed):
    result = cne.canonicalize_symbol("BTCUSDT", seed=cne_seed)
    assert result["canonical_symbol"] == "BTC"


def test_binance_schema_mapping(cne_seed):
    result = cne.map_source_schema(
        source="binance",
        raw_payload={"s": "BTCUSDT", "price": "42000.00", "E": 1693238400000},
        seed=cne_seed,
    )
    assert result["price_usd"] == "42000.00"
    assert result["schema_version"] == "1.0.0"


def test_coingecko_nested_mapping(cne_seed):
    result = cne.unify_format(
        payload={"id": "bitcoin", "bitcoin": {"usd": 42050.0, "usd_24h_vol": 1_200_000_000}},
        input_format="json",
        source="coingecko",
        seed=cne_seed,
    )
    assert result["record"]["price_usd"] == 42050.0
    assert result["record"]["volume_native"] == 1_200_000_000


def test_unit_standardization_usd(cne_seed):
    result = cne.standardize_units(
        {"price_usd": 42000.0, "volume_native": 1_000_000, "timestamp": 1693238400},
        seed=cne_seed,
    )
    assert result["price_currency"] == "USD"
    assert result["volume_usd"] == 1_000_000.0
    assert result["timestamp_utc"].endswith("+00:00")


def test_explicit_null_handling(cne_seed):
    result = cne.handle_null_fields({"source": "test"}, seed=cne_seed)
    assert result["price_usd"] is None
    assert "price_usd" in result["null_fields"]
    assert result["null_handling"]["no_fabricated_zeros"] is True


def test_cross_source_deduplication(cne_seed):
    result = cne.deduplicate_cross_source(
        [
            {"source": "binance", "symbol": "BTC", "value": 42000.0, "timestamp_utc": "2026-08-28T12:00:00+00:00"},
            {"source": "coingecko", "symbol": "BTC", "value": 42000.0, "timestamp_utc": "2026-08-28T12:00:00+00:00"},
        ],
        data_type="price",
        seed=cne_seed,
    )
    assert len(result["records"]) == 1
    assert result["records"][0]["multi_source_provenance"] is True
    assert "binance" in result["records"][0]["raw_sources"]
    assert "coingecko" in result["records"][0]["raw_sources"]


def test_normalize_observations(cne_seed):
    result = cne.normalize_observations(
        data_type="price",
        observations=[
            {"source": "binance", "value": 42000.0, "ok": True},
            {"source": "coingecko", "value": 42050.0, "ok": True},
        ],
        symbol="BTC",
        seed=cne_seed,
    )
    assert result["gate_applied"] is True
    assert result["next_step"] == "outlier_check"
    assert "normalization" in result["observations"][0]
    assert result["fee_db"]["fee_db_logged"] is True


def test_pipeline_integration_with_reconciliation(cne_seed, msr_seed):
    result = msr.reconcile_price(
        observations=[
            {"source": "binance", "value": 42000.0, "ok": True},
            {"source": "coingecko", "value": 42050.0, "ok": True},
        ],
        seed=msr_seed,
    )
    assert result["ok"] is True
    assert "normalization" in result


def test_provenance_fields(cne_seed):
    record = {
        "raw_sources": ["binance"],
        "transformations_applied": ["schema_mapping"],
        "schema_version": "1.0.0",
    }
    prov = cne.build_normalization_provenance(record=record)
    assert prov["provenance_ref"] == 945
    assert "normalization_timestamp" in prov


def test_production_gate(cne_seed):
    gate = cne.check_production_gate_1027(seed=cne_seed)
    assert gate["production_allowed"] is True
    assert gate["blocks_production"] is True


def test_audit_trail(cne_seed):
    cne.normalize_observations(
        data_type="price",
        observations=[{"source": "binance", "value": 42000.0, "ok": True}],
        seed=cne_seed,
    )
    audit = cne.get_normalization_audit_trail()
    assert audit["count"] >= 1
    assert audit["append_only"] is True


def test_e2e_all_checks(cne_seed):
    e2e = cne.run_normalization_e2e_1027(seed=cne_seed)
    assert e2e["all_passed"] is True
    failed = [c for c in e2e["checks"] if not c["passed"]]
    assert failed == [], f"Failed: {failed}"
