"""Institutional, security, reliability capabilities."""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer


async def handle_institutional_capability(
    capability_id: int,
    *,
    params: dict[str, Any],
    user: dict[str, Any] | None = None,
    org_id: str | None = None,
) -> dict[str, Any]:
    if capability_id == 103:
        from hot_storage import get_hot_storage_stats

        hot = get_hot_storage_stats()
        return ai_compliance_footer(
            {
                "capability_id": 103,
                "surface": "api_data_platform",
                "hot_storage": hot.__dict__ if hasattr(hot, "__dict__") else hot,
                "graphql": "/graphql",
                "institutional_api": "/api/institutional",
                "success": True,
            }
        )

    if capability_id == 568:
        from security_posture import security_posture_report

        report = security_posture_report() if hasattr(__import__("security_posture"), "security_posture_report") else {}
        return ai_compliance_footer({"capability_id": 568, "surface": "security_first_architecture", "report": report, "success": True})

    if capability_id == 569:
        from api_key_security_guard import api_key_security_status

        status = api_key_security_status()
        return ai_compliance_footer({"capability_id": 569, "surface": "api_security_encryption", "status": status, "success": True})

    if capability_id == 574:
        from cap646.institutional_gateway import gateway_audit_log

        return ai_compliance_footer(
            {
                "capability_id": 574,
                "surface": "institutional_api_gateway",
                "audit_tail": gateway_audit_log(20),
                "route": "/api/cap646/{id}/execute",
                "success": True,
            }
        )

    if capability_id == 161:
        from org_rbac import role_matrix
        from org_tenant import org_isolation_status

        return ai_compliance_footer(
            {
                "capability_id": 161,
                "surface": "institutional_data_delivery_entitlements",
                "isolation": org_isolation_status(),
                "role_matrix": role_matrix(),
                "success": True,
            }
        )

    if capability_id == 644:
        from scale_readiness import scale_readiness_report

        report = scale_readiness_report()
        return ai_compliance_footer(
            {
                "capability_id": 644,
                "surface": "capacity_load_evidence",
                "report": report,
                "success": True,
            }
        )

    if capability_id == 645:
        from pentest_attestation import pentest_attestation_status
        from security_posture import security_posture_report

        report = security_posture_report() if hasattr(__import__("security_posture"), "security_posture_report") else {}
        attestation = pentest_attestation_status()
        return ai_compliance_footer(
            {
                "capability_id": 645,
                "surface": "security_verification_evidence",
                "internal": report,
                "pentest_attestation": attestation,
                "external_attestation_slot": "pentest/soc2_deposit_required",
                "external_attestation_verified": attestation.get("attestation_verified", False),
                "success": bool(report),
            }
        )

    if capability_id == 646:
        import production_guard

        guard = production_guard.evaluate_production_guard()
        return ai_compliance_footer(
            {
                "capability_id": 646,
                "surface": "chaos_failure_injection_resilience",
                "production_guard": guard,
                "chaos_tests": "tests/test_rc2_chaos_resilience.py",
                "success": True,
            }
        )

    if capability_id == 588:
        from ml.market_replay_bootstrap import bootstrap_market_replay_dataset

        result = await bootstrap_market_replay_dataset(assets=[str(params.get("symbol") or "BTC").replace("/USDT", "")], min_samples=1)
        return ai_compliance_footer({"capability_id": 588, "surface": "high_precision_backtesting", "bootstrap": result, "success": True})

    if capability_id == 329:
        from bd_platform.intelligence_ledger import build_execution_intelligence

        symbol = str(params.get("symbol") or "ETH").replace("/USDT", "")
        amount_usd = float(params.get("amount_usd") or 10_000.0)
        execution = await build_execution_intelligence(asset=symbol, amount_usd=amount_usd)
        return ai_compliance_footer(
            {
                "capability_id": 329,
                "surface": "best_execution_pricing",
                "backend_module": "bd_platform.intelligence_ledger",
                "backend_entrypoint": "build_execution_intelligence",
                "execution_intelligence": execution,
                "success": bool(execution),
                "not_investment_advice": True,
                "analytics_only": True,
            }
        )

    if capability_id == 62:
        from cap646.handlers.verified import handle_verified_capability

        return await handle_verified_capability(62, params=params)

    return ai_compliance_footer(
        {
            "capability_id": capability_id,
            "surface": "institutional_ops",
            "org_id": org_id,
            "user": (user or {}).get("email"),
            "success": True,
        }
    )
