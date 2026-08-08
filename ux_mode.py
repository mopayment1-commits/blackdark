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
    """Normalize to a supported UI locale; English is default / fallback."""
    from i18n_service import normalize_lang as _norm

    return _norm(value)


def apply_ux_mode(payload: dict[str, Any], *, mode: str = "beginner", lang: str = "en") -> dict[str, Any]:
    """
    Beginner: act/wait sentence + score + verdict only (plus nested persona retail).
    Pro: full constitution payload (truth, half-life, regime, registry, conflicts).
    """
    from i18n_service import decision_sentence, t

    mode_n = normalize_ux_mode(mode)
    lang_n = normalize_lang(lang)
    out = dict(payload)
    out["ux_mode"] = mode_n
    out["lang"] = lang_n
    out["dir"] = "rtl" if lang_n == "ar" else "ltr"

    # Localize primary decision sentence when we have asset/score/action.
    asset = str(out.get("symbol") or out.get("asset") or "BTC")
    score = out.get("opportunity_score") or out.get("confidence") or 0
    action = str(out.get("decision_action") or out.get("verdict") or "WAIT")
    localized = decision_sentence(lang_n, action, asset, score)
    # Prefer richer persona text in the active language when present.
    persona = out.get("persona_clarity") or {}
    personas = persona.get("personas") or {}
    retail = personas.get("retail") or {}
    retail_text = retail.get(lang_n) or retail.get("text") or retail.get("en") or ""
    if retail_text and lang_n != "en" and retail.get(lang_n):
        out["decision_sentence"] = retail_text
    elif not out.get("decision_sentence") or lang_n != "en":
        # Keep English engine sentence if already rich and lang=en; else localize.
        if lang_n != "en" or not out.get("decision_sentence"):
            out["decision_sentence"] = localized
    out["oracle"] = out.get("decision_sentence")

    if mode_n == "beginner":
        retail_block = {
            "en": retail.get("en") or retail.get("text") or out.get("decision_sentence") or "",
            "text": retail_text or out.get("decision_sentence") or "",
            lang_n: retail.get(lang_n) or retail_text or out.get("decision_sentence") or "",
        }
        out["persona_clarity"] = {
            "action": persona.get("action") or ("ACT" if str(action).upper() in {"ACT", "BUY"} else "WAIT"),
            "personas": {"retail": retail_block},
            "hooks": {"problem_solved_retail": (persona.get("hooks") or {}).get("problem_solved_retail")},
            "lang": lang_n,
        }
        slim = {k: out[k] for k in _BEGINNER_KEYS if k in out}
        slim["dir"] = out["dir"]
        truth = out.get("net_edge_truth") or {}
        half = out.get("opportunity_half_life") or {}
        slim["upgrade_hint"] = {
            "message": t("upgrade.pro_hint", lang_n),
            "mode": "pro",
            "teaser": {
                "truth_score": truth.get("truth_score"),
                "half_life_seconds": half.get("expected_half_life_seconds"),
                "remaining_seconds": half.get("remaining_seconds"),
                "regime": out.get("market_regime"),
            },
        }
        return slim

    cleaned_personas: dict[str, Any] = {}
    for name, block in personas.items():
        if not isinstance(block, dict):
            continue
        en = block.get("en") or block.get("text") or ""
        local = block.get(lang_n) or en
        cleaned_personas[name] = {"en": en, "text": local, lang_n: local}
    if cleaned_personas:
        out["persona_clarity"] = {
            **{k: v for k, v in persona.items() if k != "personas"},
            "personas": cleaned_personas,
            "lang": lang_n,
        }
    pro = cleaned_personas.get("pro") or personas.get("pro") or {}
    out["decision_sentence_pro"] = pro.get(lang_n) or pro.get("en") or pro.get("text")
    whale = cleaned_personas.get("whale") or personas.get("whale") or {}
    out["decision_sentence_whale"] = whale.get(lang_n) or whale.get("en") or whale.get("text")
    return out
