"""Critical ops closure — deepen heroes, prod posture, limited public docs."""

from __future__ import annotations

from pathlib import Path


def test_architecture_index_exists():
    root = Path(__file__).resolve().parents[1]
    text = (root / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "CANONICAL_BINDING" in text
    assert "PostgreSQL" in text
    assert "ISO 27001" in text or "ISO" in text


def test_public_openapi_filter_omits_admin_billing():
    from public_api_docs import filter_openapi_for_public, path_is_public

    assert path_is_public("/api/trust-os")
    assert path_is_public("/api/glass-box/challenge")
    assert not path_is_public("/api/admin/launch-checklist")
    assert not path_is_public("/webhook/lemon")
    schema = {
        "openapi": "3.1.0",
        "info": {"title": "t", "version": "1"},
        "paths": {
            "/api/trust-os": {"get": {}},
            "/api/admin/secret": {"get": {}},
            "/webhook": {"post": {}},
            "/api/security/status": {"get": {}},
        },
    }
    out = filter_openapi_for_public(schema)
    assert "/api/trust-os" in out["paths"]
    assert "/api/security/status" in out["paths"]
    assert "/api/admin/secret" not in out["paths"]
    assert "/webhook" not in out["paths"]
    assert out["x-blackdark"]["policy"] == "evidence_and_read_only"


def test_production_guard_forbids_sqlite_in_strict_prod(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("SOFT_LAUNCH", raising=False)
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "x" * 32)
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "y" * 16)
    monkeypatch.setenv("ADMIN_API_KEY", "z" * 24)
    monkeypatch.setenv("LEMON_SQUEEZY_CHECKOUT_PRO", "https://example.com/c")
    monkeypatch.setenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "whsec")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import config

    monkeypatch.setattr(config, "DATABASE_URL", "")
    monkeypatch.setattr(config, "SERVICE_MODE", "web")

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert report["strict_production"] is True
    assert "sqlite_forbidden_in_strict_production" in report["required_failures"]
    assert report["acquisition_honesty"]["iso_certificates_claimed"] is False


def test_production_guard_encryption_check_present(monkeypatch):
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.delenv("SECRETS_MASTER_KEY", raising=False)
    monkeypatch.delenv("SECRETS_VAULT_KEY", raising=False)
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "y" * 16)
    monkeypatch.setenv("ADMIN_API_KEY", "z" * 24)

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    ids = {c["id"] for c in report["checks"]}
    assert "at_rest_encryption_posture" in ids
    assert "at_rest_encryption_posture" in report["required_failures"]


def test_ui_aliases_and_docs_wired():
    root = Path(__file__).resolve().parents[1]
    dash = (root / "dashboard.py").read_text(encoding="utf-8")
    assert '@app.get("/errors")' in dash
    assert '@app.get("/public/accuracy-ledger")' in dash
    assert '@app.get("/my/discipline-mirror")' in dash
    assert "docs_url=None" in dash
    assert "public-openapi.json" in dash
    acc = (root / "templates" / "oracle_accuracy.html").read_text(encoding="utf-8")
    assert "Public Misses" in acc
    assert "/errors" in acc
    assert (root / "templates" / "docs_public.html").is_file()
    landing = (root / "templates" / "landing.html").read_text(encoding="utf-8")
    assert 'href="/errors"' in landing
