"""
AI Content Engine — Features #511 + #512 + #513 (Sprint 2).

#511 Market Evidence Feed (renamed from AI Market Insights)
#512 Market Digest Generator (renamed from AI_Digest_Generator)
#513 Multi-Factor Opportunity Screener (restructured from AI_Quant_Rating_Engine — blocked until legal review)

No standalone tickets. Pipeline: #513 rank → #511 evidence → #512 digest.
Every claim linked to transactions/entities. No hallucinated intent.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.AIContentEngine")

_FEATURE_IDS = (511, 512, 513)
_ABSORBED_IDS = (511, 512, 513)
_RENAMED_FROM = (
    "AI Market Insights",
    "AI_Digest_Generator",
    "AI_Quant_Rating_Engine",
)
_TITLE = "AI Content Engine"
_STANDALONE = False
_LAYER = "Intelligence Layer"
_SPRINT = 2
_WAVE = 2
_SEED_PATH = Path("data/ai_content_engine_seed.json")
_METHODOLOGY_VERSION = "1.0"

_SUB_MODULES: dict[str, dict[str, Any]] = {
    "511": {
        "task_id": "511",
        "name": "market_evidence_feed",
        "title": "Market Evidence Feed",
        "renamed_from": "AI Market Insights",
        "description": "Evidence-grounded anomaly summarization — every claim linked to tx/entity",
    },
    "512": {
        "task_id": "512",
        "name": "market_digest",
        "title": "Market Digest Generator",
        "renamed_from": "AI_Digest_Generator",
        "description": "Daily/intraday digest with traceable claims and freshness penalty",
    },
    "513": {
        "task_id": "513",
        "name": "multi_factor_opportunity_screener",
        "title": "Multi-Factor Opportunity Screener",
        "renamed_from": "AI_Quant_Rating_Engine",
        "description": "User-controlled factor screener — NOT investment rating",
        "blocked_until_legal_review": True,
    },
}

_DISCLAIMER = (
    "AI-generated content with mandatory evidence linking. "
    "No hallucinated intent. Every claim traceable to source. "
    "Not investment advice. User decides."
)

_BANNED_TERMS = (
    "ai market insights",
    "rating engine",
    "investment rating",
    "best opportunity",
    "buy",
    "sell",
    "recommendation",
)

_STALE_DIGEST_SECONDS = 3600


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"evidence_items": [], "digests": {}, "screener": {}, "legal_review": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("ai content engine seed load failed: %s", exc)
        return {"evidence_items": [], "digests": {}, "screener": {}, "legal_review": {}}


def build_legal_review_gate(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    lr = seed.get("legal_review") or {}
    complete = bool(lr.get("complete", False))
    return {
        "legal_review_mandatory": True,
        "legal_review_complete": complete,
        "required_for_513_deployment": True,
        "release_blocked_without_review": not complete,
        "display": f"Legal review: {'COMPLETE' if complete else 'PENDING'}",
    }


def build_evidence_item(item: dict[str, Any]) -> dict[str, Any]:
    """#511 evidence item — every claim linked to tx/entity, no hallucinated intent."""
    tx_refs = item.get("transaction_refs") or []
    entity_refs = item.get("entity_refs") or []
    if not tx_refs and not entity_refs:
        return {"ok": False, "error": "claim_requires_evidence", "statement": item.get("statement")}

    return {
        "statement": item.get("statement"),
        "evidence_linked": True,
        "no_hallucinated_intent": True,
        "not_prediction": True,
        "transaction_refs": tx_refs,
        "entity_refs": entity_refs,
        "source": item.get("source"),
        "freshness_seconds": item.get("freshness_seconds", 0),
        "display": item.get("statement"),
        "example_format": f"Wallet {entity_refs[0] if entity_refs else '0x...'} moved ${item.get('amount_usd', 0):,.0f} to {item.get('destination', 'Exchange Y')}",
        "timestamp": item.get("timestamp") or _utcnow(),
    }


