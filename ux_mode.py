"""
BLACKDARK — Beginner / Pro progressive disclosure (Constitution §1.5).
"""

from __future__ import annotations

from typing import Any, Literal

UxMode = Literal["beginner", "pro"]

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
}


def normalize_ux_mode(value: str | None) -> UxMode:
    raw = (value or "beginner").strip().lower()
    return "pro" if raw in {"pro", "professional", "advanced", "expert"} else "beginner"


def normalize_lang(value: str | None) -> str:
    """English-only public site — always normalize to en for UI payloads."""
    _ = value
    return "en"


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
        # Keep a tiny pro teaser so upgrade path is clear
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

    # Pro: English-only persona lines; strip any residual ar keys
    cleaned_personas: dict[str, Any] = {}
    for name, block in personas.items():
        if not isinstance(block, dict):
            continue
        en = block.get("en") or block.get("text") or ""
        cleaned_personas[name] = {"en": en, "text": en}
    if cleaned_personas:
        out["persona_clarity"] = {
            **{k: v for k, v in persona.items() if k != "personas"},
            "personas": cleaned_personas,
            "lang": "en",
        }
    pro = cleaned_personas.get("pro") or personas.get("pro") or {}
    out["decision_sentence_pro"] = pro.get(lang_n) or pro.get("en") or pro.get("text")
    whale = cleaned_personas.get("whale") or personas.get("whale") or {}
    out["decision_sentence_whale"] = whale.get(lang_n) or whale.get("en") or whale.get("text")
    return out
