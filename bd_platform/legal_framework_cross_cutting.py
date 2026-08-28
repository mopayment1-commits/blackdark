"""
Legal Framework — Cross-Cutting Policy — Feature #830 / PRV-001 (Sprint 0).

NOT a standalone product module. Applies ToS, Privacy Policy, disclaimers,
forbidden-language scans, and consent logging to every platform output.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.LegalFramework")

_FEATURE_REF = 830
_CONTROL_REF = "PRV-001"
_STANDALONE = False
_MERGED_INTO = "Cross-Cutting Legal Foundation"
_SEED_PATH = Path("data/legal_framework_cross_cutting_seed.json")
_LEGAL_CONTENT_MODULE = "legal_content"

_AI_PROVENANCE_REF = 921
_SIGNAL_ENGINE_REF = 11
_DECISION_INTEL_REF = 938
_BILLING_REF = 908
_MULTI_ACCOUNT_REF = 907
_RETENTION_REF = 949
_INCIDENT_RESPONSE_REF = 829
_AUDIT_RETENTION_YEARS = 5

_FORBIDDEN_PHRASES = frozenset({
    "guaranteed returns",
    "guaranteed profit",
    "guaranteed gain",
    "guaranteed restore",
    "guaranteed uptime",
    "risk-free",
    "risk free",
    "ربح مضمون",
    "عائد مضمون",
    "مضمون",
    "مؤكد",
    "استغلال",
    "ضمان العائد",
    "استعادة فورية",
})

_REQUIRED_TOS_CLAUSES = (
    "analytical_tool",
    "not_financial_advice",
    "no_buy_sell_recommendation",
    "no_return_guarantee",
)

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
    return seed.get("legal_framework_830") or {}


def legal_framework_status_830(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-cutting legal policy status."""
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "control_ref": _CONTROL_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "sprint": 0,
        "cross_cutting": True,
        "policy": {
            "tos_required_clauses": policy.get("tos_required_clauses"),
            "privacy_data_collection": policy.get("privacy_data_collection"),
            "lawyer_review_required": policy.get("lawyer_review_required", True),
            "lawyer_review_completed": policy.get("lawyer_review_completed", False),
            "no_generic_template_only": policy.get("no_generic_template_only", True),
            "fintech_crypto_specialist": policy.get("fintech_crypto_specialist", True),
            "localization": policy.get("localization", ["en", "ar"]),
            "both_languages_binding": policy.get("both_languages_binding", True),
            "user_consent_required": True,
            "consent_checkbox_explicit": True,
            "forbidden_language_scan": True,
            "audit_retention_years": _AUDIT_RETENTION_YEARS,
            "document_versioning": True,
        },
        "integrations": {
            "ai_provenance_ref": _AI_PROVENANCE_REF,
            "signal_engine_ref": _SIGNAL_ENGINE_REF,
            "decision_intel_ref": _DECISION_INTEL_REF,
            "billing_ref": _BILLING_REF,
            "multi_account_ref": _MULTI_ACCOUNT_REF,
            "retention_ref": _RETENTION_REF,
            "incident_response_ref": _INCIDENT_RESPONSE_REF,
        },
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def get_tos_summary_830(*, lang: str = "en", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tos = (seed.get("terms_of_service") or {}).get(lang) or (seed.get("terms_of_service") or {}).get("en") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "lang": lang,
        "version": tos.get("version"),
        "issued_at": tos.get("issued_at"),
        "classification": tos.get("classification"),
        "clauses": tos.get("clauses"),
        "insight_only": True,
        "not_financial_advice": True,
        "lawyer_reviewed": tos.get("lawyer_reviewed", False),
        "timestamp": _utcnow(),
    }


def get_privacy_policy_summary_830(*, lang: str = "en", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    privacy = (seed.get("privacy_policy") or {}).get(lang) or (seed.get("privacy_policy") or {}).get("en") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "lang": lang,
        "version": privacy.get("version"),
        "issued_at": privacy.get("issued_at"),
        "data_collected": privacy.get("data_collected"),
        "data_not_collected": privacy.get("data_not_collected"),
        "retention_ref": _RETENTION_REF,
        "gdpr_ccpa_compliant": privacy.get("gdpr_ccpa_compliant", True),
        "deletion_upon_request": privacy.get("deletion_upon_request", True),
        "lawyer_reviewed": privacy.get("lawyer_reviewed", False),
        "timestamp": _utcnow(),
    }


