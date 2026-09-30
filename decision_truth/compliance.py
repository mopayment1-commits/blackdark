"""DTS-008 / DTS-049 compliance guards on Decision Truth outputs."""

from __future__ import annotations

import re
from typing import Any

_PROHIBITED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bBLACKDARK is the only\b", re.IGNORECASE),
    re.compile(r"\ball traders lose\b", re.IGNORECASE),
    re.compile(r"\bguaranteed\b", re.IGNORECASE),
    re.compile(r"\b100% accurate\b", re.IGNORECASE),
)


def apply_dts_compliance_guards(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip prohibited certainty/marketing claims from DTS-visible outputs."""
    out = dict(payload)
    dt = dict(out.get("decision_truth") or {})
    contract = dict(dt.get("contract") or {})

    for key in ("why", "why_not", "human_explanation"):
        val = contract.get(key) if key != "human_explanation" else (dt.get("why_not") or {}).get("human_explanation")
        if isinstance(val, list):
            contract[key] = [_sanitize_text(str(item)) for item in val]
        elif isinstance(val, str):
            if key == "human_explanation":
                dt.setdefault("why_not", {})["human_explanation"] = _sanitize_text(val)
            else:
                contract[key] = _sanitize_text(val)

    narrative = str(out.get("narrative") or out.get("analysis") or "")
    if narrative and _contains_prohibited(narrative):
        out["compliance_violation"] = "prohibited_marketing_claim"
        out["narrative"] = _sanitize_text(narrative)

    dt["contract"] = contract
    dt["compliance"] = {
        "marketing_claims_blocked": True,
        "excluded_defects_enforced": True,
        "unsupported_causality_blocked": True,
    }
    out["decision_truth"] = dt
    from decision_truth.product.causality import contains_unsupported_causality, sanitize_causal_language

    out = sanitize_causal_language(out)
    narrative = str(out.get("narrative") or out.get("analysis") or "")
    if narrative and contains_unsupported_causality(narrative):
        out["causality_violation"] = "unsupported_causal_claim"
    return out


def _contains_prohibited(text: str) -> bool:
    return any(p.search(text) for p in _PROHIBITED_PATTERNS)


def _sanitize_text(text: str) -> str:
    cleaned = text
    for pattern in _PROHIBITED_PATTERNS:
        cleaned = pattern.sub("[claim removed — insufficient evidence]", cleaned)
    return cleaned


def apply_user_agency(payload: dict[str, Any]) -> dict[str, Any]:
    """DTS-004 — informational analytics; never imperative execution instruction."""
    out = dict(payload)
    from regulatory_compliance_guard import REGULATORY_DISCLAIMER, to_public_verdict

    verdict = str(out.get("verdict") or "WAIT")
    out["verdict"] = to_public_verdict(verdict)
    out.setdefault("user_agency", {})
    out["user_agency"] = {
        "informational_only": True,
        "user_retains_decision_authority": True,
        "disclaimer": REGULATORY_DISCLAIMER,
        "not_execution_instruction": True,
    }
    state = str(out.get("decision_truth_state") or (out.get("decision_truth") or {}).get("contract", {}).get("decision_state") or "")
    if state in {"REJECTED", "ABSTAINED", "UNAVAILABLE", "DEGRADED"}:
        out["decision_action"] = "NO_DECISION"
    return out
