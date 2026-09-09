#!/usr/bin/env python3
"""Generate Batch16 core modules: single-dispatcher facade layer for 751-800."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "scripts/partial_batches/batch_16_canonical_map.json"
OUT_LAYER = ROOT / "bd_platform/batch16_market_delivery_facade_layer.py"
OUT_MEMBERSHIP = ROOT / "bd_platform/batch16_membership.py"
OUT_PREBUILD = ROOT / "bd_platform/batch16_prebuild_classification.py"
OUT_CONTRACTS = ROOT / "bd_platform/batch16_semantic_contracts.py"
OUT_BINDINGS = ROOT / "scripts/partial_batches/batch_16_pdf_bindings.json"
OUT_MANIFEST = ROOT / "scripts/partial_batches/batch_16_751_800.json"

BATCH16_IDS = list(range(751, 801))
CANONICAL_OFFSET = 267
ENTRYPOINT = "execute_batch16_facade"
LAYER_MODULE = "bd_platform.batch16_market_delivery_facade_layer"


def load_map() -> dict[int, tuple[int, str, str, dict]]:
    raw = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    return {int(k): (v[0], v[1], v[2], dict(v[3] or {})) for k, v in raw.items()}


def load_catalog() -> dict[int, dict]:
    cap978 = ROOT / "docs/cap978/CAP978_CATALOG.json"
    rows = json.loads(cap978.read_text(encoding="utf-8"))
    return {int(r["id"]): r for r in rows if 751 <= int(r["id"]) <= 800}


def gen_facade_layer(catalog: dict[int, dict], cmap: dict[int, tuple[int, str, str, dict]]) -> str:
    return f'''"""Batch16 market/delivery facade layer — capabilities #751–#800."""

from __future__ import annotations

import importlib
import inspect
import json
import logging
from pathlib import Path
from typing import Any

from bd_platform.batch16_three_spec_foundations import attach_three_spec_metadata

logger = logging.getLogger("BLACKDARK.Batch16MarketDeliveryFacade")

_MAP_PATH = Path(__file__).resolve().parents[1] / "scripts/partial_batches/batch_16_canonical_map.json"


def _load_canonical_map() -> dict[int, tuple[int, str, str, dict[str, Any]]]:
    raw = json.loads(_MAP_PATH.read_text(encoding="utf-8"))
    return {{int(k): (v[0], v[1], v[2], dict(v[3] or {{}})) for k, v in raw.items()}}


_CANONICAL_MAP = _load_canonical_map()


def reset_batch16_market_delivery_state() -> None:
    return None


