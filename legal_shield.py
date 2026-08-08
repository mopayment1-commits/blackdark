"""
BLACKDARK — Strict Disclaimer Architecture (4-layer code shield).

Engineering control pack. No third-party legal APIs.
Hardcoded, non-optional disclaimers + consent gate + public classification.
"""

from __future__ import annotations

from typing import Any

# ── Layer 2 — System classification (immutable product posture) ──────────────
SYSTEM_CLASSIFICATION = "analytical_tool"
IS_FINANCIAL_ADVISOR = False
REGULATORY_STATUS = "not_regulated"
ORACLE_CLASSIFICATION_LABEL = "[Probabilistic Analysis – Not Financial Advice]"

# ── Layer 1 — Mandatory prefix on every AI / Oracle narrative ────────────────
MANDATORY_DISCLAIMER_PREFIX = (
    "DISCLAIMER: This is not financial advice. "
    "BLACKDARK is a probabilistic analysis tool. "
    "All content is for educational purposes only. "
    "You are 100% responsible for your own investment decisions."
)

# Extended disclaimer for metadata / compliance_footer fields
STRICT_DISCLAIMER = (
    f"{MANDATORY_DISCLAIMER_PREFIX} "
    "Past performance does NOT guarantee future results. "
    "Always do your own research (DYOR) before making any trade. "
    "BLACKDARK is not a registered investment adviser, broker-dealer, or MiCA CASP."
)

# ── Layer 3 — Explicit consent copy ──────────────────────────────────────────
CONSENT_ACK_TEXT = (
    "I acknowledge that BLACKDARK is not a financial advisor. "
    "I accept full responsibility for my trades."
)
CONSENT_VERSION = "legal-shield-v1"

# ── Layer 4 — Permanent site footer ──────────────────────────────────────────
PERMANENT_FOOTER_TEXT = (
    "BLACKDARK is an analytical tool. Not financial advice. "
    "No guarantee of accuracy or profit."
)

_NARRATIVE_KEYS = (
    "oracle",
    "narrative",
    "decision_sentence",
    "action_line",
    "sentence",
    "explanation_text",
)


def get_disclaimer() -> str:
    return STRICT_DISCLAIMER


def get_mandatory_prefix() -> str:
    return MANDATORY_DISCLAIMER_PREFIX


def system_classification_payload() -> dict[str, Any]:
    return {
        "system_classification": SYSTEM_CLASSIFICATION,
        "is_financial_advisor": IS_FINANCIAL_ADVISOR,
        "regulatory_status": REGULATORY_STATUS,
        "oracle_classification_label": ORACLE_CLASSIFICATION_LABEL,
        "mandatory_disclaimer": MANDATORY_DISCLAIMER_PREFIX,
        "permanent_footer": PERMANENT_FOOTER_TEXT,
        "consent_ack_text": CONSENT_ACK_TEXT,
        "consent_version": CONSENT_VERSION,
        "legal_shield_layers": [
            "mandatory_ai_disclaimer_prefix",
            "system_classification_metadata",
            "explicit_user_consent_gate",
            "permanent_frontend_footer",
        ],
        "note": (
            "Code-level analytical-tool posture controls. "
            "Not a claim of SEC/MiCA licensing or counsel sign-off."
        ),
    }


def _already_prefixed(text: str) -> bool:
    head = (text or "").lstrip()[:48].upper()
    return head.startswith("DISCLAIMER:") or head.startswith("⚠️ DISCLAIMER:")


def prefix_disclaimer(text: str | None) -> str:
    """Hardcode Layer-1 prefix; never optional."""
    body = (text or "").strip()
    if not body:
        return MANDATORY_DISCLAIMER_PREFIX
    if _already_prefixed(body):
        return body
    return f"{MANDATORY_DISCLAIMER_PREFIX}\n\n{body}"


def apply_legal_shield(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Layer 1+2 injection into any Oracle / AI JSON payload.
    Always present — not user-toggleable.
    """
    out = dict(payload)

    for key in _NARRATIVE_KEYS:
        if isinstance(out.get(key), str) and out[key].strip():
            out[key] = prefix_disclaimer(str(out[key]))

    # Prefix long action narratives only (keep short ACT/WAIT labels clean for UI chips).
    action = out.get("action")
    if isinstance(action, str) and len(action.strip()) > 40:
        out["action"] = prefix_disclaimer(action)

    if isinstance(out.get("explanation"), dict):
        exp = dict(out["explanation"])
        for key in ("summary", "narrative", "text", "detail"):
            if isinstance(exp.get(key), str) and exp[key].strip():
                exp[key] = prefix_disclaimer(str(exp[key]))
        out["explanation"] = exp

    out["disclaimer"] = STRICT_DISCLAIMER
    out["mandatory_disclaimer_prefix"] = MANDATORY_DISCLAIMER_PREFIX
    out["oracle_classification_label"] = ORACLE_CLASSIFICATION_LABEL
    out["system_classification"] = SYSTEM_CLASSIFICATION
    out["is_financial_advisor"] = IS_FINANCIAL_ADVISOR
    out["is_investment_advice"] = False
    out["regulatory_status"] = REGULATORY_STATUS
    out["legal_shield"] = "strict_disclaimer_architecture_v1"

    footer = out.get("compliance_footer")
    if isinstance(footer, dict):
        foot = dict(footer)
    else:
        foot = {"surface": "oracle"}
    foot["disclaimer"] = STRICT_DISCLAIMER
    foot["classification_label"] = ORACLE_CLASSIFICATION_LABEL
    foot["permanent_footer"] = PERMANENT_FOOTER_TEXT
    foot["system_classification"] = SYSTEM_CLASSIFICATION
    out["compliance_footer"] = foot
    return out
