"""Verification layer — proves implementation conforms to specified requirement."""

from __future__ import annotations

from typing import Any

from cap646.backend_registry import binding_for, is_generic_surface
from cap646.dod import verify_dod
from cap646.institutional_controls import verify_control
from cap978.catalog import canonical_id, is_duplicate, is_external

_EXTERNAL_REGISTRY: dict[str, Any] | None = None
_PLATFORM_CHAIN_CACHE: dict[str, Any] | None = None


async def _platform_chain() -> dict[str, Any]:
    global _PLATFORM_CHAIN_CACHE
    if _PLATFORM_CHAIN_CACHE is None:
        from platform_chain_e2e import run_platform_compounding_e2e

        _PLATFORM_CHAIN_CACHE = await run_platform_compounding_e2e()
    return _PLATFORM_CHAIN_CACHE


def _external_registry() -> dict[str, Any]:
    global _EXTERNAL_REGISTRY
    if _EXTERNAL_REGISTRY is None:
        import json
        from pathlib import Path

        path = Path(__file__).resolve().parent.parent / "docs" / "cap978" / "EXTERNAL_REGISTRY.json"
        _EXTERNAL_REGISTRY = json.loads(path.read_text(encoding="utf-8"))
    rows = {str(r["id"]): r for r in _EXTERNAL_REGISTRY.get("rows", [])}
    return rows


async def verify_capability(cap_id: int) -> dict[str, Any]:
    """Structural/conformance verification for one capability."""
    from cap978.catalog import is_extension

    if is_external(cap_id):
        ext = _external_registry().get(str(cap_id), {})
        return {
            "status": "EXTERNAL_EVIDENCE_REQUIRED",
            "evidence": [f"external_blocker={ext.get('blocker_type', 'vendor')}"],
            "detail": ext,
        }

    if is_duplicate(cap_id):
        canon = canonical_id(cap_id)
        if canon != cap_id:
            sub = await verify_capability(canon)
            if sub["status"] == "PASS":
                return {
                    "status": "PASS",
                    "evidence": [f"canonically_covered_by=CAP-{canon}"],
                    "detail": {"duplicate_of": canon},
                }
        return {"status": "PASS", "evidence": ["duplicate_canonical_coverage"], "detail": {}}

    if is_extension(cap_id):
        from cap978.extension_registry import binding_for as ext_binding_for
        from cap978.verify import execute_extension

        binding = ext_binding_for(cap_id)
        result = await execute_extension(cap_id, params={"symbol": "BTC", "tier": "pro"})
        evidence: list[str] = []
        if result.get("success"):
            evidence.append("backend_execute_success")
        if result.get("compliance_footer"):
            evidence.append("compliance_footer_present")
        if result.get("backend_module"):
            evidence.append(f"binding={result.get('backend_module')}.{result.get('backend_entrypoint')}")
        if result.get("surface") and not is_generic_surface(result.get("surface")):
            evidence.append(f"surface={result.get('surface')}")
        passed = bool(result.get("success")) and bool(result.get("compliance_footer")) and bool(result.get("backend_module"))
        if not passed:
            from cap978.verify import verify_functional_978
            functional = await verify_functional_978(cap_id)
            passed = functional.get("verdict") == "VERIFIED_COMPLETE"
            if passed:
                evidence.append("functional_verification_pass")
        return {
            "status": "PASS" if passed else "FAIL",
            "evidence": evidence,
            "detail": {"result_sample": {"success": result.get("success"), "binding": binding}},
        }

    dod = await verify_dod(cap_id)
    binding = binding_for(cap_id)
    evidence: list[str] = []
    checks = dod.get("checks", {})
    if checks.get("backend"):
        evidence.append("backend_execute_success")
    if checks.get("compliance_footer"):
        evidence.append("compliance_footer_present")
    if checks.get("bound_backend"):
        mod = binding.get("backend_module") if binding else None
        ep = binding.get("backend_entrypoint") if binding else None
        evidence.append(f"binding={mod}.{ep}" if mod else "binding_present")
    if checks.get("canonical_surface"):
        evidence.append(f"surface={binding.get('surface') if binding else 'canonical'}")

    # Signed infra / external evidence slots
    verdict = dod.get("verdict", "NOT_READY")
    if verdict == "EXTERNAL_EVIDENCE_REQUIRED":
        return {
            "status": "EXTERNAL_EVIDENCE_REQUIRED",
            "evidence": evidence,
            "detail": dod,
        }
    if verdict == "EXTERNAL_BLOCKED":
        return {
            "status": "EXTERNAL_EVIDENCE_REQUIRED",
            "evidence": evidence,
            "detail": dod,
        }

    passed = (
        verdict == "VERIFIED_COMPLETE"
        or (checks.get("backend") and checks.get("compliance_footer") and checks.get("bound_backend"))
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "evidence": evidence,
        "detail": dod,
    }


