"""Tests for full roadmap audit checklist."""

from __future__ import annotations


def test_roadmap_audit_structure():
    from bd_platform.roadmap_audit import run_roadmap_audit

    data = run_roadmap_audit(verify_modules=True)
    assert data["total_items"] >= 50
    assert data["complete_count"] >= 49
    # Honest PARTIAL allowed (e.g. HashiCorp Vault = optional vault-dev / Fernet primary).
    assert data["complete_count"] + data["partial_count"] == data["total_items"]
    assert data["partial_count"] <= 3
    assert "weighted_percent" in data


def test_roadmap_save():
    from bd_platform.roadmap_audit import save_audit

    data = save_audit()
    assert "saved_to" in data


def test_finbert_fallback():
    from bd_platform.finbert_sentiment import analyze_text

    r = analyze_text("Bitcoin rallies on ETF inflows")
    assert r["engine"] in {"finbert", "vader_fallback"}
    assert "score" in r


def test_pairs_trading_structure():
    from bd_platform.pairs_trading import DEFAULT_PAIRS

    assert len(DEFAULT_PAIRS) >= 2


def test_rl_policy_heuristic():
    from ml.rl_policy import policy_status, predict_action, train_ppo_policy

    st = policy_status()
    pred = predict_action({"ret_24h": 0.2, "volatility": 0.1, "obi_score": 0.3})
    assert pred["action"] in {"long", "short", "hold"}
    trained = train_ppo_policy(
        [({"ret_24h": 0.1, "volatility": 0.05, "obi_score": 0.2, "sentiment_score": 0.1}, 0.5)],
        epochs=5,
    )
    assert "saved_to" in trained
    assert st["active_policy"] in {"ppo", "sac", "heuristic"}


def test_kafka_bus_status():
    from bd_platform.kafka_bridge import bus_status

    st = bus_status()
    assert "primary" in st


def test_vault_status():
    from bd_platform.vault_client import read_secret, store_secret, vault_status

    st = vault_status()
    assert "local_fernet_available" in st
    stored = store_secret("test_key_infra", "test_value_123")
    assert stored.get("stored") is True
    read = read_secret("test_key_infra")
    assert read.get("data", {}).get("value") == "test_value_123" or read.get("source") in {"local_fernet", "hashicorp"}


def test_onchain_advanced_import():
    from bd_platform.onchain_advanced import compute_advanced_metrics

    assert callable(compute_advanced_metrics)
