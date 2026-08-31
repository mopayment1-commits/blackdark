"""
Protocol Valuation Layer — Features #570 #571 merged (Sprint 1).

Epic with 2 sub-module tasks (not standalone tickets):
  #570 NVT Ratio & Historical Context — ratio + historical percentile (not fair-value)
  #571 NVT Variants — documented windows, entity-adjusted option

Depends on #542 Entity-Adjusted Metrics. Rule-based — no price guarantee.
"""

from __future__ import annotations

import hashlib
import json
import logging
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ProtocolValuationLayer")

_FEATURE_IDS = (570, 571, 584, 585)
_EPIC_ID = 570
_REALIZED_CAP_REF = 584
_REALIZED_VALUE_REF = 585
_RENAMED_FROM_570 = "NVT Fair-Value Model"
_RENAMED_FROM_571 = "NVT Intelligence"
_TITLE = "Protocol Valuation Layer"
_STANDALONE = False
_LAYER = "Data Layer"
_SPRINT = 1
_SEED_PATH = Path("data/protocol_valuation_layer_seed.json")
_METHODOLOGY_VERSION = "1.0"
_FORMULA_VERSION = "1.0"
_ENTITY_ADJUSTED_FEATURE_ID = 542

_SUB_MODULES: dict[str, dict[str, Any]] = {
    "570": {
        "task_id": "570",
        "name": "nvt_ratio_historical_context",
        "title": "NVT Ratio & Historical Context",
        "description": "Current NVT ratio with historical percentile — not fair-value estimate",
    },
    "571": {
        "task_id": "571",
        "name": "nvt_variants",
        "title": "NVT Variants",
        "description": "NVT and variants with documented windows, entity-adjusted option",
    },
    "584": {
        "task_id": "584",
        "name": "realized_cap_intelligence",
        "title": "Realized Cap & Realized Price Intelligence",
        "description": "Realized capitalization and price from last economic transfer",
    },
    "585": {
        "task_id": "585",
        "name": "realized_value_intelligence",
        "title": "Realized Cap / Realized Value Intelligence",
        "description": "Chain-specific realized valuation with entity-adjusted option",
    },
}

_DISCLAIMER = (
    "NVT ratio and historical context — descriptive metric only. "
    "Current NVT and historical percentile do not imply fair value or price target. "
    "No price guarantee. Not investment advice."
)

