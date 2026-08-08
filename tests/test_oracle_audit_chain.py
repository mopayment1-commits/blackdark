"""Tests for oracle_audit_chain — immutable track record."""

import json

import oracle_audit_chain as chain


def test_append_and_verify_chain(tmp_path, monkeypatch):
    path = tmp_path / "chain.jsonl"
    monkeypatch.setattr(chain, "CHAIN_PATH", path)

    chain.append_prediction_record({"asset": "BTC", "verdict": "bullish", "resolved": False})
    chain.append_prediction_record({"asset": "ETH", "verdict": "bearish", "resolved": True, "label": "correct"})

    result = chain.verify_chain()
    assert result["valid"] is True
    assert result["records"] == 2


def test_tamper_detection(tmp_path, monkeypatch):
    path = tmp_path / "chain.jsonl"
    monkeypatch.setattr(chain, "CHAIN_PATH", path)

    chain.append_prediction_record({"asset": "BTC", "verdict": "bullish"})
    with path.open("r") as fh:
        lines = fh.readlines()
    tampered = json.loads(lines[0])
    tampered["verdict"] = "HACKED"
    with path.open("w") as fh:
        fh.write(json.dumps(tampered) + "\n")

    result = chain.verify_chain()
    assert result["valid"] is False


def test_chain_summary(tmp_path, monkeypatch):
    path = tmp_path / "chain.jsonl"
    monkeypatch.setattr(chain, "CHAIN_PATH", path)
    chain.append_prediction_record({"asset": "SOL", "resolved": True, "label": "correct"})
    summary = chain.chain_summary()
    assert summary["integrity"]["valid"] is True
    assert summary["total_records"] == 1
