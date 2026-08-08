"""Guardrail: architectural audit v2 flaws must stay closed in-repo."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_and_architecture_exist():
    assert (ROOT / "README.md").is_file()
    assert (ROOT / "ARCHITECTURE.md").is_file()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "postgresql" in readme.lower()
    assert "docker compose" in readme.lower() or "docker-compose" in readme.lower()


def test_prod_compose_and_k8s_exist():
    assert (ROOT / "docker-compose.prod.yml").is_file()
    for name in (
        "namespace.yaml",
        "deployment.yaml",
        "service.yaml",
        "hpa.yaml",
        "configmap.yaml",
        "secret.example.yaml",
        "README.md",
    ):
        assert (ROOT / "k8s" / name).is_file(), name


def test_vault_rotation_script_exists():
    assert (ROOT / "scripts" / "rotate_vault_key.py").is_file()
    assert (ROOT / "scripts" / "run_coverage.py").is_file()
    assert (ROOT / "scripts" / "load_test_10k.py").is_file()


def test_oauth_mrr_legal_shield_modules_importable():
    import admin_mfa
    import billing_service
    import legal_shield
    import oauth_service
    import production_guard

    assert hasattr(billing_service, "generate_mrr_report")
    assert hasattr(billing_service, "compute_churn_rate")
    assert legal_shield.SYSTEM_CLASSIFICATION == "analytical_tool"
    assert callable(oauth_service.oauth_status)
    assert callable(admin_mfa.verify_totp)
    assert callable(production_guard.evaluate_production_guard)


def test_privacy_and_terms_templates():
    assert (ROOT / "templates" / "privacy.html").is_file()
    assert (ROOT / "templates" / "terms.html").is_file()
    assert (ROOT / "templates" / "request_deletion.html").is_file()