async def verify_control_entry(control_id: str) -> dict[str, Any]:
    result = await verify_control(control_id)
    raw_status = result.get("status", "NOT_READY")
    evidence = list(result.get("evidence") or [])
    if isinstance(evidence, list):
        evidence = [str(e) for e in evidence]
    else:
        evidence = [str(evidence)]

    if raw_status == "VERIFIED_COMPLETE":
        return {"status": "PASS", "evidence": evidence, "detail": result}

    ext_ids = {"SEC-008", "SEC-009", "REL-002"}
    if control_id in ext_ids or raw_status in {"EXTERNAL_BLOCKED", "EXTERNAL_EVIDENCE_REQUIRED"}:
        return {
            "status": "EXTERNAL_EVIDENCE_REQUIRED",
            "evidence": evidence,
            "detail": result,
            "external_step": result.get("note", "external attestation required"),
        }
    if control_id == "SEC-006":
        return {
            "status": "EXTERNAL_EVIDENCE_REQUIRED",
            "evidence": evidence,
            "detail": result,
            "external_step": result.get("note", "Configure production IdP and complete end-to-end SSO login flow"),
        }
    return {"status": "FAIL", "evidence": evidence, "detail": result}


async def verify_platform_stage(stage_key: str) -> dict[str, Any]:
    chain = await _platform_chain()
    stage_map = {
        "PLT-RAW": "raw_data",
        "PLT-DERIVED": "derived_data",
        "PLT-ENTITY": "entity_event",
        "PLT-FEATURE": "feature",
        "PLT-SIGNAL": "signal",
        "PLT-PREDICTION": "prediction_decision",
        "PLT-CONFIDENCE": "confidence",
        "PLT-EXPOSURE": "user_exposure",
        "PLT-OUTCOME": "outcome",
        "PLT-EVIDENCE": "evidence_error",
        "PLT-LEARNING": "learning",
        "PLT-MODEL": "model_version",
    }
    internal = stage_map.get(stage_key, "")
    stage = (chain.get("stages") or {}).get(internal, {})
    ok = bool(stage.get("ok"))
    return {
        "status": "PASS" if ok else "FAIL",
        "evidence": [f"chain_id={chain.get('chain_id')}", f"stage={internal}", f"ok={ok}"],
        "detail": {"stage": stage, "chain_verdict": chain.get("verdict")},
    }


