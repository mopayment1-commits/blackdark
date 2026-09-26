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
    # Fail closed — never extend a broken chain.
    try:
        chain.append_prediction_record({"asset": "ETH", "verdict": "bullish"})
        raise AssertionError("expected oracle_audit_chain_integrity_failed")
    except RuntimeError as exc:
        assert "oracle_audit_chain_integrity_failed" in str(exc)


def test_chain_summary(tmp_path, monkeypatch):
    path = tmp_path / "chain.jsonl"
    monkeypatch.setattr(chain, "CHAIN_PATH", path)
    chain.append_prediction_record({"asset": "SOL", "resolved": True, "label": "correct"})
    summary = chain.chain_summary()
    assert summary["integrity"]["valid"] is True
    assert summary["total_records"] == 1


def test_repair_tip_prev_hash_race(tmp_path, monkeypatch):
    path = tmp_path / "chain.jsonl"
    monkeypatch.setattr(chain, "CHAIN_PATH", path)
    first = chain.append_prediction_record({"asset": "BTC", "verdict": "bullish"})
    second = chain.append_prediction_record({"asset": "ETH", "verdict": "bearish"})
    chain.append_prediction_record({"asset": "SOL", "verdict": "neutral"})
    lines = path.read_text(encoding="utf-8").splitlines()
    broken = json.loads(lines[-1])
    stale_prev = first["chain_hash"]
    broken["prev_hash"] = stale_prev
    broken.pop("chain_hash", None)
    broken["chain_hash"] = chain._hash_record(broken, stale_prev)
    path.write_text("\n".join(lines[:-1] + [json.dumps(broken)]) + "\n", encoding="utf-8")
    assert chain.verify_chain()["valid"] is False

    result = chain.repair_tip_prev_hash_race(path)
    assert result["repaired"] is True
    assert chain.verify_chain()["valid"] is True
    assert result["verify"]["records"] == 3
