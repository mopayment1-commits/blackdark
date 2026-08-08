"""P0 radical hardening regressions."""

from __future__ import annotations

import inspect

from ml.labeling_pipeline import score_verdict_accuracy
from oracle_unified import ENGINE_ID, apply_unified_adjustments
from production_guard import evaluate_production_guard
from security_auth import is_production_env


def test_unified_engine_constant():
    assert ENGINE_ID == "unified_multimodal_v1"


def test_apply_unified_adjustments_no_double_macro():
    score, breakdown = apply_unified_adjustments(
        70.0,
        "BTC",
        {
            "macro_score_weight": 1.08,
            "macro_regime": "Risk-On",
            "sentiment_compound_index": {"BTC": 0.1},
        },
        change_24h=2.0,
        quote_volume=1_000_000_000,
    )
    assert 0.0 <= score <= 100.0
    assert breakdown.get("engine") == ENGINE_ID
    assert "conflicts" in breakdown


def test_ai_oracle_uses_unified_scoring():
    import ai_oracle

    assert hasattr(ai_oracle, "score_opportunity_with_breakdown")
    src = inspect.getsource(ai_oracle.calculate_opportunity_score)
    assert "score_opportunity_with_breakdown" in src


def test_execution_engine_has_security_gates():
    import execution_engine

    src = inspect.getsource(execution_engine._place_binance_market_order)
    assert "live_execution_allowed" in src
    assert "resolve_binance_credentials" in src or "user_id" in src


def test_platform_execute_requires_admin():
    import platform_api

    # FastAPI dependency is on signature annotations/defaults via Depends
    sig = inspect.signature(platform_api.cex_dex_execute)
    assert "_admin" in sig.parameters


def test_production_guard_reads_service_mode_env(monkeypatch):
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("LEMON_SQUEEZY_CHECKOUT_PRO", "https://example.com/c")
    monkeypatch.setenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "whsec")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    report = evaluate_production_guard()
    assert report["service_mode"] == "web"
    ids = {c["id"] for c in report["checks"]}
    assert "secrets_master_key" in ids
    assert "session_token_pepper" in ids
    assert "billing_entitlement_webhook" in ids


def test_expanded_feature_columns():
    from ml.training_utils import FEATURE_COLUMNS

    for col in ("funding_spread_bps", "whale_sii", "onchain_netflow"):
        assert col in FEATURE_COLUMNS
    assert "opportunity_score" not in FEATURE_COLUMNS


def test_verdict_scoring_still_public_safe():
    outcome, _, direction = score_verdict_accuracy("BULLISH_ANALYTICS", 100.0, 104.0)
    assert outcome == "correct"
    assert direction == "up"


def test_is_production_env_respects_explicit_prod_over_local_dev(monkeypatch):
    """LOCAL_DEV must never downgrade an explicit production ENV (admin/vault footgun)."""
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("LOCAL_DEV", "true")
    assert is_production_env() is True
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("LOCAL_DEV", "true")
    assert is_production_env() is False