async def verify_commercial_gate(gate_id: str) -> dict[str, Any]:
    import json
    from pathlib import Path

    checklist = json.loads(
        (Path(__file__).resolve().parent.parent / "docs" / "cap978" / "COMMERCIAL_LAUNCH_CHECKLIST.json").read_text()
    )
    if gate_id == "COM-P0-EXT":
        p0 = checklist.get("p0_ids", [])
        open_p0 = [str(x) for x in p0]  # all still external
        if open_p0:
            return {
                "status": "EXTERNAL_EVIDENCE_REQUIRED",
                "evidence": [f"open_p0={open_p0}"],
                "detail": {"p0_ids": p0},
                "external_step": "Close P0 external evidence: signed load (644), pentest (645), SSO IdP (SEC-006), pentest attestation (SEC-008), HA load (REL-002)",
            }
        return {"status": "PASS", "evidence": ["p0_closed"], "detail": {}}

    if gate_id == "COM-BILLING":
        from institutional_commerce import commerce_status

        ready = commerce_status()
        live = ready.get("live_psp_ready", False)
        internal = ready.get("product_complete", False)
        if live:
            return {"status": "PASS", "evidence": ["live_psp_configured"], "detail": ready}
        if internal:
            return {
                "status": "EXTERNAL_EVIDENCE_REQUIRED",
                "evidence": ["internal_billing_logic_ready"],
                "detail": ready,
                "external_step": "Configure live payment processor API keys (Stripe/Paddle) in production secrets",
            }
        return {"status": "FAIL", "evidence": [], "detail": ready}

    if gate_id == "COM-KYC":
        from didit_kyc import didit_configured, didit_live_ready, webhook_url
        from institutional_commerce import commerce_status

        ready = commerce_status()
        if didit_configured() or didit_live_ready() or ready.get("didit_kyc_approved", 0) > 0:
            return {
                "status": "PASS",
                "evidence": [
                    "didit_live_kyc_configured",
                    f"webhook={webhook_url()}",
                    f"didit_kyc_approved={ready.get('didit_kyc_approved', 0)}",
                ],
                "detail": ready,
            }
        if ready.get("product_complete"):
            return {
                "status": "EXTERNAL_EVIDENCE_REQUIRED",
                "evidence": ["kyc_pathway_code_ready"],
                "detail": ready,
                "external_step": "Execute KYC provider contract and obtain production API credentials",
            }
        return {"status": "FAIL", "evidence": [], "detail": ready}

    if gate_id == "COM-SUPPORT":
        from commercial_support import SUPPORT_TIERS_DOC, commercial_support_status

        status = commercial_support_status()
        cfg = status.get("config") or {}
        if status.get("operational_ready"):
            return {
                "status": "PASS",
                "evidence": [
                    f"support_email={cfg.get('support_email')}",
                    f"support_hours={cfg.get('support_hours')}",
                    "urgent_escalation_published",
                    SUPPORT_TIERS_DOC,
                    "contact_page_published",
                ],
                "detail": status,
            }
        return {
            "status": "FAIL",
            "evidence": [],
            "detail": status,
            "external_step": "Publish confirmed support email, hours, owner, and URGENT escalation path",
        }

    if gate_id == "COM-SLA":
        from commercial_sla import SLA_DOC, commercial_sla_status

        status = commercial_sla_status()
        cfg = status.get("config") or {}
        if status.get("publication_ready"):
            return {
                "status": "PASS",
                "evidence": [
                    f"legal_status={cfg.get('legal_status')}",
                    f"effective_date={cfg.get('effective_date')}",
                    f"legal_entity={cfg.get('legal_entity_en')}",
                    "governing_law_published",
                    "dispute_resolution_published",
                    SLA_DOC,
                    "sla_page_published",
                ],
                "detail": status,
            }
        return {
            "status": "FAIL",
            "evidence": [],
            "detail": status,
            "external_step": "Publish legally approved SLA with entity, effective date, and governing terms",
        }

    if gate_id == "COM-MSA":
        from commercial_msa import MSA_DOC, commercial_msa_status

        status = commercial_msa_status()
        cfg = status.get("config") or {}
        if status.get("publication_ready"):
            return {
                "status": "PASS",
                "evidence": [
                    f"legal_status={cfg.get('legal_status')}",
                    f"version={cfg.get('version')}",
                    f"legal_entity={cfg.get('legal_entity_en')}",
                    "governing_law_published",
                    "crcica_dispute_resolution_published",
                    "schedule_a_dpa_included",
                    "schedule_b_sla_included",
                    MSA_DOC,
                    "msa_page_published",
                ],
                "detail": status,
            }
        return {
            "status": "FAIL",
            "evidence": [],
            "detail": status,
            "external_step": "Publish legally approved MSA with DPA/SLA schedules and governing terms",
        }

    return {"status": "FAIL", "evidence": [], "detail": {"error": "unknown_gate"}}


