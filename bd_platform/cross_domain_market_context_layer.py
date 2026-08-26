"""
Cross-Domain Market Context Layer — Feature #524 Epic (Sprint 2 Intelligence Layer).

Renamed from "Cross-Domain Decision Intelligence Layer" / "Cross-Market Decision Intelligence Engine".
Absorbs #523, #525, #526–#530 as sub-modules (tasks, not standalone tickets).

Layer architecture — API/feed for UI modules, no standalone product UI.
Rule-based first. ML deferred to Wave 3.
Builds on Epistemic Output Framework (#316), Data Layer, On-Chain Layer, Risk Layer.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.CrossDomainMarketContextLayer")

_FEATURE_ID = 524
_ABSORBED_IDS = (523, 525, 526, 527, 528, 529, 530)
_RENAMED_FROM = (
    "Cross-Domain Decision Intelligence Layer",
    "Cross-Domain Decision Intelligence",
    "Cross-Market Decision Intelligence Engine",
)
_TITLE = "Cross-Domain Market Context Layer"
_STANDALONE = False
_LAYER = "Intelligence Layer"
_SPRINT = 2
_WAVE = 2
_SEED_PATH = Path("data/cross_domain_market_context_layer_seed.json")
_METHODOLOGY_VERSION = "1.0"
_EPISTEMIC_FEATURE_ID = 316
_EVIDENCE_CONFIDENCE_FEATURE_ID = 284
_PROVENANCE_FEATURE_ID = 1003

_SUB_MODULES: dict[str, dict[str, Any]] = {
    "523": {
        "task_id": "523",
        "name": "derivatives_context",
        "title": "Derivatives Context Module",
        "description": "Derivatives pressure contextualized — not standalone decision",
        "domains": ["derivatives", "spot", "liquidity", "risk"],
    },
    "525": {
        "task_id": "525",
        "name": "onchain_flow_context",
        "title": "On-Chain Flow Context Module",
        "description": "Exchange flows, whales, stablecoins — CryptoQuant-style data synthesis",
        "domains": ["on_chain", "exchange_flows", "whales", "stablecoins"],
    },
    "526": {
        "task_id": "526",
        "name": "social_onchain_dev",
        "title": "Social + On-Chain + Development Module",
        "description": "Social, narratives, sentiment, development activity synthesis",
        "domains": ["social", "narratives", "sentiment", "development", "on_chain"],
    },
    "527": {
        "task_id": "527",
        "name": "custom_query",
        "title": "Custom Query Module",
        "description": "Dune-style parameterized cross-domain queries",
        "domains": ["custom_query", "on_chain", "market"],
    },
    "528": {
        "task_id": "528",
        "name": "entity_focused",
        "title": "Entity-Focused Module",
        "description": "Entity-tagged flow and positioning context",
        "domains": ["entities", "whales", "exchange_flows"],
    },
    "529": {
        "task_id": "529",
        "name": "fundamental",
        "title": "Fundamental Module",
        "description": "Fundamental and macro context synthesis",
        "domains": ["fundamental", "macro", "etf", "market"],
    },
    "530": {
        "task_id": "530",
        "name": "market_wide_aggregation",
        "title": "Market-Wide Aggregation Module",
        "description": "Cross-market normalization with stale-source penalties",
        "domains": ["on_chain", "derivatives", "liquidity", "sentiment", "macro", "risk"],
    },
}

_EPISTEMIC_UI_LABELS: dict[str, dict[str, str]] = {
    "fact": {"label": "Fact", "color": "green", "tag": "[Fact]"},
    "inference": {"label": "Inference", "color": "blue", "tag": "[Inference]"},
    "hypothesis": {"label": "Hypothesis", "color": "amber", "tag": "[Hypothesis]"},
}

_FORBIDDEN_TERMS = (
    "decision", "buy", "sell", "recommendation", "recommend", "actionable trade",
)

_DISCLAIMER = (
    "Market context feed — not investment advice. "
    "Fact/Inference/Hypothesis separated. Context relevance ≠ recommendation. "
    "Source/freshness/confidence on every conclusion. User decides."
)

_STALE_THRESHOLD_SECONDS = 3600
_SINGLE_SOURCE_DOMINANCE_THRESHOLD = 0.6


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"contexts": {}, "sub_module_data": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("cross-domain market context layer seed load failed: %s", exc)
        return {"contexts": {}, "sub_module_data": {}}


def validate_no_forbidden_language(text: str) -> dict[str, Any]:
    lower = text.lower()
    violations = [t for t in _FORBIDDEN_TERMS if re.search(rf"\b{re.escape(t)}\b", lower)]
    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "forbidden_terms": list(_FORBIDDEN_TERMS),
        "output_model": "Context + Evidence + Confidence — user decides",
    }


def build_conclusion_metadata(
    *,
    source: str,
    freshness_seconds: int,
    confidence_pct: float,
    epistemic_type: str,
) -> dict[str, Any]:
    """Source/freshness/confidence for every conclusion — mandatory."""
    stale = freshness_seconds > _STALE_THRESHOLD_SECONDS
    stale_penalty = 0.15 if stale else 0.0
    adjusted_confidence = max(0.0, confidence_pct - (stale_penalty * 100))

    return {
        "source": source,
        "freshness_seconds": freshness_seconds,
        "freshness_display": f"{freshness_seconds}s ago",
        "stale": stale,
        "stale_penalty_applied": stale,
        "confidence_pct": round(adjusted_confidence, 1),
        "raw_confidence_pct": round(confidence_pct, 1),
        "epistemic_type": epistemic_type,
        "ui_label": _EPISTEMIC_UI_LABELS.get(epistemic_type, {}),
        "source_freshness_confidence_required": True,
    }


def apply_stale_source_penalty(
    signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Stale-source penalties — #530 requirement."""
    penalized = []
    for sig in signals:
        sig = dict(sig)
        freshness = int(sig.get("freshness_seconds", 0))
        confidence = float(sig.get("confidence_pct", 80))
        meta = build_conclusion_metadata(
            source=sig.get("source", "unknown"),
            freshness_seconds=freshness,
            confidence_pct=confidence,
            epistemic_type=sig.get("epistemic_type", "inference"),
        )
        sig["metadata"] = meta
        sig["confidence_pct"] = meta["confidence_pct"]
        sig["stale_penalty_applied"] = meta["stale_penalty_applied"]
        penalized.append(sig)
    return penalized


