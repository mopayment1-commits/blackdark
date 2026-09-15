"""DTS-055 — 38-locale i18n presentation boundary for Decision Truth."""

from __future__ import annotations

import re
from typing import Any

from decision_truth.cross_cutting.locales import CANONICAL_38_LOCALES, normalize_dts_locale
from i18n_service import EN, t

DTS_MESSAGE_KEYS: tuple[str, ...] = tuple(k for k in EN if k.startswith("dts."))

_REASON_CODE_KEYS: dict[str, str] = {
    "freshness_gate_failed": "dts.reason.freshness_gate_failed",
    "net_edge_truth_reject": "dts.reason.net_edge_truth_reject",
    "execution_feasibility_low": "dts.reason.execution_feasibility_low",
    "portfolio_risk_reject": "dts.reason.portfolio_risk_reject",
    "portfolio_risk_abstain": "dts.reason.portfolio_risk_abstain",
    "uncertainty_too_high": "dts.reason.uncertainty_too_high",
    "data_quality_below_floor": "dts.reason.data_quality_below_floor",
    "evidence_class_insufficient": "dts.reason.evidence_class_insufficient",
    "calibration_weak": "dts.reason.calibration_weak",
}

_STATE_KEYS = {
    "AVAILABLE": "dts.state.available",
    "DEGRADED": "dts.state.degraded",
    "ABSTAINED": "dts.state.abstained",
    "REJECTED": "dts.state.rejected",
    "UNAVAILABLE": "dts.state.unavailable",
}

_HERO_KEYS = {
    "my_capital": "dts.hero.my_capital",
    "market_state": "dts.hero.market_state",
    "best_verified_opportunity": "dts.hero.best_opportunity",
    "main_risk": "dts.hero.main_risk",
    "smart_money_evidence": "dts.hero.smart_money",
    "todays_decision_brief": "dts.hero.daily_brief",
}


def translate_reason_code(code: str, lang: str) -> str:
    for suffix, key in _REASON_CODE_KEYS.items():
        if suffix in code:
            return t(key, lang)
    return t("dts.reason.generic", lang, code=code)


def localize_dts_payload(payload: dict[str, Any], lang: str | None) -> dict[str, Any]:
    """Render user-facing DTS copy at presentation boundary only."""
    out = dict(payload)
    locale = normalize_dts_locale(lang or out.get("lang"))
    out["lang"] = locale
    product = dict(out.get("product_experience") or {})
    localized = _localize_product(product, locale)
    out["dts_i18n"] = localized
    out["product_experience"] = {**product, "localized": localized}
    dt = dict(out.get("decision_truth") or {})
    if dt:
        dt["localized"] = localized
        out["decision_truth"] = dt
    surface = out.get("todays_decision_surface")
    if isinstance(surface, dict):
        out["todays_decision_surface"] = _localize_decision_surface(surface, locale)
    return out


def _localize_product(product: dict[str, Any], lang: str) -> dict[str, Any]:
    state = str(
        ((product.get("no_decision") or {}).get("decision_truth_state"))
        or ((product.get("why_not_engine") or {}).get("decision_state"))
        or "UNAVAILABLE"
    )
    why = product.get("why_not_engine") or {}
    codes = list(why.get("codes") or [])
    localized_why = _localize_why_not(why, lang, state, codes)
    localized_no_decision = _localize_no_decision(product.get("no_decision") or {}, lang, state, codes)
    heroes = _localize_heroes(product.get("six_heroes") or {}, lang)
    daily = _localize_daily(product.get("daily_evidence_autopsy") or {}, lang)
    trail = _localize_trail(product.get("full_evidence_trail") or {}, lang)
    thirty = _localize_thirty(product.get("thirty_second_truth") or {}, lang, state)
    command = product.get("command_view")
    localized_command = (
        {"title": t("dts.command_view.title", lang), "enabled": True} if command else None
    )
    return {
        "locale": lang,
        "fallback_locale": "en",
        "canonical_message_keys": True,
        "decision_state_label": t(_STATE_KEYS.get(state, "dts.state.unavailable"), lang),
        "no_decision_label": t("dts.action.no_decision", lang),
        "why_not": localized_why,
        "no_decision": localized_no_decision,
        "rejection_summary": t(
            "dts.rejection.summary" if state == "REJECTED" else "dts.abstention.summary",
            lang,
        ),
        "six_heroes": heroes,
        "daily_evidence_autopsy": daily,
        "full_evidence_trail": trail,
        "thirty_second_truth": thirty,
        "command_view": localized_command,
        "reason_labels": [translate_reason_code(c, lang) for c in codes],
        "methodology_version": "dts-p6-i18n-1.0",
    }


