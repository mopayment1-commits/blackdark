"""Regression gates for CodeQL clear-text logging / improper sanitization closures."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(".")


def test_setup_stripe_production_never_prints_secret_expressions():
    src = (ROOT / "scripts/setup_stripe_production.py").read_text(encoding="utf-8")
    assert 'print(f"  Livemode: {not secret.startswith' not in src
    assert "body[:200]" not in src
    assert "print(f\"  Stripe API error {exc.code}: {body" not in src
    assert "_is_set(" in src
    assert "live_label" in src
    # Checklist must carry booleans, not raw secret strings.
    assert '("STRIPE_SECRET_KEY", _is_set("STRIPE_SECRET_KEY")' in src


def test_setup_stripe_writes_private_secret_file_not_env():
    src = (ROOT / "scripts/setup_stripe.py").read_text(encoding="utf-8")
    assert "write_private_text" in src
    assert "STRIPE_SECRETS_FILE" in src
    assert 'print(sk)' not in src
    assert 'print(wh)' not in src
    assert 'f"STRIPE_SECRET_KEY={sk}"' in src  # only into private file block
    # Must strip legacy clear-text secret lines from .env
    assert 'not ln.startswith("STRIPE_SECRET_KEY=")' in src


def test_activate_infra_never_prints_vault_dev_token():
    src = (ROOT / "scripts/activate_infra.py").read_text(encoding="utf-8")
    assert "blackdark-dev-root" not in src
    assert "never print it" in src


def test_coin_stats_use_dom_not_innerhtml_escape():
    coin = (ROOT / "templates/coin.html").read_text(encoding="utf-8")
    js = (ROOT / "static/js/coin_detail.js").read_text(encoding="utf-8")
    assert "statsEl.textContent" in js or "statsEl.replaceChildren" in js or "appendChild" in js
    assert ".replace(/<[^>]+>/g" not in coin
    assert ".replace(/<[^>]+>/g" not in js
    assert "function esc(" not in coin
    assert "/static/js/coin_detail.js" in coin


def test_dashboard_chat_uses_dom_text_nodes():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert "function appendChat" in dash
    assert "createTextNode" in dash
    assert "row.innerHTML = role === 'user'" not in dash


def test_setup_production_env_never_prints_secret_block():
    src = (ROOT / "scripts/setup_production_env.py").read_text(encoding="utf-8")
    assert "write_private_text" in src
    assert "print(block)" not in src
    assert "SECRETS_MASTER_KEY=set" in src
    assert "never echo it to CI logs" in src


def test_vault_client_logs_event_codes_not_exception_text():
    src = (ROOT / "bd_platform/vault_client.py").read_text(encoding="utf-8")
    assert 'logger.warning("Vault read failed: %s", exc)' not in src
    assert "event=vault_read_failed" in src
    assert "event=vault_store_failed" in src


def test_half_life_clock_builds_svg_via_dom_not_raw_html():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert "createElementNS('http://www.w3.org/2000/svg'" in dash or 'createElementNS("http://www.w3.org/2000/svg"' in dash
    assert "svg.innerHTML = /<script" not in dash
    assert "rawSvg" not in dash


def test_admin_audit_tables_use_dom_not_innerhtml():
    for name in ("admin_roadmap.html", "admin_plan.html"):
        src = (ROOT / "templates" / name).read_text(encoding="utf-8")
        assert "innerHTML" not in src
        assert "createElement('tr')" in src or 'createElement("tr")' in src
        assert "textContent" in src


def test_extension_oracle_surfaces_use_dom_not_innerhtml():
    popup = (ROOT / "browser_extension/src/popup.js").read_text(encoding="utf-8")
    content = (ROOT / "browser_extension/src/content.js").read_text(encoding="utf-8")
    assert "innerHTML" not in popup
    assert "textContent" in popup
    assert "body.innerHTML" not in content
    assert "createElement" in content
    # Broken quote escapes from prior revision must stay gone.
    assert '.replaceAll("",' not in popup
    assert '.replaceAll("",' not in content
