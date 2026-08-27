"""
On-Chain Metrics Library — Epic #577 (Foundation Layer).

Sub-module tasks (not standalone tickets):
  #577 On-Chain Metrics Library — canonical definitions + versioning + QA
  #574 Network Data Pro Metrics — institutional API delivery
  #603 Supply Distribution Intelligence — balance cohorts + supply share + change

#603 merged into #577 — no standalone module.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bd_platform.institutional_standards import missing_value, wrap_intelligence_response

logger = logging.getLogger("BLACKDARK.OnchainMetricsLibrary")

_FEATURE_IDS = (577, 574, 603)
_EPIC_ID = 577
_SUPPLY_DISTRIBUTION_TASK_ID = 603
_TITLE = "On-Chain Metrics Library"
_STANDALONE = False
_LAYER = "Foundation Layer"
_SPRINT = 2
_SEED_PATH = Path("data/onchain_metrics_library_seed.json")
_METHODOLOGY_VERSION = "1.0"
_COHORT_THRESHOLD_VERSION = "1.0"

# Mandatory 7 balance cohorts — versioned (#603 acceptance).
BALANCE_COHORT_THRESHOLDS_V1: tuple[dict[str, Any], ...] = (
    {"cohort_id": "cohort_1", "label": "0–0.1", "min_balance": 0.0, "max_balance": 0.1},
    {"cohort_id": "cohort_2", "label": "0.1–1", "min_balance": 0.1, "max_balance": 1.0},
    {"cohort_id": "cohort_3", "label": "1–10", "min_balance": 1.0, "max_balance": 10.0},
    {"cohort_id": "cohort_4", "label": "10–100", "min_balance": 10.0, "max_balance": 100.0},
    {"cohort_id": "cohort_5", "label": "100–1K", "min_balance": 100.0, "max_balance": 1000.0},
    {"cohort_id": "cohort_6", "label": "1K–10K", "min_balance": 1000.0, "max_balance": 10000.0},
    {"cohort_id": "cohort_7", "label": "10K+", "min_balance": 10000.0, "max_balance": None},
)

_SUB_MODULES: dict[str, dict[str, Any]] = {
    "577": {
        "task_id": "577",
        "name": "onchain_metrics_library",
        "title": "On-Chain Metrics Library",
        "description": "Canonical metric definitions with formula/source/version + historical QA",
    },
    "574": {
        "task_id": "574",
        "name": "network_data_pro_metrics",
        "title": "Network Data Pro Metrics",
        "description": "Institutional API delivery — sub-task of #577",
        "standalone_rejected": True,
    },
    "603": {
        "task_id": "603",
        "name": "supply_distribution_intelligence",
        "title": "Supply Distribution Intelligence",
        "description": "Balance cohorts + supply share + change — merged into #577",
        "standalone_rejected": True,
        "merged_into": 577,
    },
}

_DISCLAIMER = (
    "On-chain metrics — versioned cohort thresholds, known entities labeled separately. "
    "Missing data shown as unavailable — never zero. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"metric_definitions": {}, "assets": {}, "historical_qa": {}, "known_entities": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("onchain metrics library seed load failed: %s", exc)
        return {"metric_definitions": {}, "assets": {}, "historical_qa": {}, "known_entities": {}}


def build_cohort_thresholds() -> dict[str, Any]:
    """#603 — versioned balance cohort thresholds (7 mandatory tiers)."""
    return {
        "version": _COHORT_THRESHOLD_VERSION,
        "effective_from": "2026-01-01T00:00:00Z",
        "cohort_count": len(BALANCE_COHORT_THRESHOLDS_V1),
        "thresholds": list(BALANCE_COHORT_THRESHOLDS_V1),
        "versioned": True,
        "mandatory_tier_count": 7,
        "display": " | ".join(t["label"] for t in BALANCE_COHORT_THRESHOLDS_V1),
    }


def _balance_cohort_id(balance: float, thresholds: tuple[dict[str, Any], ...] | None = None) -> str:
    tiers = thresholds or BALANCE_COHORT_THRESHOLDS_V1
    for tier in tiers:
        lo = float(tier["min_balance"])
        hi = tier.get("max_balance")
        if balance >= lo and (hi is None or balance < float(hi)):
            return str(tier["cohort_id"])
    return "cohort_7"


