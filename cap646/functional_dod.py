"""Functional Definition of Done — domain logic, not generic handlers."""

from __future__ import annotations

import re
from typing import Any

from cap646.catalog import catalog_by_id, is_duplicate, is_external
from cap646.backend_registry import is_generic_surface
from cap646.runtime import execute_capability
from cap646.waves import EXTERNAL_EVIDENCE_SLOTS, SIGNED_INFRA_SLOTS, USER_FACING
from cap646.ui_pages import user_surface_for


def _payload(result: dict[str, Any]) -> dict[str, Any]:
    inner = result.get("result")
    return inner if isinstance(inner, dict) else result


def _reject_failover(result: dict[str, Any]) -> str | None:
    if result.get("failover_module"):
        return "failover_to_unrelated_module"
    if result.get("readiness") and not result.get("result"):
        return "generic_readiness_only"
    if is_generic_surface(result.get("surface")):
        return "generic_surface"
    return None


def _domain_check(capability_id: int, name: str, track: str, result: dict[str, Any]) -> str | None:
    nl = name.lower()
    data = _payload(result)

    if "order book" in nl or "depth" in nl or "liquidity" in nl:
        book_keys = ("book", "order_book", "depth", "bids", "asks", "liquidity")
        if not any(result.get(k) or data.get(k) for k in book_keys):
            return "missing_order_book_payload"
    if "ohlcv" in nl or "candle" in nl or "price history" in nl:
        if not (data.get("ohlcv") or result.get("ohlcv") or data.get("bars") or result.get("bars")):
            if "ohlcv" in nl:
                return "missing_ohlcv_payload"
    if "gas" in nl and "cost" in nl:
        if result.get("gas_usd") is None and data.get("gas_usd") is None:
            return "missing_gas_truth"
    if "alert" in nl:
        if not any(k in result or k in data for k in ("engine", "alerts", "inbox", "alert", "context")):
            return "missing_alert_payload"
    if "provenance" in nl or ("data quality" in nl and capability_id in {478, 525, 636}):
        prov_keys = ("provenance", "provenance_sample", "data_provenance", "lineage", "provenance_score")
        if not any(result.get(k) or data.get(k) for k in prov_keys):
            return "missing_data_provenance_surface"
    if "decision" in nl or "certificate" in nl:
        if "certificate" not in result and "certificate" not in data:
            if capability_id in {641, 642}:
                return "missing_decision_certificate"
    if re.search(r"\barbitrage\b", nl):
        if not any(k in result or k in data for k in ("scan", "opportunities", "verdict")):
            if track in {"T06", "T07"} and capability_id not in {584}:
                return "missing_arbitrage_payload"
    return None


async def verify_functional(
    capability_id: int,
    *,
    user: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = catalog_by_id().get(capability_id, {})
    name = row.get("capability", "")

    if is_external(capability_id):
        return {"id": capability_id, "verdict": "EXTERNAL_BLOCKED", "checks": {"external": True}}

    if is_duplicate(capability_id):
        return {"id": capability_id, "verdict": "CANONICALLY_COVERED", "checks": {"duplicate": True}}

    if capability_id in EXTERNAL_EVIDENCE_SLOTS:
        from pentest_attestation import verify_pentest_attestation

        attested = verify_pentest_attestation()
        return {
            "id": capability_id,
            "verdict": "VERIFIED_COMPLETE" if attested else "EXTERNAL_EVIDENCE_REQUIRED",
            "checks": {"external_attestation": attested},
        }

    if capability_id in SIGNED_INFRA_SLOTS:
        result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "BTC"})
        signed = bool((result.get("report") or {}).get("signed_load_evidence", {}).get("present"))
        return {
            "id": capability_id,
            "verdict": "VERIFIED_COMPLETE" if signed else "EXTERNAL_EVIDENCE_REQUIRED",
            "checks": {"signed_load_evidence": signed},
        }

    result = await execute_capability(
        capability_id,
        skip_entitlement=False,
        user=user or {"email": "functional-test@blackdark.local", "tier": "whale"},
        params={"symbol": "BTC", "tier": "whale"},
    )

    failover_reason = _reject_failover(result)
    domain_reason = _domain_check(capability_id, name, row.get("track", ""), result)
    ui = user_surface_for(capability_id) if capability_id in USER_FACING else None
    ui_ok = ui is not None if capability_id in USER_FACING else None

    checks = {
        "backend": bool(result.get("success")),
        "compliance_footer": bool(result.get("compliance_footer")),
        "evidence_class": result.get("evidence_class") is not None,
        "bound_backend": bool(result.get("backend_module")),
        "canonical_surface": bool(result.get("surface")) and not is_generic_surface(result.get("surface")),
        "no_failover_mask": failover_reason is None,
        "domain_logic": domain_reason is None,
        "user_surface": ui_ok,
        "fail_closed": result.get("error") not in {"demo_only", "mock_only"},
    }

    verdict = (
        "VERIFIED_COMPLETE"
        if not any(v is False for v in checks.values() if v is not None)
        and all(v for v in checks.values() if v is not None)
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


async def verify_functional_wave(wave_ids: tuple[int, ...]) -> dict[str, Any]:
    rows = [await verify_functional(cid) for cid in wave_ids]
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    return {"total": len(rows), "counts": counts, "rows": rows}
