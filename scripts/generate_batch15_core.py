#!/usr/bin/env python3
"""Generate Batch15 core modules: canonical-reuse facade layer for capabilities 701-750."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAP978_PATH = ROOT / "docs/cap978/CAP978_CATALOG.json"
OUT_LAYER = ROOT / "bd_platform/batch15_defi_risk_data_facade_layer.py"
OUT_MEMBERSHIP = ROOT / "bd_platform/batch15_membership.py"
OUT_PREBUILD = ROOT / "bd_platform/batch15_prebuild_classification.py"
OUT_CONTRACTS = ROOT / "bd_platform/batch15_semantic_contracts.py"
OUT_MANIFEST = ROOT / "scripts/partial_batches/batch_15_701_750.json"

BATCH15_IDS = list(range(701, 751))
CANONICAL_OFFSET = 267
SPECIAL_CANONICAL: dict[int, tuple[int, str, str, dict[str, str]]] = {
    725: (
        458,
        "bd_platform.heroes_capability_layer",
        "metric_methodology_registry_458",
        {"locale": "en"},
    ),
}


def snake(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return re.sub(r"_+", "_", s)


def load_catalog() -> dict[int, dict]:
    ext = json.loads(CAP978_PATH.read_text(encoding="utf-8"))
    return {int(r["id"]): r for r in ext if 701 <= int(r["id"]) <= 750}


def canonical_target(cap_id: int) -> tuple[int, str, str, dict[str, str]]:
    if cap_id in SPECIAL_CANONICAL:
        cid, mod, fn, extra = SPECIAL_CANONICAL[cap_id]
        return cid, mod, fn, extra
    prior = cap_id - CANONICAL_OFFSET
    cat = load_catalog()
    cap_name = cat[cap_id]["capability"]
    fn = f"{snake(cap_name)}_{prior}"
    return prior, "bd_platform.defi_yield_intelligence_layer", fn, {}


def fn_name(cap_id: int, capability: str) -> str:
    return f"{snake(capability)}_{cap_id}"


def gen_facade_layer(catalog: dict[int, dict]) -> str:
    lines = [
        '"""Batch15 DeFi/Risk/Data facade layer — capabilities #701–#750.',
        "",
        "CAP978 extension IDs delegate to canonical Batch09 DeFi/risk/data semantics (434–483)",
        "and hero delegate #458 for Risk-to-Decision Intelligence (#725).",
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
        "from bd_platform.batch15_three_spec_foundations import attach_three_spec_metadata",
        "",
        'logger = logging.getLogger("BLACKDARK.Batch15DeFiRiskDataFacade")',
        "",
        '_SEED_PATH = Path("data/legal_retail_commercial_seed.json")',
        "",
        "",
        "def reset_batch15_defi_risk_data_state() -> None:",
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
        '        logger.warning("batch15 seed load failed: %s", exc)',
        "        return {}",
        "",
        "",
        'def _disclaimer(locale: str = "en") -> str:',
        '    if locale.lower().startswith("ar"):',
        '        return "تحليل فقط — ليس توصية مالية ولا تنفيذ."',
        '    return "Analysis only — not financial advice, guarantee, or execution."',
        "",
        "",
        "def _facade(",
        "    cap_id: int,",
        "    canonical_id: int,",
        "    mod_path: str,",
        "    fn_name: str,",
        "    *,",
        '    symbol: str = "BTC",',
        "    seed: dict[str, Any] | None = None,",
        "    extra_kwargs: dict[str, Any] | None = None,",
        ") -> dict[str, Any]:",
        "    import importlib",
        "    import inspect",
        "    mod = importlib.import_module(mod_path)",
        "    canonical_fn = getattr(mod, fn_name)",
        "    call_kwargs: dict[str, Any] = dict(extra_kwargs or {})",
        "    sig = inspect.signature(canonical_fn)",
        "    if 'symbol' in sig.parameters:",
        "        call_kwargs.setdefault('symbol', symbol)",
        "    if seed is not None and 'seed' in sig.parameters:",
        "        call_kwargs['seed'] = seed",
        "    canonical = canonical_fn(**call_kwargs)",
        "    payload = {",
        "        **canonical,",
        '        "ok": canonical.get("ok", True),',
        '        "capability_id": cap_id,',
        '        "canonical_reuse_of": canonical_id,',
        '        "facade_layer": "batch15_defi_risk_data_facade",',
        '        "attribution": f"BLACKDARK batch15 facade → {mod_path}.{fn_name}",',
        '        "analysis_only": True,',
        '        "no_execution": True,',
        "    }",
        "    attach_three_spec_metadata(payload, cap_id=cap_id)",
        "    return payload",
        "",
        "",
    ]

    for cid in BATCH15_IDS:
        cap = catalog[cid]["capability"]
        fn = fn_name(cid, cap)
        prior, mod, prior_fn, extra = canonical_target(cid)
        extra_repr = repr(extra)
        lines.extend(
            [
                f"def {fn}(*, symbol: str = \"BTC\", seed: dict[str, Any] | None = None) -> dict[str, Any]:",
                f'    """{cap} (#{cid}) — canonical reuse of #{prior}."""',
                "    return _facade(",
                f"        {cid},",
                f"        {prior},",
                f'        "{mod}",',
                f'        "{prior_fn}",',
                "        symbol=symbol,",
                "        seed=seed,",
                f"        extra_kwargs={extra_repr},",
                "    )",
                "",
                "",
            ]
        )
    return "\n".join(lines)


