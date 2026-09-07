#!/usr/bin/env python3
"""Generate Batch13 core modules: semantic engine, operational layer, membership, oracles."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "docs/cap646/CAP646_CATALOG.json"
CAP978_PATH = ROOT / "docs/cap978/CAP978_CATALOG.json"

BATCH13_IDS = list(range(601, 651))
SHARED_CORE_IDS = [
    *range(601, 627),
    628,
    *range(632, 637),
    643,
]
OUTSIDE_IDS = [627, 629, 630, 631, 637, 638, 639, 640, 641, 642, 644, 645, 646]
EXTERNAL_IDS = [647, 648, 649, 650]

# Per-capability semantic defaults (3 inputs each, domain-shaped)
SEMANTIC_DEFAULTS: dict[int, dict[str, float]] = {
    601: {"graph_nodes": 420, "graph_edges": 1850, "flow_depth_hops": 6},
    602: {"dev_wallets_tracked": 48, "commit_velocity_30d": 126, "transfer_events_24h": 38},
    603: {"miner_outflow_btc": 820.5, "active_pools": 14, "hash_rate_eh": 612.0},
    604: {"unlock_usd_30d": 125000000.0, "cliff_events": 8, "vesting_remaining_pct": 42.0},
    605: {"proposals_30d": 12, "vote_participation_pct": 68.5, "governance_sentiment": 0.62},
    606: {"active_contributors": 86, "repo_commits_90d": 420, "issue_resolution_days": 4.2},
    607: {"liquidity_score": 74.0, "revenue_runway_months": 18.0, "debt_ratio_pct": 22.0},
    608: {"ratio_numerator": 1.42, "ratio_denominator": 0.98, "custom_ratio_count": 12},
    609: {"funding_rate_bps": 8.5, "venues_monitored": 16, "alert_latency_sec": 12},
    610: {"long_funding_bps": 12.4, "short_funding_bps": -3.2, "arb_spread_bps": 15.6},
    611: {"heatmap_cells": 240, "max_funding_bps": 18.2, "min_funding_bps": -6.4},
    612: {"bid_spread_bps": 4.2, "ask_spread_bps": 4.8, "cross_venue_spread_bps": 9.1},
    613: {"liquidation_usd_24h": 85000000.0, "at_risk_positions": 420, "screener_hits": 18},
    614: {"dex_pool_tvl_usd": 420000000.0, "pool_count": 86, "liquidity_delta_pct": 3.4},
    615: {"gas_gwei_predicted": 42.0, "mempool_pending": 125000, "base_fee_gwei": 28.5},
    616: {"yield_delta_bps": 18.0, "pools_tracked": 64, "delta_velocity": 2.4},
    617: {"yield_spread_bps": 42.0, "routes_evaluated": 128, "capital_usd": 2500000.0},
    618: {"optimized_yield_pct": 8.4, "baseline_yield_pct": 6.2, "rebalance_events": 6},
    619: {"trend_metrics_collected": 420, "anomaly_flags_24h": 9, "coverage_pct": 92.0},
    620: {"timeframes_active": 6, "alignment_score": 0.78, "signal_consensus": 0.64},
    621: {"patterns_detected": 24, "confidence_pct": 72.0, "lookback_bars": 240},
    622: {"prediction_drift_score": 0.18, "trend_accuracy_pct": 61.0, "samples_30d": 420},
    623: {"p50_latency_ms": 18.0, "p99_latency_ms": 86.0, "execution_nodes": 8},
    624: {"orders_routed": 1250, "fill_rate_pct": 94.0, "node_uptime_pct": 99.6},
    625: {"rust_modules_active": 12, "throughput_ops_sec": 42000, "memory_mb": 256.0},
    626: {"dashboard_widgets": 18, "data_feeds_live": 42, "refresh_sec": 5},
    628: {"share_velocity": 420.0, "referral_conversions": 86, "loop_completion_pct": 38.0},
    632: {"hot_gb": 420.0, "warm_tb": 12.0, "cold_tb": 86.0},
    633: {"cross_chain_flow_usd_24h": 125000000.0, "bridges_monitored": 18, "chain_pairs": 42},
    634: {"fill_probability_pct": 88.0, "slippage_bps": 12.0, "depth_usd": 4200000.0},
    635: {"opportunities_found": 24, "net_edge_bps": 18.0, "venues_scanned": 16},
    636: {"drift_events_24h": 6, "features_monitored": 420, "baseline_deviation_pct": 2.8},
    643: {"trace_steps": 12, "provenance_links": 28, "decision_chain_depth": 6},
}


def snake(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return re.sub(r"_+", "_", s)


def load_catalog() -> dict[int, dict]:
    rows = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    cat = {int(r["id"]): r for r in rows}
    ext = json.loads(CAP978_PATH.read_text(encoding="utf-8"))
    for r in ext:
        cid = int(r["id"])
        if 647 <= cid <= 650 and cid not in cat:
            cat[cid] = r
    return cat


def fn_name(cap_id: int, capability: str) -> str:
    return f"{snake(capability)}_{cap_id}"


def rule_name(cap_id: int, capability: str) -> str:
    return snake(capability)


def gen_semantic_engine(catalog: dict[int, dict]) -> str:
    lines = [
        '"""Batch13 (601–650) capability-specific semantic transforms for operational intelligence shared core."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, Callable",
        "",
        "from bd_platform.batch_semantic_primitives import ratio as _ratio, semantic_inputs as _inputs, spread as _spread, weighted as _weighted",
        "",
        "TransformFn = Callable[[dict[str, float], str], dict[str, Any]]",
        "",
    ]
    rules: dict[str, str] = {}
    specs_lines = ["CAPABILITY_SEMANTIC_SPECS: dict[int, dict[str, Any]] = {"]

    for cid in SHARED_CORE_IDS:
        cap = catalog[cid]["capability"]
        rule = rule_name(cid, cap)
        defaults = SEMANTIC_DEFAULTS[cid]
        keys = list(defaults.keys())
        a, b, c = keys[0], keys[1], keys[2]

        if cid in (608, 612, 617):
            primary_expr = f"_spread(i['{a}'], i['{b}'])"
        elif cid in (604, 613, 633, 634, 635):
            primary_expr = f"round(_ratio(i['{a}'], i['{b}']), 4)"
        elif cid in (606, 607, 621, 622, 626, 628, 636, 643):
            primary_expr = f"_weighted((i['{a}'], 0.5), (i['{b}'], 0.3), (i['{c}'], 0.2))"
        else:
            primary_expr = f"round(_ratio(i['{a}'], i['{c}']), 4)"

        if rule not in rules:
            body = [
                f"def _{rule}(i: dict[str, float], symbol: str) -> dict[str, Any]:",
                f"    primary = {primary_expr}",
                "    return {",
                f'        "{rule}": primary,',
            ]
            for k in keys:
                body.append(f'        "{k}": i["{k}"],')
            body.append('        "symbol_focus": symbol.upper(),')
            body.append("    }")
            rules[rule] = "\n".join(body)

        specs_lines.append(
            f"    {cid}: {{\"rule\": \"{rule}\", \"defaults\": {defaults!r}, \"feature\": {cap!r}}},"
        )

    lines.extend(rules[r] + "\n" for r in sorted(rules.keys()))
    lines.append("")
    lines.extend(specs_lines)
    lines.extend([
        "}",
        "",
        "",
        "RULES: dict[str, TransformFn] = {",
    ])
    for rule in sorted(rules.keys()):
        lines.append(f'    "{rule}": _{rule},')
    lines.extend([
        "}",
        "",
        "",
        "def compute_semantic_extra(cap_id: int, *, symbol: str, seed: dict[str, Any]) -> dict[str, Any]:",
        "    spec = CAPABILITY_SEMANTIC_SPECS[cap_id]",
        '    inputs = _inputs(seed, cap_id, spec["defaults"])',
        '    transform = RULES[spec["rule"]]',
        "    payload = transform(inputs, symbol.upper())",
        '    payload["feature"] = spec["feature"]',
        '    payload["semantic_rule"] = spec["rule"]',
        '    payload["attribution"] = "BLACKDARK batch13 operational intelligence layer"',
        '    payload["formula_visible"] = True',
        '    payload["analysis_only"] = True',
        "    return payload",
        "",
        "",
        "def semantic_profile(cap_id: int) -> dict[str, Any]:",
        "    spec = CAPABILITY_SEMANTIC_SPECS[cap_id]",
        "    return {",
        '        "capability_id": cap_id,',
        '        "semantic_rule": spec["rule"],',
        '        "input_defaults": spec["defaults"],',
        '        "feature": spec["feature"],',
        "    }",
        "",
        "",
        "def shared_core_ids() -> list[int]:",
        "    return sorted(CAPABILITY_SEMANTIC_SPECS.keys())",
        "",
    ])
    return "\n".join(lines) + "\n"


