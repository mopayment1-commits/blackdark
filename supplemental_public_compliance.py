"""
Launch-57 public layer — Supplemental Memorandum (21 Sep 2026) controls.

UK-S01/S02, UK-S03, EGY-C04/C05, EU-S01–S06, SUB-C01–C03, PRV-C01–C06.
Applies to visitor + free-account public surfaces only (not institutional/paid gating expansion).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from starlette.requests import Request

logger = logging.getLogger("BLACKDARK.SupplementalPublicCompliance")

CONDITIONS_MET_REVIEW_LINE = (
    "Analytical state only - the model's stated conditions are currently met. "
    "No transaction or investment action is recommended."
)

PUBLIC_MODEL_STATE_CONDITIONS_MET = "CONDITIONS MET"
PUBLIC_MODEL_STATE_WAIT = "WAIT"
PUBLIC_MODEL_STATE_ABSTAIN = "ABSTAIN"

REGULATORY_DISCLAIMER_EGY = (
    "BLACKDARK provides market-data and analytical technology. "
    "Regulatory treatment depends on the service and jurisdiction."
)

# PRV-C — Supplemental Memorandum §8.4 (optional analytics; verbatim structure)
EU_OPTIONAL_ANALYTICS_BANNER_BODY = (
    "BLACKDARK uses strictly necessary technologies to operate and secure the service. "
    "With your permission, we may also use optional analytics technologies to understand how the service is used. "
    "Optional technologies remain disabled unless you choose to accept them. "
    "You can accept, reject, or manage your preferences."
)

CONSENT_COOKIE = "bd_optional_analytics"
CONSENT_CHOICE_ACCEPT = "accept"
CONSENT_CHOICE_REJECT = "reject"
CONSENT_DISMISS_COOKIE = "bd_optional_analytics_banner_seen"

_EEA_ISO2 = frozenset(
    {
        "AT",
        "BE",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "HU",
        "IE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE",
        "IS",
        "LI",
        "NO",
        "CH",
        "GB",
        "GI",
        "IM",
        "JE",
        "GG",
    }
)

_TRADE_CTA_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bBuy Now\b", re.I),
    re.compile(r"\bStart Trading\b", re.I),
    re.compile(r"\bTrade now\b", re.I),
    re.compile(r"\bBest opportunity\b", re.I),
    re.compile(r"\bExpected return\b", re.I),
    re.compile(r"\bACT\s*[-–—:]\s*Buy\b", re.I),
    re.compile(r"\bACT on\b", re.I),
)

_SUBSCRIPTION_DENY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bMake money\b", re.I),
    re.compile(r"\bGuaranteed\b", re.I),
    re.compile(r"\bEarn\s+\d+\s*%", re.I),
    re.compile(r"\bBest crypto to buy\b", re.I),
    re.compile(r"\bStart trading\b", re.I),
    re.compile(r"\bBeat the market\b", re.I),
)

_REGULATORY_CLAIM_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bFCA authorised\b", re.I),
    re.compile(r"\bCASP\b", re.I),
    re.compile(r"\bMiCA regulated\b", re.I),
    re.compile(r"\bCBE\b", re.I),
    re.compile(r"\bFRA\b", re.I),
    re.compile(r"\bUK compliant\b", re.I),
    re.compile(r"\bEU compliant\b", re.I),
)

_ALLOWED_PRICING_PHRASES = (
    "Access advanced analytics",
    "Unlock tools",
    "Higher limits",
    "Upgrade for more capacity",
    "Decision Pro trial",
)

_CONSENT_LOG = Path("data/supplemental_optional_analytics_consent.jsonl")


def is_public_free_layer(user: Mapping[str, Any] | None) -> bool:
    if user is None:
        return True
    tier = str(user.get("tier") or "free").lower()
    return tier in {"free", ""}


def _country_from_request(request: Request | None) -> str:
    if request is None:
        return ""
    for header in (
        "CF-IPCountry",
        "CloudFront-Viewer-Country",
        "X-Vercel-IP-Country",
        "X-Country-Code",
    ):
        raw = (request.headers.get(header) or "").strip().upper()
        if len(raw) == 2:
            return raw
    if (request.headers.get("X-BD-EEA-SIMULATE") or "").strip().lower() in {"1", "true", "yes"}:
        return "DE"
    return ""


def is_eea_request(request: Request | None) -> bool:
    code = _country_from_request(request)
    return code in _EEA_ISO2


def consent_choice_from_request(request: Request | None) -> str | None:
    if request is None:
        return None
    raw = (request.cookies.get(CONSENT_COOKIE) or "").strip().lower()
    if raw in {CONSENT_CHOICE_ACCEPT, CONSENT_CHOICE_REJECT}:
        return raw
    return None


def optional_analytics_allowed(request: Request | None) -> bool:
    if not is_eea_request(request):
        return True
    return consent_choice_from_request(request) == CONSENT_CHOICE_ACCEPT


def eu_personalization_blocked(request: Request | None, user: Mapping[str, Any] | None) -> bool:
    """EU-S01–S06: no portfolio/personalized recommendation path for EEA public layer."""
    return is_eea_request(request) and is_public_free_layer(user)


def map_public_decision_action(raw: str | None) -> str:
    token = (raw or "").strip().upper()
    if token in {"ACT", "BUY", "LONG", "BULLISH", "BULLISH_ANALYTICS"}:
        return PUBLIC_MODEL_STATE_CONDITIONS_MET
    if token in {
        "SELL",
        "SHORT",
        "EXIT",
        "CAUTION",
        "AVOID",
        "DO_NOT_TOUCH",
        "BEARISH",
        "BEARISH_ANALYTICS",
    }:
        return PUBLIC_MODEL_STATE_ABSTAIN
    if token in {"WAIT", "HOLD", "NEUTRAL", "NEUTRAL_OBSERVE", "ABSTAIN"}:
        return PUBLIC_MODEL_STATE_WAIT
    if "CONDITION" in token:
        return PUBLIC_MODEL_STATE_CONDITIONS_MET
    return PUBLIC_MODEL_STATE_WAIT


def public_decision_sentence(asset: str, model_state: str) -> str:
    sym = (asset or "ASSET").strip().upper() or "ASSET"
    if model_state == PUBLIC_MODEL_STATE_CONDITIONS_MET:
        return f"MODEL STATE: {PUBLIC_MODEL_STATE_CONDITIONS_MET} — {sym}. {CONDITIONS_MET_REVIEW_LINE}"
    if model_state == PUBLIC_MODEL_STATE_ABSTAIN:
        return f"MODEL STATE: {PUBLIC_MODEL_STATE_ABSTAIN} — {sym}. Analytical abstention; no action recommended."
    return f"MODEL STATE: {PUBLIC_MODEL_STATE_WAIT} — {sym}. Monitoring state; no action recommended."


def scrub_prohibited_phrases(text: str) -> str:
    if not text:
        return text
    out = text
    for pattern in _TRADE_CTA_PATTERNS + _SUBSCRIPTION_DENY_PATTERNS + _REGULATORY_CLAIM_PATTERNS:
        out = pattern.sub("", out)
    return re.sub(r"\s{2,}", " ", out).strip()


def scrub_regulatory_claims(text: str) -> str:
    if not text:
        return text
    out = text
    for pattern in _REGULATORY_CLAIM_PATTERNS:
        if pattern.search(out):
            out = pattern.sub(REGULATORY_DISCLAIMER_EGY, out)
    return out


def _strip_personalization_keys(payload: dict[str, Any]) -> None:
    for key in (
        "persona_clarity",
        "portfolio_hint",
        "retention_hint",
        "personalized",
        "portfolio_ai",
        "holdings",
        "loss_tolerance",
        "investment_objective",
    ):
        payload.pop(key, None)


def apply_supplemental_public_layer(
    payload: dict[str, Any],
    *,
    user: Mapping[str, Any] | None = None,
    request: Request | None = None,
) -> dict[str, Any]:
    if not is_public_free_layer(user):
        return payload

    out = dict(payload)
    raw_action = str(
        out.get("decision_action") or out.get("action") or out.get("verdict") or ""
    )
    model_state = map_public_decision_action(raw_action)
    asset = str(out.get("symbol") or out.get("asset") or "ASSET")

    out["decision_action"] = model_state
    out["model_state"] = model_state
    out["public_layer"] = True
    if model_state == PUBLIC_MODEL_STATE_CONDITIONS_MET:
        out["conditions_met_review"] = CONDITIONS_MET_REVIEW_LINE
        out["decision_sentence"] = public_decision_sentence(asset, model_state)
        out["oracle"] = out.get("decision_sentence")
        out["action_line"] = out["decision_sentence"]

    for field in ("decision_sentence", "oracle", "action", "action_line", "narrative", "sentence"):
        if isinstance(out.get(field), str):
            out[field] = scrub_prohibited_phrases(scrub_regulatory_claims(str(out[field])))

    if eu_personalization_blocked(request, user):
        _strip_personalization_keys(out)
        out["eu_public_uniform_output"] = True
        out["personalization_blocked"] = "eea_fail_closed"

    out["supplemental_memo"] = "2026-09-21-public-layer"
    out["regulatory_posture_line"] = REGULATORY_DISCLAIMER_EGY
    return out


def record_optional_analytics_consent(
    *,
    choice: str,
    request: Request | None,
    user_email: str | None = None,
) -> dict[str, Any]:
    normalized = (choice or "").strip().lower()
    if normalized not in {CONSENT_CHOICE_ACCEPT, CONSENT_CHOICE_REJECT}:
        raise ValueError("invalid_consent_choice")
    row = {
        "ts": datetime.now(UTC).isoformat(),
        "choice": normalized,
        "eea": is_eea_request(request),
        "country": _country_from_request(request),
        "user_email": (user_email or "").strip().lower() or None,
        "path": (request.url.path if request else ""),
    }
    try:
        _CONSENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _CONSENT_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        logger.warning("optional analytics consent log failed", exc_info=True)
    return {"ok": True, "choice": normalized, "optional_analytics": normalized == CONSENT_CHOICE_ACCEPT}


def optional_analytics_banner_payload(request: Request | None) -> dict[str, Any]:
    eea = is_eea_request(request)
    choice = consent_choice_from_request(request)
    dismissed = False
    if request is not None:
        dismissed = (request.cookies.get(CONSENT_DISMISS_COOKIE) or "").strip() == "1"
    return {
        "eea_visitor": eea,
        "show_banner": bool(eea and choice is None and not dismissed),
        "body": EU_OPTIONAL_ANALYTICS_BANNER_BODY,
        "buttons": {
            "accept": "ACCEPT OPTIONAL",
            "reject": "REJECT OPTIONAL",
            "manage": "MANAGE PREFERENCES",
        },
        "choice": choice,
        "optional_analytics_allowed": optional_analytics_allowed(request),
        "dismiss_is_not_consent": True,
    }


def supplemental_public_compliance_status() -> dict[str, Any]:
    return {
        "governing": "Supplemental Memorandum 2026-09-21 + Principal Opinion",
        "scope": "public_visitor_and_free_account",
        "model_state_conditions_met": PUBLIC_MODEL_STATE_CONDITIONS_MET,
        "conditions_met_review_line": CONDITIONS_MET_REVIEW_LINE,
        "allowed_pricing_samples": list(_ALLOWED_PRICING_PHRASES),
        "regulatory_line": REGULATORY_DISCLAIMER_EGY,
        "eea_countries_supported": len(_EEA_ISO2),
    }
