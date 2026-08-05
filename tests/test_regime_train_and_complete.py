"""D5 regime train + product-complete surfaces."""

from __future__ import annotations

import json
from pathlib import Path


def test_regime_train_force_writes_artifact(tmp_path, monkeypatch):
    import ml.regime_models as rm
    import ml.train_regime_models as tr

    monkeypatch.setattr(rm, "_REGIME_MODEL_ROOT", tmp_path / "regime")
    monkeypatch.setattr(tr, "_REGIME_MODEL_ROOT", tmp_path / "regime")
    monkeypatch.setattr(tr, "STATUS_PATH", tmp_path / "training_status.json")

    samples = []
    for i in range(45):
        samples.append(
            {
                "timestamp": f"2026-01-01T00:{i:02d}:00+00:00",
                "direction_label": "up" if i % 2 == 0 else "down",
                "label": "correct",
                "verdict": "BUY" if i % 2 == 0 else "SELL",
                "price_at_prediction": 100 + i,
                "features_json": json.dumps(
                    {
                        "price": 100 + i,
                        "ret_1h": 0.01 * ((-1) ** i),
                        "ret_4h": 0.02,
                        "ret_24h": 0.03,
                        "volatility": 0.05,
                        "sentiment_score": 0.1,
                        "sentiment_momentum": 0.0,
                        "obi_score": 0.2,
                        "obi_imbalance": 0.1,
                        "macro_weight": 1.0,
                        "funding_spread_bps": 1.0,
                        "whale_sii": 50.0,
                        "onchain_netflow": 0.0,
                    }
                ),
                "market_regime": "neutral",
            }
        )

    async def _buckets():
        return {"risk_on": [], "neutral": samples, "risk_off": [], "panic": []}

    monkeypatch.setattr(tr, "collect_regime_buckets", _buckets)

    import asyncio

    out = asyncio.run(tr.train_regime_models(force=True))
    assert out["artifacts_written"] >= 1
    assert (tmp_path / "regime" / "neutral" / "model.joblib").is_file()


def test_email_outbox_enqueue(tmp_path, monkeypatch):
    import email_outbox as eo

    monkeypatch.setattr(eo, "_PATH", tmp_path / "outbox.jsonl")
    row = eo.enqueue_email("a@b.com", "t", "body")
    assert row["status"] == "queued"
    assert len(eo.list_queued()) == 1


def test_product_complete_docs_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs" / "PRODUCT_COMPLETE_STATUS.md").is_file()
    assert (root / "docs" / "DEFERRED_HUMAN_STEPS.md").is_file()
    text = (root / "docs" / "PRODUCT_COMPLETE_STATUS.md").read_text(encoding="utf-8")
    assert "Deferred human" in text