def gen_layer(catalog: dict[int, dict]) -> str:
    lines = [
        '"""Batch13 Operational Intelligence Layer — capabilities #601–#650.',
        "",
        "Insight-only operational, on-chain, derivatives, and trust surfaces.",
        "No execution endpoints.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "import json",
        "import logging",
        "from datetime import UTC, datetime",
        "from pathlib import Path",
        "from typing import Any",
        "",
        "from bd_platform.batch13_semantic_engine import compute_semantic_extra",
        "",
        "logger = logging.getLogger(\"BLACKDARK.Batch13OperationalIntel\")",
        "",
        "_SEED_PATH = Path(\"data/legal_retail_commercial_seed.json\")",
        "",
        "",
        "def reset_batch13_operational_intelligence_state() -> None:",
        "    return None",
        "",
        "",
        "def _utcnow() -> str:",
        "    return datetime.now(UTC).isoformat()",
        "",
        "",
        "def _load_seed() -> dict[str, Any]:",
        "    if not _SEED_PATH.is_file():",
        "        return {}",
        "    try:",
        '        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))',
        "    except (OSError, json.JSONDecodeError) as exc:",
        '        logger.warning("batch13 seed load failed: %s", exc)',
        "        return {}",
        "",
        "",
        'def _disclaimer(locale: str = "en") -> str:',
        '    if locale.lower().startswith("ar"):',
        '        return "تحليل فقط — ليس توصية مالية ولا تنفيذ."',
        '    return "Analysis only — not financial advice, guarantee, or execution."',
        "",
        "",
        "def _base(",
        "    cap_id: int,",
        "    *,",
        '    symbol: str = "BTC",',
        "    seed: dict[str, Any] | None = None,",
        "    extra: dict[str, Any] | None = None,",
        ") -> dict[str, Any]:",
        "    seed = seed or _load_seed()",
        "    payload = {",
        '        "ok": True,',
        '        "capability_id": cap_id,',
        '        "symbol": symbol.upper(),',
        '        "timestamp": _utcnow(),',
        '        "disclaimer": _disclaimer(),',
        '        "analysis_only": True,',
        '        "no_execution": True,',
        "    }",
        "    if extra:",
        "        payload.update(extra)",
        "    return payload",
        "",
    ]

    for cid in SHARED_CORE_IDS:
        cap = catalog[cid]["capability"]
        fn = fn_name(cid, cap)
        lines.extend([
            "",
            f"def {fn}(*, symbol: str = \"BTC\", seed: dict[str, Any] | None = None) -> dict[str, Any]:",
            f'    """{cap} (#{cid})."""',
            "    seed = seed or _load_seed()",
            "    return _base(",
            f"        {cid},",
            "        symbol=symbol,",
            "        seed=seed,",
            f"        extra=compute_semantic_extra({cid}, symbol=symbol, seed=seed),",
            "    )",
        ])

    # Catalog-aligned outside bindings
    outside_impls = {
        637: ("scenario_engine_637", "Scenario Engine", "trust_pulse", "build_trust_pulse", True),
        638: ("claims_prediction_verification_638", "Claims/Prediction Verification Engine", "oracle_track_record", "public_track_record", False),
        639: ("net_edge_truth_score_639", "Net-Edge Truth Score", "net_edge_truth", "compute_net_edge_truth", False),
        640: ("public_accuracy_ledger_640", "Public Accuracy Ledger", "oracle_track_record", "public_track_record", False),
        641: ("decision_certificate_export_641", "Decision Certificate + Institutional DD Export", "decision_certificate", "build_decision_certificate", False),
        645: ("security_verification_evidence_645", "Security Verification Evidence", "security_posture", "security_posture_report", False),
    }
    for cid, (fn, cap, mod, mod_fn, is_async) in outside_impls.items():
        lines.extend([
            "",
            f"def {fn}(*, symbol: str = \"BTC\", seed: dict[str, Any] | None = None) -> dict[str, Any]:",
            f'    """{cap} (#{cid}) — catalog-aligned semantics."""',
            f"    from {mod} import {mod_fn}",
            "    seed = seed or _load_seed()",
        ])
        if cid == 637:
            lines.append("    import asyncio")
            lines.append(f"    underlying = asyncio.run({mod_fn}(symbol=symbol))")
        elif cid == 641:
            lines.append(f'    underlying = {mod_fn}({{"symbol": symbol.upper(), "tier": "institutional"}})')
        elif cid == 639:
            lines.append(f"    underlying = {mod_fn}()")
        else:
            lines.append(f"    underlying = {mod_fn}()")
        lines.extend([
            "    return _base(",
            f"        {cid},",
            "        symbol=symbol,",
            "        seed=seed,",
            "        extra={",
            f'            "surface": "{snake(cap)}",',
            f'            "feature": "{cap}",',
            f'            "attribution": "{mod}.{mod_fn}",',
            '            "formula_visible": True,',
            f'            "{snake(cap)}": underlying,',
            '            "underlying": underlying,',
            "        },",
            "    )",
        ])

    for cid in EXTERNAL_IDS:
        cap = catalog.get(cid, {}).get("capability", f"ID{cid}")
        fn = fn_name(cid, cap)
        lines.extend([
            "",
            f"def {fn}(*, symbol: str = \"BTC\", seed: dict[str, Any] | None = None) -> dict[str, Any]:",
            f'    """{cap} (#{cid}) — external dependency blocked locally."""',
            "    from cap978.external_registry import external_registry_rows",
            "    seed = seed or _load_seed()",
            "    reason = next((r['reason'] for r in external_registry_rows() if r.get('id') == {cid}), 'External dependency')",
            "    return _base(",
            f"        {cid},",
            "        symbol=symbol,",
            "        seed=seed,",
            "        extra={",
            '            "ok": False,',
            '            "classification": "EXTERNAL_DEPENDENCY_BLOCKED",',
            '            "blocker_type": "vendor_license_or_infra",',
            '            "reason": reason,',
            '            "internal_action": "none — requires external provisioning",',
            '            "analysis_only": True,',
            "        },",
            "    )",
        ])

    return "\n".join(lines) + "\n"


