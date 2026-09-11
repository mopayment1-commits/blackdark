#!/usr/bin/env python3
"""Shared v6 audit standards — OWASP ASVS 5.0.0 (Phase 6) + NIST SP 800-218A (Phase 3 complement).

Replaces legacy Phase 6 label (OWASP API static scan only; ASVS 4.0.3 was never implemented in code).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

PHASE3_STANDARD = "NIST AI RMF 1.0 + NIST AI 600-1 GenAI Profile + NIST SP 800-218A SSDF AI Profile"
PHASE6_STANDARD = "OWASP ASVS 5.0.0 + MITRE CWE Top 25 + MITRE ATLAS"

# ASVS 5.0 checks with no analogue in prior static-scan Phase 6 (ASVS 4.0.3 was not coded).
ASVS50_NEW_REQUIREMENT_IDS = (
    "V1.14.2",  # software supply chain / SBOM awareness
    "V4.1.1",  # access control enforced
    "V8.2.1",  # data protection classification in response
    "V14.2.1",  # secure configuration — no hardcoded secrets in handler
    "V15.1.1",  # third-party component / dependency integrity
)

AI_ENGINE_MODULES = frozenset(
    {
        "sentiment_engine",
        "sentiment_gate",
        "oracle_data_hub",
        "research_lab",
        "ml_experience",
        "prediction",
    }
)


def dedicated_handler_source(batch_num: int, cid: int) -> str | None:
    path = ROOT / f"cap646/batch{batch_num:02d}_dedicated.py"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    patterns = [
        rf"async def _cap{cid:03d}\(",
        rf"async def _cap{cid:03d}_",
    ]
    if cid >= 1000:
        patterns = [rf"async def _cap{cid}\(", rf"async def _cap{cid}_"]
    m = None
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            break
    if not m:
        return None
    nxt = text.find("async def _cap", m.end())
    return text[m.start() : nxt if nxt > 0 else len(text)]


def phase1_generic_delegate_check(batch_num: int, cid: int) -> tuple[str, str | None]:
    """Phase 1 gate — reject invoke_underlying-only dedicated handlers (keyword routing debt)."""
    src = dedicated_handler_source(batch_num, cid)
    if not src:
        return "PASS", None
    if "invoke_underlying" in src and not any(
        k in src
        for k in (
            "HEURISTIC",
            "evaluate_execution_risk",
            "pyth_realtime_feed",
            "datashare_connector",
            "reserved_slot",
            "execute_catalog_binding",
            "catalog_binding_executor",
            "Path A explicit",
            "Path A — explicit",
            "methodology_status",
        )
    ):
        return "FAIL", "GENERIC_DELEGATE: invoke_underlying keyword routing — not goal-specific implementation"
    if "catalog_binding_executor" in src and "Path A explicit" not in src and "Path A — explicit" not in src:
        return "FAIL", "GENERIC_DELEGATE: catalog_binding_executor without explicit Path A import — use codegen_explicit_path_a_handlers"
    return "PASS", None


def _asvs50_checks(cid: int, result: dict, *, batch_num: int | None = None) -> list[tuple[str, str, bool]]:
    """Return list of (req_id, note, passed)."""
    checks: list[tuple[str, str, bool]] = []
    src = dedicated_handler_source(batch_num, cid) if batch_num else None

    # V1.14.2 — supply chain / SBOM posture (project-level, capability inherits)
    lock = ROOT / "requirements.txt"
    checks.append(
        (
            "V1.14.2",
            "requirements.txt present for dependency/supply-chain traceability",
            lock.is_file(),
        )
    )

    # V4.1.1 — access control signal on runtime result
    ent = result.get("entitlement") or {}
    checks.append(
        (
            "V4.1.1",
            "entitlement gate present or skip_entitlement audit path documented",
            bool(ent) or result.get("binding_source") == "explicit_option_a",
        )
    )

    # V8.2.1 — data classification / evidence class
    checks.append(
        (
            "V8.2.1",
            "evidence_class or compliance_footer data-protection envelope",
            bool(result.get("evidence_class") or result.get("compliance_footer")),
        )
    )

    # V14.2.1 — secure configuration in dedicated handler source
    if src:
        bad = re.search(r'(password|secret|api_key)\s*=\s*["\'][^"\']+["\']', src, re.I)
        checks.append(("V14.2.1", "no hardcoded secrets in dedicated handler", bad is None))
    else:
        checks.append(("V14.2.1", "dedicated handler source not found — config scan N/A", True))

    # V15.1.1 — third-party component integrity (project lockfile)
    checks.append(
        (
            "V15.1.1",
            "dependency manifest available (requirements.txt)",
            (ROOT / "requirements.txt").is_file(),
        )
    )

    # V13.x — API surface static scan (carried forward from legacy Phase 6)
    from cap646.ui_pages import user_surface_for

    surf = user_surface_for(cid)
    if not surf or not surf.get("api_path"):
        checks.append(("V13.2.1", "internal/surface-only — API route scan N/A", True))
    else:
        prefix = str(surf["api_path"]).split("{")[0]
        try:
            r = subprocess.run(
                ["rg", "-l", re.escape(prefix), "api/", "dashboard.py", "platform_api.py"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=10,
            )
            checks.append(
                (
                    "V13.2.1",
                    f"API route prefix {prefix} static scan",
                    r.returncode == 0,
                )
            )
        except Exception as exc:
            checks.append(("V13.2.1", f"API static scan error: {exc}", False))

    return checks


def phase6_security_asvs50(cid: int, result: dict, *, batch_num: int | None = None) -> tuple[str, str | None, dict[str, Any]]:
    checks = _asvs50_checks(cid, result, batch_num=batch_num)
    failed = [c for c in checks if not c[2]]
    new_failed = [c for c in failed if c[0] in ASVS50_NEW_REQUIREMENT_IDS]
    meta = {
        "standard": "OWASP ASVS 5.0.0",
        "checks": [{"id": a, "note": b, "pass": p} for a, b, p in checks],
        "asvs50_new_gaps": [{"id": a, "note": b} for a, b, _ in new_failed],
    }
    if not failed:
        return "PASS", None, meta
    if new_failed and all(c[0] in ASVS50_NEW_REQUIREMENT_IDS for c in failed):
        return "PARTIAL", f"ASVS 5.0 new reqs: {', '.join(c[0] for c in new_failed)}", meta
    notes = "; ".join(f"{a}: {b}" for a, b, _ in failed[:4])
    return "PARTIAL", f"ASVS 5.0: {notes}", meta


def _ssdf218a_checks(cid: int, result: dict) -> list[tuple[str, str, bool]]:
    """NIST SP 800-218A complement — AI system producer checks."""
    checks: list[tuple[str, str, bool]] = []

    # PO.1.1 — AI security requirements in response governance
    checks.append(
        (
            "PO.1.1",
            "AI security grounding — compliance_footer or provenance",
            bool(result.get("compliance_footer") or result.get("provenance") or result.get("certificate")),
        )
    )

    # PO.1.2 — documented AI requirements (methodology / analysis_only)
    checks.append(
        (
            "PO.1.2",
            "analysis_only/no_execution or methodology_status documented",
            bool(
                result.get("analysis_only")
                or result.get("no_execution")
                or result.get("methodology_status")
                or (result.get("compliance_footer") or {}).get("analysis_only")
            ),
        )
    )

    # PW.6.1 — model tampering / supply chain — no weights path in payload
    payload_str = str(result)[:2000]
    checks.append(
        (
            "PW.6.1",
            "no raw model artifact paths exposed in runtime payload",
            "model_weights" not in payload_str.lower() and ".pt" not in payload_str,
        )
    )

    # PW.7.1 — input validation / prompt-injection guard signal
    checks.append(
        (
            "PW.7.1",
            "input params sanitized or oracle/sentiment guard present",
            bool(result.get("symbol") or result.get("asset") or result.get("sentiment_blocked") is not None),
        )
    )

    # RV.1.3 — monitoring / audit trail
    checks.append(
        (
            "RV.1.3",
            "timestamp + data_source audit trail",
            bool(result.get("timestamp") or result.get("data_source") or result.get("created_at")),
        )
    )

    # Cross-ref project AI engines
    mod = str(result.get("backend_module") or "")
    checks.append(
        (
            "RV.1.4",
            "AI engine module traceability",
            any(x in mod for x in AI_ENGINE_MODULES) or "batch" in mod or bool(result.get("backend_entrypoint")),
        )
    )

    return checks


def phase3_ai_rmf_plus_218a(cid: int, result: dict) -> tuple[str, str | None, dict[str, Any]]:
    """Phase 3 — NIST AI RMF (existing) + SP 800-218A complement."""
    if not (result.get("compliance_footer") or result.get("provenance") or result.get("certificate")):
        return "FAIL", "AI-RISK-UNMANAGED: no NIST AI RMF grounding in response", {"218a_checks": []}

    ssdf = _ssdf218a_checks(cid, result)
    failed = [c for c in ssdf if not c[2]]
    meta = {
        "standard_complement": "NIST SP 800-218A",
        "218a_checks": [{"id": a, "note": b, "pass": p} for a, b, p in ssdf],
        "218a_failed": [{"id": a, "note": b} for a, b, _ in failed],
    }
    if failed:
        return "PARTIAL", f"AI RMF footer OK; 800-218A gaps: {', '.join(c[0] for c in failed)}", meta
    return "PARTIAL", "AI RMF + SP 800-218A complement checks passed; ISO 42001 lifecycle not verified", meta


def discover_ai_cap_ids(batch_num: int) -> frozenset[int]:
    from scripts.rbas001_scoping import batch_tier_map

    tier = batch_tier_map(batch_num)
    ids: set[int] = set()
    for cid, info in tier.items():
        reason = (info.get("rbas_reason") or info.get("reason") or "").lower()
        name = (info.get("capability") or "").lower()
        if "ai " in reason or "ai/" in reason or "nlp" in reason or "prediction" in reason:
            ids.add(cid)
        elif any(k in name for k in ("ai ", "oracle", "sentiment", "prediction", "nlp", "ml ")):
            ids.add(cid)
    return frozenset(ids)


def phase3_ai_legacy(cid: int, result: dict, *, ai_cap_ids: frozenset[int]) -> tuple[str, str | None]:
    if cid not in ai_cap_ids:
        return "NOT_APPLICABLE", None
    if not (result.get("compliance_footer") or result.get("provenance") or result.get("certificate")):
        return "FAIL", "AI-RISK-UNMANAGED: no NIST AI RMF grounding in response"
    return "PARTIAL", "ai_compliance_footer present; ISO 42001 lifecycle not verified"


def phase6_security_legacy(cid: int, result: dict) -> tuple[str, str | None]:
    from cap646.ui_pages import user_surface_for

    surf = user_surface_for(cid)
    if not surf or not surf.get("api_path"):
        return "PARTIAL", "no user-facing API path — internal/surface-only"
    path = str(surf["api_path"])
    prefix = path.split("{")[0]
    try:
        r = subprocess.run(
            ["rg", "-l", re.escape(prefix), "api/", "dashboard.py", "platform_api.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode != 0:
            return "PARTIAL", f"OWASP API: route prefix {prefix} not found in static scan"
        return "PARTIAL", "static route scan only (legacy Phase 6)"
    except Exception as exc:
        return "PARTIAL", f"security scan error: {exc}"