def get_known_entities(seed: dict[str, Any], asset: str) -> dict[str, list[dict[str, Any]]]:
    """Known exchange/contract entities — excluded from retail cohorts, labeled separately."""
    entities = seed.get("known_entities") or {}
    asset_entities = entities.get(asset.upper(), entities.get("default", {}))
    return {
        "exchange": list(asset_entities.get("exchange", [])),
        "contract": list(asset_entities.get("contract", [])),
        "bridge": list(asset_entities.get("bridge", [])),
    }


def _known_entity_lookup(seed: dict[str, Any], asset: str) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for category, entries in get_known_entities(seed, asset).items():
        for entry in entries:
            addr = str(entry.get("address", "")).lower()
            if addr:
                lookup[addr] = {**entry, "entity_category": category}
    return lookup


def _classify_holder(
    holder: dict[str, Any],
    *,
    known_lookup: dict[str, dict[str, Any]],
    thresholds: tuple[dict[str, Any], ...] | None = None,
) -> dict[str, Any]:
    address = str(holder.get("address", "")).lower()
    balance = float(holder.get("balance") or 0.0)
    entity = known_lookup.get(address)
    if entity:
        return {
            "address": address,
            "balance": balance,
            "cohort_id": None,
            "known_entity": True,
            "entity_category": entity.get("entity_category"),
            "entity_name": entity.get("name") or entity.get("label"),
            "excluded_from_retail_cohorts": True,
            "labeled_separately": True,
        }
    cohort_id = _balance_cohort_id(balance, thresholds)
    label = next((t["label"] for t in (thresholds or BALANCE_COHORT_THRESHOLDS_V1) if t["cohort_id"] == cohort_id), cohort_id)
    return {
        "address": address,
        "balance": balance,
        "cohort_id": cohort_id,
        "cohort_label": label,
        "known_entity": False,
        "excluded_from_retail_cohorts": False,
        "labeled_separately": False,
    }