def _localize_why_not(why: dict[str, Any], lang: str, state: str, codes: list[str]) -> dict[str, Any]:
    if state == "AVAILABLE":
        text = t("dts.why.admitted", lang)
    else:
        parts = [t("dts.why.generic_blocked", lang, state=t(_STATE_KEYS.get(state, "dts.state.unavailable"), lang))]
        machine = why.get("machine_readable") or {}
        econ = machine.get("economic_state") or {}
        if econ.get("expected_net_edge_bps") is not None:
            parts.append(t("dts.why.net_edge", lang, bps=econ["expected_net_edge_bps"]))
        exec_s = machine.get("execution_state") or {}
        if exec_s.get("score") is not None:
            parts.append(t("dts.why.execution", lang, score=exec_s["score"]))
        if (machine.get("freshness_state") or {}).get("state") in {"STALE", "UNKNOWN"}:
            parts.append(t("dts.why.freshness", lang))
        if any("conflict" in c.lower() for c in codes):
            parts.append(t("dts.why.conflict", lang))
        if codes:
            reasons = ", ".join(translate_reason_code(c, lang) for c in codes[:5])
            parts.append(t("dts.why.blocking", lang, reasons=reasons))
        text = " ".join(parts)
    return {
        "human_explanation": text,
        "reason_labels": [translate_reason_code(c, lang) for c in codes],
        "message_keys_used": True,
    }


def _localize_no_decision(no_dec: dict[str, Any], lang: str, state: str, codes: list[str]) -> dict[str, Any]:
    reasons = ", ".join(translate_reason_code(c, lang) for c in codes[:3]) or translate_reason_code("gate_failure", lang)
    key = no_dec.get("reason_message_key") or _default_no_decision_key(state)
    params = {"reasons": reasons} if key == "dts.no_decision.rejected" else {}
    reason = t(key, lang, **params)
    return {**no_dec, "reason": reason, "label": t("dts.action.no_decision", lang)}


def _default_no_decision_key(state: str) -> str:
    return {
        "ABSTAINED": "dts.no_decision.abstained",
        "REJECTED": "dts.no_decision.rejected",
        "DEGRADED": "dts.no_decision.degraded",
    }.get(state, "dts.action.no_decision")


def _localize_heroes(six: dict[str, Any], lang: str) -> dict[str, Any]:
    heroes = dict(six.get("heroes") or {})
    labels = {}
    for key, i18n_key in _HERO_KEYS.items():
        hero = dict(heroes.get(key) or {})
        hero["label"] = t(i18n_key, lang)
        labels[key] = hero
    return {"heroes": labels, "labels_localized": True}


def _localize_daily(daily: dict[str, Any], lang: str) -> dict[str, Any]:
    return {
        **daily,
        "section_labels": {
            "WHAT_CHANGED": t("dts.daily.what_changed", lang),
            "WHY_IT_MATTERS": t("dts.daily.why_matters", lang),
            "RISKS_INVALIDATION": t("dts.daily.risks", lang),
        },
    }


def _localize_trail(trail: dict[str, Any], lang: str) -> dict[str, Any]:
    return {**trail, "view_label": t("dts.trail.view", lang)}


def _localize_thirty(thirty: dict[str, Any], lang: str, state: str) -> dict[str, Any]:
    return {
        **thirty,
        "grasp_label": t("dts.thirty_second.grasp", lang),
        "state_label": t(_STATE_KEYS.get(state, "dts.state.unavailable"), lang),
    }


def _localize_decision_surface(surface: dict[str, Any], lang: str) -> dict[str, Any]:
    out = dict(surface)
    unknowns = []
    for item in out.get("F_unknowns") or []:
        if "NO DECISION" in str(item):
            unknowns.append(t("dts.surface.unknown", lang))
        elif item == "STALE INPUT":
            unknowns.append(t("dts.surface.stale", lang))
        elif item == "SOURCE CONFLICT":
            unknowns.append(t("dts.surface.conflict", lang))
        elif item == "INSUFFICIENT EVIDENCE":
            unknowns.append(t("dts.surface.insufficient", lang))
        else:
            unknowns.append(str(item))
    out["F_unknowns"] = unknowns
    return out


def validate_38_locale_coverage() -> dict[str, Any]:
    gaps: list[str] = []
    for locale in CANONICAL_38_LOCALES:
        for key in DTS_MESSAGE_KEYS:
            text = t(key, locale)
            if not text or not str(text).strip():
                gaps.append(f"{locale}:{key}")
            if "{" in EN.get(key, "") and "{" in text and not _placeholders_preserved(EN[key], text):
                gaps.append(f"interpolation:{locale}:{key}")
    return {
        "locale_count": len(CANONICAL_38_LOCALES),
        "message_key_count": len(DTS_MESSAGE_KEYS),
        "gaps": gaps,
        "ok": not gaps,
    }


def _placeholders_preserved(source: str, translated: str) -> bool:
    src = set(re.findall(r"\{[^}]+\}", source))
    dst = set(re.findall(r"\{[^}]+\}", translated))
    return src == dst or not src