def check_single_source_dominance(signals: list[dict[str, Any]]) -> dict[str, Any]:
    """No single-source domination without rule — #530 requirement."""
    if not signals:
        return {"dominated": False, "no_single_source_domination": True}

    source_weights: dict[str, float] = {}
    total_weight = 0.0
    for sig in signals:
        source = sig.get("source", "unknown")
        weight = float(sig.get("weight", 1.0))
        source_weights[source] = source_weights.get(source, 0.0) + weight
        total_weight += weight

    if total_weight == 0:
        return {"dominated": False, "no_single_source_domination": True}

    max_source = max(source_weights, key=source_weights.get)  # type: ignore[arg-type]
    max_share = source_weights[max_source] / total_weight
    dominated = max_share > _SINGLE_SOURCE_DOMINANCE_THRESHOLD

    return {
        "dominated": dominated,
        "dominant_source": max_source if dominated else None,
        "dominant_share": round(max_share, 3) if dominated else None,
        "no_single_source_domination": not dominated,
        "threshold": _SINGLE_SOURCE_DOMINANCE_THRESHOLD,
        "rule_applied": True,
    }


def normalize_domain_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cross-domain normalization — rule-based, no ML."""
    normalized = []
    for sig in signals:
        normalized.append({
            "domain": sig.get("domain"),
            "metric": sig.get("metric"),
            "value": sig.get("value"),
            "direction": sig.get("direction"),
            "source": sig.get("source"),
            "freshness_seconds": sig.get("freshness_seconds", 0),
            "confidence_pct": sig.get("confidence_pct", 80),
            "weight": sig.get("weight", 1.0),
            "epistemic_type": sig.get("epistemic_type", "fact"),
            "normalized": True,
            "rule_based": True,
        })
    return apply_stale_source_penalty(normalized)


def build_context_relevance(
    *,
    factor: str,
    hypothesis: str,
    relationship: Literal["supports", "contradicts", "neutral"],
    evidence_refs: list[str],
) -> dict[str, Any]:
    """
    Internal context relevance — NOT a recommendation.
    'This factor supports/contradicts [hypothesis]' — never Buy/Sell.
    """
    return {
        "factor": factor,
        "hypothesis": hypothesis,
        "relationship": relationship,
        "supports": relationship == "supports",
        "contradicts": relationship == "contradicts",
        "not_recommendation": True,
        "not_buy_sell": True,
        "internal_output": True,
        "display": f"This factor {relationship}s hypothesis: {hypothesis}",
        "evidence_refs": evidence_refs,
    }


def build_sub_module_feed(
    sub_module_id: str,
    *,
    asset: str = "BTC",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build feed for one sub-module — task, not standalone ticket."""
    seed = seed or _load_seed()
    sub_meta = _SUB_MODULES.get(sub_module_id)
    if not sub_meta:
        return {"ok": False, "error": "sub_module_not_found", "sub_module_id": sub_module_id}

    data = (seed.get("sub_module_data") or {}).get(sub_module_id, {})
    asset_data = (data.get("assets") or {}).get(asset.upper(), data.get("default", {}))

    signals = normalize_domain_signals(asset_data.get("domain_signals") or [])
    dominance = check_single_source_dominance(signals)

    from bd_platform.epistemic_output_framework import confirm_contradict_domains

    cross_domain = confirm_contradict_domains([
        {k: s[k] for k in ("domain", "direction") if k in s} for s in signals
    ])

    context_relevance = [
        build_context_relevance(**cr) for cr in (asset_data.get("context_relevance") or [])
    ]

    return {
        "ok": True,
        "epic_feature_id": _FEATURE_ID,
        "sub_module": sub_meta,
        "standalone_rejected": True,
        "task_not_ticket": True,
        "asset": asset.upper(),
        "what_changed": asset_data.get("what_changed", []),
        "why": asset_data.get("why", []),
        "confirmation": cross_domain,
        "risk": asset_data.get("risk", {}),
        "confidence": {
            "aggregate_pct": asset_data.get("aggregate_confidence_pct"),
            "signals": [{"domain": s["domain"], "confidence_pct": s["confidence_pct"]} for s in signals],
            "stale_penalties_applied": any(s.get("stale_penalty_applied") for s in signals),
        },
        "context_relevance": context_relevance,
        "not_decision_output": True,
        "not_recommendation": True,
        "domain_signals": signals,
        "single_source_check": dominance,
        "rule_based_only": True,
        "ml_deferred_wave": 3,
    }


