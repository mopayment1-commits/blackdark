"""
BLACKDARK — Acquisition asset audit (honest due diligence).

Separates code (copyable) from non-code assets: Data, Community, Brand,
Models, and Behavior Data — what a strategic buyer actually pays for.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal

import config

logger = logging.getLogger("BLACKDARK.AcquisitionAssets")

PillarVerdict = Literal["none", "emerging", "moderate", "strong"]

BRANDED_IP_MARKS = (
    "BLACKDARK",
    "CVVD (Cross-Venue Volume Discrepancy)",
    "SII (Sector Inflow Index)",
    "Oracle Flywheel",
    "77-Type Arbitrage Taxonomy",
)


def _pillar_score(label: PillarVerdict) -> int:
    return {"none": 0, "emerging": 25, "moderate": 55, "strong": 85}[label]


async def _audit_data_asset() -> dict[str, Any]:
    from data_moat_guard import fetch_dataset_stats

    dataset = await fetch_dataset_stats()
    try:
        from database import fetch_system_telemetry

        telemetry = await fetch_system_telemetry()
        pricing_rows = int(telemetry.get("pricing_count") or 0)
        db_mb = round(float(telemetry.get("database_size_bytes") or 0) / (1024 * 1024), 2)
    except Exception:
        pricing_rows = 0
        db_mb = 0.0

    live_labeled = int(dataset.get("live_labeled") or 0)
    if live_labeled >= 5000 and pricing_rows >= 500_000:
        verdict: PillarVerdict = "moderate"
    elif live_labeled >= 50 or pricing_rows >= 50_000:
        verdict = "emerging"
    else:
        verdict = "none"

    return {
        "pillar": "data",
        "verdict": verdict,
        "score": _pillar_score(verdict),
        "acquirable_today": verdict in {"moderate", "strong"},
        "evidence": {
            "pricing_ticks": pricing_rows,
            "database_mb": db_mb,
            "live_oracle_predictions": dataset.get("live_predictions"),
            "live_labeled_oracle": live_labeled,
            "synthetic_rows_excluded": dataset.get("synthetic_predictions"),
            "features_coverage_pct": dataset.get("features_coverage_pct"),
        },
        "honest_note_en": (
            "Majority is re-ingested public API data. "
            "Defensible slice = live oracle labels + self-generated audit trail."
        ),
    }


async def _audit_community_asset() -> dict[str, Any]:
    counts = {
        "waitlist": 0,
        "registered_users": 0,
        "paid_subscribers": 0,
        "telegram_free": 0,
        "alert_subscribers": 0,
    }
    try:
        from database import (
            count_telegram_free_subscribers,
            db_count_subscribers,
            db_count_waitlist,
            fetch_active_alert_subscriptions,
            fetch_user_count,
        )

        counts["waitlist"] = await db_count_waitlist()
        counts["registered_users"] = await fetch_user_count()
        counts["paid_subscribers"] = await db_count_subscribers()
        counts["telegram_free"] = await count_telegram_free_subscribers()
        counts["alert_subscribers"] = len(await fetch_active_alert_subscriptions())
    except Exception:
        logger.debug("Community counts failed", exc_info=True)

    community_size = (
        counts["waitlist"]
        + counts["registered_users"]
        + counts["telegram_free"]
        + counts["alert_subscribers"]
    )
    if counts["paid_subscribers"] >= 100 or community_size >= 10_000:
        verdict: PillarVerdict = "moderate"
    elif counts["paid_subscribers"] >= 10 or community_size >= 500:
        verdict = "emerging"
    else:
        verdict = "none"

    return {
        "pillar": "community",
        "verdict": verdict,
        "score": _pillar_score(verdict),
        "acquirable_today": counts["paid_subscribers"] >= 10 or community_size >= 1000,
        "evidence": counts,
        "honest_note_en": (
            "Community is not acquirable until registered users + paying subscribers "
            "or a large waitlist/Telegram base exists outside the codebase."
        ),
    }


def _audit_brand_asset() -> dict[str, Any]:
    manifest_path = Path(__file__).resolve().parent / "static" / "manifest.json"
    has_pwa = manifest_path.exists()
    domain = getattr(config, "APP_PUBLIC_NAME", "BLACKDARK")

    verdict: PillarVerdict = "emerging" if has_pwa else "none"

    return {
        "pillar": "brand",
        "verdict": verdict,
        "score": _pillar_score(verdict),
        "acquirable_today": False,
        "evidence": {
            "product_name": domain,
            "branded_ip_marks": list(BRANDED_IP_MARKS),
            "pwa_manifest": has_pwa,
            "external_traffic_proof_in_repo": False,
            "social_following_in_repo": False,
        },
        "honest_note_en": (
            "Brand equity (search, trust, press) is not in the repo. "
            "Only naming/IP marks and PWA shell exist today."
        ),
    }


async def _audit_models_asset() -> dict[str, Any]:
    from data_moat_guard import fetch_dataset_stats

    dataset = await fetch_dataset_stats()
    model_dir = getattr(config, "ML_MODELS_DIR", Path("data/models"))
    artifacts = []
    if model_dir.exists():
        artifacts = [p.name for p in model_dir.glob("*.joblib")] + [p.name for p in model_dir.glob("*.pkl")]

    labeled = int(dataset.get("live_labeled") or 0)
    min_train = int(getattr(config, "ML_MIN_TRAIN_SAMPLES", 50))
    has_deployed = any("latest" in name for name in artifacts)

    if has_deployed and labeled >= min_train:
        verdict: PillarVerdict = "emerging"
    else:
        verdict = "none"

    return {
        "pillar": "models",
        "verdict": verdict,
        "score": _pillar_score(verdict),
        "acquirable_today": has_deployed and labeled >= min_train,
        "evidence": {
            "model_artifacts": artifacts,
            "live_labeled_samples": labeled,
            "min_train_threshold": min_train,
            "production_engine": "rules_engine",
        },
        "honest_note_en": (
            "No trained .joblib in production path today. "
            "Rules engine is code — not a models asset."
        ),
    }


async def _audit_behavior_asset() -> dict[str, Any]:
    from behavior_data_service import fetch_behavior_asset_stats

    stats = await fetch_behavior_asset_stats(days=30)
    events = int(stats.get("total_events") or 0)
    unique = int(stats.get("unique_actor_count") or 0)

    if events >= 50_000 and unique >= 500:
        verdict: PillarVerdict = "moderate"
    elif events >= 1_000 and unique >= 50:
        verdict = "emerging"
    else:
        verdict = "none"

    return {
        "pillar": "behavior_data",
        "verdict": verdict,
        "score": _pillar_score(verdict),
        "acquirable_today": events >= 10_000 and unique >= 100,
        "evidence": stats,
        "honest_note_en": (
            "Behavior data accumulates only while the product runs with real users. "
            "Cannot be backfilled — this is the fastest non-code moat to build now."
        ),
    }


async def build_acquisition_asset_audit() -> dict[str, Any]:
    """Full honest audit for M&A — code vs non-code value split."""
    pillars = [
        await _audit_data_asset(),
        await _audit_community_asset(),
        _audit_brand_asset(),
        await _audit_models_asset(),
        await _audit_behavior_asset(),
    ]

    non_code_scores = [p["score"] for p in pillars]
    avg_non_code = round(sum(non_code_scores) / len(non_code_scores), 1)
    code_dominance_pct = max(0, min(100, int(100 - avg_non_code * 0.85)))

    acquirable_pillars = [p["pillar"] for p in pillars if p.get("acquirable_today")]
    strong_count = sum(1 for p in pillars if p["verdict"] in {"moderate", "strong"})

    if strong_count >= 3:
        deal_verdict = "consider_strategic_acquisition"
        buyer_action = "Proceed to data room — non-code assets justify premium."
    elif strong_count >= 1 or acquirable_pillars:
        deal_verdict = "asset_or_acqui_hire_only"
        buyer_action = "Code is copyable; price on team + partial assets only."
    else:
        deal_verdict = "pass_build_instead"
        buyer_action = (
            "Do not buy for tech. Value is ~85% rewriteable code. "
            "Build in 6 months or buy only if revenue/community proof exists off-repo."
        )

    return {
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "question": "Is value in code only?",
        "answer_en": "Mostly yes today — non-code assets are emerging, not investable alone.",
        "code_value_estimate_pct": code_dominance_pct,
        "non_code_value_estimate_pct": 100 - code_dominance_pct,
        "deal_verdict": deal_verdict,
        "buyer_recommendation_en": buyer_action,
        "acquirable_pillars_today": acquirable_pillars,
        "pillars": {p["pillar"]: p for p in pillars},
        "transferable_if_acquired": [
            item
            for item in (
                "Live-only oracle label stream (if flywheel running)",
                "User behavior event history (if volume sufficient)",
                "Waitlist + subscriber emails (with consent / GDPR review)",
                "Telegram community chat IDs",
                "Branded product name + taxonomy catalog",
                "Encrypted user API key vault (if populated)",
            )
            if item
        ],
        "not_transferable_or_weak": [
            "Generic arb/oracle Python modules (rewriteable)",
            "Public API cached ticks",
            "Rules engine weights without trained model",
            "100-exchange registry metadata without live feeds",
        ],
        "build_non_code_moat_now": [
            "Run DATA_MOAT + behavior logging on every user action",
            "Grow paid subscribers — community is the moat",
            "Deploy first ML model at 50+ live labels",
            "Publish transparent live-only accuracy — brand trust",
        ],
    }


def acquisition_assets_status() -> dict[str, Any]:
    return {
        "audit_available": True,
        "behavior_data_enabled": getattr(config, "BEHAVIOR_DATA_ENABLED", True),
        "data_moat_enabled": getattr(config, "DATA_MOAT_GUARD_ENABLED", True),
    }