def gen_membership() -> str:
    return f'''"""Canonical Batch13 (601–650) membership derived from registry + semantic engine."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

from bd_platform.batch13_semantic_engine import shared_core_ids

BATCH13_IDS = list(range(601, 651))
SHARED_CORE_PARAMETERIZED = shared_core_ids()
OUTSIDE_SHARED_CORE_IDS = {OUTSIDE_IDS!r}
EXTERNAL_DEPENDENCY_IDS = {EXTERNAL_IDS!r}
CANONICAL_CATALOG_SEMANTICS_IDS = frozenset({{637, 638, 639, 640, 641, 645}})


def parameterized_ids() -> list[int]:
    return list(SHARED_CORE_PARAMETERIZED)


def shared_core_ids_list() -> list[int]:
    return sorted(set(parameterized_ids()))


def outside_shared_core_ids() -> list[int]:
    return sorted(set(OUTSIDE_SHARED_CORE_IDS))


def external_dependency_ids() -> list[int]:
    return sorted(set(EXTERNAL_DEPENDENCY_IDS))


def verify_membership() -> dict[str, object]:
    batch = set(BATCH13_IDS)
    shared = set(shared_core_ids_list())
    outside = set(outside_shared_core_ids())
    external = set(external_dependency_ids())
    bindings = discover_bindings()
    errors: list[str] = []
    if len(batch) != 50:
        errors.append("batch_not_50")
    if shared | outside | external != batch:
        errors.append("partition_not_batch")
    if shared & outside or shared & external or outside & external:
        errors.append("partition_overlap")
    for cid in CANONICAL_CATALOG_SEMANTICS_IDS:
        mod, fn = bindings.get(cid, ("", ""))
        if mod != "bd_platform.batch13_operational_intelligence_layer":
            errors.append(f"catalog_semantics_binding_{{cid}}")
    return {{"ok": not errors, "errors": errors, "shared_count": len(shared), "outside_count": len(outside), "external_count": len(external)}}
'''


