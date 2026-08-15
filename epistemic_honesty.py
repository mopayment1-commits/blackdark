"""Epistemic honesty — prefer I DON'T KNOW over a theatrical WAIT.

Public directional labels (bullish/bearish/neutral/risk) are only allowed when
the system actually formed a view. Dimension conflict veto/abstain and typed
insufficient evidence must surface as I_DONT_KNOW — not NEUTRAL_OBSERVE.

This module never invents a view. Execution stays blocked (internal WAIT /
Do Not Touch). Net-Edge reject of an otherwise formed view remains a known
stand-down, not ignorance.
"""

from __future__ import annotations

from typing import Any

from regulatory_compliance_guard import PUBLIC_VERDICT_UNKNOWN, to_public_verdict

REASON_VETO = "dimension_conflict_veto"
REASON_ABSTAIN = "dimension_conflict_abstain"
REASON_INSUFFICIENT = "insufficient_evidence"


def is_i_dont_know(verdict: Any) -> bool:
    v = str(verdict or "").strip().upper().replace(" ", "_").replace("-", "_")
    return v in {"I_DONT_KNOW", "I_DON'T_KNOW", "INSUFFICIENT", "INSUFFICIENT_EVIDENCE", "UNKNOWN", "ABSTAIN"}


def _conflict_meta(payload: dict[str, Any]) -> dict[str, Any]:
    meta = payload.get("dimension_conflict")
    if isinstance(meta, dict):
        return meta
    return {}


def _confidence_claim(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("confidence_claim")
    if isinstance(raw, dict):
        return raw
    conf = payload.get("confidence")
    if isinstance(conf, dict) and conf.get("confidence_type"):
        return conf
    return {}


def epistemic_reasons(payload: dict[str, Any]) -> list[str]:
    """Return why a formed directional view is forbidden. Empty = view allowed."""
    reasons: list[str] = []
    conflict = _conflict_meta(payload)
    if conflict.get("veto"):
        reasons.append(REASON_VETO)
    elif conflict.get("abstain"):
        reasons.append(REASON_ABSTAIN)
    claim = _confidence_claim(payload)
    if claim.get("confidence_type") == "insufficient_evidence" or is_i_dont_know(claim.get("display")):
        reasons.append(REASON_INSUFFICIENT)
    if is_i_dont_know(payload.get("verdict") or payload.get("oracle_verdict")):
        if REASON_INSUFFICIENT not in reasons and REASON_VETO not in reasons and REASON_ABSTAIN not in reasons:
            reasons.append(REASON_INSUFFICIENT)
    # Unique, stable order.
    seen: set[str] = set()
    ordered: list[str] = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            ordered.append(r)
    return ordered


def apply_epistemic_honesty(payload: dict[str, Any]) -> dict[str, Any]:
    """Stamp I_DONT_KNOW when no directional view is justified."""
    out = dict(payload)
    reasons = epistemic_reasons(out)
    if not reasons:
        out.setdefault("epistemic_state", "formed_view")
        out["i_dont_know"] = False
        out.setdefault("epistemic_reasons", [])
        return out

    prior = str(out.get("verdict") or "")
    if prior and not is_i_dont_know(prior):
        out.setdefault("verdict_before_epistemic", prior)
    public = to_public_verdict(PUBLIC_VERDICT_UNKNOWN)
    out["verdict"] = public
    if "oracle_verdict" in out:
        out["oracle_verdict"] = public
    out["epistemic_state"] = "i_dont_know"
    out["i_dont_know"] = True
    out["epistemic_reasons"] = reasons
    out["decision_action"] = PUBLIC_VERDICT_UNKNOWN
    return out
