"""CI-deterministic structural closure — binding/import checks only, no live network I/O.

Used when ``BLACKDARK_CI_DETERMINISTIC_CLOSURE`` is set (``verify_institutional_closure --ci``).
Replaces live ``execute_capability`` / ``execute_extension`` calls that caused flaky
``sample_incomplete_ids`` from aiohttp timeouts and exchange geo-blocks.
"""

from __future__ import annotations

import importlib
import os
from typing import Any

from cap646.backend_registry import is_generic_surface, resolve_binding
from cap646.catalog import catalog_by_id, is_duplicate, is_external
from cap646.ui_pages import user_surface_for
from cap646.waves import EXTERNAL_EVIDENCE_SLOTS, SIGNED_INFRA_SLOTS, USER_FACING
from cap978.catalog import catalog_by_id as catalog_978_by_id
from cap978.catalog import is_duplicate as is_duplicate_978
from cap978.catalog import is_external as is_external_978
from cap978.extension_registry import resolve_extension_binding

_VERIFICATION_MODE = "ci_structural_no_network"


def ci_deterministic_closure_enabled() -> bool:
    return os.getenv("BLACKDARK_CI_DETERMINISTIC_CLOSURE", "").strip().lower() in {"1", "true", "yes"}


def _binding_importable(module_path: str, entrypoint: str) -> bool:
    try:
        mod = importlib.import_module(module_path)
        return callable(getattr(mod, entrypoint))
    except Exception:
        return False


def _free_tier_structural(capability_id: int) -> dict[str, Any] | None:
    from bd_platform.free_tier_capabilities import FREE_TIER_CAP_IDS, _EXECUTORS, surface_for

    if capability_id not in FREE_TIER_CAP_IDS:
        return None
    fn = _EXECUTORS.get(capability_id)
    surface = surface_for(capability_id)
    ok = fn is not None and callable(fn) and bool(surface) and not is_generic_surface(surface)
    return {
        "checks": {
            "free_tier_executor": fn is not None,
            "callable": callable(fn) if fn else False,
            "canonical_surface": bool(surface) and not is_generic_surface(surface),
        },
        "verdict": "VERIFIED_COMPLETE" if ok else "FUNCTIONALLY_INCOMPLETE",
    }


def _evidence_slot_verdict(capability_id: int) -> dict[str, Any]:
    if capability_id in EXTERNAL_EVIDENCE_SLOTS:
        from pentest_attestation import verify_pentest_attestation

        attested = verify_pentest_attestation()
        return {
            "verdict": "VERIFIED_COMPLETE" if attested else "EXTERNAL_EVIDENCE_REQUIRED",
            "checks": {"external_attestation": attested},
        }
    if capability_id in SIGNED_INFRA_SLOTS:
        from institutional_assurance import get_signed_capacity, verify_signed_capacity

        cap = get_signed_capacity()
        signed = bool(cap and verify_signed_capacity(cap))
        return {
            "verdict": "VERIFIED_COMPLETE" if signed else "EXTERNAL_EVIDENCE_REQUIRED",
            "checks": {"signed_load_evidence": signed},
        }
    return {}


async def verify_functional_ci_deterministic(
    capability_id: int,
    *,
    user: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if capability_id <= 646:
        return await _verify_cap646_ci(capability_id)
    return await _verify_extension_ci(capability_id)


async def _verify_cap646_ci(capability_id: int) -> dict[str, Any]:
    row = catalog_by_id().get(capability_id, {})
    name = row.get("capability", "")

    if is_external(capability_id):
        return {
            "id": capability_id,
            "verdict": "EXTERNAL_BLOCKED",
            "checks": {"external": True},
            "verification_mode": _VERIFICATION_MODE,
        }

    if is_duplicate(capability_id):
        return {
            "id": capability_id,
            "verdict": "CANONICALLY_COVERED",
            "checks": {"duplicate": True},
            "verification_mode": _VERIFICATION_MODE,
        }

    evidence = _evidence_slot_verdict(capability_id)
    if evidence:
        return {
            "id": capability_id,
            "capability": name,
            "track": row.get("track"),
            "verification_mode": _VERIFICATION_MODE,
            **evidence,
        }

    ft = _free_tier_structural(capability_id)
    if ft is not None:
        return {
            "id": capability_id,
            "capability": name,
            "track": row.get("track"),
            "verification_mode": _VERIFICATION_MODE,
            **ft,
        }

    binding = resolve_binding(capability_id)
    from cap646.runtime import _route_handler

    handler = _route_handler(row.get("track", ""), name, capability_id)
    ui = user_surface_for(capability_id) if capability_id in USER_FACING else None
    ui_ok = ui is not None if capability_id in USER_FACING else None

    importable = _binding_importable(binding.module, binding.entrypoint)
    handler_ok = callable(handler)
    surface_ok = bool(binding.surface) and not is_generic_surface(binding.surface)
    generic_binding = binding.source in {"platform_hash", "generic"}

    checks = {
        "binding_importable": importable,
        "handler_resolved": handler_ok,
        "canonical_surface": surface_ok,
        "no_generic_handler": not generic_binding,
        "user_surface": ui_ok,
    }
    verdict = (
        "VERIFIED_COMPLETE"
        if importable
        and handler_ok
        and surface_ok
        and not generic_binding
        and all(v for k, v in checks.items() if v is not None and v is not False)
        else "FUNCTIONALLY_INCOMPLETE"
    )
    return {
        "id": capability_id,
        "capability": name,
        "track": row.get("track"),
        "verdict": verdict,
        "checks": checks,
        "verification_mode": _VERIFICATION_MODE,
    }


async def _verify_extension_ci(capability_id: int) -> dict[str, Any]:
    row = catalog_978_by_id().get(capability_id, {})
    name = row.get("capability", "")

    if is_external_978(capability_id):
        return {
            "id": capability_id,
            "verdict": "EXTERNAL_BLOCKED",
            "checks": {"external": True},
            "verification_mode": _VERIFICATION_MODE,
        }

    if is_duplicate_978(capability_id):
        return {
            "id": capability_id,
            "verdict": "CANONICALLY_COVERED",
            "checks": {"duplicate": True},
            "verification_mode": _VERIFICATION_MODE,
        }

    ft = _free_tier_structural(capability_id)
    if ft is not None:
        return {
            "id": capability_id,
            "capability": name,
            "track": row.get("track"),
            "verification_mode": _VERIFICATION_MODE,
            **ft,
        }

    binding = resolve_extension_binding(capability_id)
    importable = _binding_importable(binding.module, binding.entrypoint)
    surface_ok = bool(binding.surface) and not is_generic_surface(binding.surface)
    generic_binding = binding.source in {"platform_hash", "generic"}

    checks = {
        "binding_importable": importable,
        "canonical_surface": surface_ok,
        "no_generic_handler": not generic_binding,
    }
    verdict = (
        "VERIFIED_COMPLETE"
        if importable and surface_ok and not generic_binding
        else "FUNCTIONALLY_INCOMPLETE"
    )
    return {
        "id": capability_id,
        "capability": name,
        "track": row.get("track"),
        "verdict": verdict,
        "checks": checks,
        "verification_mode": _VERIFICATION_MODE,
    }
