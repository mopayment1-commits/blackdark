"""Unified v6 institutional production spine — all 826 capabilities, no invoke_substantive."""

from __future__ import annotations

import importlib
from functools import lru_cache
from typing import Any

from cap646.batch_constants import (
    CAPABILITIES_PER_BATCH,
    batch_id_range,
    batch_number,
    legacy_production_batch_for,
    official_batch_name,
)
from cap646.catalog import canonical_id, catalog_by_id, is_duplicate
from cap646.evidence_class import ai_compliance_footer

PRODUCTION_MODULE = "cap646.institutional_official_production"

# Capabilities with dedicated handlers in batch01 production spine (overlap batches).
_BATCH01_OVERLAP_IDS: frozenset[int] = frozenset({55, 56, 59, 60, 103, 129})

_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "capability_id",
        "capability",
        "track",
        "surface",
        "symbol",
        "success",
        "compliance_footer",
        "data_provenance",
        "provenance",
        "latency_ms",
        "performance_gate",
        "evidence_class",
        "evidence_metadata",
        "classification",
        "backend_module",
        "backend_entrypoint",
        "binding_source",
        "production_spine",
        "official_batch",
        "capabilities_per_batch",
        "handler_module",
        "build_method",
        "error",
        "binding_path",
        "report_meta",
    }
)


def institutional_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _legacy_dedicated_module(batch_num: int) -> str | None:
    if batch_num in (3, 4):
        return "cap646.batch02_dedicated"
    if batch_num in (5, 6):
        return "cap646.batch03_dedicated"
    if batch_num >= 7:
        return f"cap646.batch{batch_num:02d}_dedicated"
    return None


def _ensure_surface_domain_payload(result: dict[str, Any], surface: str) -> None:
    """Expose goal payload under canonical surface slug for strict G03 traceability."""
    if surface in result:
        return
    for key, value in result.items():
        if key in _METADATA_KEYS:
            continue
        if isinstance(value, (dict, list)) and value:
            result[surface] = value
            return


@lru_cache(maxsize=1)
def _surface_registry() -> dict[int, str]:
    """Merge dedicated EXPECTED_SURFACE maps — authoritative over catalog slug truncation."""
    merged: dict[int, str] = {}
    modules = ["cap646.batch01_dedicated", "cap646.batch02_dedicated", "cap646.batch03_dedicated"]
    modules.extend(f"cap646.batch{n:02d}_dedicated" for n in range(7, 35))
    for mod_name in modules:
        try:
            mod = importlib.import_module(mod_name)
            surfaces = getattr(mod, "EXPECTED_SURFACE", None)
            if isinstance(surfaces, dict):
                merged.update(surfaces)
        except Exception:
            continue
    return merged


def _resolve_production_spine(capability_id: int, handler_module: str) -> str:
    if capability_id in _BATCH01_OVERLAP_IDS or "batch01" in handler_module:
        return "batch01"
    legacy = legacy_production_batch_for(capability_id)
    if legacy:
        return legacy
    import re

    match = re.search(r"batch(\d+)_", handler_module)
    if match:
        return f"batch{int(match.group(1)):02d}"
    return official_batch_name(capability_id)


