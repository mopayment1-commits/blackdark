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
    ]
    for path in files:
        text = Path(path).read_text(encoding="utf-8")
        assert "isalnum()" in text, path


def test_dashboard_lens_allowlist_csrf():
    html = Path("templates/dashboard.html").read_text(encoding="utf-8")
    assert "ALLOWED_LENSES" in html
    assert "encodeURIComponent(currentLens)" in html