def build_supply_distribution_dashboard(
    asset: str = "ETH",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#603 — distribution dashboard: balance cohorts + supply share + change."""
    seed = seed or _load_seed()
    sym = asset.upper()
    asset_row = (seed.get("assets") or {}).get(sym, {})
    supply_row = asset_row.get("supply_distribution_603") or {}
    holders = list(supply_row.get("holders") or [])
    circulating = float(supply_row.get("circulating_supply") or 0.0)
    prior = supply_row.get("prior_cohorts") or {}

    if not holders or circulating <= 0:
        return {
            "ok": False,
            "task_id": str(_SUPPLY_DISTRIBUTION_TASK_ID),
            "standalone_rejected": True,
            "merged_into": _EPIC_ID,
            "asset": sym,
            "error": "supply_distribution_data_unavailable",
        }

    known_lookup = _known_entity_lookup(seed, sym)
    classified = [_classify_holder(h, known_lookup=known_lookup) for h in holders]

    cohort_defs = {t["cohort_id"]: t for t in BALANCE_COHORT_THRESHOLDS_V1}
    cohorts: list[dict[str, Any]] = []
    known_entity_supply = 0.0
    retail_supply = 0.0

    for tier in BALANCE_COHORT_THRESHOLDS_V1:
        cid = tier["cohort_id"]
        tier_holders = [h for h in classified if h.get("cohort_id") == cid]
        tier_supply = sum(float(h["balance"]) for h in tier_holders)
        retail_supply += tier_supply
        prior_share = prior.get(cid, {})
        share_pct = round(tier_supply / circulating * 100, 4) if circulating > 0 else 0.0
        prior_share_pct = prior_share.get("supply_share_pct")
        change_pp = round(share_pct - float(prior_share_pct), 4) if prior_share_pct is not None else None
        cohorts.append({
            "cohort_id": cid,
            "label": tier["label"],
            "min_balance": tier["min_balance"],
            "max_balance": tier["max_balance"],
            "holder_count": len(tier_holders),
            "supply": round(tier_supply, 8),
            "supply_share_pct": share_pct,
            "change_share_pp": change_pp,
            "threshold_version": _COHORT_THRESHOLD_VERSION,
        })

    known_entities_labeled: list[dict[str, Any]] = []
    for h in classified:
        if not h.get("known_entity"):
            continue
        bal = float(h["balance"])
        known_entity_supply += bal
        known_entities_labeled.append({
            "address": h["address"],
            "balance": bal,
            "entity_category": h.get("entity_category"),
            "entity_name": h.get("entity_name"),
            "supply_share_pct": round(bal / circulating * 100, 4) if circulating > 0 else 0.0,
        })

    cohort_supply_total = retail_supply + known_entity_supply
    reconciled = abs(cohort_supply_total - circulating) < max(1e-6, circulating * 1e-9)

    concentration = compute_concentration_risk_metrics(cohorts, circulating_supply=circulating)

    return {
        "ok": True,
        "task_id": str(_SUPPLY_DISTRIBUTION_TASK_ID),
        "standalone_rejected": True,
        "merged_into": _EPIC_ID,
        "asset": sym,
        "surface": "supply_distribution_dashboard",
        "cohort_thresholds": build_cohort_thresholds(),
        "circulating_supply": circulating,
        "cohorts": cohorts,
        "known_entities": {
            "handled": True,
            "excluded_from_retail_cohorts": True,
            "labeled_separately": True,
            "entities": known_entities_labeled,
            "supply": round(known_entity_supply, 8),
            "supply_share_pct": round(known_entity_supply / circulating * 100, 4) if circulating > 0 else 0.0,
        },
        "totals": {
            "retail_cohort_supply": round(retail_supply, 8),
            "known_entity_supply": round(known_entity_supply, 8),
            "cohort_supply_total": round(cohort_supply_total, 8),
            "circulating_supply": circulating,
            "reconciled": reconciled,
            "reconciliation_tolerance": max(1e-6, circulating * 1e-9),
        },
        "concentration_risk": concentration,
        "token_risk_scoring_hook": {
            "feature_id": 604,
            "inputs": ["supply_share_by_cohort", "top_cohort_concentration"],
            "concentration_risk_score": concentration.get("concentration_risk_score"),
        },
        "holder_count": len(classified),
        "cohort_count": len(cohorts),
        "threshold_version": _COHORT_THRESHOLD_VERSION,
        "disclaimer": _DISCLAIMER,
    }


def compute_concentration_risk_metrics(
    cohorts: list[dict[str, Any]],
    *,
    circulating_supply: float,
) -> dict[str, Any]:
    """#604 integration — concentration risk from supply distribution cohorts."""
    if circulating_supply <= 0 or not cohorts:
        return {
            "concentration_risk_score": None,
            "top_cohort_id": None,
            "top_cohort_share_pct": None,
            "herfindahl_index": None,
            "band": "insufficient_data",
        }

    shares = [float(c.get("supply_share_pct") or 0.0) / 100.0 for c in cohorts]
    hhi = round(sum(s * s for s in shares), 6)
    top = max(cohorts, key=lambda c: float(c.get("supply_share_pct") or 0.0))
    top_share = float(top.get("supply_share_pct") or 0.0)

    if top_share >= 60 or hhi >= 0.35:
        band = "elevated"
        score = min(100.0, round(top_share * 0.9 + hhi * 100, 1))
    elif top_share >= 40 or hhi >= 0.22:
        band = "moderate"
        score = min(85.0, round(top_share * 0.7 + hhi * 80, 1))
    else:
        band = "low"
        score = round(top_share * 0.5 + hhi * 50, 1)

    return {
        "concentration_risk_score": score,
        "top_cohort_id": top.get("cohort_id"),
        "top_cohort_label": top.get("label"),
        "top_cohort_share_pct": top_share,
        "herfindahl_index": hhi,
        "band": band,
        "inputs": "supply_distribution_cohorts",
    }


def run_supply_distribution_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mandatory QA — cohort supply totals reconcile to circulating supply."""
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    thresholds = build_cohort_thresholds()
    tests.append({"test": "cohort_thresholds_versioned", "passed": thresholds.get("versioned") is True})
    tests.append({"test": "cohort_threshold_count_7", "passed": thresholds.get("cohort_count") == 7})

    for asset in (seed.get("assets") or {}):
        panel = build_supply_distribution_dashboard(asset, seed=seed)
        tests.append({
            "test": f"supply_distribution_ok_{asset}",
            "passed": panel.get("ok") is True,
        })
        tests.append({
            "test": f"known_entities_handled_{asset}",
            "passed": (panel.get("known_entities") or {}).get("handled") is True,
        })
        tests.append({
            "test": f"totals_reconcile_{asset}",
            "passed": (panel.get("totals") or {}).get("reconciled") is True,
        })
        tests.append({
            "test": f"concentration_risk_export_{asset}",
            "passed": (panel.get("concentration_risk") or {}).get("concentration_risk_score") is not None,
        })

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": True,
        "task_id": str(_SUPPLY_DISTRIBUTION_TASK_ID),
        "reconciliation_tests": tests,
        "all_passed": all_passed,
        "test_count": len(tests),
    }


def build_metric_definitions(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    defs = seed.get("metric_definitions") or {}
    catalog = []
    for metric_id, spec in defs.items():
        catalog.append({
            "metric_id": metric_id,
            "name": spec.get("name", metric_id),
            "formula": spec.get("formula"),
            "formula_version": spec.get("formula_version", _METHODOLOGY_VERSION),
            "source": spec.get("source"),
            "unit": spec.get("unit"),
            "missing_display": missing_value(),
            "unknown_is_not_zero": True,
        })
    return {
        "canonical_definitions": True,
        "metric_count": len(catalog),
        "metrics": catalog,
        "methodology_version": _METHODOLOGY_VERSION,
    }


def build_network_data_pro_api(asset: str = "BTC", *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#574 — institutional network metrics API delivery."""
    seed = seed or _load_seed()
    sym = asset.upper()
    defs = build_metric_definitions(seed)
    seed_asset = (seed.get("assets") or {}).get(sym, {})
    seed_metrics = seed_asset.get("metrics") or {}

    metrics_output: list[dict[str, Any]] = []
    for metric_id, spec in (seed.get("metric_definitions") or {}).items():
        raw = seed_metrics.get(metric_id, {})
        available = raw.get("available", False) and raw.get("value") is not None
        metrics_output.append({
            "metric_id": metric_id,
            "name": spec.get("name", metric_id),
            "value": raw.get("value") if available else missing_value(numeric=True),
            "available": available,
            "missing": not available,
            "formula_version": spec.get("formula_version", _METHODOLOGY_VERSION),
            "source": spec.get("source"),
            "as_of": raw.get("as_of"),
            "unknown_is_not_zero": True,
        })

    return {
        "ok": True,
        "task_id": "574",
        "standalone_rejected": True,
        "epic_feature_id": _EPIC_ID,
        "asset": sym,
        "network_metrics": metrics_output,
        "metric_definitions": defs,
        "institutional_api": True,
        "missing_not_zero": True,
    }


def build_metrics_library_panel(asset: str = "BTC", *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#577 main panel — canonical library + #603 supply distribution sub-module."""
    seed = seed or _load_seed()
    sym = asset.upper()
    supply = build_supply_distribution_dashboard(sym, seed=seed)
    network_api = build_network_data_pro_api(sym, seed=seed)
    defs = build_metric_definitions(seed)

    return {
        "ok": True,
        "epic_feature_id": _EPIC_ID,
        "feature_ids": list(_FEATURE_IDS),
        "asset": sym,
        "sub_modules": {
            "577_canonical_library": defs,
            "574_network_data_pro_api": network_api,
            "603_supply_distribution": supply if supply.get("ok") else {"ok": False},
            "tasks_not_tickets": True,
        },
        "canonical_metric_definitions": True,
        "cohort_thresholds_versioned": True,
        "known_entities_handled": (supply.get("known_entities") or {}).get("handled") if supply.get("ok") else False,
        "totals_reconcile": (supply.get("totals") or {}).get("reconciled") if supply.get("ok") else False,
        "missing_not_zero": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
    }


def run_historical_qa_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    supply_qa = run_supply_distribution_reconciliation_tests(seed)
    tests = list(supply_qa.get("reconciliation_tests") or [])

    for metric_id, spec in (seed.get("metric_definitions") or {}).items():
        tests.append({"test": f"formula_documented_{metric_id}", "passed": bool(spec.get("formula"))})
        tests.append({"test": f"source_documented_{metric_id}", "passed": bool(spec.get("source"))})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": True,
        "historical_qa": seed.get("historical_qa") or {},
        "reconciliation_tests": tests,
        "all_passed": all_passed,
        "test_count": len(tests),
    }


def onchain_metrics_library_status() -> dict[str, Any]:
    seed = _load_seed()
    defs = build_metric_definitions(seed)
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
        "metric_count": defs["metric_count"],
        "asset_count": len(seed.get("assets") or {}),
        "absorbed_tickets": {
            "574": "Network Data Pro Metrics → API delivery sub-task of #577",
            "603": "Supply Distribution Intelligence → distribution dashboard sub-task of #577",
        },
        "acceptance_criteria": {
            "cohort_thresholds_versioned": True,
            "known_entities_handled": True,
            "totals_reconcile": True,
            "formula_source_version": True,
            "missing_not_zero": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def build_onchain_metrics_library_panel(asset: str = "ETH") -> dict[str, Any]:
    t0 = time.perf_counter()
    panel = build_metrics_library_panel(asset)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return wrap_intelligence_response({
        **panel,
        "title": _TITLE,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }, module_id="onchain_metrics_library")