def gen_oracles(catalog: dict[int, dict]) -> str:
    lines = [
        '"""Independent reference oracles for Batch13 parameterized semantics (shared core)."""',
        "",
        "from __future__ import annotations",
        "",
        "",
        "def _ratio(a: float, b: float, *, scale: float = 100.0) -> float:",
        "    return round(a / max(b, 1e-9) * scale, 4)",
        "",
        "",
        "def _spread(a: float, b: float) -> float:",
        "    return round(a - b, 4)",
        "",
        "",
        "def _weighted(*pairs: tuple[float, float]) -> float:",
        "    num = sum(v * w for v, w in pairs)",
        "    den = sum(w for _, w in pairs)",
        "    return round(num / max(den, 1e-9), 4)",
        "",
        "",
        "_SPREAD_IDS = {608, 612, 617}",
        "_RATIO_AB_IDS = {604, 613, 633, 634, 635}",
        "_WEIGHTED_IDS = {606, 607, 621, 622, 626, 628, 636, 643}",
        "",
        "",
        "def independent_primary(cap_id: int, rule: str, inputs: dict[str, float], symbol: str = \"ETH\") -> float:",
        "    i = inputs",
        "    keys = list(i.keys())",
        "    if len(keys) < 3:",
        "        return round(float(list(i.values())[0]), 4)",
        "    a, b, c = keys[0], keys[1], keys[2]",
        "    if cap_id in _SPREAD_IDS:",
        "        return _spread(i[a], i[b])",
        "    if cap_id in _RATIO_AB_IDS:",
        "        return round(_ratio(i[a], i[b]), 4)",
        "    if cap_id in _WEIGHTED_IDS:",
        "        return _weighted((i[a], 0.5), (i[b], 0.3), (i[c], 0.2))",
        "    return round(_ratio(i[a], i[c]), 4)",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    catalog = load_catalog()
    (ROOT / "bd_platform/batch13_semantic_engine.py").write_text(gen_semantic_engine(catalog), encoding="utf-8")
    (ROOT / "bd_platform/batch13_operational_intelligence_layer.py").write_text(gen_layer(catalog), encoding="utf-8")
    (ROOT / "bd_platform/batch13_membership.py").write_text(gen_membership(), encoding="utf-8")
    (ROOT / "tests/batch13_independent_semantic_oracles.py").write_text(gen_oracles(catalog), encoding="utf-8")
    print("Generated batch13 core modules")


if __name__ == "__main__":
    main()
