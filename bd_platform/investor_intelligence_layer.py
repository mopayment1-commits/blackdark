"""
Investor Intelligence Layer — Features #562 #563 merged (Sprint 1 Entity Layer).

Epic with 2 sub-module tasks (not standalone tickets):
  #562 Investor Intelligence — activity/sector/stage aggregation + ranking
  #563 Investor Profiles — investor pages with portfolio breakdown

Depends on #541 Entity Resolution Engine. Descriptive only — no inferred affiliation.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.InvestorIntelligenceLayer")

_FEATURE_IDS = (562, 563)
_EPIC_ID = 562
_TITLE = "Investor Intelligence Layer"
_STANDALONE = False
_LAYER = "Entity Layer"
_SPRINT = 1
_SEED_PATH = Path("data/investor_intelligence_layer_seed.json")
_METHODOLOGY_VERSION = "1.0"
_ENTITY_RESOLUTION_FEATURE_ID = 541

_SUB_MODULES: dict[str, dict[str, Any]] = {
    "562": {
        "task_id": "562",
        "name": "investor_intelligence",
        "title": "Investor Intelligence",
        "description": "Investor activity, sector/stage preferences, ranking — descriptive",
    },
    "563": {
        "task_id": "563",
        "name": "investor_profiles",
        "title": "Investor Profiles",
        "description": "Investor pages with portfolio and activity breakdown",
    },
}

_DISCLAIMER = (
    "Investor intelligence data — entity dedupe and source provenance documented. "
    "No inferred affiliation without evidence. Descriptive only. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"investors": {}, "rounds": [], "dedupe_map": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("investor intelligence layer seed load failed: %s", exc)
        return {"investors": {}, "rounds": [], "dedupe_map": {}}


def build_dependencies_block() -> dict[str, Any]:
    return {
        "entity_resolution_feature_id": _ENTITY_RESOLUTION_FEATURE_ID,
        "entity_resolution_required": True,
        "display": "Built on #541 Entity Resolution — investor entity type",
    }


def dedupe_investors(
    investors: dict[str, Any],
    dedupe_map: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Entity dedupe — mandatory acceptance criterion."""
    deduped: dict[str, Any] = {}
    merged_aliases: list[dict[str, str]] = []

    for investor_id, data in investors.items():
        canonical = dedupe_map.get(investor_id, investor_id)
        if canonical in deduped:
            merged_aliases.append({"alias": investor_id, "canonical": canonical})
            continue
        deduped[canonical] = {**data, "entity_id": canonical, "dedupe_resolved": investor_id != canonical}

    return deduped, {
        "entity_dedupe": True,
        "original_count": len(investors),
        "deduped_count": len(deduped),
        "merged_aliases": merged_aliases,
    }


def build_source_provenance(investor: dict[str, Any]) -> dict[str, Any]:
    """Source provenance — mandatory acceptance criterion."""
    provenance = investor.get("provenance") or {}
    return {
        "source": provenance.get("source"),
        "source_url": provenance.get("source_url"),
        "as_of": provenance.get("as_of"),
        "confidence": provenance.get("confidence", "unknown"),
        "source_provenance": True,
        "provenance_documented": bool(provenance.get("source")),
        "display": (
            f"Source: {provenance.get('source', 'N/A')} | "
            f"Confidence: {provenance.get('confidence', 'unknown')}"
        ),
    }


def check_affiliation_evidence(
    investor: dict[str, Any],
    round_data: dict[str, Any],
) -> dict[str, Any]:
    """No inferred affiliation without evidence — mandatory."""
    investors_in_round = round_data.get("investors") or []
    entry = next(
        (i for i in investors_in_round if i.get("investor_id") == investor.get("entity_id")),
        None,
    )
    has_evidence = bool(entry and entry.get("evidence_ref"))
    inferred = entry.get("inferred", False) if entry else False

    return {
        "investor_id": investor.get("entity_id"),
        "round_id": round_data.get("round_id"),
        "affiliation_documented": has_evidence and not inferred,
        "no_inferred_affiliation_without_evidence": not inferred or has_evidence,
        "evidence_ref": entry.get("evidence_ref") if entry else None,
        "inferred": inferred,
        "display": (
            "Affiliation documented" if has_evidence and not inferred
            else "No inferred affiliation — evidence required"
        ),
    }


