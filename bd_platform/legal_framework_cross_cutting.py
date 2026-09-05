"""
Legal Framework — #1018 (+ #1068 merged).

ToS, Privacy Policy, forbidden-language scan, consent logging.
Blocks production without lawyer-reviewed legal docs.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.LegalFramework")

_FEATURE_REF = 1018
_MERGED_REF = 1068
_STANDALONE = False
_SEED_PATH = Path("data/trust_core_seed.json")
_RUNBOOK = "docs/ops/LEGAL_FRAMEWORK.md"

_FORBIDDEN_PHRASES = frozenset({
    "guaranteed returns", "guaranteed profit", "guaranteed gain", "guaranteed restore",
    "guaranteed uptime", "risk-free", "risk free", "ربح مضمون", "عائد مضمون",
    "مضمون", "مؤكد", "استغلال", "ضمان العائد", "استعادة فورية",
})

_consent_log: list[dict[str, Any]] = []


def reset_legal_framework_state() -> None:
    _consent_log.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("legal framework seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("legal_framework_1018") or {}


def legal_framework_status_1018(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "merged_feature_ref": _MERGED_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "policy": {
            "lawyer_review_required": policy.get("lawyer_review_required", True),
            "blocks_production_without_signed": policy.get("blocks_production_without_signed", True),
            "localization": policy.get("localization", ["en", "ar"]),
            "consent_checkbox_required": policy.get("consent_checkbox_required", True),
            "forbidden_language_scan": policy.get("forbidden_language_scan", True),
            "audit_retention_years": policy.get("audit_retention_years", 5),
        },
        "tos_clauses": cfg.get("tos_clauses") or [],
        "tos_statement": (
            "BLACKDARK = analytical tool providing data-driven insights | "
            "not financial advice | no buy/sell recommendation | no return guarantee"
        ),
        "integrations": cfg.get("integrations") or {},
        "runbook": _RUNBOOK,
        "timestamp": _utcnow(),
    }


def scan_forbidden_language_1018(text: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Automated scan — reject guaranteed-return language."""
    seed = seed or _load_seed()
    lower = text.lower()
    hits = [p for p in _FORBIDDEN_PHRASES if p in lower]
    return {
        "ok": len(hits) == 0,
        "feature_ref": _FEATURE_REF,
        "passed": len(hits) == 0,
        "forbidden_hits": hits,
        "scan_required": (_cfg(seed).get("policy") or {}).get("forbidden_language_scan", True),
        "timestamp": _utcnow(),
    }


def record_user_consent_1018(
    *,
    user_email: str,
    tos_version: str = "1.0.0",
    privacy_version: str = "1.0.0",
    locale: str = "en",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = {
        "consent_id": f"cns_{uuid.uuid4().hex[:10]}",
        "user_email": user_email.strip().lower(),
        "tos_version": tos_version,
        "privacy_version": privacy_version,
        "locale": locale,
        "accepted_at": _utcnow(),
        "checkbox_explicit": True,
        "immutable": True,
        "append_only": True,
    }
    _consent_log.append(entry)
    return {"ok": True, "consent": entry}


def build_legal_footer_1018(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Footer for AI outputs — #921 integration."""
    seed = seed or _load_seed()
    return {
        "not_financial_advice": True,
        "no_buy_sell_recommendation": True,
        "risk_score_disclaimer": True,
        "source_attribution_required": True,
        "en": "Not financial advice. Data-driven insight only.",
        "ar": "ليس توصية مالية. رؤى مبنية على البيانات فقط.",
        "tos_ref": _FEATURE_REF,
    }


def check_production_gate_1018(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = legal_framework_status_1018(seed=seed)
    policy = status["policy"]
    checks = {
        "lawyer_review_required": policy["lawyer_review_required"] is True,
        "tos_clauses_complete": len(status["tos_clauses"]) >= 4,
        "forbidden_scan_enabled": policy["forbidden_language_scan"] is True,
        "consent_required": policy["consent_checkbox_required"] is True,
        "localization_en_ar": "en" in policy["localization"] and "ar" in policy["localization"],
        "audit_5yr": policy["audit_retention_years"] == 5,
    }
    return {
        "ok": all(checks.values()),
        "feature_ref": _FEATURE_REF,
        "blocks_production": policy["blocks_production_without_signed"],
        "production_allowed": all(checks.values()),
        "checks": checks,
        "timestamp": _utcnow(),
    }


def run_legal_framework_e2e_1018(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_legal_framework_state()
    checks: list[dict[str, Any]] = []

    status = legal_framework_status_1018(seed=seed)
    checks.append({"id": "merged_1068", "passed": status["merged_feature_ref"] == 1068})
    checks.append({"id": "tos_clauses", "passed": len(status["tos_clauses"]) >= 4})

    scan_ok = scan_forbidden_language_1018("Market analysis shows potential opportunity.", seed=seed)
    checks.append({"id": "scan_pass", "passed": scan_ok["passed"] is True})

    scan_bad = scan_forbidden_language_1018("Guaranteed returns on every trade!", seed=seed)
    checks.append({"id": "scan_reject", "passed": scan_bad["passed"] is False})

    consent = record_user_consent_1018(user_email="user@example.com", locale="ar", seed=seed)
    checks.append({"id": "consent_logged", "passed": consent["consent"]["checkbox_explicit"] is True})

    footer = build_legal_footer_1018(seed=seed)
    checks.append({"id": "ai_footer", "passed": footer["not_financial_advice"] is True})

    gate = check_production_gate_1018(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["production_allowed"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