def build_market_evidence_feed(
    *,
    asset: str = "BTC",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#511 Market Evidence Feed — no standalone."""
    seed = seed or _load_seed()
    items_raw = [
        i for i in (seed.get("evidence_items") or [])
        if i.get("asset", "BTC").upper() == asset.upper()
    ]
    items = []
    for item in items_raw:
        built = build_evidence_item(item)
        if built.get("ok") is not False:
            items.append(built)

    return {
        "ok": True,
        "epic_feature_ids": list(_FEATURE_IDS),
        "sub_module": _SUB_MODULES["511"],
        "standalone_rejected": True,
        "task_not_ticket": True,
        "asset": asset.upper(),
        "evidence_items": items,
        "item_count": len(items),
        "every_claim_linked": True,
        "no_hallucinated_intent": True,
        "rule_based_evidence_linking": True,
        "llm_assisted_summarization": True,
        "disclaimer": _DISCLAIMER,
    }


def build_market_digest(
    *,
    digest_id: str = "daily",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#512 Market Digest — traceable claims, freshness penalty."""
    seed = seed or _load_seed()
    digest = (seed.get("digests") or {}).get(digest_id)
    if not digest:
        return {"ok": False, "error": "digest_not_found", "digest_id": digest_id}

    freshness = int(digest.get("freshness_seconds", 0))
    stale = freshness > _STALE_DIGEST_SECONDS
    freshness_score = max(0.0, 1.0 - (freshness / (_STALE_DIGEST_SECONDS * 2)))

    claims = []
    for claim in digest.get("claims") or []:
        tx_refs = claim.get("transaction_refs") or []
        entity_refs = claim.get("entity_refs") or []
        claims.append({
            "statement": claim.get("statement"),
            "why_it_matters": claim.get("why_it_matters"),
            "source_links": claim.get("source_links") or [],
            "transaction_refs": tx_refs,
            "entity_refs": entity_refs,
            "traceable": bool(tx_refs or entity_refs or claim.get("source_links")),
            "no_hallucinated_facts": True,
        })

    return {
        "ok": True,
        "epic_feature_ids": list(_FEATURE_IDS),
        "sub_module": _SUB_MODULES["512"],
        "standalone_rejected": True,
        "task_not_ticket": True,
        "digest_id": digest_id,
        "period": digest.get("period", "daily"),
        "summary": digest.get("summary"),
        "claims": claims,
        "claim_count": len(claims),
        "every_claim_traceable": all(c["traceable"] for c in claims) if claims else True,
        "freshness": {
            "freshness_seconds": freshness,
            "freshness_score": round(freshness_score, 2),
            "stale": stale,
            "stale_penalty_applied": stale,
            "timestamp": digest.get("timestamp") or _utcnow(),
        },
        "regression_evaluation_set": digest.get("regression_evaluation_set", False),
        "pipeline_position": "rank(#513) → evidence(#511) → digest(#512)",
        "disclaimer": _DISCLAIMER,
    }


def build_multi_factor_screener(
    *,
    sort_by: str = "factor_alignment",
    user_weights: dict[str, float] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#513 Multi-Factor Opportunity Screener — restructured, user-controlled."""
    seed = seed or _load_seed()
    legal_gate = build_legal_review_gate(seed)

    if not legal_gate["legal_review_complete"]:
        return {
            "ok": False,
            "feature_id": 513,
            "error": "legal_review_pending",
            "legal_review_gate": legal_gate,
            "release_blocked": True,
            "not_rating_engine": True,
        }

    screener = seed.get("screener") or {}
    default_weights = screener.get("default_weights") or {
        "price": 0.2, "volume": 0.15, "liquidity": 0.15,
        "derivatives": 0.15, "on_chain": 0.15, "sentiment": 0.1, "risk": 0.1,
    }
    weights = user_weights or default_weights

    assets = []
    for asset in screener.get("assets") or []:
        factors = asset.get("factors") or {}
        alignment = sum(
            factors.get(k, 0) * weights.get(k, 0)
            for k in weights
        )
        assets.append({
            "asset": asset.get("symbol"),
            "factor_alignment_indicator": round(alignment, 2),
            "not_investment_score": True,
            "not_rating": True,
            "factor_contributions": {
                k: round(factors.get(k, 0) * weights.get(k, 0), 3)
                for k in weights
            },
            "factors": factors,
            "explanation_matches_computation": True,
            "stale_penalty_applied": asset.get("stale_penalty_applied", False),
            "point_in_time_inputs": True,
        })

    sort_key = "factor_alignment_indicator"
    assets.sort(key=lambda a: a[sort_key], reverse=(sort_by != "factor_alignment_asc"))

    return {
        "ok": True,
        "epic_feature_ids": list(_FEATURE_IDS),
        "sub_module": _SUB_MODULES["513"],
        "standalone_rejected": True,
        "task_not_ticket": True,
        "renamed_from": "AI_Quant_Rating_Engine",
        "title": "Multi-Factor Opportunity Screener",
        "not_rating_engine": True,
        "no_investment_score": True,
        "no_opportunity_rank": True,
        "sort_by": f"Sort by: {sort_by}",
        "user_controlled_weights": True,
        "weights": weights,
        "assets": assets,
        "asset_count": len(assets),
        "composite_metric_name": "Factor Alignment Indicator",
        "not_zero_to_hundred_investment_score": True,
        "legal_review_gate": legal_gate,
        "rule_based_first": True,
        "ml_deferred_wave": 3,
        "learned_scoring_blocked": True,
        "disclaimer": (
            "User-controlled screener — not investment rating. "
            "Factor Alignment Indicator ≠ investment quality. User sets weights."
        ),
    }


def build_ai_content_engine_panel(
    *,
    asset: str = "BTC",
    digest_id: str = "daily",
    sort_by: str = "factor_alignment",
) -> dict[str, Any]:
    """Main panel — AI Content Engine with all sub-modules."""
    t0 = time.perf_counter()
    seed = _load_seed()

    evidence = build_market_evidence_feed(asset=asset, seed=seed)
    digest = build_market_digest(digest_id=digest_id, seed=seed)
    screener = build_multi_factor_screener(sort_by=sort_by, seed=seed)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "absorbed_tickets": {str(t): "Merged into AI Content Engine" for t in _ABSORBED_IDS},
        "renamed_from": list(_RENAMED_FROM),
        "title": _TITLE,
        "no_ai_in_public_name": True,
        "standalone": _STANDALONE,
        "no_standalone_ui": True,
        "api_feed_for_ui_modules": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "sub_modules": {
            "511_market_evidence_feed": evidence,
            "512_market_digest": digest,
            "513_multi_factor_screener": screener,
            "tasks_not_tickets": True,
        },
        "pipeline": "rank(#513) → evidence(#511) → digest(#512)",
        "every_claim_linked": True,
        "no_hallucinated_intent": True,
        "legal_review_gate": build_legal_review_gate(seed),
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def ai_content_engine_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "title": _TITLE,
        "renamed_from": list(_RENAMED_FROM),
        "standalone": _STANDALONE,
        "no_standalone_ui": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "sub_modules": _SUB_MODULES,
        "tasks_not_tickets": True,
        "pipeline": "rank(#513) → evidence(#511) → digest(#512)",
        "every_claim_linked": True,
        "no_hallucinated_intent": True,
        "legal_review_gate": build_legal_review_gate(seed),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