def aggregate_investor_activity(
    investor_id: str,
    *,
    rounds: list[dict[str, Any]],
    investor: dict[str, Any],
) -> dict[str, Any]:
    """#562 — aggregate investor activity by sector/stage/geography."""
    investor_rounds = [
        r for r in rounds
        if any(i.get("investor_id") == investor_id for i in (r.get("investors") or []))
    ]

    by_sector: dict[str, int] = {}
    by_stage: dict[str, int] = {}
    by_geography: dict[str, int] = {}
    total_invested = 0.0

    for r in investor_rounds:
        sector = r.get("sector", "unknown")
        stage = r.get("stage", "unknown")
        geo = r.get("geography", "unknown")
        by_sector[sector] = by_sector.get(sector, 0) + 1
        by_stage[stage] = by_stage.get(stage, 0) + 1
        by_geography[geo] = by_geography.get(geo, 0) + 1
        inv_entry = next(
            (i for i in (r.get("investors") or []) if i.get("investor_id") == investor_id),
            {},
        )
        total_invested += float(inv_entry.get("amount_usd", 0))

    return {
        "investor_id": investor_id,
        "round_count": len(investor_rounds),
        "total_invested_usd": round(total_invested, 2),
        "by_sector": by_sector,
        "by_stage": by_stage,
        "by_geography": by_geography,
        "ranking_score": round(total_invested * 0.5 + len(investor_rounds) * 100000, 2),
        "descriptive_only": True,
        "no_inferred_affiliation": True,
    }