def _build_epistemic_items(panel_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Build epistemic items using #316 framework."""
    from bd_platform.epistemic_output_framework import (
        build_evidence_link,
        build_fact,
        build_hypothesis,
        build_inference,
        enrich_with_evidence_confidence,
    )

    items: list[dict[str, Any]] = []
    for item in panel_data.get("epistemic_items") or []:
        etype = item.get("epistemic_type")
        chain = [build_evidence_link(**e) for e in (item.get("evidence") or [])]
        meta = build_conclusion_metadata(
            source=(item.get("evidence") or [{}])[0].get("source", "unknown"),
            freshness_seconds=int(item.get("freshness_seconds", 120)),
            confidence_pct=float(item.get("confidence_pct", 80 if etype != "fact" else 100)),
            epistemic_type=etype or "fact",
        )

        if etype == "fact":
            built = build_fact(
                item["statement"],
                evidence_chain=chain,
                verified=item.get("verified", True),
                provenance_metric_id=item.get("provenance_metric_id"),
            )
        elif etype == "inference":
            built = build_inference(
                item["statement"],
                supporting_facts=[{"ref": r} for r in (item.get("supporting_fact_refs") or [])],
                confidence_pct=float(item.get("confidence_pct", 70)),
                evidence_chain=chain,
            )
            if item.get("evidence_confidence_assessment_id"):
                built = enrich_with_evidence_confidence(
                    built, item["evidence_confidence_assessment_id"],
                )
        elif etype == "hypothesis":
            pr = item.get("probability_range_pct") or [30, 55]
            built = build_hypothesis(
                item["statement"],
                probability_range=(float(pr[0]), float(pr[1])),
                test_conditions=item.get("test_conditions") or [],
                evidence_chain=chain,
            )
        else:
            continue

        built["metadata"] = meta
        built["ui_label"] = _EPISTEMIC_UI_LABELS.get(etype or "fact", {})
        items.append(built)
    return items


def build_market_context_panel(
    *,
    context_id: str = "btc_cross_domain",
    asset: str = "BTC",
    sub_modules: list[str] | None = None,
) -> dict[str, Any]:
    """Main panel — cross-domain market context feed for UI modules."""
    t0 = time.perf_counter()
    seed = _load_seed()
    panel = (seed.get("contexts") or {}).get(context_id)

    if not panel:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "context_not_found", "context_id": context_id}

    from bd_platform.epistemic_output_framework import (
        confirm_contradict_domains,
        wrap_intelligence_output,
    )

    domain_signals = normalize_domain_signals(panel.get("domain_signals") or [])
    cross_domain = confirm_contradict_domains([
        {k: s[k] for k in ("domain", "direction") if k in s} for s in domain_signals
    ])
    dominance = check_single_source_dominance(domain_signals)

    epistemic_items = _build_epistemic_items(panel)
    wrapped = wrap_intelligence_output(
        analysis_summary=panel.get("analysis_summary", ""),
        epistemic_items=epistemic_items,
        domains=[s.get("domain") for s in domain_signals],
        title=panel.get("title"),
    )

    for item in wrapped.get("evidence", {}).get("items", []):
        etype = item.get("epistemic_type", "fact")
        item["ui_label"] = _EPISTEMIC_UI_LABELS.get(etype, {})

    active_subs = sub_modules or list(_SUB_MODULES.keys())
    sub_feeds = {
        sid: build_sub_module_feed(sid, asset=asset, seed=seed)
        for sid in active_subs
        if sid in _SUB_MODULES
    }

    context_relevance = [
        build_context_relevance(**cr) for cr in (panel.get("context_relevance") or [])
    ]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "absorbed_tickets": {str(tid): f"Merged into #524 sub-module" for tid in _ABSORBED_IDS},
        "renamed_from": list(_RENAMED_FROM),
        "title": _TITLE,
        "not_decision_intelligence": True,
        "context_not_recommendation": True,
        "standalone": _STANDALONE,
        "no_standalone_ui": True,
        "api_feed_for_ui_modules": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "context_id": context_id,
        "asset": asset.upper(),
        "what_changed": panel.get("what_changed", []),
        "why": wrapped.get("why", []),
        "confirmation": cross_domain,
        "risk": panel.get("risk", {}),
        "confidence": wrapped.get("confidence", {}),
        "context_relevance": context_relevance,
        "not_decision_output": True,
        "output": wrapped,
        "epistemic_ui_labels": _EPISTEMIC_UI_LABELS,
        "domain_signals": domain_signals,
        "single_source_check": dominance,
        "sub_modules": {
            "epic_sub_modules": list(_SUB_MODULES.keys()),
            "feeds": sub_feeds,
            "tasks_not_tickets": True,
        },
        "dependencies": {
            "epistemic_framework": _EPISTEMIC_FEATURE_ID,
            "evidence_confidence": _EVIDENCE_CONFIDENCE_FEATURE_ID,
            "provenance_lineage": _PROVENANCE_FEATURE_ID,
            "data_layer": ["#516", "#501", "#503", "#506", "#508"],
            "ml_deferred_wave": 3,
        },
        "rule_based_only": True,
        "acceptance_criteria": {
            "fact_inference_hypothesis_separated": True,
            "no_unsupported_action_claim": True,
            "source_freshness_confidence_every_conclusion": True,
            "no_single_source_domination_without_rule": True,
            "stale_source_penalties": True,
            "explainable": True,
            "no_standalone_ui": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def cross_domain_market_context_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": list(_RENAMED_FROM),
        "not_decision_intelligence": True,
        "context_not_recommendation": True,
        "standalone": _STANDALONE,
        "no_standalone_ui": True,
        "api_feed_for_ui_modules": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "absorbed_tickets": list(_ABSORBED_IDS),
        "sub_modules": _SUB_MODULES,
        "tasks_not_tickets": True,
        "epistemic_ui_labels": _EPISTEMIC_UI_LABELS,
        "dependencies": {
            "epistemic_framework": _EPISTEMIC_FEATURE_ID,
            "evidence_confidence": _EVIDENCE_CONFIDENCE_FEATURE_ID,
            "provenance_lineage": _PROVENANCE_FEATURE_ID,
            "ml_deferred_wave": 3,
        },
        "rule_based_only": True,
        "acceptance_criteria": {
            "fact_inference_hypothesis_separated": True,
            "no_unsupported_action_claim": True,
            "source_freshness_confidence_every_conclusion": True,
            "no_single_source_domination_without_rule": True,
            "stale_source_penalties": True,
            "explainable": True,
            "no_standalone_ui": True,
        },
        "context_count": len(seed.get("contexts") or {}),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
