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
    assert "statsEl.textContent" in coin or "statsEl.replaceChildren" in coin or "appendChild" in coin
    assert ".replace(/<[^>]+>/g" not in coin
    assert "function esc(" not in coin


def test_dashboard_chat_uses_dom_text_nodes():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert "function appendChat" in dash
    assert "createTextNode" in dash
    assert "row.innerHTML = role === 'user'" not in dash
