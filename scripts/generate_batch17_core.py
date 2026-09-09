#!/usr/bin/env python3
"""Generate Batch17 core modules: single-dispatcher facade layer for 801-826."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))
OUT_MAP = ROOT / "scripts/partial_batches/batch_17_canonical_map.json"
OUT_LAYER = ROOT / "bd_platform/batch17_final_program_facade_layer.py"
OUT_MEMBERSHIP = ROOT / "bd_platform/batch17_membership.py"
OUT_PREBUILD = ROOT / "bd_platform/batch17_prebuild_classification.py"
OUT_CONTRACTS = ROOT / "bd_platform/batch17_semantic_contracts.py"
OUT_BINDINGS = ROOT / "scripts/partial_batches/batch_17_pdf_bindings.json"
OUT_MANIFEST = ROOT / "scripts/partial_batches/batch_17_801_826.json"

BATCH17_IDS = list(range(801, 827))
CANONICAL_OFFSET = 267
ENTRYPOINT = "execute_batch17_facade"
LAYER_MODULE = "bd_platform.batch17_final_program_facade_layer"
CANONICAL_MODULE = "bd_platform.institutional_delivery_intelligence_layer"


def load_catalog() -> dict[int, dict]:
    rows = json.loads((ROOT / "docs/cap978/CAP978_CATALOG.json").read_text(encoding="utf-8"))
    return {int(r["id"]): r for r in rows if 801 <= int(r["id"]) <= 826}


def build_canonical_map(catalog: dict[int, dict]) -> dict[str, list]:
    import inspect
    import importlib

    mod = importlib.import_module(CANONICAL_MODULE)
    cmap: dict[str, list] = {}
    for cid in BATCH17_IDS:
        prior = cid - CANONICAL_OFFSET
        cap = catalog[cid]["capability"]
        fn_name = None
        for name, obj in inspect.getmembers(mod):
            if not (name.endswith(f"_{prior}") and callable(obj)):
                continue
            fn_name = name
            break
        if fn_name is None:
            raise RuntimeError(f"No canonical function for {cid} -> {prior} ({cap})")
        cmap[str(cid)] = [prior, CANONICAL_MODULE, fn_name, {}]
    return cmap


def gen_facade_layer() -> str:
    return f'''"""Batch17 final-program facade layer — capabilities #801–#826."""

from __future__ import annotations

import importlib
import inspect
import json
import logging
from pathlib import Path
from typing import Any

from bd_platform.batch17_three_spec_foundations import attach_three_spec_metadata

logger = logging.getLogger("BLACKDARK.Batch17FinalProgramFacade")

_MAP_PATH = Path(__file__).resolve().parents[1] / "scripts/partial_batches/batch_17_canonical_map.json"


def _load_canonical_map() -> dict[int, tuple[int, str, str, dict[str, Any]]]:
    raw = json.loads(_MAP_PATH.read_text(encoding="utf-8"))
    return {{int(k): (v[0], v[1], v[2], dict(v[3] or {{}})) for k, v in raw.items()}}


_CANONICAL_MAP = _load_canonical_map()


def reset_batch17_final_program_state() -> None:
    return None


