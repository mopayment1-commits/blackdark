"""AI / analytics / support data boundary enforcement (FDS-24 / SDG-08)."""

from __future__ import annotations

from typing import Any

from financial_data.classification import FDSClass, classify_field, classify_payload
from financial_data.dlp import sanitize_financial_payload
from financial_data.sink_policy import PolicyViolation, Sink, enforce_sink_policy

_ALLOWED_LLM_KEYS = frozenset(
    {
        "asset",
        "symbol",
        "score",
        "opportunity_score",
        "summary",
        "macro_regime_proxy",
        "fear_greed_index",
        "geopolitical_headline_count",
        "macro_news_tone",
        "derivatives_bias",
        "regime",
        "change_24h_pct",
        "reasons",
        "risk_factors",
    }
)


def _reject_restricted(mapping: dict[str, FDSClass], sink: Sink) -> None:
    for path, cls in mapping.items():
        if cls in {FDSClass.C1_SAD, FDSClass.C2_PAN, FDSClass.C3_BANKING, FDSClass.C4_SECRET, FDSClass.UNKNOWN}:
            enforce_sink_policy({path.split(".")[-1]: "x"}, sink, field_hint=path.split(".")[-1])


def gate_external_llm_payload(payload: dict[str, Any] | str | None, *, field_hint: str | None = None) -> None:
    if payload is None:
        return
    if isinstance(payload, str):
        enforce_sink_policy(payload, Sink.AI_LLM, field_hint=field_hint)
        return
    _reject_restricted(classify_payload(payload), Sink.AI_LLM)


def gate_analytics_export(payload: dict[str, Any] | None) -> None:
    if not payload:
        return
    mapping = classify_payload(payload)
    for path, cls in mapping.items():
        if cls in {FDSClass.C1_SAD, FDSClass.C2_PAN, FDSClass.C3_BANKING, FDSClass.C4_SECRET, FDSClass.UNKNOWN}:
            raise PolicyViolation(sink=Sink.ANALYTICS, classification=cls, field=path)
        if cls == FDSClass.C5_SENSITIVE_FINANCIAL:
            enforce_sink_policy(payload, Sink.ANALYTICS, purpose="minimized_analytics")


def gate_support_export(payload: dict[str, Any] | None) -> None:
    if not payload:
        return
    mapping = classify_payload(payload)
    for path, cls in mapping.items():
        if cls in {FDSClass.C1_SAD, FDSClass.C2_PAN, FDSClass.C3_BANKING, FDSClass.C4_SECRET, FDSClass.UNKNOWN}:
            raise PolicyViolation(sink=Sink.SUPPORT_EXPORT, classification=cls, field=path)


def prepare_llm_context(hub_context: dict[str, Any] | None) -> dict[str, Any]:
    """Minimize and policy-filter context before external LLM prompt construction."""
    if not isinstance(hub_context, dict):
        return {}
    safe: dict[str, Any] = {}
    for key, value in hub_context.items():
        if key not in _ALLOWED_LLM_KEYS and not isinstance(value, dict):
            cls = classify_field(str(key), value)
            if cls and cls in {FDSClass.C1_SAD, FDSClass.C2_PAN, FDSClass.C3_BANKING, FDSClass.C4_SECRET, FDSClass.UNKNOWN}:
                continue
        if isinstance(value, dict):
            nested = prepare_llm_context(value)
            if nested:
                safe[key] = nested
            continue
        cls = classify_field(str(key), value)
        if cls in {FDSClass.C5_SENSITIVE_FINANCIAL, FDSClass.C6_PAYMENT_REFERENCE}:
            continue
        if cls and cls in {FDSClass.C1_SAD, FDSClass.C2_PAN, FDSClass.C3_BANKING, FDSClass.C4_SECRET, FDSClass.UNKNOWN}:
            continue
        safe[key] = value
    gate_external_llm_payload(safe)
    return safe


def build_llm_prompt_text(*, asset: str, opportunity_score: float, summary: str, hub_context: dict[str, Any]) -> str:
    ctx = prepare_llm_context(hub_context)
    macro = ctx.get("macro") or {}
    sentiment = ctx.get("sentiment") or {}
    geo = ctx.get("geo_news") or {}
    gate_external_llm_payload(
        {
            "asset": asset,
            "score": opportunity_score,
            "summary": summary,
            "macro": macro,
            "sentiment": sentiment,
            "geo": geo,
        }
    )
    return (
        "You are a crypto oracle. Return ONE sentence starting with 'Buy Now' or 'Do Not Touch', "
        "then em dash, then reason. Consider war/peace news, macro, fear/greed, derivatives.\n"
        f"Asset={asset}, score={opportunity_score}, summary={summary}\n"
        f"Macro regime={macro.get('macro_regime_proxy')}, "
        f"FearGreed={sentiment.get('fear_greed_index')}, "
        f"Geo headlines={geo.get('geopolitical_headline_count')}"
    )
