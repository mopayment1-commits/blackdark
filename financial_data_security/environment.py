"""Environment isolation — production/staging/development trust boundaries."""

from __future__ import annotations

import os
from typing import Any


def current_environment() -> str:
    for name in ("ENV", "APP_ENV", "ENVIRONMENT", "RAILWAY_ENVIRONMENT"):
        val = (os.getenv(name) or "").strip().lower()
        if val in {"production", "prod"}:
            return "production"
        if val in {"staging", "stage", "preview"}:
            return "staging"
        if val in {"development", "dev", "local", "test"}:
            return "development"
    return "development"


def environment_isolation_status() -> dict[str, Any]:
    env = current_environment()
    stripe_live = (os.getenv("STRIPE_SECRET_KEY") or "").startswith("sk_live_")
    stripe_test = (os.getenv("STRIPE_SECRET_KEY") or "").startswith("sk_test_")
    violations: list[str] = []
    if env == "development" and stripe_live:
        violations.append("live_stripe_key_in_development")
    if env == "production" and stripe_test and os.getenv("STRIPE_SECRET_KEY"):
        violations.append("test_stripe_key_in_production")
    return {
        "environment": env,
        "production_secrets_in_dev": "live_stripe_key_in_development" in violations,
        "test_secrets_in_production": "test_stripe_key_in_production" in violations,
        "violations": violations,
        "pass": not violations,
    }
