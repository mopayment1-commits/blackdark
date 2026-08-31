"""
BLACKDARK — Beginner / Pro progressive disclosure (Constitution §1.5).

#461 Beginner Decision Mode + #468 Decision-First Mode — merged UI/UX layer.
Presentation only: same data, different disclosure levels.
Risk warning always visible in beginner mode.
"""

from __future__ import annotations

from typing import Any, Literal

UxMode = Literal["beginner", "pro"]
DecisionLayer = Literal["summary", "details", "raw"]

_BEGINNER_KEYS = {
    "symbol",
    "price",
    "change_24h",
    "opportunity_score",
    "verdict",
    "decision_sentence",
    "decision_action",
    "persona_clarity",
    "confidence",
    "disclaimer",
    "timestamp",
    "ux_mode",
    "lang",
    "prediction_id",
    "chain_hash",
    "proof",
    "decision_certificate",
    "compliance_footer",
    "explanation",
    "oracle",
    "narrative",
    "risk_warning",
    "decision_card",
}

_RISK_WARNING_TEXT = (
    "Risk Warning: Analytics only — not investment advice. "
    "Past performance does not guarantee future results. "
    "You may lose capital. Review full details before acting."
)

_DECISION_FIRST_FEATURE_REF = 468
_BEGINNER_DECISION_FEATURE_REF = 461


def _utcnow() -> str:
    from datetime import UTC, datetime
    return datetime.now(UTC).isoformat()


def normalize_ux_mode(value: str | None) -> UxMode:
    raw = (value or "beginner").strip().lower()
    return "pro" if raw in {"pro", "professional", "advanced", "expert"} else "beginner"


def normalize_lang(value: str | None) -> str:
    from i18n_service import normalize_lang as _i18n_lang

    return _i18n_lang(value)


def _beginner_payload(out: dict[str, Any], persona: dict[str, Any], personas: dict[str, Any]) -> dict[str, Any]:
    retail = personas.get("retail") or {}
    retail_en = {
        "en": retail.get("en") or retail.get("text") or "",
        "text": retail.get("en") or retail.get("text") or "",
    }
    out["persona_clarity"] = {
        "action": persona.get("action"),
        "personas": {"retail": retail_en},
        "hooks": {"problem_solved_retail": (persona.get("hooks") or {}).get("problem_solved_retail")},
    }
    slim = {k: out[k] for k in _BEGINNER_KEYS if k in out}
    slim["risk_warning"] = {
        "text": _RISK_WARNING_TEXT,
        "always_visible": True,
        "cannot_be_hidden": True,
    }
    slim["decision_card"] = build_beginner_decision_card(out, layer="summary")
    # Keep a tiny pro teaser so upgrade path is clear.
    truth = out.get("net_edge_truth") or {}
    half = out.get("opportunity_half_life") or {}
    slim["upgrade_hint"] = {
        "message": "Switch to Pro to unlock Net-Edge Truth Score and Opportunity Half-Life.",
        "mode": "pro",
        "teaser": {
            "truth_score": truth.get("truth_score"),
            "half_life_seconds": half.get("expected_half_life_seconds"),
            "remaining_seconds": half.get("remaining_seconds"),
            "regime": out.get("market_regime"),
        },
    }
    return slim


def _clean_personas(personas: dict[str, Any]) -> dict[str, Any]:
    cleaned_personas: dict[str, Any] = {}
    for name, block in personas.items():
        if not isinstance(block, dict):
            continue
        en = block.get("en") or block.get("text") or ""
        cleaned_personas[name] = {"en": en, "text": en}
    return cleaned_personas


def _pro_payload(out: dict[str, Any], lang: str, persona: dict[str, Any], personas: dict[str, Any]) -> dict[str, Any]:
    cleaned_personas = _clean_personas(personas)
    if cleaned_personas:
        out["persona_clarity"] = {
            **{k: v for k, v in persona.items() if k != "personas"},
            "personas": cleaned_personas,
            "lang": "en",
        }
    pro = cleaned_personas.get("pro") or personas.get("pro") or {}
    out["decision_sentence_pro"] = pro.get(lang) or pro.get("en") or pro.get("text")
    whale = cleaned_personas.get("whale") or personas.get("whale") or {}
    out["decision_sentence_whale"] = whale.get(lang) or whale.get("en") or whale.get("text")
    return out


def apply_ux_mode(payload: dict[str, Any], *, mode: str = "beginner", lang: str = "en") -> dict[str, Any]:
    """
    Beginner: act/wait sentence + score + verdict only (plus nested persona retail).
    Pro: full constitution payload (truth, half-life, regime, registry, conflicts).
    """
    mode_n = normalize_ux_mode(mode)
    lang_n = normalize_lang(lang)
    out = dict(payload)
    out["ux_mode"] = mode_n
    out["lang"] = lang_n

    persona = out.get("persona_clarity") or {}
    personas = persona.get("personas") or {}
    if mode_n == "beginner":
        return _beginner_payload(out, persona, personas)

    # Pro: English-only persona lines; strip any residual ar keys
    return _pro_payload(out, lang_n, persona, personas)


def build_beginner_decision_card(
    payload: dict[str, Any],
    *,
    layer: DecisionLayer = "summary",
) -> dict[str, Any]:
    """
    #461 Beginner Decision Mode / #468 Decision-First Mode.
    Progressive disclosure: Summary → Details → Raw Data.
    Same calculations — presentation layer only.
    """
    truth = payload.get("net_edge_truth") or {}
    risk = payload.get("risk_assessment") or payload.get("fill_risk_assessment") or {}

    summary = {
        "feature_ref": _BEGINNER_DECISION_FEATURE_REF,
        "decision_first_ref": _DECISION_FIRST_FEATURE_REF,
        "layer": "summary",
        "verdict": payload.get("verdict"),
        "decision_sentence": payload.get("decision_sentence"),
        "confidence": payload.get("confidence"),
        "why": payload.get("explanation") or payload.get("narrative"),
        "risk_level": risk.get("severity") or risk.get("risk_level") or "review_required",
        "risk_warning": _RISK_WARNING_TEXT,
        "calculations_unchanged": True,
        "presentation_only": True,
        "expand_to": "details",
    }

    details = {
        **summary,
        "layer": "details",
        "opportunity_score": payload.get("opportunity_score"),
        "truth_score": truth.get("truth_score"),
        "net_edge_score": truth.get("net_edge_score"),
        "persona_clarity": payload.get("persona_clarity"),
        "risk_breakdown": risk,
        "expand_to": "raw",
    }

    raw = {
        **details,
        "layer": "raw",
        "raw_payload": payload,
        "expand_to": None,
    }

    layers = {"summary": summary, "details": details, "raw": raw}
    card = layers.get(layer, summary)
    card["risk_warning_always_visible"] = True
    return card


def beginner_decision_mode_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_ref": _BEGINNER_DECISION_FEATURE_REF,
        "decision_first_ref": _DECISION_FIRST_FEATURE_REF,
        "title": "Beginner Decision Mode",
        "merged_with": "Decision-First Mode (#468)",
        "standalone": False,
        "merged_into": "UI/UX Layer",
        "risk_warning_always_visible": True,
        "calculations_unchanged": True,
        "presentation_only": True,
        "layers": ["summary", "details", "raw"],
        "timestamp": _utcnow(),
    }
