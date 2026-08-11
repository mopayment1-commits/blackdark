"""Regression gates for the 18 CodeQL alerts closed on main."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(".")


def test_workflows_declare_permissions():
    for name in ("ci.yml", "security.yml"):
        src = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
        assert "permissions:" in src
        assert "contents: read" in src


def test_setup_admin_never_prints_or_stores_clear_key_in_env():
    src = (ROOT / "scripts/setup_admin.py").read_text(encoding="utf-8")
    assert "ADMIN_API_KEY_FILE" in src
    assert "write_private_text" in src
    # Stronger than masking: raw key material never reaches stdout.
    assert "fingerprint" not in src
    assert "mask_secret" not in src
    assert "print(api_key)" not in src
    assert 'print(f"  ADMIN_API_KEY={api_key}")' not in src
    assert 'lines = _upsert(lines, "ADMIN_API_KEY", api_key)' not in src
    assert "Raw key is not printed" in src


def test_launch_secrets_never_print_cleartext():
    src = (ROOT / "scripts/generate_launch_secrets.py").read_text(encoding="utf-8")
    assert "write_private_text" in src
    assert "print(text)" not in src
    assert "values never printed" in src
    assert "mask_secret(value)" not in src
    assert 'print(f"  {key}={value}")' not in src


def test_telegram_setup_masks_secrets():
    src = (ROOT / "scripts/setup_telegram_production.py").read_text(encoding="utf-8")
    assert 'print(f"  {key}={val or hint}")' not in src
    assert "present" in src
    assert "missing" in src
    assert "mask_secret(val)" not in src
    assert "Webhook set successfully" in src


def test_railway_checklist_no_secret_json_dump():
    src = (ROOT / "scripts/railway_production_checklist.py").read_text(encoding="utf-8")
    assert "json.dumps(report" not in src
    assert "statuses only" in src or "required_failures" in src


def test_exception_sinks_do_not_echo_str_exc():
    vault = (ROOT / "bd_platform/vault_client.py").read_text(encoding="utf-8")
    assert '"error": str(exc)' not in vault
    assert "vault_read_failed" in vault
    assert "_safe_secret_key" in vault
    assert "invalid_vault_secret_key" in vault
    sse = (ROOT / "bd_platform/sse_stream.py").read_text(encoding="utf-8")
    assert "str(exc)" not in sse
    assert "stream_unavailable" in sse
    dash_sse = (ROOT / "dashboard_sse.py").read_text(encoding="utf-8")
    assert "str(exc)" not in dash_sse
    cov = (ROOT / "bd_platform/coverage_report.py").read_text(encoding="utf-8")
    assert "str(exc)" not in cov
    lc = (ROOT / "launch_checklist.py").read_text(encoding="utf-8")
    assert "errors.append(str(exc))" not in lc


def test_dashboard_escapes_oracle_dom():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert "function esc(" in dash
    assert "esc(sentence)" in dash
    assert ("el.appendChild(empty)" in dash) or ("el.replaceChildren(empty)" in dash)
    # Must not interpolate symbol into innerHTML; textContent path is OK.
    assert "innerHTML = '<div class=\"empty\">Could not analyze ' + sym" not in dash
    assert "textContent" in dash


def test_coin_no_incomplete_regex_sanitizer():
    coin = (ROOT / "templates/coin.html").read_text(encoding="utf-8")
    assert ".replace(/<[^>]+>/g" not in coin
    assert "plainText" in coin
    assert "textContent" in coin
    # Stats grid must not rebuild via escaped HTML strings.
    assert "stats.innerHTML" not in coin


def test_admin_key_file_loader():
    from security_auth import _admin_api_key_expected, verify_admin_key

    assert _admin_api_key_expected() == "" or isinstance(_admin_api_key_expected(), str)
    assert verify_admin_key(None) is False


def test_public_error_sanitizer():
    from safe_errors import public_error

    assert public_error(ValueError("Invalid code"), fallback="x") == "Invalid code"
    assert "traceback" not in public_error(ValueError("see /workspace/secret"), fallback="safe").lower()
    assert public_error(RuntimeError("boom"), fallback="Request failed") == "Request failed"
