#!/usr/bin/env python3
"""Generate Batch14 core modules: semantic engine, extension analytics layer, membership."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAP978_PATH = ROOT / "docs/cap978/CAP978_CATALOG.json"

BATCH14_IDS = list(range(651, 701))
CANONICAL_DUPLICATE_TARGETS = {660: 354, 661: 394}
SHARED_CORE_IDS = [i for i in BATCH14_IDS if i not in CANONICAL_DUPLICATE_TARGETS]
OUTSIDE_IDS = [656, 657, 658, 659, 676, 682, 692, 695, 696]
# Remove outside from shared if listed
SHARED_CORE_IDS = [i for i in SHARED_CORE_IDS if i not in OUTSIDE_IDS]

# Domain-shaped defaults (3 numeric inputs each)
def _defaults_for(cap_id: int, capability: str) -> dict[str, float]:
    blob = capability.lower()
    if "mcp" in blob or "agent" in blob or "prompt" in blob or "dashboard" in blob:
        return {"agent_sessions": 42.0, "tool_calls": 128.0, "latency_ms": 240.0}
    if "lineage" in blob or "governance" in blob or "performance" in blob:
        return {"nodes_traced": 86.0, "edges_verified": 420.0, "query_cost_units": 12.5}
    if "tvl" in blob or "chain" in blob:
        return {"tvl_usd_b": 42.0, "protocols_count": 128.0, "change_7d_pct": 3.2}
    if "volume" in blob or "dex" in blob or "perps" in blob or "options" in blob:
        return {"volume_usd_24h": 850000000.0, "venues": 24.0, "share_pct": 18.5}
    if "yield" in blob or "borrow" in blob or "staking" in blob:
        return {"apy_pct": 8.4, "tvl_usd": 420000000.0, "risk_score": 32.0}
    if "stablecoin" in blob or "bridge" in blob:
        return {"supply_usd_b": 125.0, "flow_usd_24h": 4200000000.0, "peg_deviation_bps": 4.2}
    if "unlock" in blob or "airdrop" in blob or "treasury" in blob or "raise" in blob:
        return {"events_30d": 18.0, "value_usd_m": 420.0, "participants": 1250.0}
    if "research" in blob or "thesis" in blob or "analyst" in blob or "comparable" in blob:
        return {"sources_cited": 24.0, "confidence_pct": 72.0, "coverage_score": 0.84}
    if "api" in blob or "excel" in blob or "integration" in blob:
        return {"endpoints_active": 42.0, "requests_24h": 125000.0, "error_rate_pct": 0.8}
    if "risk" in blob or "defi" in blob or "passport" in blob:
        return {"risk_flags": 6.0, "exposure_usd": 2500000.0, "mitigation_score": 78.0}
    if "developer" in blob or "sector" in blob or "fundamental" in blob:
        return {"commits_90d": 420.0, "active_devs": 86.0, "growth_pct": 12.5}
    if "payment" in blob or "usage" in blob or "on-chain" in blob:
        return {"tx_count_24h": 1250000.0, "active_addresses": 42000.0, "fee_usd": 850000.0}
    return {"metric_a": 100.0, "metric_b": 50.0, "metric_c": 25.0}


def snake(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return re.sub(r"_+", "_", s)


def load_catalog() -> dict[int, dict]:
    ext = json.loads(CAP978_PATH.read_text(encoding="utf-8"))
    return {int(r["id"]): r for r in ext if 651 <= int(r["id"]) <= 700}


def fn_name(cap_id: int, capability: str) -> str:
    return f"{snake(capability)}_{cap_id}"


def rule_name(cap_id: int, capability: str) -> str:
    return snake(capability)[:64]


def gen_semantic_engine(catalog: dict[int, dict]) -> str:
    lines = [
        '"""Batch14 (651–700) capability-specific semantic transforms for extension analytics shared core."""',
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
        defaults = _defaults_for(cid, cap)
        keys = list(defaults.keys())
        a, b, c = keys[0], keys[1], keys[2]
        blob = cap.lower()
        if "spread" in blob or "arbitrage" in blob:
            primary_expr = f"_spread(i['{a}'], i['{b}'])"
        elif any(x in blob for x in ("tvl", "volume", "yield", "stablecoin", "bridge", "unlock")):
            primary_expr = f"round(_ratio(i['{a}'], i['{b}']), 4)"
        elif any(x in blob for x in ("research", "analyst", "risk", "developer")):
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
        '    payload["attribution"] = "BLACKDARK batch14 extension analytics layer"',
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
        '"""Batch14 Extension Analytics Layer — capabilities #651–#700.',
        "",
        "978 extension analytics, research, DeFi fundamentals, and agent surfaces.",
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
        "from bd_platform.batch14_semantic_engine import compute_semantic_extra",
        "from bd_platform.batch14_three_spec_foundations import attach_three_spec_metadata",
        "",
        "logger = logging.getLogger(\"BLACKDARK.Batch14ExtensionAnalytics\")",
        "",
        "_SEED_PATH = Path(\"data/legal_retail_commercial_seed.json\")",
        "",
        "",
        "def reset_batch14_extension_analytics_state() -> None:",
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
        "        return json.loads(_SEED_PATH.read_text(encoding=\"utf-8\"))",
        "    except (OSError, json.JSONDecodeError) as exc:",
        "        logger.warning(\"batch14 seed load failed: %s\", exc)",
        "        return {}",
        "",
        "",
        "def _disclaimer(locale: str = \"en\") -> str:",
        "    if locale.lower().startswith(\"ar\"):",
        "        return \"تحليل فقط — ليس توصية مالية ولا تنفيذ.\"",
        "    return \"Analysis only — not financial advice, guarantee, or execution.\"",
        "",
        "",
        "def _base(",
        "    cap_id: int,",
        "    *,",
        "    symbol: str = \"BTC\",",
        "    seed: dict[str, Any] | None = None,",
        "    extra: dict[str, Any] | None = None,",
        ") -> dict[str, Any]:",
        "    seed = seed or _load_seed()",
        "    payload = {",
        "        \"ok\": True,",
        "        \"capability_id\": cap_id,",
        "        \"symbol\": symbol.upper(),",
        "        \"timestamp\": _utcnow(),",
        "        \"disclaimer\": _disclaimer(),",
        "        \"analysis_only\": True,",
        "        \"no_execution\": True,",
        "    }",
        "    if extra:",
        "        payload.update(extra)",
        "    attach_three_spec_metadata(payload, cap_id=cap_id)",
        "    return payload",
        "",
    ]

    # Canonical reuse facades
    lines.extend([
        "",
        "def tvl_intelligence_660(*, symbol: str = \"BTC\", seed: dict[str, Any] | None = None) -> dict[str, Any]:",
        '    """TVL Intelligence (#660) — canonical reuse of #354."""',
        "    from bd_platform.charting_market_intelligence_layer import tvl_intelligence_354",
        "    canonical = tvl_intelligence_354(symbol=symbol, seed=seed)",
        "    return {",
        "        **canonical,",
        "        \"capability_id\": 660,",
        "        \"canonical_reuse_of\": 354,",
        "        \"surface\": \"tvl_intelligence\",",
        "        \"attribution\": \"BLACKDARK batch14 facade → charting layer #354\",",
        "    }",
        "",
        "def chain_tvl_comparison_661(*, symbol: str = \"BTC\", seed: dict[str, Any] | None = None) -> dict[str, Any]:",
        '    """Chain TVL Comparison (#661) — canonical reuse of #394."""',
        "    from bd_platform.charting_market_intelligence_layer import chain_tvl_comparison_394",
        "    canonical = chain_tvl_comparison_394(symbol=symbol, seed=seed)",
        "    return {",
        "        **canonical,",
        "        \"capability_id\": 661,",
        "        \"canonical_reuse_of\": 394,",
        "        \"surface\": \"chain_tvl_comparison\",",
        "        \"attribution\": \"BLACKDARK batch14 facade → charting layer #394\",",
        "    }",
        "",
        "def unlocks_676(*, symbol: str = \"BTC\", seed: dict[str, Any] | None = None) -> dict[str, Any]:",
        '    """Unlocks (#676) — facade to token unlock forecaster #604 semantics."""',
        "    from bd_platform.batch13_operational_intelligence_layer import token_unlock_forecaster_604",
        "    canonical = token_unlock_forecaster_604(symbol=symbol, seed=seed)",
        "    return {",
        "        **canonical,",
        "        \"capability_id\": 676,",
        "        \"canonical_reuse_of\": 604,",
        "        \"surface\": \"unlocks\",",
        "    }",
        "",
    ])

    # Special outside handlers
    special_handlers = {
        656: ("data_lineage_656", "Data Lineage", "lineage_graph_nodes"),
        657: ("query_performance_governance_657", "Query Performance Governance", "governance_score"),
        658: ("white_label_embedded_analytics_658", "White-Label Embedded Analytics", "embed_score"),
        659: ("cross_domain_decision_layer_659", "Cross-Domain Decision Layer", "decision_score"),
        682: ("api_aggregation_layer_682", "API Aggregation Layer", "aggregation_score"),
        692: ("ai_analyst_692", "AI Analyst", "analyst_score"),
        695: ("excel_sheets_integration_695", "Excel / Sheets Integration", "integration_score"),
        696: ("api_data_platform_696", "API Data Platform", "platform_score"),
    }
    for cid, (fn, cap, score_key) in special_handlers.items():
        lines.extend([
            f"def {fn}(*, symbol: str = \"BTC\", seed: dict[str, Any] | None = None) -> dict[str, Any]:",
            f'    """{cap} (#{cid})."""',
            "    seed = seed or _load_seed()",
            "    from bd_platform.batch14_three_spec_foundations import build_special_surface",
            f"    extra = build_special_surface({cid}, symbol=symbol, seed=seed, score_key={score_key!r})",
            "    return _base(",
            f"        {cid},",
            "        symbol=symbol,",
            "        seed=seed,",
            "        extra=extra,",
            "    )",
            "",
        ])

    for cid in SHARED_CORE_IDS:
        cap = catalog[cid]["capability"]
        fn = fn_name(cid, cap)
        lines.extend([
            f"def {fn}(*, symbol: str = \"BTC\", seed: dict[str, Any] | None = None) -> dict[str, Any]:",
            f'    """{cap} (#{cid})."""',
            "    seed = seed or _load_seed()",
            "    return _base(",
            f"        {cid},",
            "        symbol=symbol,",
            "        seed=seed,",
            f"        extra=compute_semantic_extra({cid}, symbol=symbol, seed=seed),",
            "    )",
            "",
        ])

    return "\n".join(lines) + "\n"