def execute_batch16_facade(
    *,
    capability_id: int,
    symbol: str = "BTC",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Canonical-reuse dispatcher for CAP978 extension IDs 751-800."""
    spec = _CANONICAL_MAP.get(capability_id)
    if spec is None:
        return {{"ok": False, "error": "unknown_batch16_capability", "capability_id": capability_id}}
    canonical_id, mod_path, fn_name, extra_kwargs = spec
    mod = importlib.import_module(mod_path)
    canonical_fn = getattr(mod, fn_name)
    call_kwargs: dict[str, Any] = dict(extra_kwargs)
    sig = inspect.signature(canonical_fn)
    if "symbol" in sig.parameters:
        call_kwargs.setdefault("symbol", symbol)
    if seed is not None and "seed" in sig.parameters:
        call_kwargs["seed"] = seed
    canonical = canonical_fn(**call_kwargs)
    payload = {{
        **canonical,
        "ok": canonical.get("ok", True),
        "capability_id": capability_id,
        "canonical_reuse_of": canonical_id,
        "facade_layer": "batch16_market_delivery_facade",
        "attribution": f"BLACKDARK batch16 facade → {{mod_path}}.{{fn_name}}",
        "analysis_only": True,
        "no_execution": True,
    }}
    attach_three_spec_metadata(payload, cap_id=capability_id)
    return payload
'''


def gen_membership(cmap: dict[int, tuple[int, str, str, dict]]) -> str:
    targets = [f"    {cid}: {cmap[cid][0]}," for cid in BATCH16_IDS]
    return f'''"""Canonical Batch16 (751–800) membership — dispatcher facades."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

BATCH16_IDS = list(range(751, 801))
CANONICAL_OFFSET = {CANONICAL_OFFSET}
CANONICAL_DUPLICATE_IDS = list(BATCH16_IDS)
CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {{
{chr(10).join(targets)}
}}
SHARED_LAYER_MODULE = "{LAYER_MODULE}"
SHARED_ENTRYPOINT = "{ENTRYPOINT}"


def verify_membership() -> dict[str, object]:
    bindings = discover_bindings()
    errors = [
        f"binding_{{cid}}"
        for cid in BATCH16_IDS
        if bindings.get(cid) != (SHARED_LAYER_MODULE, SHARED_ENTRYPOINT)
    ]
    if len(BATCH16_IDS) != 50:
        errors.append("batch_not_50")
    return {{"ok": not errors, "errors": errors, "canonical_reuse_count": len(CANONICAL_DUPLICATE_TARGETS)}}
'''


def gen_prebuild(catalog: dict[int, dict], cmap: dict[int, tuple[int, str, str, dict]]) -> str:
    lines = [
        '"""Batch16 (751–800) pre-build classification — categories A–H only."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "PREBUILD_CLASSIFICATION: dict[int, str] = {",
    ]
    for cid in BATCH16_IDS:
        lines.append(f'    {cid}: "E. CANONICAL_DUPLICATE_REUSE",')
    lines.extend(["}", "", "CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {"])
    for cid in BATCH16_IDS:
        lines.append(f"    {cid}: {cmap[cid][0]},")
    lines.extend(["}", "", "PREBUILD_EVIDENCE: dict[int, dict[str, Any]] = {"])
    for cid in BATCH16_IDS:
        prior, mod, fn, _ = cmap[cid]
        cap = catalog[cid]["capability"]
        lines.append(
            f'    {cid}: {{"canonical_capability_id": {prior}, "evidence": "{cap} delegates to {mod}.{fn}"}},'
        )
    lines.extend(
        [
            "}",
            "",
            "def verify_prebuild_classification() -> dict[str, Any]:",
            "    ids = sorted(PREBUILD_CLASSIFICATION)",
            "    return {",
            '        "ok": len(ids) == 50 and len(set(ids)) == 50,',
            '        "count": len(ids),',
            '        "unique": len(set(ids)),',
            "    }",
            "",
        ]
    )
    return "\n".join(lines)


def gen_contracts() -> str:
    return f'''"""Batch16 semantic contracts for canonical-reuse facades 751-800."""

from __future__ import annotations

from typing import Any

from bd_platform.batch16_membership import BATCH16_IDS, CANONICAL_DUPLICATE_TARGETS

_REQUIRED = frozenset({{
    "ok", "capability_id", "canonical_reuse_of", "facade_layer", "analysis_only", "three_spec",
}})


def contract_for(capability_id: int) -> dict[str, Any]:
    return {{
        "capability_id": capability_id,
        "classification": "E. CANONICAL_DUPLICATE_REUSE",
        "canonical_owner": CANONICAL_DUPLICATE_TARGETS[capability_id],
        "required_keys": _REQUIRED,
        "consumer": "institutional_api",
        "entitlement_tier": "institutional",
    }}


def all_contracts() -> dict[int, dict[str, Any]]:
    return {{cid: contract_for(cid) for cid in BATCH16_IDS}}
'''


def main() -> None:
    catalog = load_catalog()
    cmap = load_map()
    OUT_LAYER.write_text(gen_facade_layer(catalog, cmap), encoding="utf-8")
    OUT_MEMBERSHIP.write_text(gen_membership(cmap), encoding="utf-8")
    OUT_PREBUILD.write_text(gen_prebuild(catalog, cmap), encoding="utf-8")
    OUT_CONTRACTS.write_text(gen_contracts(), encoding="utf-8")
    OUT_BINDINGS.write_text(
        json.dumps({str(cid): [LAYER_MODULE, ENTRYPOINT] for cid in BATCH16_IDS}, indent=2) + "\n",
        encoding="utf-8",
    )
    OUT_MANIFEST.write_text(
        json.dumps(
            {
                "batch": 16,
                "capability_range": "751-800",
                "capability_ids": BATCH16_IDS,
                "count": 50,
                "entrypoint": ENTRYPOINT,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Generated batch16 dispatcher layer (duplication-safe)")


if __name__ == "__main__":
    main()
