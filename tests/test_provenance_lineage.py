"""Tests — #1003 Data Provenance & Lineage Layer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blackdark.data import provenance_lineage as pl


@pytest.fixture
def lineage_seed(tmp_path, monkeypatch):
    p = tmp_path / "provenance_lineage_seed.json"
    p.write_text(json.dumps({
        "layer_defaults": {
            "spot_metrics": {
                "source": "Binance API v3",
                "source_kind": "api",
                "transformation": "venue_aggregate",
                "transformation_version": "1.4",
                "source_schema_version": "2.1",
                "confidence": "high",
            },
        },
        "metrics": {
            "spot.btc.price": {
                "name": "BTC Spot Price",
                "source": "Binance API v3",
                "source_kind": "api",
                "transformation": "zscore_filter",
                "transformation_version": "1.4",
                "transformation_key": "zscore_outlier_filter",
                "source_schema_version": "2.1",
                "source_schema_key": "binance_spot_schema",
                "last_verified_utc": "2024-01-15T14:32:00+00:00",
                "confidence": "high",
                "historical_recomputable": True,
                "lineage_steps": [
                    {"stage": "ingest", "description": "Binance API v3", "version": "3.0"},
                    {"stage": "normalize", "description": "normalized via schema v2.1", "version": "2.1"},
                ],
                "historical_samples": [{"as_of": "2026-08-20", "value": 65000}],
            },
        },
        "schema_versions": {
            "binance_spot_schema": [{"version": "2.1", "effective_from": "2025-06-01"}],
        },
        "transformation_versions": {
            "zscore_outlier_filter": [{"version": "1.4", "effective_from": "2025-09-01"}],
        },
    }), encoding="utf-8")
    monkeypatch.setattr(pl, "_SEED_PATH", p)
    return p


def test_1003_mandatory_tag(lineage_seed):
    tag = pl.build_provenance_tag(
        source="Binance API v3",
        transformation="zscore_filter",
        transformation_version="1.4",
        source_schema_version="2.1",
        confidence="high",
    )
    assert "Source: Binance API v3" in tag["display_tag"]
    assert "Transformation:" in tag["display_tag"]
    assert "Confidence: high" in tag["display_tag"]
    assert tag["mandatory"] is True


def test_1003_badge_system(lineage_seed):
    tag = pl.build_provenance_tag(
        source="Binance API v3",
        transformation="zscore_filter",
        transformation_version="1.4",
        confidence="high",
    )
    chain = pl.build_lineage_chain([
        {"description": "Binance API v3"},
        {"description": "normalized via schema v2.1"},
        {"description": "outlier filtered via Z-score v1.4"},
    ])
    wrapped = pl.wrap_metric(
        65000,
        metric_id="spot.btc.price",
        metric_name="spot_price",
        provenance=tag,
        lineage_chain=chain,
    )
    assert wrapped["badge"]["clickable"] is True
    assert wrapped["provenance"]["verification_hash"]
    assert "Binance API v3" in wrapped["provenance"]["lineage_display"]


def test_1003_require_provenance_raises():
    with pytest.raises(ValueError, match="provenance"):
        pl.require_provenance({"value": 1})


def test_1003_lineage_and_audit(lineage_seed):
    lineage = pl.get_metric_lineage("spot.btc.price")
    assert lineage["ok"] is True
    assert lineage["version_control"]["historical_recomputable"] is True
    assert "schema v2.1" in lineage["lineage_display"]

    audit = pl.audit_lineage("spot.btc.price")
    assert audit["verifiable"] is True
    assert audit["audit_hash"]
    assert len(audit["schema_version_history"]) >= 1


def test_1003_recompute_historical(lineage_seed):
    result = pl.recompute_historical("spot.btc.price", as_of_schema_version="2.1")
    assert result["ok"] is True
    assert result["historical_recomputable"] is True
    assert result["recompute_checksum"]


def test_1003_status(lineage_seed):
    status = pl.provenance_lineage_status()
    assert status["mandatory"] is True
    assert status["cross_cutting"] is True
    assert status["acceptance_criteria"]["end_to_end_traceability"] is True


def test_1003_spot_metrics_integration(lineage_seed):
    from blackdark.data import spot_metrics_venue_quality as sm
    import json as _json

    seed_path = lineage_seed.parent / "spot_metrics_venue_quality_seed.json"
    seed_path.write_text(_json.dumps({
        "venues": [],
        "symbols": {
            "BTC/USDT": {
                "venues": [{
                    "venue": "binance", "last_price": 95000, "volume_24h": 1e9,
                    "source": "binance", "timestamp_utc": "2026-08-26T00:00:00+00:00",
                }],
            },
        },
    }), encoding="utf-8")
    import blackdark.data.spot_metrics_venue_quality as sm_mod
    sm_mod._SEED_PATH = seed_path

    panel = sm.build_spot_metrics_panel("BTC/USDT")
    assert panel["provenance_layer"]["mandatory"] is True
    assert panel["venues"][0]["badge"]["clickable"] is True
    assert panel["venues"][0]["provenance_mandatory"] is True


def test_api_routes(lineage_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/v1/data/provenance-lineage/status").status_code == 200
    assert c.get("/api/v1/data/provenance-lineage/metrics").status_code == 200
    assert c.get("/api/v1/data/provenance-lineage/lineage/spot.btc.price").status_code == 200
    assert c.get("/api/v1/data/provenance-lineage/audit/spot.btc.price").status_code == 200
    assert c.get("/api/v1/data/provenance-lineage/recompute/spot.btc.price").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/provenance_lineage_seed.json").read_text())
    assert seed["feature_id"] == 1003
    assert seed["mandatory"] is True