def execute_batch17_facade(
    *,
    capability_id: int,
    symbol: str = "BTC",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Canonical-reuse dispatcher for CAP978 extension IDs 801-826."""
    spec = _CANONICAL_MAP.get(capability_id)
    if spec is None:
        return {{"ok": False, "error": "unknown_batch17_capability", "capability_id": capability_id}}
    canonical_id, mod_path, fn_name, extra_kwargs = spec
    mod = importlib.import_module(mod_path)
    canonical_fn = getattr(mod, fn_name)
    call_kwargs: dict[str, Any] = dict(extra_kwargs)
    sig = inspect.signature(canonical_fn)
    if "symbol" in sig.parameters:
        call_kwargs.setdefault("symbol", symbol)
    if seed is not None and "seed" in sig.parameters:
        call_kwargs["seed"] = seed
    if inspect.iscoroutinefunction(canonical_fn):
        import asyncio
        import concurrent.futures

        def _run_coro() -> Any:
            return asyncio.run(canonical_fn(**call_kwargs))

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            canonical = _run_coro()
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                canonical = pool.submit(_run_coro).result()
    else:
        canonical = canonical_fn(**call_kwargs)
    if not isinstance(canonical, dict):
        canonical = {{"result": canonical}}
    payload = {{
        **canonical,
        "ok": canonical.get("ok", True),
        "capability_id": capability_id,
        "canonical_reuse_of": canonical_id,
        "facade_layer": "batch17_final_program_facade",
        "attribution": f"BLACKDARK batch17 facade → {{mod_path}}.{{fn_name}}",
        "analysis_only": True,
        "no_execution": True,
    }}
    attach_three_spec_metadata(payload, cap_id=capability_id)
    return payload
'''


def gen_membership(cmap: dict[str, list]) -> str:
    targets = [f"    {cid}: {cmap[str(cid)][0]}," for cid in BATCH17_IDS]
    return f'''"""Canonical Batch17 (801–826) membership — dispatcher facades."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

BATCH17_IDS = list(range(801, 827))
CANONICAL_OFFSET = {CANONICAL_OFFSET}
CANONICAL_DUPLICATE_IDS = list(BATCH17_IDS)
CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {{
{chr(10).join(targets)}
}}
SHARED_LAYER_MODULE = "{LAYER_MODULE}"
SHARED_ENTRYPOINT = "{ENTRYPOINT}"


def verify_membership() -> dict[str, object]:
    bindings = discover_bindings()
    errors = [
        f"binding_{{cid}}"
        for cid in BATCH17_IDS
        if bindings.get(cid) != (SHARED_LAYER_MODULE, SHARED_ENTRYPOINT)
    ]
    if len(BATCH17_IDS) != 26:
        errors.append("batch_not_26")
    return {{"ok": not errors, "errors": errors, "canonical_reuse_count": len(CANONICAL_DUPLICATE_TARGETS)}}
'''


def gen_prebuild(catalog: dict[int, dict], cmap: dict[str, list]) -> str:
    lines = [
        '"""Batch17 (801–826) pre-build classification — categories A–H only."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "from bd_platform.batch17_membership import BATCH17_IDS, CANONICAL_DUPLICATE_TARGETS",
        "",
        '_CLASS = "E. CANONICAL_DUPLICATE_REUSE"',
        "PREBUILD_CLASSIFICATION: dict[int, str] = {cid: _CLASS for cid in BATCH17_IDS}",
        "PREBUILD_EVIDENCE: dict[int, dict[str, Any]] = {",
    ]
    for cid in BATCH17_IDS:
        prior, mod, fn, _ = cmap[str(cid)]
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
            '    return {"ok": len(ids) == 26 and len(set(ids)) == 26, "count": len(ids), "unique": len(set(ids))}',
            "",
        ]
    )
    return "\n".join(lines)


def gen_contracts() -> str:
    return f'''"""Batch17 semantic contracts for canonical-reuse facades 801-826."""

from __future__ import annotations

from typing import Any

from bd_platform.batch17_membership import BATCH17_IDS, CANONICAL_DUPLICATE_TARGETS

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
    return {{cid: contract_for(cid) for cid in BATCH17_IDS}}
'''


def main() -> None:
    catalog = load_catalog()
    cmap = build_canonical_map(catalog)
    OUT_MAP.write_text(json.dumps(cmap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT_LAYER.write_text(gen_facade_layer(), encoding="utf-8")
    OUT_MEMBERSHIP.write_text(gen_membership(cmap), encoding="utf-8")
    OUT_PREBUILD.write_text(gen_prebuild(catalog, cmap), encoding="utf-8")
    OUT_CONTRACTS.write_text(gen_contracts(), encoding="utf-8")
    bindings = {str(cid): [LAYER_MODULE, ENTRYPOINT] for cid in BATCH17_IDS}
    OUT_BINDINGS.write_text(json.dumps(bindings, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "batch": 17,
        "range": "801-826",
        "count": 26,
        "capability_ids": BATCH17_IDS,
        "canonical_offset": CANONICAL_OFFSET,
        "facade_module": LAYER_MODULE,
        "facade_entrypoint": ENTRYPOINT,
        "capabilities": [
            {
                "id": cid,
                "capability": catalog[cid]["capability"],
                "canonical_id": cid - CANONICAL_OFFSET,
                "canonical_module": CANONICAL_MODULE,
                "canonical_function": cmap[str(cid)][2],
            }
            for cid in BATCH17_IDS
        ],
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Generated batch17 core for {len(BATCH17_IDS)} capabilities")


if __name__ == "__main__":
    main()
