"""Tests for oracle_audit_chain — immutable track record."""

import json
from pathlib import Path

import oracle_audit_chain as chain


def _test_chain(monkeypatch, tag: str) -> Path:
    path = chain.isolated_chain_path_for_tests(tag)
    if path.exists():
        path.unlink()
    monkeypatch.setattr(chain, "CHAIN_PATH", path)
    return path


def test_append_and_verify_chain(monkeypatch):
    path = _test_chain(monkeypatch, "append")

    chain.append_prediction_record({"asset": "BTC", "verdict": "bullish", "resolved": False})
    chain.append_prediction_record({"asset": "ETH", "verdict": "bearish", "resolved": True, "label": "correct"})

    result = chain.verify_chain()
    assert result["valid"] is True
    assert result["records"] == 2
    path.unlink(missing_ok=True)


def test_tamper_detection(monkeypatch):
    path = _test_chain(monkeypatch, "tamper")

    chain.append_prediction_record({"asset": "BTC", "verdict": "bullish"})
    with path.open("r") as fh:
        lines = fh.readlines()
    tampered = json.loads(lines[0])
    tampered["verdict"] = "HACKED"
    with path.open("w") as fh:
        fh.write(json.dumps(tampered) + "\n")

    result = chain.verify_chain()
    assert result["valid"] is False
    # Fail closed — never extend a broken chain.
    try:
        chain.append_prediction_record({"asset": "ETH", "verdict": "bullish"})
        raise AssertionError("expected oracle_audit_chain_integrity_failed")
    except RuntimeError as exc:
        assert "oracle_audit_chain_integrity_failed" in str(exc)
    path.unlink(missing_ok=True)


def test_chain_summary(monkeypatch):
    path = _test_chain(monkeypatch, "summary")
    chain.append_prediction_record({"asset": "SOL", "resolved": True, "label": "correct"})
    summary = chain.chain_summary()
    assert summary["integrity"]["valid"] is True
    assert summary["total_records"] == 1
    path.unlink(missing_ok=True)
