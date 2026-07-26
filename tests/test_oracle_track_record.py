"""Tests for automatic oracle track record."""

import pytest

import oracle_audit_chain as chain
import oracle_track_record as tr


@pytest.fixture
def clean_chain(tmp_path, monkeypatch):
    path = tmp_path / "chain.jsonl"
    monkeypatch.setattr(chain, "CHAIN_PATH", path)
    return path


def test_auto_on_create(clean_chain):
    tr.on_prediction_created(
        1, asset="BTC", price_at_prediction=50000, verdict="BUY", confidence=80
    )
    assert chain.verify_chain()["records"] == 1
    records = tr._read_all_records()
    assert records[0]["event"] == "prediction_created"
    assert records[0]["prediction_id"] == 1


def test_auto_on_resolve(clean_chain):
    tr.on_prediction_created(2, asset="ETH", price_at_prediction=3000, verdict="BUY")
    tr.on_prediction_resolved(
        2,
        asset="ETH",
        verdict="BUY",
        price_at_prediction=3000,
        price_after=3100,
        outcome="correct",
        accuracy_score=85.0,
        label="correct",
    )
    assert chain.verify_chain()["records"] == 2
    assert chain.verify_chain()["valid"] is True


def test_public_track_record(clean_chain):
    tr.on_prediction_resolved(
        3, asset="SOL", verdict="BUY", price_at_prediction=100,
        price_after=105, outcome="correct", accuracy_score=90, label="correct",
    )
    stats = tr.public_track_record()
    assert stats["auto_accumulation"] is True
    assert stats["immutable_chain"]["valid"] is True