def gen_membership() -> str:
    return '''"""Canonical Batch14 (651–700) membership derived from registry + semantic engine."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

from bd_platform.batch14_semantic_engine import shared_core_ids

BATCH14_IDS = list(range(651, 701))
SHARED_CORE_PARAMETERIZED = shared_core_ids()
OUTSIDE_SHARED_CORE_IDS = [656, 657, 658, 659, 676, 682, 692, 695, 696]
CANONICAL_DUPLICATE_IDS = [660, 661, 676]
CANONICAL_CATALOG_SEMANTICS_IDS = frozenset({656, 657, 658, 659, 682, 692, 695, 696})


def parameterized_ids() -> list[int]:
    return list(SHARED_CORE_PARAMETERIZED)


def shared_core_ids_list() -> list[int]:
    return sorted(set(parameterized_ids()))


def outside_shared_core_ids() -> list[int]:
    return sorted(set(OUTSIDE_SHARED_CORE_IDS))


def canonical_duplicate_ids() -> list[int]:
    return sorted(set(CANONICAL_DUPLICATE_IDS))


def verify_membership() -> dict[str, object]:
    batch = set(BATCH14_IDS)
    shared = set(shared_core_ids_list())
    outside = set(outside_shared_core_ids())
    canonical = set(canonical_duplicate_ids())
    errors: list[str] = []
    if len(batch) != 50:
        errors.append("batch_not_50")
    if not shared <= batch:
        errors.append("shared_not_subset")
    for cid in CANONICAL_CATALOG_SEMANTICS_IDS:
        mod, fn = discover_bindings().get(cid, ("", ""))
        if mod != "bd_platform.batch14_extension_analytics_layer":
            errors.append(f"catalog_semantics_binding_{cid}")
    return {
        "ok": not errors,
        "errors": errors,
        "shared_count": len(shared),
        "outside_count": len(outside),
        "canonical_count": len(canonical),
    }
'''


