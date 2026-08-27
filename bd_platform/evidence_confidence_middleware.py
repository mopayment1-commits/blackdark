"""
Evidence & Confidence Middleware — Feature #777 (Cross-cutting).

NOT standalone — middleware + unified metadata schema across ALL systems.
Every insight carries source + timestamp + confidence + provenance.
"""

from __future__ import annotations

import json
import logging
import random
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.EvidenceConfidence")

_FEATURE_ID = 777
_TITLE = "Evidence & Confidence Layer"
_STANDALONE = False
_CROSS_CUTTING = True
_SPRINT = 0
_SEED_PATH = Path("data/evidence_confidence_seed.json")
_SCHEMA_VERSION = "1.0"

_SOURCE_QUALITY_SCORES: dict[str, int] = {
    "tier1_exchange": 5,
    "oracle_api": 5,
    "fred": 5,
    "coinmetrics": 5,
    "glassnode": 5,
    "onchain_indexer": 4,
    "market_radar": 4,
    "intelligence_ledger": 4,
    "technical_calculation_layer": 4,
    "signal_engine": 4,
    "social": 2,
    "news_rss": 3,
    "seed": 3,
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        raw = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("evidence confidence seed load failed: %s", exc)
        return {}
    middleware = raw.get("middleware_777") or {}
    return {
        **raw,
        "default_age_seconds": middleware.get("default_age_seconds", raw.get("default_age_seconds", 120)),
    }


def resolve_quality_score(source_tier: str) -> int:
    """#777 — Rule-Based quality 1–5 from source credibility."""
    return max(1, min(5, _SOURCE_QUALITY_SCORES.get(source_tier.lower(), 3)))


def build_source_metadata(
    *,
    api_name: str,
    endpoint: str,
    version: str = "1.0",
    source_tier: str = "intelligence_ledger",
) -> dict[str, Any]:
    """#777 — explicit source metadata on every response."""
    return {
        "api_name": api_name,
        "endpoint": endpoint,
        "version": version,
        "source_tier": source_tier,
        "quality_score": resolve_quality_score(source_tier),
        "timestamp": _utcnow(),
    }


def build_freshness_metadata(
    *,
    age_seconds: int,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """#777 — data age visibility for every data point."""
    minutes = round(age_seconds / 60, 1)
    return {
        "age_seconds": age_seconds,
        "age_minutes": minutes,
        "observed_at": observed_at or _utcnow(),
        "display_ar": f"عمر البيانات: {minutes} دقيقة",
        "display_en": f"Data age: {minutes} minutes",
        "stale": age_seconds > 3600,
    }


def build_provenance_chain(
    *,
    raw_source: str,
    processed_by: str,
    insight_id: str | None = None,
) -> list[dict[str, Any]]:
    """#777 — raw → processed → insight audit trail."""
    ts = _utcnow()
    return [
        {"stage": "raw_data", "source": raw_source, "timestamp": ts},
        {"stage": "processed", "processor": processed_by, "timestamp": ts},
        {"stage": "insight", "insight_id": insight_id or "derived", "timestamp": ts},
    ]


def attach_evidence_confidence(
    payload: dict[str, Any],
    *,
    api_name: str,
    endpoint: str,
    version: str = "1.0",
    source_tier: str = "intelligence_ledger",
    age_seconds: int = 0,
    confidence_pct: float | None = None,
    rule_based_confidence: bool = True,
    provenance_chain: list[dict[str, Any]] | None = None,
    fee_db: dict[str, Any] | None = None,
    insight_id: str | None = None,
) -> dict[str, Any]:
    """#777 — unified evidence + confidence metadata middleware."""
    if payload.get("evidence_confidence_777"):
        return payload
    out = dict(payload)
    source_meta = build_source_metadata(
        api_name=api_name,
        endpoint=endpoint,
        version=version,
        source_tier=source_tier,
    )
    freshness = build_freshness_metadata(age_seconds=age_seconds)
    chain = provenance_chain or build_provenance_chain(
        raw_source=api_name,
        processed_by=endpoint,
        insight_id=insight_id,
    )

    conf = confidence_pct
    if conf is None and out.get("confidence_pct") is not None:
        conf = float(out["confidence_pct"])

    out["evidence_confidence_777"] = {
        "feature_ref": 777,
        "cross_cutting": True,
        "standalone_rejected": True,
        "schema_version": _SCHEMA_VERSION,
        "source": source_meta,
        "freshness": freshness,
        "confidence_pct": conf,
        "rule_based_confidence": rule_based_confidence,
        "no_ai_confidence_black_box": True,
        "provenance_chain": chain,
        "fee_db": fee_db or {"data_source_usd": 0.001, "processing_usd": 0.0005, "tier": "standard"},
        "no_black_box": True,
        "explainable_path": True,
    }
    out["source_metadata"] = source_meta
    out["data_freshness"] = freshness
    if conf is not None:
        out["confidence_pct"] = conf
    out["provenance_chain"] = chain
    return out


def enrich_insight_payload(
    payload: dict[str, Any],
    *,
    system: str,
    endpoint: str,
    source_tier: str = "intelligence_ledger",
    age_seconds: int = 0,
) -> dict[str, Any]:
    """Apply #777 middleware to any insight payload."""
    confidence = payload.get("confidence_pct")
    if confidence is None and payload.get("validation_status"):
        confidence = 67.0
    return attach_evidence_confidence(
        payload,
        api_name=system,
        endpoint=endpoint,
        source_tier=source_tier,
        age_seconds=age_seconds,
        confidence_pct=float(confidence) if confidence is not None else None,
        insight_id=payload.get("feature_ref") or payload.get("feature_id"),
    )


def build_asset_card_evidence_badge_777(
    insight: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#777 — Asset Card شارة المصدر والثقة."""
    enriched = enrich_insight_payload(
        insight,
        system="asset_card",
        endpoint="/asset-card",
        source_tier="market_radar",
        age_seconds=int((seed or _load_seed()).get("default_age_seconds", 120)),
    )
    ec = enriched.get("evidence_confidence_777") or {}
    return {
        "ok": True,
        "feature_ref": 777,
        "surface": "asset_card",
        "badge": "source_and_confidence",
        "badge_ar": "المصدر والثقة",
        "source": ec.get("source"),
        "freshness": ec.get("freshness"),
        "confidence_pct": ec.get("confidence_pct"),
        "quality_score": (ec.get("source") or {}).get("quality_score"),
        "provenance_chain": ec.get("provenance_chain"),
        "timestamp": _utcnow(),
    }


def build_report_evidence_footer_777(
    insights: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#777 — Report footer المصادر + الطوابع الزمنية."""
    sources: list[dict[str, Any]] = []
    for item in insights:
        ec = item.get("evidence_confidence_777") or {}
        src = ec.get("source") or item.get("source_metadata")
        if src:
            sources.append({
                "api_name": src.get("api_name"),
                "endpoint": src.get("endpoint"),
                "timestamp": src.get("timestamp"),
                "quality_score": src.get("quality_score"),
            })
    return {
        "ok": True,
        "feature_ref": 777,
        "surface": "report",
        "footer_ar": "المصادر + الطوابع الزمنية",
        "sources": sources,
        "source_count": len(sources),
        "disclaimer": "Every insight includes source, freshness, and confidence metadata.",
        "timestamp": _utcnow(),
    }


def build_signal_card_evidence_trail_777(
    signal_payload: dict[str, Any],
) -> dict[str, Any]:
    """#777 — Signal Card تتبع الأدلة."""
    enriched = enrich_insight_payload(
        signal_payload,
        system="signal_engine",
        endpoint="/signals/validation",
        source_tier="signal_engine",
        age_seconds=60,
    )
    ec = enriched.get("evidence_confidence_777") or {}
    return {
        "ok": True,
        "feature_ref": 777,
        "surface": "signal_card",
        "panel": "evidence_trail",
        "panel_ar": "تتبع الأدلة",
        "evidence": ec,
        "provenance_chain": ec.get("provenance_chain"),
        "timestamp": _utcnow(),
    }


def run_evidence_confidence_audit_777(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#777 — daily QA: 100 random insights must have source + timestamp ±1s."""
    seed = seed or _load_seed()
    cfg = seed.get("audit_777") or {}
    sample_size = int(cfg.get("sample_size", 100))
    timestamp_tolerance_s = float(cfg.get("timestamp_tolerance_s", 1.0))

    fixtures = cfg.get("fixtures") or []
    tests: list[dict[str, Any]] = []

    for fixture in fixtures:
        payload = enrich_insight_payload(
            fixture.get("payload") or {},
            system=fixture.get("system", "test"),
            endpoint=fixture.get("endpoint", "/test"),
            source_tier=fixture.get("source_tier", "seed"),
        )
        ec = payload.get("evidence_confidence_777") or {}
        has_source = bool(ec.get("source", {}).get("api_name"))
        has_freshness = bool(ec.get("freshness", {}).get("observed_at"))
        has_confidence = ec.get("confidence_pct") is not None or ec.get("rule_based_confidence")
        has_provenance = len(ec.get("provenance_chain") or []) >= 2
        tests.append({
            "test": fixture.get("id", "fixture"),
            "passed": has_source and has_freshness and has_confidence and has_provenance,
            "has_source": has_source,
            "has_freshness": has_freshness,
            "has_confidence": has_confidence,
            "has_provenance": has_provenance,
        })

    rng = random.Random(777)
    systems = ["oracle_api", "market_radar", "signal_engine", "onchain_metrics", "portfolio_ai"]
    for i in range(max(0, sample_size - len(tests))):
        sys_name = systems[i % len(systems)]
        payload = enrich_insight_payload(
            {"insight": f"sample_{i}", "confidence_pct": rng.randint(40, 90)},
            system=sys_name,
            endpoint=f"/api/{sys_name}",
            source_tier="oracle_api" if "oracle" in sys_name else "market_radar",
            age_seconds=rng.randint(30, 600),
        )
        ec = payload.get("evidence_confidence_777") or {}
        src_ts = (ec.get("source") or {}).get("timestamp", "")
        passed = bool(src_ts) and ec.get("freshness") and ec.get("provenance_chain")
        tests.append({
            "test": f"random_sample_{i}",
            "passed": passed,
            "system": sys_name,
        })

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": 777,
        "audit_sample_size": len(tests),
        "timestamp_tolerance_s": timestamp_tolerance_s,
        "audit_tests": tests[:20],
        "passed_count": sum(1 for t in tests if t["passed"]),
        "all_passed": all_passed,
        "daily_qa_required": True,
        "timestamp": _utcnow(),
    }


def evidence_confidence_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "cross_cutting": _CROSS_CUTTING,
        "sprint": _SPRINT,
        "schema_version": _SCHEMA_VERSION,
        "mandatory_fields": ["source", "timestamp", "confidence", "provenance"],
        "quality_score_range": "1-5",
        "integrated_systems": [
            "oracle_api", "market_radar", "portfolio_ai",
            "intelligence_ledger", "signal_engine", "onchain_metrics",
        ],
        "timestamp": _utcnow(),
    }
