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


# --- #804 Beginner / Professional Modes (cross-cutting UX pattern) ---

_BEGINNER_WIDGET_METRIC_LIMIT = 4
_BEGINNER_PROFESSIONAL_REF = 804


def normalize_view_mode_804(value: str | None) -> UxMode:
    """#804 — per-widget view mode (not global dashboard switch)."""
    return normalize_ux_mode(value)


def apply_widget_view_mode_804(
    widget: dict[str, Any],
    *,
    view_mode: str = "beginner",
    widget_id: str = "default",
) -> dict[str, Any]:
    """
    #804 — cross-cutting UX: beginner vs professional per widget.
    Beginner: 4 metrics + tooltips + explain button.
    Professional: all metrics + formulas + sources + raw values.
  No global mode switch — each widget keeps independent mode.
    """
    mode = normalize_view_mode_804(view_mode)
    out = dict(widget)
    metrics = list(out.get("metrics") or [])
    formulas = out.get("formulas") or {}
    sources = out.get("sources") or {}

    if mode == "beginner":
        out["view_mode"] = "beginner"
        out["view_mode_label_ar"] = "بسيط"
        out["metrics_shown"] = metrics[:_BEGINNER_WIDGET_METRIC_LIMIT]
        out["metrics_hidden_count"] = max(0, len(metrics) - _BEGINNER_WIDGET_METRIC_LIMIT)
        out["tooltips_enabled"] = True
        out["explain_button_ar"] = "اشرح لي"
        out["explain_button_en"] = "Explain this"
        out["formulas_visible"] = False
        out["raw_values_visible"] = False
    else:
        out["view_mode"] = "professional"
        out["view_mode_label_ar"] = "متقدم"
        out["metrics_shown"] = metrics
        out["metrics_hidden_count"] = 0
        out["tooltips_enabled"] = False
        out["formulas_visible"] = True
        out["formulas"] = formulas
        out["sources"] = sources
        out["raw_values_visible"] = True
        out["raw_values"] = out.get("raw_values") or widget.get("raw_data")

    out["feature_ref"] = _BEGINNER_PROFESSIONAL_REF
    out["widget_id"] = widget_id
    out["no_global_mode_switch"] = True
    out["per_widget_mode"] = True
    out["presentation_only"] = True
    out["calculations_unchanged"] = True
    return out


def build_asset_card_view_modes_804(
    asset: str = "BTC",
    *,
    view_mode: str = "beginner",
) -> dict[str, Any]:
    """#804 — Asset Card toggle بسيط/متقدم."""
    from bd_platform.market_radar_indicators import build_interactive_chart_overlay_800

    chart = build_interactive_chart_overlay_800(asset)
    ind = (chart.get("indicators") or {}) if chart.get("ok") else {}
    metrics = [
        {"key": "rsi_14", "label": "RSI(14)", "value": (ind.get("RSI") or {}).get("value"), "tooltip": "Relative Strength Index"},
        {"key": "macd", "label": "MACD", "value": (ind.get("MACD") or {}).get("trend_label"), "tooltip": "Moving Average Convergence Divergence"},
        {"key": "sma_20", "label": "SMA(20)", "value": (ind.get("SMA") or {}).get("value"), "tooltip": "Simple Moving Average 20 periods"},
        {"key": "volume", "label": "Volume", "value": "enabled" if (ind.get("Volume") or {}).get("enabled") else "n/a", "tooltip": "Trading volume"},
        {"key": "price", "label": "Price", "value": chart.get("asset"), "tooltip": "Current asset"},
        {"key": "source", "label": "Source", "value": chart.get("ohlcv_source"), "tooltip": "Data source"},
    ]
    widget = {
        "asset": asset.upper(),
        "surface": "asset_card",
        "metrics": metrics,
        "formulas": {
            "rsi_14": "RSI(14) — TradingView Formula v1.0",
            "macd": "MACD(12,26,9) — TradingView Formula v1.0",
            "sma_20": "SMA(20) — simple arithmetic mean",
        },
        "sources": {"ohlcv": "Oracle API", "indicators": "#754 Technical Indicator Library"},
        "raw_data": ind,
        "toggle_ar": "بسيط/متقدم",
        "toggle_en": "Simple/Advanced",
    }
    return apply_widget_view_mode_804(widget, view_mode=view_mode, widget_id=f"asset_card_{asset.upper()}")


def beginner_professional_modes_status_804() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _BEGINNER_PROFESSIONAL_REF,
        "standalone_rejected": True,
        "merged_into": "UX Design System",
        "cross_cutting": True,
        "no_global_mode_switch": True,
        "per_widget_mode": True,
        "beginner_metric_limit": _BEGINNER_WIDGET_METRIC_LIMIT,
        "beginner_features": ["tooltips", "explain_button_ar"],
        "professional_features": ["all_metrics", "formulas", "sources", "raw_values"],
        "surfaces": ["asset_card", "market_radar", "intelligence_ledger", "portfolio_ai"],
        "fee_db": {"additional_cost_usd": 0, "ui_concern_only": True},
        "timestamp": _utcnow(),
    }


