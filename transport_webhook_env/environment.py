"""Environment isolation and crossover detection (FDS-14)."""

from __future__ import annotations

import hashlib
import os
import re
from typing import Any
from urllib.parse import urlparse

_STRIPE_TEST_RE = re.compile(r"^(sk|pk|rk|whsec)_test_", re.I)
_STRIPE_LIVE_RE = re.compile(r"^(sk|pk|rk|whsec)_live_", re.I)


def _env_tokens() -> list[str]:
    return [
        (os.getenv("ENV") or "").strip().lower(),
        (os.getenv("APP_ENV") or "").strip().lower(),
        (os.getenv("ENVIRONMENT") or "").strip().lower(),
        (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
    ]


def _is_production() -> bool:
    return any(t in {"production", "prod"} for t in _env_tokens())


def environment_identity() -> str:
    explicit = (os.getenv("DEPLOY_ENV") or os.getenv("ENVIRONMENT_NAME") or "").strip().lower()
    if explicit in {"production", "prod", "staging", "stage", "development", "dev", "test"}:
        if explicit in {"prod", "production"}:
            return "production"
        if explicit in {"stage", "staging"}:
            return "staging"
        return "development"
    if _is_production():
        return "production"
    if (os.getenv("STAGING", "").strip().lower() in {"1", "true", "yes"}) or (
        os.getenv("APP_ENV", "").strip().lower() in {"staging", "stage"}
    ):
        return "staging"
    return "development"


def _secret_namespace() -> str:
    return (os.getenv("SECRET_NAMESPACE") or os.getenv("DEPLOY_ENV") or environment_identity()).strip().lower()


def _db_host_fingerprint() -> str:
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        return "sqlite-local"
    try:
        host = urlparse(url).hostname or "unknown"
        return hashlib.sha256(host.encode("utf-8")).hexdigest()[:16]
    except Exception:
        return "invalid"


def detect_environment_crossovers() -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    env = environment_identity()
    stripe_key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    webhook_secret = (os.getenv("STRIPE_WEBHOOK_SECRET") or "").strip()

    if env == "production":
        if _STRIPE_TEST_RE.match(stripe_key):
            findings.append({"check": "production_test_stripe_key", "env": env})
        if _STRIPE_TEST_RE.match(webhook_secret):
            findings.append({"check": "production_test_webhook_secret", "env": env})
        if (os.getenv("SECRETS_MASTER_KEY") or "").strip() in {
            "blackdark-dev-change-me-in-production",
            "change-me",
        }:
            findings.append({"check": "production_development_default_secret", "env": env})
        if (os.getenv("SECRET_NAMESPACE") or "").strip().lower() in {"development", "dev", "test"}:
            findings.append({"check": "production_development_secret_namespace", "env": env})
    elif env in {"development", "staging"}:
        if _STRIPE_LIVE_RE.match(stripe_key):
            findings.append({"check": "nonprod_live_stripe_key", "env": env})
        if _STRIPE_LIVE_RE.match(webhook_secret):
            findings.append({"check": "nonprod_live_webhook_secret", "env": env})

    prod_db = (os.getenv("PRODUCTION_DATABASE_FINGERPRINT") or "").strip()
    current_db = _db_host_fingerprint()
    if env in {"development", "staging"} and prod_db and prod_db == current_db:
        findings.append({"check": "nonprod_production_database", "env": env})

    return findings


def environment_status() -> dict[str, Any]:
    return {
        "identity": environment_identity(),
        "secret_namespace": _secret_namespace(),
        "database_fingerprint": _db_host_fingerprint(),
        "crossovers": detect_environment_crossovers(),
    }