def gen_prebuild(catalog: dict[int, dict]) -> str:
    lines = [
        '"""Batch14 (651–700) pre-build classification — categories A–H only."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "PREBUILD_CLASSIFICATION: dict[int, str] = {",
    ]
    for cid in BATCH14_IDS:
        if cid in (660, 661, 676):
            cls = "E. CANONICAL_DUPLICATE_REUSE"
        elif cid in OUTSIDE_IDS:
            cls = "B. EXISTING_NEEDS_EXTENSION"
        else:
            cls = "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE"
        lines.append(f'    {cid}: "{cls}",')
    lines.extend([
        "}",
        "",
        "CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {660: 354, 661: 394, 676: 604}",
        "",
        "PREBUILD_EVIDENCE: dict[int, dict[str, Any]] = {",
        "    660: {\"canonical_capability_id\": 354, \"evidence\": \"TVL Intelligence delegates to charting layer #354\"},",
        "    661: {\"canonical_capability_id\": 394, \"evidence\": \"Chain TVL Comparison delegates to charting layer #394\"},",
        "    676: {\"canonical_capability_id\": 604, \"evidence\": \"Unlocks facade delegates to token unlock forecaster #604\"},",
        "    656: {\"binding_module\": \"batch14_three_spec_foundations\", \"evidence\": \"Data lineage via three-spec foundation layer\"},",
        "    659: {\"binding_module\": \"batch14_three_spec_foundations\", \"evidence\": \"Cross-domain decision via adaptive foundation\"},",
        "    692: {\"binding_module\": \"bd_platform.adaptive_intelligence\", \"evidence\": \"AI Analyst integrates adaptive spine\"},",
        "}",
        "",
        "",
        "def verify_prebuild_classification() -> dict[str, Any]:",
        "    ids = sorted(PREBUILD_CLASSIFICATION)",
        "    allowed = {",
        '        "A. EXISTING_VERIFIED", "B. EXISTING_NEEDS_EXTENSION", "C. PARTIAL_IMPLEMENTATION",',
        '        "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE", "E. CANONICAL_DUPLICATE_REUSE",',
        '        "F. NEW_BUILD_REQUIRED", "G. EXTERNAL_DEPENDENCY_BLOCKED", "H. NOT_APPLICABLE_WITH_EVIDENCE",',
        "    }",
        "    categories = set(PREBUILD_CLASSIFICATION.values())",
        "    double = [cid for cid in ids if list(PREBUILD_CLASSIFICATION.keys()).count(cid) > 1]",
        "    return {",
        '        "expected_ids": 50,',
        '        "actual_unique_ids": len(set(ids)),',
        '        "missing_ids": [i for i in range(651, 701) if i not in PREBUILD_CLASSIFICATION],',
        '        "extra_ids": [i for i in PREBUILD_CLASSIFICATION if i < 651 or i > 700],',
        '        "duplicate_ids": double,',
        '        "invalid_categories": [c for c in categories if c not in allowed],',
        '        "double_classifications": double,',
        '        "ok": len(ids) == 50 and not double and categories <= allowed,',
        "    }",
        "",
    ])
    return "\n".join(lines) + "\n"


def gen_manifest() -> None:
    manifest = {
        "batch": 14,
        "capability_range": "651-700",
        "capability_ids": BATCH14_IDS,
        "count": 50,
    }
    path = ROOT / "scripts/partial_batches/batch_14_651_700.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    catalog = load_catalog()
    assert len(catalog) == 50, f"expected 50 catalog rows, got {len(catalog)}"
    (ROOT / "bd_platform/batch14_semantic_engine.py").write_text(gen_semantic_engine(catalog), encoding="utf-8")
    (ROOT / "bd_platform/batch14_extension_analytics_layer.py").write_text(gen_layer(catalog), encoding="utf-8")
    (ROOT / "bd_platform/batch14_membership.py").write_text(gen_membership(), encoding="utf-8")
    (ROOT / "bd_platform/batch14_prebuild_classification.py").write_text(gen_prebuild(catalog), encoding="utf-8")
    gen_manifest()
    print("Generated batch14 core modules for 50 capabilities")


if __name__ == "__main__":
    main()
