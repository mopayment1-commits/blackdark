"""Regression: CodeQL py/clear-text-logging-sensitive-data (#151–#154) stay closed."""

from __future__ import annotations

import io
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(".")


def test_log_production_guard_emits_catalog_codes_not_secret_values(monkeypatch, caplog):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "super-secret-master-key-value-xyz")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "super-secret-pepper-value-xyz")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_SHOULD_NEVER_APPEAR")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:TELEGRAM-SECRET-TOKEN")
    monkeypatch.setenv("SENTRY_DSN", "https://secret@o.ingest.sentry.io/1")
    monkeypatch.setenv("BLACKDARK_B2B_DEMO_KEY", "demo-secret-key-value")
    monkeypatch.setenv("PRODUCTION_GUARD_FAIL_CLOSED", "false")

    from production_guard import CHECK_ID_CATALOG, log_production_guard

    with caplog.at_level(logging.INFO, logger="BLACKDARK.ProductionGuard"):
        log_production_guard()

    text = "\n".join(r.getMessage() for r in caplog.records)
    assert "super-secret-master-key-value-xyz" not in text
    assert "super-secret-pepper-value-xyz" not in text
    assert "sk_live_SHOULD_NEVER_APPEAR" not in text
    assert "TELEGRAM-SECRET-TOKEN" not in text
    assert "secret@o.ingest.sentry.io" not in text
    assert "demo-secret-key-value" not in text
    # Any emitted codes must be catalog literals.
    for token in text.replace(",", " ").split():
        if token.startswith("codes="):
            codes = token.split("=", 1)[1]
            for code in codes.split(","):
                if code:
                    assert code in CHECK_ID_CATALOG


def test_public_guard_console_summary_never_contains_secret_material(monkeypatch):
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "cleartext-master-should-not-leak")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "cleartext-pepper-should-not-leak")
    monkeypatch.setenv("REDIS_URL", "redis://:password@redis-host:6379/0")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")

    from production_guard import public_guard_console_summary

    summary = public_guard_console_summary()
    blob = repr(summary)
    assert "cleartext-master-should-not-leak" not in blob
    assert "cleartext-pepper-should-not-leak" not in blob
    assert "password@redis-host" not in blob
    assert "user:pass@host" not in blob
    assert "redis://" not in blob
    assert "postgresql://" not in blob


def test_setup_production_launch_stdout_has_no_secret_values(monkeypatch, capsys):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "999:LEAKED-TELEGRAM")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "LEAKED-MASTER")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "LEAKED-PEPPER")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_LEAKED")
    monkeypatch.setenv("SENTRY_DSN", "https://leaked@sentry/1")

    import scripts.setup_production_launch as mod

    # Avoid live HTTP probes.
    monkeypatch.setattr(mod, "_probe", lambda _url: (True, 200))
    with patch.object(mod, "_print_production_guard", lambda: None):
        # Still exercise env checklist path.
        missing = mod._print_env_checks(
            [
                ("TELEGRAM_BOT_TOKEN", "from @BotFather"),
                ("SECRETS_MASTER_KEY", "vault"),
            ]
        )
    out = capsys.readouterr().out
    assert "LEAKED-TELEGRAM" not in out
    assert "LEAKED-MASTER" not in out
    assert "LEAKED-PEPPER" not in out
    assert "sk_live_LEAKED" not in out
    assert "[SET]" in out
    assert missing == 0


def test_railway_checklist_stdout_has_no_live_secrets(monkeypatch, capsys):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "111:RAIL-LEAK")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "RAIL-MASTER-LEAK")
    monkeypatch.setenv("REDIS_URL", "redis://:railpass@host:6379/0")

    import scripts.railway_production_checklist as mod

    assert mod.main() == 0
    out = capsys.readouterr().out
    assert "RAIL-LEAK" not in out
    assert "RAIL-MASTER-LEAK" not in out
    assert "railpass" not in out
    assert "statuses only" in out or "required_failure_count=" in out
    assert "json.dumps" not in Path("scripts/railway_production_checklist.py").read_text(
        encoding="utf-8"
    )


def test_source_guards_forbid_logging_required_failures_join_directly():
    src = Path("production_guard.py").read_text(encoding="utf-8")
    # Historical sinks for alerts #151/#152 — must stay gone.
    assert '", ".join(report["required_failures"])' not in src
    assert '", ".join(report["warnings"])' not in src
    assert "public_guard_console_summary" in src
    assert "untainted_catalog_ids" in src or "_safe_failure_ids" in src


def test_setup_scripts_forbid_printing_guard_required_failures_join():
    launch = Path("scripts/setup_production_launch.py").read_text(encoding="utf-8")
    rail = Path("scripts/railway_production_checklist.py").read_text(encoding="utf-8")
    assert "guard['required_failures']" not in launch
    assert "evaluate_production_guard" not in launch
    assert "public_guard_console_summary" in launch
    assert "evaluate_production_guard" not in rail
    assert "public_guard_console_summary" in rail
    assert "check.get('status')" not in rail


def test_secret_hygiene_uses_contained_compare_not_retained_cleartext():
    src = Path("production_guard.py").read_text(encoding="utf-8")
    assert "env_matches_any" in src
    assert "secrets_raw.lower() not in insecure_defaults" not in src
    assert "session_pepper.lower() not in insecure_defaults" not in src
    assert "sha256" not in src.lower()
    # Connection strings must not be retained on guard state/report keys.
    assert '"redis_url"' not in src
    assert "'redis_url'" not in src
    safety = Path("log_safety.py").read_text(encoding="utf-8")
    assert "sha256" not in safety.lower()
    assert "env_matches_any" in safety


def test_log_safety_redacts_secretish_strings():
    from log_safety import env_configured, redact_secret, sanitize_log_value

    assert sanitize_log_value("Bearer abc.def") == "[redacted]"
    assert sanitize_log_value("redis://:pw@h/0") == "[redacted]"
    assert redact_secret("anything") == "[redacted]"
    assert env_configured("PATH") is True


def test_restore_postgres_redacts_psql_stderr():
    src = Path("scripts/restore_postgres.py").read_text(encoding="utf-8")
    assert "print(proc.stderr" not in src
    assert "stderr redacted" in src
