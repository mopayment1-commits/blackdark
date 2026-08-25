"""Tests — #206 Analyst Notes Feed, #208 Source Registry & Provenance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import analyst_notes_feed as anf
from bd_platform import source_registry_provenance as srp


# ── #206 Analyst Notes Feed ────────────────────────────────────────────────────


@pytest.fixture
def isolated_analyst_store(tmp_path, monkeypatch):
    store = tmp_path / "analyst_notes.json"
    seed = tmp_path / "analyst_notes_seed.json"
    seed.write_text(
        json.dumps([
            {
                "id": "n1", "analyst": "@alice", "firm": "Messari", "view": "bullish",
                "confidence_pct": 70, "assets": ["BTC"], "source": "Messari Pro",
                "published_date": "2026-03-01", "summary": "BTC bullish",
            },
            {
                "id": "n2", "analyst": "Bob", "firm": "Kaiko", "view": "neutral",
                "confidence_pct": 50, "assets": ["BTC"], "source": "Manual Curation",
                "published_date": "2026-03-02", "summary": "BTC neutral",
            },
            {
                "id": "n3", "analyst": "Carol", "firm": "Delphi", "view": "bearish",
                "confidence_pct": 60, "assets": ["BTC"], "source": "Manual Curation",
                "published_date": "2026-03-03", "summary": "BTC bearish",
            },
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(anf, "_STORE_PATH", store)
    monkeypatch.setattr(anf, "_SEED_PATH", seed)
    monkeypatch.setattr(srp, "_AUDIT_LOG", tmp_path / "audit.jsonl")
    return store


def test_analyst_attribution_required(isolated_analyst_store):
    note = anf.get_analyst_note("n1")["note"]
    assert "Analyst:" in note["attribution_line"]
    assert "Firm:" in note["attribution_line"]
    assert "Date:" in note["attribution_line"]


def test_not_prediction_format(isolated_analyst_store):
    note = anf.get_analyst_note("n1")["note"]
    assert note["not_a_prediction"] is True
    assert "Analyst View:" in note["display"]
    assert "Confidence:" in note["display"]
    assert "prediction" not in note["display"].lower()


def test_disclaimer_not_hideable(isolated_analyst_store):
    listed = anf.list_analyst_notes()
    assert "opinions, not facts" in listed["disclaimer"]
    assert listed["disclaimer_hideable"] is False


def test_divergence_counts_not_average(isolated_analyst_store):
    summary = anf.get_asset_analyst_summary("BTC")
    div = summary["divergence"]
    assert div["no_average_score"] is True
    assert "Bullish" in div["display"]
    assert "Neutral" in div["display"]
    assert "Bearish" in div["display"]
    assert div["bullish"] == 1
    assert div["neutral"] == 1
    assert div["bearish"] == 1


def test_no_consensus_engine(isolated_analyst_store):
    status = anf.analyst_notes_status()
    assert status["consensus_engine"] is False
    assert status["wave_3_consensus_deferred"] is True


def test_full_seed_file_exists():
    rows = json.loads(Path("data/analyst_notes_seed.json").read_text(encoding="utf-8"))
    assert len(rows) >= 10


# ── #208 Source Registry & Provenance ──────────────────────────────────────────


def test_source_registry_no_undocumented():
    registry = srp.build_source_registry()
    assert registry["source_count"] >= 10
    assert registry["no_undocumented_source_policy"] is True
    for src in registry["sources"]:
        assert src["source_id"]
        assert src["license_status"]
        assert src["secrets_in_logs"] is False


def test_deterministic_normalization():
    raw = {"asset": "BTC", "price": 50000.0, "timestamp": "2026-01-01T00:00:00+00:00"}
    a = srp.normalize_record(raw, source_id="binance_spot")
    b = srp.normalize_record(raw, source_id="binance_spot")
    assert a["normalization_checksum"] == b["normalization_checksum"]
    assert a["raw_checksum"] == b["raw_checksum"]


def test_raw_vs_normalized_separation():
    raw = {"asset": "ETH", "price": 3000}
    norm = srp.normalize_record(raw, source_id="coingecko_prices")
    assert "raw_checksum" in norm
    assert norm["schema"] == "canonical_v1"


def test_reconciliation_display():
    readings = [
        {"source_id": "binance", "price_usd": 100000},
        {"source_id": "coinbase", "price_usd": 100500},
    ]
    result = srp.reconcile_sources(readings)
    assert "Source binance" in result["display"]
    assert "Variance:" in result["display"]


def test_secrets_redacted_in_audit(tmp_path, monkeypatch):
    monkeypatch.setattr(srp, "_AUDIT_LOG", tmp_path / "audit.jsonl")
    redacted = srp._redact_secrets('api_key=supersecret123 Bearer abc.def.ghi')
    assert "supersecret" not in redacted
    assert "REDACTED" in redacted


def test_lineage_trace_audit(tmp_path, monkeypatch):
    audit = tmp_path / "audit.jsonl"
    monkeypatch.setattr(srp, "_AUDIT_LOG", audit)
    result = srp.trace_metric_lineage("price", "BTC")
    assert result["lineage"]["chain"]
    assert audit.is_file()


@pytest.mark.asyncio
async def test_provider_degradation_test(monkeypatch, tmp_path):
    monkeypatch.setattr(srp, "_AUDIT_LOG", tmp_path / "audit.jsonl")

    async def fake_coverage(**kwargs):
        return {"venues": [{"venue_id": "binance", "live": True}, {"venue_id": "mexc", "live": False}]}

    monkeypatch.setattr("bd_platform.connector_coverage_map.build_coverage_map", fake_coverage)
    result = await srp.run_provider_degradation_test()
    assert result["degradation_detected"] is True
    assert "mexc" in result["degraded"]


def test_provenance_status_policies():
    status = srp.source_registry_status()
    policies = status["policies"]
    assert policies["no_undocumented_source"] is True
    assert policies["secrets_never_in_logs"] is True
    assert policies["deterministic_normalization"] is True
    assert 118 in status["merged_features"]