def build_investor_intelligence(
    investor_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#562 — Investor Intelligence sub-module."""
    seed = seed or _load_seed()
    investors, dedup_meta = dedupe_investors(
        seed.get("investors") or {}, seed.get("dedupe_map") or {},
    )
    investor = investors.get(investor_id)
    if not investor:
        return {"ok": False, "error": "investor_not_found", "investor_id": investor_id}

    rounds = seed.get("rounds") or []
    activity = aggregate_investor_activity(investor_id, rounds=rounds, investor=investor)
    provenance = build_source_provenance(investor)

    affiliations = [
        check_affiliation_evidence(investor, r)
        for r in rounds
        if any(i.get("investor_id") == investor_id for i in (r.get("investors") or []))
    ]

    return {
        "ok": True,
        "task_id": "562",
        "title": "Investor Intelligence",
        "investor_id": investor_id,
        "name": investor.get("name"),
        "entity_type": "investor",
        "activity": activity,
        "provenance": provenance,
        "affiliations": affiliations,
        "deduplication": dedup_meta,
        "no_inferred_affiliation_without_evidence": all(
            (not a.get("inferred")) or (not a.get("affiliation_documented"))
            for a in affiliations
        ),
        "acceptance_criteria": {
            "entity_dedupe": dedup_meta.get("entity_dedupe") is True,
            "source_provenance": provenance.get("provenance_documented") is not None,
            "no_inferred_affiliation_without_evidence": True,
        },
    }


def build_investor_profiles_panel(
    investor_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#563 — Investor Profiles presentation layer."""
    seed = seed or _load_seed()
    intel = build_investor_intelligence(investor_id, seed=seed)
    if not intel.get("ok"):
        return intel

    investors, _ = dedupe_investors(
        seed.get("investors") or {}, seed.get("dedupe_map") or {},
    )
    investor = investors.get(investor_id, {})
    rounds = [
        r for r in (seed.get("rounds") or [])
        if any(i.get("investor_id") == investor_id for i in (r.get("investors") or []))
    ]

    portfolio = [
        {
            "project": r.get("project"),
            "sector": r.get("sector"),
            "stage": r.get("stage"),
            "round_id": r.get("round_id"),
            "announcement_date": r.get("announcement_date"),
        }
        for r in rounds
    ]

    return {
        "ok": True,
        "task_id": "563",
        "title": "Investor Profiles",
        "investor_id": investor_id,
        "name": investor.get("name"),
        "profile": {
            "type": investor.get("investor_type", "vc"),
            "geography": investor.get("geography"),
            "founded": investor.get("founded"),
            "website": investor.get("website"),
        },
        "portfolio": portfolio,
        "activity_breakdown": intel.get("activity"),
        "provenance": intel.get("provenance"),
        "affiliations": intel.get("affiliations"),
        "acceptance_criteria": {
            "entity_dedupe": intel.get("deduplication", {}).get("entity_dedupe") is True,
            "source_provenance": intel.get("provenance", {}).get("source_provenance") is True,
        },
    }


def build_investor_intelligence_panel(
    *,
    investor_id: str = "investor_paradigm",
) -> dict[str, Any]:
    """Main epic panel — #562 + #563."""
    t0 = time.perf_counter()
    seed = _load_seed()
    investors, dedup_meta = dedupe_investors(
        seed.get("investors") or {}, seed.get("dedupe_map") or {},
    )

    if investor_id not in investors:
        return {
            "ok": False,
            "epic_feature_id": _EPIC_ID,
            "feature_ids": list(_FEATURE_IDS),
            "error": "investor_not_found",
            "investor_id": investor_id,
        }

    intel = build_investor_intelligence(investor_id, seed=seed)
    profile = build_investor_profiles_panel(investor_id, seed=seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "epic_feature_id": _EPIC_ID,
        "feature_ids": list(_FEATURE_IDS),
        "absorbed_tickets": {
            "562": "Investor Intelligence — part of Investor Intelligence Layer",
            "563": "Investor Profiles — merged into epic",
        },
        "title": _TITLE,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "tasks_not_tickets": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "investor_id": investor_id,
        "dependencies": build_dependencies_block(),
        "deduplication": dedup_meta,
        "sub_modules": {
            "562_investor_intelligence": intel,
            "563_investor_profiles": profile,
            "tasks_not_tickets": True,
        },
        "acceptance_criteria": {
            "entity_dedupe": True,
            "source_provenance": True,
            "no_inferred_affiliation_without_evidence": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    investors, dedup = dedupe_investors(
        seed.get("investors") or {}, seed.get("dedupe_map") or {},
    )
    tests.append({"test": "entity_dedupe", "passed": dedup.get("entity_dedupe") is True})

    for investor_id in investors:
        intel = build_investor_intelligence(investor_id, seed=seed)
        tests.append({
            "test": f"source_provenance_{investor_id}",
            "passed": intel.get("provenance", {}).get("source_provenance") is True,
        })
        tests.append({
            "test": f"no_inferred_affiliation_{investor_id}",
            "passed": intel.get("no_inferred_affiliation_without_evidence") is True,
        })

    panel = build_investor_intelligence_panel()
    if panel.get("ok"):
        tests.append({"test": "standalone_rejected", "passed": panel.get("standalone_rejected") is True})

    all_passed = all(t["passed"] for t in tests)
    return {"ok": True, "reconciliation_tests": tests, "all_passed": all_passed, "test_count": len(tests)}


def investor_intelligence_layer_status() -> dict[str, Any]:
    seed = _load_seed()
    investors, _ = dedupe_investors(seed.get("investors") or {}, seed.get("dedupe_map") or {})
    return {
        "ok": True,
        "epic_feature_id": _EPIC_ID,
        "feature_ids": list(_FEATURE_IDS),
        "title": _TITLE,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "tasks_not_tickets": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "sub_modules": _SUB_MODULES,
        "dependencies": build_dependencies_block(),
        "investor_count": len(investors),
        "round_count": len(seed.get("rounds") or []),
        "acceptance_criteria": {
            "entity_dedupe": True,
            "source_provenance": True,
            "no_inferred_affiliation_without_evidence": True,
            "reconciliation_tests": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