# --- #815 Progressive Disclosure (cross-cutting UX pattern) ---

_PROGRESSIVE_DISCLOSURE_REF = 815
_COLLAPSED_METRIC_KEYS = ("price", "change_24h_pct", "symbol", "asset")


def apply_progressive_disclosure_815(
    payload: dict[str, Any],
    *,
    surface: str = "asset_card",
    widget_id: str = "default",
    expanded: bool = False,
) -> dict[str, Any]:
    """
    #815 — basic info first, advanced metrics on expand demand.
    Asset Card: price + change first → expand for full metrics.
    Report: summary first → 'التفاصيل' for full detail.
    """
    out = dict(payload)
    metrics = list(out.get("metrics") or [])
    collapsed = [m for m in metrics if (m.get("key") or m.get("label", "")).lower() in _COLLAPSED_METRIC_KEYS]
    if not collapsed and metrics:
        collapsed = metrics[:2]

    out["feature_ref"] = _PROGRESSIVE_DISCLOSURE_REF
    out["standalone_rejected"] = True
    out["cross_cutting"] = True
    out["surface"] = surface
    out["widget_id"] = widget_id
    out["expanded"] = expanded
    out["collapsed_metrics"] = collapsed if not expanded else metrics
    out["full_metrics"] = metrics
    out["metrics_hidden_until_expand"] = max(0, len(metrics) - len(collapsed)) if not expanded else 0
    out["expand_cta_ar"] = "عرض المزيد"
    out["expand_cta_en"] = "Show more"
    out["collapse_cta_ar"] = "عرض أقل"
    out["details_cta_ar"] = "التفاصيل"
    out["details_cta_en"] = "Details"
    out["presentation_only"] = True
    out["calculations_unchanged"] = True
    out["basic_info_first"] = True
    out["advanced_on_demand"] = True
    return out


def build_asset_card_progressive_disclosure_815(
    asset: str = "BTC",
    *,
    price_usd: float | None = None,
    change_24h_pct: float | None = None,
    expanded: bool = False,
) -> dict[str, Any]:
    """#815 — Asset Card: price + change first, expand for full metrics."""
    sym = asset.upper()
    price = price_usd if price_usd is not None else 98500.0
    change = change_24h_pct if change_24h_pct is not None else 2.4
    metrics = [
        {"key": "price", "label": "Price", "value": price, "unit": "USD"},
        {"key": "change_24h_pct", "label": "24h Change", "value": change, "unit": "%"},
        {"key": "market_cap", "label": "Market Cap", "value": "1.28T", "unit": "USD"},
        {"key": "volume_24h", "label": "24h Volume", "value": "28.5B", "unit": "USD"},
        {"key": "nvt", "label": "NVT", "value": 42.5},
        {"key": "realized_cap", "label": "Realized Cap", "value": "580B", "unit": "USD"},
    ]
    widget = {
        "asset": sym,
        "surface": "asset_card",
        "metrics": metrics,
        "summary_line": f"{sym} ${price:,.0f} ({change:+.1f}% 24h)",
    }
    return apply_progressive_disclosure_815(
        widget, surface="asset_card", widget_id=f"asset_card_{sym}", expanded=expanded,
    )


def build_report_progressive_disclosure_815(
    report_id: str = "market-brief",
    *,
    summary: str | None = None,
    expanded: bool = False,
) -> dict[str, Any]:
    """#815 — Report: summary first, 'التفاصيل' expands full analysis."""
    payload = {
        "report_id": report_id,
        "surface": "report",
        "summary": summary or "BTC network activity stable; NVT within historical band.",
        "summary_ar": "نشاط شبكة BTC مستقر؛ NVT ضمن النطاق التاريخي.",
        "details": {
            "sections": ["market_overview", "on_chain_activity", "sentiment", "risk_flags"],
            "full_analysis_available": True,
        },
        "metrics": [
            {"key": "headline", "label": "Headline", "value": summary or "Market brief"},
            {"key": "change_24h_pct", "label": "BTC 24h", "value": 2.4},
            {"key": "nvt", "label": "NVT", "value": 42.5},
            {"key": "daa", "label": "DAA", "value": 890000},
        ],
    }
    out = apply_progressive_disclosure_815(
        payload, surface="report", widget_id=report_id, expanded=expanded,
    )
    if not expanded:
        out["visible_content"] = {"summary": out["summary"], "summary_ar": out.get("summary_ar")}
    else:
        out["visible_content"] = {"summary": out["summary"], "details": out.get("details")}
    return out


def progressive_disclosure_status_815() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _PROGRESSIVE_DISCLOSURE_REF,
        "standalone_rejected": True,
        "merged_into": "UX Design System",
        "cross_cutting": True,
        "pattern": "basic_info_first_advanced_on_demand",
        "surfaces": ["asset_card", "report", "market_radar", "portfolio_ai", "landing_page"],
        "asset_card_cta_ar": "عرض المزيد",
        "report_cta_ar": "التفاصيل",
        "complements_feature_ref": 804,
        "fee_db": {"additional_cost_usd": 0, "ui_concern_only": True},
        "timestamp": _utcnow(),
    }