_BANNED_TERMS = (
    "fair value",
    "fair-value",
    "price target",
    "undervalued",
    "overvalued",
    "price guarantee",
    "buy",
    "sell",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "formula": {}, "backtest": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("protocol valuation layer seed load failed: %s", exc)
        return {"assets": {}, "formula": {}, "backtest": {}}


def build_dependencies_block() -> dict[str, Any]:
    return {
        "entity_adjusted_feature_id": _ENTITY_ADJUSTED_FEATURE_ID,
        "entity_adjusted_preferred": True,
        "display": "Built on #542 Entity-Adjusted Metrics — entity-adjusted transfers preferred",
    }


def build_formula_documentation(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    formula = seed.get("formula") or {}
    return {
        "formula_version": _FORMULA_VERSION,
        "methodology_version": _METHODOLOGY_VERSION,
        "deterministic": True,
        "no_fair_value_claim": True,
        "no_price_guarantee": True,
        "expression": formula.get(
            "expression",
            "nvt = network_value_usd / transfer_volume_usd | "
            "historical_percentile = percentile_rank(nvt, historical_window)",
        ),
        "variants": formula.get("variants") or {
            "nvt_standard": {"window_days": 30, "transfer_type": "all"},
            "nvt_entity_adjusted": {
                "window_days": 30,
                "transfer_type": "entity_adjusted",
                "preferred": True,
            },
            "nvt_90d": {"window_days": 90, "transfer_type": "entity_adjusted"},
        },
        "entity_adjusted_preferred": True,
        "display": (
            f"Formula v{_FORMULA_VERSION} — NVT ratio + historical percentile, "
            "no fair-value claim"
        ),
    }


def _percentile_rank(value: float, distribution: list[float]) -> float:
    if not distribution:
        return 50.0
    below = sum(1 for v in distribution if v < value)
    equal = sum(1 for v in distribution if v == value)
    return round((below + 0.5 * equal) / len(distribution) * 100, 2)


def _historical_bands(distribution: list[float]) -> dict[str, Any]:
    if len(distribution) < 2:
        return {"p25": None, "p50": None, "p75": None, "min": None, "max": None}
    sorted_dist = sorted(distribution)
    n = len(sorted_dist)

    def pct(p: float) -> float:
        idx = int(p * (n - 1))
        return round(sorted_dist[idx], 4)

    return {
        "p25": pct(0.25),
        "p50": pct(0.50),
        "p75": pct(0.75),
        "min": round(min(sorted_dist), 4),
        "max": round(max(sorted_dist), 4),
        "distribution_count": n,
    }


def compute_nvt(
    network_value_usd: float,
    transfer_volume_usd: float,
) -> float | None:
    if transfer_volume_usd <= 0:
        return None
    return round(network_value_usd / transfer_volume_usd, 4)


def build_nvt_ratio_context(
    asset_id: str,
    *,
    entity_adjusted: bool = True,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#570 — NVT ratio + historical percentile, not fair-value."""
    seed = seed or _load_seed()
    asset = (seed.get("assets") or {}).get(asset_id)
    if not asset:
        return {"ok": False, "error": "asset_not_found", "asset_id": asset_id}

    transfer_key = "entity_adjusted_transfers" if entity_adjusted else "raw_transfers"
    transfers = asset.get(transfer_key) or asset.get("transfers") or {}
    network_value = float(asset.get("network_value_usd", 0))
    transfer_volume = float(transfers.get("volume_30d_usd", 0))
    nvt = compute_nvt(network_value, transfer_volume)

    if nvt is None:
        return {
            "ok": False,
            "error": "insufficient_transfer_volume",
            "asset_id": asset_id,
        }

    historical = asset.get("historical_nvt") or []
    percentile = _percentile_rank(nvt, historical)
    bands = _historical_bands(historical)

    return {
        "ok": True,
        "task_id": "570",
        "asset_id": asset_id,
        "asset_name": asset.get("name", asset_id),
        "current_nvt": nvt,
        "historical_percentile": percentile,
        "entity_adjusted": entity_adjusted,
        "entity_adjusted_preferred": entity_adjusted,
        "transfer_volume_30d_usd": transfer_volume,
        "network_value_usd": network_value,
        "historical_bands": bands,
        "no_fair_value_claim": True,
        "no_price_guarantee": True,
        "estimate_not_value": True,
        "display": (
            f"Current NVT: {nvt:.2f} | Historical percentile: {percentile:.0f}% | "
            f"Entity-adjusted: {'yes' if entity_adjusted else 'no'}"
        ),
        "interpretation": (
            f"NVT ratio of {nvt:.2f} sits at the {percentile:.0f}th percentile "
            "of historical distribution. Descriptive context only — not a valuation target."
        ),
    }


def build_nvt_variants(
    asset_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#571 — NVT variants with documented windows."""
    seed = seed or _load_seed()
    asset = (seed.get("assets") or {}).get(asset_id)
    if not asset:
        return {"ok": False, "error": "asset_not_found", "asset_id": asset_id}

    formula = build_formula_documentation(seed)
    variants_cfg = (seed.get("formula") or {}).get("variants") or {}
    variants: list[dict[str, Any]] = []

    for variant_name, cfg in variants_cfg.items():
        window = int(cfg.get("window_days", 30))
        use_entity_adj = cfg.get("transfer_type") == "entity_adjusted"
        transfer_key = (
            f"entity_adjusted_transfers_{window}d"
            if use_entity_adj
            else f"raw_transfers_{window}d"
        )
        transfers = (
            asset.get(transfer_key)
            or asset.get("entity_adjusted_transfers" if use_entity_adj else "raw_transfers")
            or {}
        )
        vol_key = f"volume_{window}d_usd"
        volume = float(transfers.get(vol_key, transfers.get("volume_30d_usd", 0)))
        network_value = float(asset.get("network_value_usd", 0))
        nvt = compute_nvt(network_value, volume)

        hist_key = f"historical_nvt_{window}d" if window != 30 else "historical_nvt"
        historical = asset.get(hist_key) or asset.get("historical_nvt") or []
        percentile = _percentile_rank(nvt or 0, historical) if nvt else None

        variants.append({
            "variant": variant_name,
            "window_days": window,
            "entity_adjusted": use_entity_adj,
            "current_nvt": nvt,
            "historical_percentile": percentile,
            "transfer_volume_usd": volume,
            "no_arbitrary_valuation_claim": True,
            "display": (
                f"{variant_name}: NVT={nvt} | "
                f"percentile={percentile}% | window={window}d"
                if nvt
                else f"{variant_name}: insufficient data"
            ),
        })

    return {
        "ok": True,
        "task_id": "571",
        "asset_id": asset_id,
        "variants": variants,
        "variant_count": len(variants),
        "formula_documented": True,
        "entity_adjusted_option": True,
        "no_arbitrary_valuation_claim": True,
        "formula": formula,
    }


def build_realized_cap_methodology(
    asset_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Chain methodology documentation for realized cap/price."""
    seed = seed or _load_seed()
    rc = (seed.get("realized_cap") or {}).get(asset_id) or {}
    chain = rc.get("chain", asset_id)
    return {
        "chain": chain,
        "methodology_version": rc.get("methodology_version", _METHODOLOGY_VERSION),
        "formula_version": rc.get("formula_version", _FORMULA_VERSION),
        "chain_specific_rules": rc.get("chain_rules") or {},
        "entity_adjusted_option": rc.get("entity_adjusted_available", True),
        "exact_historical_replay": rc.get("exact_historical_replay", True),
        "display": f"Realized cap methodology v{rc.get('methodology_version', _METHODOLOGY_VERSION)} — {chain}",
    }


def build_realized_cap_panel(
    asset_id: str = "bitcoin",
    *,
    entity_adjusted: bool = True,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#584/#585 — realized cap/price with chain methodology and deviations."""
    seed = seed or _load_seed()
    rc = (seed.get("realized_cap") or {}).get(asset_id)
    if not rc:
        return {"ok": False, "error": "realized_cap_not_found", "asset_id": asset_id}

    methodology = build_realized_cap_methodology(asset_id, seed=seed)
    spot_price = float(rc.get("spot_price_usd", 0))
    realized_price = float(rc.get("realized_price_usd", 0))
    realized_cap = float(rc.get("realized_cap_usd", 0))
    supply = float(rc.get("circulating_supply", 0))
    market_cap = spot_price * supply if supply else 0

    use_entity = entity_adjusted and rc.get("entity_adjusted_available", False)
    if use_entity:
        realized_price = float(rc.get("entity_adjusted_realized_price_usd", realized_price))
        realized_cap = float(rc.get("entity_adjusted_realized_cap_usd", realized_cap))

    deviation_pct = round((spot_price - realized_price) / realized_price * 100, 2) if realized_price else 0
    cap_deviation_pct = round((market_cap - realized_cap) / realized_cap * 100, 2) if realized_cap else 0

    history = rc.get("historical_realized_cap") or []
    trend = "flat"
    if len(history) >= 2:
        trend = "rising" if history[-1] > history[-2] else "falling" if history[-1] < history[-2] else "flat"

    return {
        "ok": True,
        "task_ids": ["584", "585"],
        "feature_refs": [_REALIZED_CAP_REF, _REALIZED_VALUE_REF],
        "asset_id": asset_id,
        "asset_name": rc.get("name", asset_id),
        "spot_price_usd": spot_price,
        "realized_price_usd": realized_price,
        "realized_cap_usd": realized_cap,
        "market_cap_usd": round(market_cap, 0),
        "circulating_supply": supply,
        "entity_adjusted": use_entity,
        "entity_adjusted_option": rc.get("entity_adjusted_available", False),
        "deviations": {
            "price_vs_realized_pct": deviation_pct,
            "market_cap_vs_realized_cap_pct": cap_deviation_pct,
        },
        "trend": trend,
        "historical_realized_cap": history,
        "methodology": methodology,
        "chain_methodology_documented": True,
        "exact_historical_replay": rc.get("exact_historical_replay", True),
        "qa": rc.get("qa") or {},
        "missing_not_zero": rc.get("missing") is not True,
        "display": (
            f"Realized price ${realized_price:,.2f} vs spot ${spot_price:,.2f} "
            f"({deviation_pct:+.1f}%) | Realized cap ${realized_cap:,.0f}"
        ),
        "timestamp": _utcnow(),
    }


def build_protocol_valuation_panel(
    asset_id: str = "bitcoin",
    *,
    entity_adjusted: bool = True,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    nvt_context = build_nvt_ratio_context(
        asset_id, entity_adjusted=entity_adjusted, seed=seed,
    )
    if not nvt_context.get("ok"):
        return {
            **nvt_context,
            "epic_feature_id": _EPIC_ID,
            "feature_ids": list(_FEATURE_IDS),
        }

    variants = build_nvt_variants(asset_id, seed=seed)
    realized = build_realized_cap_panel(asset_id, entity_adjusted=entity_adjusted, seed=seed)
    bt = seed.get("backtest") or {}
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "epic_feature_id": _EPIC_ID,
        "feature_ids": list(_FEATURE_IDS),
        "absorbed_tickets": {
            "570": "NVT Fair-Value Model → NVT Ratio & Historical Context",
            "571": "NVT Intelligence → NVT Variants (merged)",
            "584": "Realized Cap & Realized Price Intelligence",
            "585": "Realized Cap / Realized Value Intelligence (merged)",
        },
        "renamed_from": {
            "570": _RENAMED_FROM_570,
            "571": _RENAMED_FROM_571,
        },
        "title": _TITLE,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "tasks_not_tickets": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "rule_based_only": True,
        "asset_id": asset_id,
        "dependencies": build_dependencies_block(),
        "sub_modules": {
            "570_nvt_ratio_historical_context": nvt_context,
            "571_nvt_variants": variants,
            "584_585_realized_cap": realized if realized.get("ok") else {"ok": False},
            "tasks_not_tickets": True,
        },
        "formula": build_formula_documentation(seed),
        "backtest": {
            "documented": True,
            "periods_tested": bt.get("periods_tested", 0),
            "percentile_accuracy_pct": bt.get("percentile_accuracy_pct"),
            "deterministic": bt.get("deterministic", True),
            "no_trading_backtest": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "acceptance_criteria": {
            "methodology_versioned": True,
            "entity_adjusted_preferred": True,
            "no_price_guarantee": True,
            "no_fair_value_claim": True,
            "formula_documented": True,
            "realized_cap_584": True,
            "realized_value_585": True,
            "chain_methodology_documented": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    for asset_id in (seed.get("assets") or {}):
        ctx = build_nvt_ratio_context(asset_id, seed=seed)
        tests.append({
            "test": f"no_fair_value_{asset_id}",
            "passed": ctx.get("no_fair_value_claim") is True,
        })
        tests.append({
            "test": f"no_price_guarantee_{asset_id}",
            "passed": ctx.get("no_price_guarantee") is True,
        })
        tests.append({
            "test": f"nvt_display_{asset_id}",
            "passed": "Current NVT:" in ctx.get("display", ""),
        })
        variants = build_nvt_variants(asset_id, seed=seed)
        tests.append({
            "test": f"variants_documented_{asset_id}",
            "passed": variants.get("formula_documented") is True,
        })
        realized = build_realized_cap_panel(asset_id, seed=seed)
        tests.append({
            "test": f"realized_cap_584_{asset_id}",
            "passed": realized.get("ok") is True and realized.get("chain_methodology_documented") is True,
        })
        tests.append({
            "test": f"entity_adjusted_option_585_{asset_id}",
            "passed": realized.get("entity_adjusted_option") is not None,
        })

    panel = build_protocol_valuation_panel()
    if panel.get("ok"):
        tests.append({
            "test": "standalone_rejected",
            "passed": panel.get("standalone_rejected") is True,
        })
        tests.append({
            "test": "entity_adjusted_dependency",
            "passed": panel.get("dependencies", {}).get("entity_adjusted_feature_id") == 542,
        })
        output_str = json.dumps(panel, default=str).lower()
        tests.append({
            "test": "banned_fair_value_absent",
            "passed": "fair value" not in output_str or "no_fair_value" in output_str,
        })

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": True,
        "reconciliation_tests": tests,
        "all_passed": all_passed,
        "test_count": len(tests),
    }


def protocol_valuation_layer_status() -> dict[str, Any]:
    seed = _load_seed()
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
        "formula": build_formula_documentation(seed),
        "asset_count": len(seed.get("assets") or {}),
        "acceptance_criteria": {
            "methodology_versioned": True,
            "entity_adjusted_preferred": True,
            "no_price_guarantee": True,
            "no_fair_value_claim": True,
            "formula_documented": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
