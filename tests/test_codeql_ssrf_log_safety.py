"""Guards for CodeQL partial-SSRF + log-injection remediations."""

from __future__ import annotations

from pathlib import Path


def test_log_safety_strips_crlf_explicitly():
    from log_safety import sanitize_asset, sanitize_log_value

    src = Path("log_safety.py").read_text(encoding="utf-8")
    assert '.replace("\\r"' in src or ".replace('\\r'" in src
    assert '.replace("\\n"' in src or ".replace('\\n'" in src
    dirty = "btc\r\nALERT forged"
    clean = sanitize_log_value(dirty)
    assert "\r" not in clean and "\n" not in clean
    assert sanitize_asset("BTC/USDT") == "BTC/USDT" or sanitize_asset("BTC") == "BTC"
    assert sanitize_asset("evil\ninject") == "invalid_asset"


def test_weight_aggregator_logger_uses_inline_crlf_scrub():
    src = Path("weight_aggregator.py").read_text(encoding="utf-8")
    assert "sanitize_asset(" not in src
    assert "sanitize_log_value(" not in src
    assert '.replace("\\r"' in src
    assert '.replace("\\n"' in src
    # Every logger line that interpolates asset must scrub CRLF inline at the sink.
    for line in src.splitlines():
        if "logger." in line and "asset=" in line:
            assert '.replace("\\r"' in line, line


def test_listed_modules_inline_log_scrub_not_helper_only():
    files = [
        "voice_service.py",
        "trust_pulse.py",
        "sentiment_engine.py",
        "sentiment_gate.py",
        "risk_manager.py",
        "retention_service.py",
        "billing_service.py",
        "execution_engine.py",
        "database.py",
        "oracle_unified.py",
        "oracle_track_record.py",
        "oracle_data_hub.py",
        "onchain_tracker.py",
        "obi_predictor.py",
        "market_context.py",
        "forecast_engine.py",
        "ml/feature_store.py",
        "api_key_security_guard.py",
        "bd_platform/free_integrations.py",
        "bd_platform/derivatives_hub.py",
    ]
    for path in files:
        text = Path(path).read_text(encoding="utf-8")
        assert "sanitize_asset(" not in text, path
        assert "sanitize_log_value(" not in text, path
        assert '.replace("\\r"' in text, path


def test_binance_fetchers_guard_isalnum():
    files = [
        "trade_simulator.py",
        "research_lab.py",
        "execution_engine.py",
        "forecast_engine.py",
        "market_context.py",
        "api/routers/market.py",
        "bd_platform/onchain_advanced.py",
        "market_intel.py",
        "bd_platform/pairs_trading.py",
        "bd_platform/cex_dex_arbitrage.py",
        "plan_audit.py",
        "bd_platform/free_market_data.py",
        "oracle_data_hub.py",
        "defi_arbitrage_engine.py",
        "bd_platform/free_integrations.py",
        "coingecko_cex_fetcher.py",
    ]
    for path in files:
        text = Path(path).read_text(encoding="utf-8")
        assert "isalnum()" in text, path


def test_expert_execution_base_url_allowlisted():
    src = Path("expert_execution.py").read_text(encoding="utf-8")
    assert "assert_safe_http_url" in src
    assert "from path_safety import assert_safe_http_url" in src

    from expert_execution import run_acceptance_60s
    import pytest

    with pytest.raises(ValueError):
        run_acceptance_60s("https://evil.example/ssrf")


def test_dashboard_lens_allowlist_csrf():
    html = Path("templates/dashboard.html").read_text(encoding="utf-8")
    assert "ALLOWED_LENSES" in html
    assert "encodeURIComponent(currentLens)" in html


def test_market_klines_uses_fixed_path_and_params():
    src = Path("api/routers/market.py").read_text(encoding="utf-8")
    assert '"https://api.binance.com/api/v3/klines"' in src
    assert "params=" in src
    assert "if not sym.isalnum()" in src


def test_execution_live_order_log_avoids_upstream_payload():
    src = Path("execution_engine.py").read_text(encoding="utf-8")
    assert "Live order placed | side=%s asset=%s amount_usd=%.2f source=%s" in src
    assert 'payload["message"] = "Live order failed"' in src
    # Do not interpolate exception objects into user-visible live-order failure messages.
    assert "Live order failed: {exc}" not in src