def gen_membership() -> str:
    targets_lines = []
    for cid in BATCH15_IDS:
        prior, _, _, _ = canonical_target(cid)
        targets_lines.append(f"    {cid}: {prior},")
    return f'''"""Canonical Batch15 (701–750) membership — all CAP978 extension facades."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

BATCH15_IDS = list(range(701, 751))
CANONICAL_DUPLICATE_IDS = list(BATCH15_IDS)
CANONICAL_OFFSET = {CANONICAL_OFFSET}
CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {{
{chr(10).join(targets_lines)}
}}
SHARED_LAYER_MODULE = "bd_platform.batch15_defi_risk_data_facade_layer"


def canonical_duplicate_ids() -> list[int]:
    return sorted(set(CANONICAL_DUPLICATE_IDS))


def verify_membership() -> dict[str, object]:
    batch = set(BATCH15_IDS)
    errors: list[str] = []
    if len(batch) != 50:
        errors.append("batch_not_50")
    bindings = discover_bindings()
    for cid in BATCH15_IDS:
        mod, fn = bindings.get(cid, ("", ""))
        if mod != SHARED_LAYER_MODULE:
            errors.append(f"binding_{cid}_not_batch15_layer")
    return {{
        "ok": not errors,
        "errors": errors,
        "canonical_reuse_count": len(CANONICAL_DUPLICATE_TARGETS),
    }}
'''


def gen_prebuild(catalog: dict[int, dict]) -> str:
    lines = [
        '"""Batch15 (701–750) pre-build classification — categories A–H only."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "PREBUILD_CLASSIFICATION: dict[int, str] = {",
    ]
    for cid in BATCH15_IDS:
        lines.append(f'    {cid}: "E. CANONICAL_DUPLICATE_REUSE",')
    lines.extend(["}", ""])
    lines.append("CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {")
    for cid in BATCH15_IDS:
        prior, _, _, _ = canonical_target(cid)
        lines.append(f"    {cid}: {prior},")
    lines.extend(["}", "", "PREBUILD_EVIDENCE: dict[int, dict[str, Any]] = {"])
    for cid in BATCH15_IDS:
        cap = catalog[cid]["capability"]
        prior, mod, prior_fn, _ = canonical_target(cid)
        lines.append(
            f"    {cid}: {{"
            f'"canonical_capability_id": {prior}, '
            f'"evidence": "{cap} delegates to {mod}.{prior_fn}"'
            f"}},"
        )
    lines.extend(
        [
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
            "    return {",
            '        "ok": len(ids) == 50 and len(set(ids)) == 50 and categories <= allowed,',
            '        "count": len(ids),',
            '        "unique": len(set(ids)),',
            "    }",
            "",
        ]
    )
    return "\n".join(lines)


def gen_contracts(catalog: dict[int, dict]) -> str:
    lines = [
        '"""Batch15 semantic contracts for canonical-reuse facades 701-750."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "from bd_platform.batch15_membership import BATCH15_IDS, CANONICAL_DUPLICATE_TARGETS",
        "",
        "_REQUIRED = frozenset({",
        '    "ok", "capability_id", "canonical_reuse_of", "facade_layer", "analysis_only", "three_spec",',
        "})",
        "",
        "",
        "def contract_for(capability_id: int) -> dict[str, Any]:",
        "    return {",
        '        "capability_id": capability_id,',
        '        "classification": "E. CANONICAL_DUPLICATE_REUSE",',
        '        "canonical_owner": CANONICAL_DUPLICATE_TARGETS[capability_id],',
        '        "required_keys": _REQUIRED,',
        '        "consumer": "institutional_api",',
        '        "entitlement_tier": "institutional",',
        "    }",
        "",
        "",
        "def all_contracts() -> dict[int, dict[str, Any]]:",
        "    return {cid: contract_for(cid) for cid in BATCH15_IDS}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    catalog = load_catalog()
    assert len(catalog) == 50, len(catalog)
    OUT_LAYER.write_text(gen_facade_layer(catalog), encoding="utf-8")
    OUT_MEMBERSHIP.write_text(gen_membership(), encoding="utf-8")
    OUT_PREBUILD.write_text(gen_prebuild(catalog), encoding="utf-8")
    OUT_CONTRACTS.write_text(gen_contracts(catalog), encoding="utf-8")
    OUT_MANIFEST.write_text(
        json.dumps(
            {
                "batch": 15,
                "capability_range": "701-750",
                "capability_ids": BATCH15_IDS,
                "count": 50,
                "canonical_strategy": "facade_to_434_483_offset_267",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Generated batch15 core modules for 50 capabilities")


if __name__ == "__main__":
    main()