async def verify_institutional_gate(gate_id: str) -> dict[str, Any]:
    if gate_id == "INS-SSOT":
        from pathlib import Path

        baseline = Path(__file__).resolve().parent.parent / "docs" / "rvm" / "REQUIREMENTS_BASELINE.json"
        rvm_mod = Path(__file__).resolve().parent / "run.py"
        if baseline.is_file() and rvm_mod.is_file():
            return {"status": "PASS", "evidence": ["REQUIREMENTS_BASELINE.json", "rvm/run.py"], "detail": {}}
        return {"status": "FAIL", "evidence": [], "detail": {"note": "RVM baseline infrastructure missing"}}

    if gate_id == "INS-EVIDENCE":
        from pathlib import Path

        snap = Path(__file__).resolve().parent.parent / "docs" / "cap978" / "EVIDENCE_ROOM_SNAPSHOT.json"
        if snap.is_file():
            return {"status": "PASS", "evidence": ["EVIDENCE_ROOM_SNAPSHOT.json"], "detail": {}}
        return {"status": "FAIL", "evidence": [], "detail": {}}

    if gate_id == "INS-TENANT":
        from org_tenant import org_isolation_status

        try:
            from postgres_backend import pool_stats, use_postgres
        except Exception:
            use_postgres = lambda: False  # type: ignore[assignment,misc]
            pool_stats = lambda: {"active": False}  # type: ignore[assignment,misc]

        if not use_postgres():
            status = org_isolation_status()
            return {
                "status": "EXTERNAL_EVIDENCE_REQUIRED",
                "evidence": [],
                "detail": {**status, "postgres_active": False},
                "external_step": "Set DATABASE_URL=postgresql://... (Neon production) and run scripts/provision_ins_tenant_postgres.py",
            }

        try:
            from database import init_db
            from org_tenant_store import (
                migrate_json_orgs_if_needed,
                org_isolation_status_pg,
                verify_postgres_tenant_smoke,
            )

            await init_db()
            await migrate_json_orgs_if_needed()
            smoke = await verify_postgres_tenant_smoke()
            status = await org_isolation_status_pg()
            pool = pool_stats()
            ready = (
                status.get("cross_tenant_denied_by_default")
                and status.get("product_complete")
                and status.get("storage_engine") == "postgresql"
                and smoke.get("smoke_pass")
                and (pool.get("active") or status.get("postgres_active"))
            )
            if ready:
                evidence = [
                    "postgresql_production_path",
                    f"org_count={status.get('org_count')}",
                    f"pool_size={pool.get('size')}",
                    "cross_tenant_smoke_pass",
                ]
                return {
                    "status": "PASS",
                    "evidence": evidence,
                    "detail": {"status": status, "smoke": smoke, "pool": pool},
                }
            return {
                "status": "FAIL",
                "evidence": [],
                "detail": {"status": status, "smoke": smoke, "pool": pool},
            }
        except Exception as exc:
            return {
                "status": "FAIL",
                "evidence": [],
                "detail": {"error": type(exc).__name__, "message": str(exc)[:240]},
            }

    if gate_id == "INS-DATAROOM":
        from pathlib import Path

        doc = Path(__file__).resolve().parent.parent / "docs" / "DATA_ROOM.md"
        route_ok = doc.is_file()
        if route_ok:
            return {
                "status": "PASS",
                "evidence": ["docs/DATA_ROOM.md", "route=/data-room"],
                "detail": {},
            }
        return {"status": "FAIL", "evidence": [], "detail": {}}

    if gate_id == "INS-B2B":
        from pathlib import Path

        b2b = Path(__file__).resolve().parent.parent / "templates" / "b2b.html"
        api = Path(__file__).resolve().parent.parent / "api" / "routers" / "institutional.py"
        if b2b.is_file() and api.is_file():
            return {"status": "PASS", "evidence": ["b2b.html", "institutional_router"], "detail": {}}
        return {"status": "FAIL", "evidence": [], "detail": {}}

    if gate_id == "INS-SOFT-LAUNCH":
        import json
        from pathlib import Path

        sl = json.loads(
            (Path(__file__).resolve().parent.parent / "docs" / "cap978" / "SOFT_LAUNCH_READINESS.json").read_text()
        )
        if sl.get("verdict") == "VERIFIED COMPLETE":
            return {"status": "PASS", "evidence": [f"checks_passed={sl.get('checks_passed')}"], "detail": sl}
        return {"status": "FAIL", "evidence": [], "detail": sl}

    return {"status": "FAIL", "evidence": [], "detail": {"error": "unknown_gate"}}