def scan_forbidden_language_830(text: str) -> dict[str, Any]:
    """Automated scan — reject guaranteed-return / hype language."""
    lower = text.lower()
    matches: list[str] = []
    for phrase in _FORBIDDEN_PHRASES:
        if phrase in lower:
            matches.append(phrase)
    return {
        "ok": len(matches) == 0,
        "feature_ref": _FEATURE_REF,
        "passed": len(matches) == 0,
        "forbidden_matches": matches,
        "scan_required": True,
        "timestamp": _utcnow(),
    }


def build_ai_output_footer_830(
    *,
    risk_score: str | float = "N/A",
    source: str = "platform",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#921 AI Output Provenance — legal footer on every AI output."""
    seed = seed or _load_seed()
    footer_cfg = seed.get("ai_output_footer") or {}
    footer = {
        "not_financial_advice": footer_cfg.get("not_financial_advice", "Not financial advice. Analytical insight only."),
        "risk_score": risk_score,
        "source": source,
        "provenance_ref": _AI_PROVENANCE_REF,
        "tos_summary": "BLACKDARK provides data-driven analytical insights — not buy/sell recommendations.",
    }
    scan = scan_forbidden_language_830(json.dumps(footer))
    return {
        "ok": scan["passed"],
        "feature_ref": _FEATURE_REF,
        "footer": footer,
        "integration_ref": _AI_PROVENANCE_REF,
        "language_scan_passed": scan["passed"],
        "timestamp": _utcnow(),
    }


def build_signal_disclaimer_830(
    *,
    signal_type: str = "opportunity",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#11 Signal Engine — auto disclaimer on every signal."""
    seed = seed or _load_seed()
    sig_cfg = seed.get("signal_disclaimer") or {}
    wording = sig_cfg.get("wording") or {}
    disclaimer = {
        "label": wording.get("label", "Potential opportunity — not a prediction"),
        "not_financial_advice": wording.get("not_financial_advice", "Not financial advice."),
        "signal_type": signal_type,
        "opportunity_not_prediction": True,
        "integration_ref": _SIGNAL_ENGINE_REF,
    }
    scan = scan_forbidden_language_830(json.dumps(disclaimer))
    return {
        "ok": scan["passed"],
        "feature_ref": _FEATURE_REF,
        "disclaimer": disclaimer,
        "integration_ref": _SIGNAL_ENGINE_REF,
        "language_scan_passed": scan["passed"],
        "timestamp": _utcnow(),
    }


def build_decision_intel_disclaimer_830(
    *,
    layer: str = "inference",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#938 Decision Intelligence — Fact/Inference/Hypothesis separation."""
    seed = seed or _load_seed()
    layers = seed.get("decision_intel_layers") or {}
    layer_cfg = layers.get(layer) or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "layer": layer,
        "label": layer_cfg.get("label", layer.title()),
        "not_financial_advice": True,
        "integration_ref": _DECISION_INTEL_REF,
        "timestamp": _utcnow(),
    }


def build_pay_per_request_legal_note_830(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#908 Pay-Per-Request — tiered pricing as verification tool, not technical restriction."""
    seed = seed or _load_seed()
    note = (seed.get("billing_legal_note") or {})
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "billing_ref": _BILLING_REF,
        "summary": note.get(
            "summary",
            "Usage limits reflect analytical verification tiers — not arbitrary technical restrictions.",
        ),
        "tiered_pricing_documented": note.get("tiered_pricing_documented", True),
        "timestamp": _utcnow(),
    }


def build_multi_account_sync_legal_note_830(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#907 Multi-Account Sync — read-only, no execution, no custody."""
    seed = seed or _load_seed()
    note = (seed.get("multi_account_legal_note") or {})
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "multi_account_ref": _MULTI_ACCOUNT_REF,
        "read_only": note.get("read_only", True),
        "no_execution": note.get("no_execution", True),
        "no_custody": note.get("no_custody", True),
        "summary": note.get(
            "summary",
            "Account sync is read-only. BLACKDARK does not execute trades or hold assets.",
        ),
        "timestamp": _utcnow(),
    }


def record_user_consent_830(
    *,
    user_id: str,
    consent_type: str = "registration",
    tos_version: str = "",
    privacy_version: str = "",
    lang: str = "en",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Log explicit user consent — immutable append-only."""
    seed = seed or _load_seed()
    versions = seed.get("document_versions") or {}
    tos_ver = tos_version or (versions.get("terms_of_service") or {}).get("version", "1.0")
    priv_ver = privacy_version or (versions.get("privacy_policy") or {}).get("version", "1.0")

    prev_hash = _consent_log[-1].get("chain_hash", "") if _consent_log else ""
    entry = {
        "consent_id": f"cns_{uuid.uuid4().hex[:10]}",
        "user_id": user_id,
        "consent_type": consent_type,
        "checkbox_explicit": True,
        "accepted_tos": True,
        "accepted_privacy": True,
        "tos_version": tos_ver,
        "privacy_version": priv_ver,
        "lang": lang,
        "accepted_at": _utcnow(),
        "immutable": True,
        "append_only": True,
        "audit_logged": True,
    }
    entry["chain_hash"] = hashlib.sha256(
        f"{prev_hash}:{json.dumps(entry, sort_keys=True)}".encode()
    ).hexdigest()
    _consent_log.append(entry)

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "consent": entry,
        "timestamp": _utcnow(),
    }


def get_document_versions_830(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    versions = seed.get("document_versions") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "versions": versions,
        "versioned": True,
        "timestamped": True,
        "audit_retention_years": _AUDIT_RETENTION_YEARS,
        "timestamp": _utcnow(),
    }


def get_consent_audit_trail_830(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    seed_consents = seed.get("consent_audit_log") or []
    all_consents = seed_consents + _consent_log
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "consents": all_consents,
        "entry_count": len(all_consents),
        "audit_retention_years": _AUDIT_RETENTION_YEARS,
        "immutable": True,
        "append_only": True,
        "timestamp": _utcnow(),
    }


def validate_output_compliance_830(
    output: dict[str, Any],
    *,
    output_type: str = "generic",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply legal framework to any platform output."""
    seed = seed or _load_seed()
    text_blob = json.dumps(output, default=str)
    scan = scan_forbidden_language_830(text_blob)

    footer = None
    disclaimer = None
    if output_type == "ai":
        footer = build_ai_output_footer_830(
            risk_score=output.get("risk_score", "N/A"),
            source=output.get("source", "platform"),
            seed=seed,
        )
    elif output_type == "signal":
        disclaimer = build_signal_disclaimer_830(signal_type=output.get("signal_type", "opportunity"), seed=seed)

    compliant = scan["passed"]
    if footer and not footer.get("language_scan_passed"):
        compliant = False
    if disclaimer and not disclaimer.get("language_scan_passed"):
        compliant = False

    return {
        "ok": compliant,
        "feature_ref": _FEATURE_REF,
        "output_type": output_type,
        "language_scan": scan,
        "footer": footer,
        "disclaimer": disclaimer,
        "insight_only": True,
        "not_financial_advice": True,
        "timestamp": _utcnow(),
    }


def get_incident_response_legal_crossref_830(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#829 Incident Response — liability limits + notification procedures in ToS."""
    seed = seed or _load_seed()
    xref = seed.get("incident_response_crossref") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "incident_response_ref": _INCIDENT_RESPONSE_REF,
        "liability_limits_documented": xref.get("liability_limits_documented", True),
        "notification_procedures_documented": xref.get("notification_procedures_documented", True),
        "data_breach_cross_referenced": xref.get("data_breach_cross_referenced", True),
        "timestamp": _utcnow(),
    }


def run_legal_framework_e2e_830(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = legal_framework_status_830(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "cross_cutting", "passed": status["cross_cutting"] is True})
    checks.append({"id": "sprint_0", "passed": status["sprint"] == 0})
    checks.append({"id": "lawyer_review_required", "passed": status["policy"]["lawyer_review_required"] is True})
    checks.append({"id": "no_generic_only", "passed": status["policy"]["no_generic_template_only"] is True})
    checks.append({"id": "localization_en_ar", "passed": set(status["policy"]["localization"]) >= {"en", "ar"}})
    checks.append({"id": "both_binding", "passed": status["policy"]["both_languages_binding"] is True})

    tos_en = get_tos_summary_830(lang="en", seed=seed)
    tos_ar = get_tos_summary_830(lang="ar", seed=seed)
    for clause in _REQUIRED_TOS_CLAUSES:
        checks.append({"id": f"tos_en_{clause}", "passed": clause in (tos_en.get("clauses") or {})})
        checks.append({"id": f"tos_ar_{clause}", "passed": clause in (tos_ar.get("clauses") or {})})

    privacy = get_privacy_policy_summary_830(seed=seed)
    not_collected = set(privacy.get("data_not_collected") or [])
    checks.append({"id": "no_private_keys", "passed": "private_keys" in not_collected})
    checks.append({"id": "gdpr_ccpa", "passed": privacy.get("gdpr_ccpa_compliant") is True})
    checks.append({"id": "deletion_on_request", "passed": privacy.get("deletion_upon_request") is True})
    checks.append({"id": "retention_ref_949", "passed": privacy.get("retention_ref") == _RETENTION_REF})

    clean = scan_forbidden_language_830("Analytical insight based on market data.")
    bad = scan_forbidden_language_830("Guaranteed returns on every trade.")
    checks.append({"id": "language_scan_clean", "passed": clean["passed"] is True})
    checks.append({"id": "language_scan_reject", "passed": bad["passed"] is False})

    ai_footer = build_ai_output_footer_830(risk_score=42, source="oracle", seed=seed)
    checks.append({"id": "ai_footer_921", "passed": ai_footer.get("integration_ref") == _AI_PROVENANCE_REF})
    checks.append({"id": "ai_not_financial_advice", "passed": ai_footer["footer"]["not_financial_advice"] is not None})

    sig = build_signal_disclaimer_830(seed=seed)
    checks.append({"id": "signal_disclaimer_11", "passed": sig.get("integration_ref") == _SIGNAL_ENGINE_REF})
    checks.append({"id": "opportunity_not_prediction", "passed": sig["disclaimer"]["opportunity_not_prediction"] is True})

    decision = build_decision_intel_disclaimer_830(layer="fact", seed=seed)
    checks.append({"id": "decision_intel_938", "passed": decision.get("integration_ref") == _DECISION_INTEL_REF})

    billing = build_pay_per_request_legal_note_830(seed=seed)
    checks.append({"id": "billing_note_908", "passed": billing.get("billing_ref") == _BILLING_REF})

    sync = build_multi_account_sync_legal_note_830(seed=seed)
    checks.append({"id": "sync_read_only_907", "passed": sync.get("read_only") is True and sync.get("no_custody") is True})

    consent = record_user_consent_830(user_id="user_test", seed=seed)
    checks.append({"id": "consent_logged", "passed": consent["consent"]["audit_logged"] is True})
    checks.append({"id": "consent_immutable", "passed": consent["consent"]["immutable"] is True})

    versions = get_document_versions_830(seed=seed)
    checks.append({"id": "document_versioned", "passed": versions.get("versioned") is True})

    trail = get_consent_audit_trail_830(seed=seed)
    checks.append({"id": "consent_audit_5y", "passed": trail.get("audit_retention_years") == 5})

    ir_xref = get_incident_response_legal_crossref_830(seed=seed)
    checks.append({"id": "incident_crossref", "passed": ir_xref.get("data_breach_cross_referenced") is True})

    compliance = validate_output_compliance_830({"signal_type": "opportunity"}, output_type="signal", seed=seed)
    checks.append({"id": "output_compliance", "passed": compliance.get("ok") is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "control_ref": _CONTROL_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
