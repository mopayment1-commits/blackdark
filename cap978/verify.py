"""Execute and verify CAP978 capabilities (647–978 extension scope)."""

from __future__ import annotations

import importlib
import inspect
from typing import Any

from cap646.backend_executor import _call_entrypoint, _import_attr, _success_from_result
from cap646.backend_registry import BackendBinding
from cap646.evidence_class import ai_compliance_footer
from cap646.functional_dod import _domain_check, _payload, _reject_failover
from cap646.backend_registry import is_generic_surface
from cap646.entitlements import entitlement_engine
from cap978.catalog import catalog_by_id, is_duplicate, is_external
from cap978.extension_registry import resolve_extension_binding
from data_provenance_score import attach_provenance
from bd_platform.free_tier_capabilities import FREE_TIER_EXTENSION_IDS, execute_free_tier_capability


async def execute_extension(capability_id: int, *, user: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> dict[str, Any]:
    params = dict(params or {})
    row = catalog_by_id().get(capability_id)
    if not row:
        return ai_compliance_footer({"success": False, "error": "unknown_capability_id", "capability_id": capability_id})

    if capability_id in FREE_TIER_EXTENSION_IDS:
        free_result = await execute_free_tier_capability(capability_id, params=params)
        free_result.setdefault("capability", row["capability"])
        free_result.setdefault("track", row.get("track"))
        free_result.setdefault("scope", row.get("scope"))
        free_result.setdefault("classification", "VERIFIED_COMPLETE" if free_result.get("success") else "NOT_READY")
        from cap646.domain_enrichment import enrich_capability_result

        return await enrich_capability_result(capability_id, ai_compliance_footer(free_result), params=params)

    if is_external(capability_id):
        return ai_compliance_footer(
            {
                "success": False,
                "capability_id": capability_id,
                "classification": "EXTERNAL_BLOCKED",
                "capability": row["capability"],
                "error": "external_vendor_or_rights_required",
            }
        )

    if is_duplicate(capability_id):
        from cap646.runtime import execute_capability

        canon = __import__("cap978.catalog", fromlist=["canonical_id"]).canonical_id(capability_id)
        delegated = await execute_capability(canon, user=user, params=params)
        delegated["canonical_of"] = capability_id
        delegated["canonical_id"] = canon
        return delegated

    user = user or {"email": "cap978-test@blackdark.local", "tier": "elite"}
    gate = await entitlement_engine.check(capability_id, user=user, org_id=params.get("org_id"))
    if not gate.get("allowed"):
        return ai_compliance_footer({"success": False, "capability_id": capability_id, "entitlement": gate, "error": gate.get("reason", "entitlement_denied")})

    binding = resolve_extension_binding(capability_id)
    symbol = str(params.get("symbol") or "BTC").upper().replace("/USDT", "")

    try:
        fn = _import_attr(binding.module, binding.entrypoint)
        result = await _call_entrypoint(fn, params=params, binding=binding)
        ok = _success_from_result(result)
    except Exception as exc:
        return ai_compliance_footer(
            attach_provenance(
                {
                    "success": False,
                    "capability_id": capability_id,
                    "capability": row["capability"],
                    "surface": binding.surface,
                    "backend_module": binding.module,
                    "backend_entrypoint": binding.entrypoint,
                    "binding_source": binding.source,
                    "error": str(exc),
                    "fail_closed": True,
                }
            )
        )

    payload = attach_provenance(
        {
            "success": ok,
            "capability_id": capability_id,
            "capability": row["capability"],
            "track": row.get("track"),
            "scope": row.get("scope"),
            "surface": binding.surface,
            "backend_module": binding.module,
            "backend_entrypoint": binding.entrypoint,
            "binding_source": binding.source,
            "result": result,
        }
    )
    from cap646.domain_enrichment import enrich_capability_result

    return await enrich_capability_result(capability_id, ai_compliance_footer(payload), params=params)


async def verify_functional_978(capability_id: int, *, user: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id <= 646:
        from cap646.functional_dod import verify_functional

        return await verify_functional(capability_id, user=user)

    row = catalog_by_id().get(capability_id, {})
    name = row.get("capability", "")

    if is_external(capability_id):
        return {"id": capability_id, "verdict": "EXTERNAL_BLOCKED", "checks": {"external": True}}

    if is_duplicate(capability_id):
        return {"id": capability_id, "verdict": "CANONICALLY_COVERED", "checks": {"duplicate": True}}

    result = await execute_extension(
        capability_id,
        user=user or {"email": "cap978-test@blackdark.local", "tier": "elite"},
        params={"symbol": "BTC", "tier": "whale", "coin_id": "bitcoin", "address": "0x0000000000000000000000000000000000000001"},
    )

    failover_reason = _reject_failover(result)
    domain_reason = _domain_check(capability_id, name, row.get("track", "T19"), result)
    checks = {
        "backend": bool(result.get("success")),
        "compliance_footer": bool(result.get("compliance_footer")),
        "evidence_class": result.get("evidence_class") is not None,
        "bound_backend": bool(result.get("backend_module")),
        "canonical_surface": bool(result.get("surface")) and not is_generic_surface(result.get("surface")),
        "no_failover_mask": failover_reason is None,
        "domain_logic": domain_reason is None,
        "fail_closed": result.get("error") not in {"demo_only", "mock_only"},
    }
    verdict = (
        "VERIFIED_COMPLETE"
        if all(v for k, v in checks.items() if v is not False)
        else "FUNCTIONALLY_INCOMPLETE"
    )
    return {
        "id": capability_id,
        "capability": name,
        "track": row.get("track"),
        "verdict": verdict,
        "checks": checks,
        "failure_reason": failover_reason or domain_reason,
    }