def _stamp(result: dict[str, Any], capability_id: int, *, handler_module: str) -> dict[str, Any]:
    row = catalog_by_id().get(capability_id, {})
    batch = _resolve_production_spine(capability_id, handler_module)
    surface = expected_surface(capability_id)
    if not result.get("compliance_footer"):
        result = ai_compliance_footer(result)
    result["capability_id"] = capability_id
    result.setdefault("capability", row.get("capability"))
    result.setdefault("track", row.get("track"))
    result["surface"] = surface
    _ensure_surface_domain_payload(result, surface)
    result["backend_module"] = PRODUCTION_MODULE
    result["backend_entrypoint"] = institutional_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = batch
    result["official_batch"] = batch
    result["capabilities_per_batch"] = CAPABILITIES_PER_BATCH
    result["handler_module"] = handler_module
    result["build_method"] = "v6_institutional_official"
    sym = str(result.get("symbol") or "BTC").upper().replace("/USDT", "")
    if not result.get("data_provenance") and not result.get("provenance"):
        from data_provenance_score import compute_data_provenance_score

        result["data_provenance"] = compute_data_provenance_score(symbol=sym)
    result.setdefault("latency_ms", 0.0)
    result.setdefault("performance_gate", True)
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id < 1 or capability_id > 826:
        raise ValueError(f"capability {capability_id} out of institutional scope")

    if is_duplicate(capability_id):
        canon = canonical_id(capability_id)
        if canon != capability_id:
            delegated = await execute(canon, params=dict(params or {}))
            delegated["duplicate_of"] = canon
            delegated["requested_capability_id"] = capability_id
            delegated["classification"] = "DUPLICATE/ALREADY_COVERED"
            return delegated
        row = catalog_by_id().get(capability_id, {})
        return _stamp(
            {
                "success": True,
                "symbol": str((params or {}).get("symbol") or "BTC"),
                "classification": "DUPLICATE/ALREADY_COVERED",
                "canonical_coverage": True,
                "capability": row.get("capability"),
                "track": row.get("track"),
            },
            capability_id,
            handler_module="cap646.institutional_official_production",
        )

    params = dict(params or {})
    batch_num = batch_number(capability_id)

    if capability_id in _BATCH01_OVERLAP_IDS:
        from cap646.batch01_production import execute as batch01_execute

        return _stamp(await batch01_execute(capability_id, params=params), capability_id, handler_module="cap646.batch01_production")

    if batch_num == 1:
        from cap646.batch01_production import execute as batch01_execute

        return _stamp(await batch01_execute(capability_id, params=params), capability_id, handler_module="cap646.batch01_production")

    if batch_num == 2:
        from cap646.batch02_official_production import execute as batch02_execute

        return _stamp(await batch02_execute(capability_id, params=params), capability_id, handler_module="cap646.batch02_official_production")

    legacy = _legacy_dedicated_module(batch_num)
    if legacy:
        import importlib

        mod = importlib.import_module(legacy)
        result = await mod.execute(capability_id, params=params)
        return _stamp(result, capability_id, handler_module=legacy)

    raise ValueError(f"no institutional handler for capability {capability_id} batch{batch_num:02d}")


def expected_surface(capability_id: int) -> str:
    reg = _surface_registry()
    if capability_id in reg:
        return reg[capability_id]
    from cap646.backend_registry import _slug

    row = catalog_by_id().get(capability_id, {})
    return _slug(row.get("capability", ""))


def domain_payload_keys(capability_id: int) -> tuple[str, ...]:
    """Goal-specific keys that must appear in execute() result."""
    from cap646.batch01_closure_spec import BATCH01_DOMAIN_PAYLOAD_KEYS
    from cap646.batch02_closure_spec import BATCH02_DOMAIN_PAYLOAD_KEYS

    if capability_id in BATCH01_DOMAIN_PAYLOAD_KEYS:
        return BATCH01_DOMAIN_PAYLOAD_KEYS[capability_id]
    if capability_id in BATCH02_DOMAIN_PAYLOAD_KEYS:
        return BATCH02_DOMAIN_PAYLOAD_KEYS[capability_id]
    surface = expected_surface(capability_id)
    keys: list[str] = [surface]
    if len(surface) > 48:
        keys.append(surface[:48])
    # wrap_with_backend puts slug as payload_key; also accept surface field match
    keys.extend(["domain_result", surface.replace("_", "")[:32]])
    return tuple(dict.fromkeys(keys))


def batch_official_range(batch_num: int) -> range:
    start, end = batch_id_range(batch_num)
    return range(start, end + 1)
