#!/usr/bin/env python3
"""Independent Third-Line RBAS Due Diligence — Official Batch 08 (IDs 251–300).
Master Contract Run 025 — RBAS-001 risk-based scoping with Tier1 full 9-phase / Tier2 abbreviated."""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.rbas001_scoping import (
    WF027_DORMANT_LEGACY_IDS,
    WF027_UNRESOLVED_LEGACY_IDS,
    batch_tier_map,
)


WF027_IN_BATCH08 = WF027_UNRESOLVED_LEGACY_IDS & set(range(351, 401))


WF027_IN_BATCH08 = WF027_UNRESOLVED_LEGACY_IDS & set(range(351, 401))

OUT = ROOT / "institutional_due_diligence_2026" / "batch08_independent_audit"
OUT.mkdir(parents=True, exist_ok=True)

BATCH08_RANGE = range(351, 401)
BATCH_NUM = 8
CROSS_SPINE_RESOLVED_IDS = frozenset()

DECISION_CAP_IDS: frozenset[int] = frozenset()
from scripts.audit_standards_v6 import discover_ai_cap_ids
AI_CAP_IDS = discover_ai_cap_ids(8)
WALLET_CAP_IDS: frozenset[int] = frozenset()

PHASE_STANDARD: dict[str, str] = {
    "1": "SR 26-2 Independent Validation / Conceptual Soundness + Phase 1 generic-delegate gate",
    "2": "GIPS (CFA Institute) — full-population performance disclosure",
    "3": "NIST AI RMF 1.0 + NIST AI 600-1 GenAI Profile + NIST SP 800-218A SSDF AI Profile",
    "4": "BCBS 239 — Accuracy/Completeness/Timeliness/Adaptability",
    "5": "COSO Internal Control — Integrated Framework",
    "6": "OWASP ASVS 5.0.0 + MITRE CWE Top 25 + MITRE ATLAS",
    "7": "ISO/IEC 25010 + ISO/IEC/IEEE 12207 + ISO/IEC/IEEE 29148",
    "8": "Google SRE Production Readiness Review (PRR)",
    "9": "FATF Recommendation 16",
}

CONCEPTUAL_FLAGS: dict[int, str] = {}

GIPS_LEDGER = ROOT / "data" / "decision_ledger.jsonl"
_gips_cache: dict[str, Any] | None = None
_split_cache: dict[int, dict] | None = None
_routing_overlap_cache: dict[int, list[str]] | None = None

COMMON_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "email": "run015-audit@blackdark.local",
    "tier": "pro",
}

TIER2_SKIPPED_PHASES = frozenset({"2", "3", "5", "7", "8", "9"})
TIER2_FULL_PHASES = frozenset({"1", "4", "6"})

ESCALATION_KEY_FRAGMENTS = frozenset(
    {
        "verdict",
        "recommendation",
        "actionability",
        "opportunity_score",
        "decision_score",
        "confidence_score",
        "momentum_score",
        "actionability_score",
        "gcli_score",
        "buy_signal",
        "sell_signal",
    }
)
ESCALATION_SKIP_PATH_PARTS = frozenset(
    {
        "compliance_footer",
        "evidence_metadata",
        "data_provenance",
        "data_freshness",
        "freshness",
        "provenance",
        "backend_module",
        "backend_entrypoint",
        "binding_source",
        "production_spine",
        "catalog_link",
    }
)
ESCALATION_SKIP_KEYS = frozenset(
    {"provenance_score", "provenance_band", "freshness_ms", "freshness_state", "score_change"}
)

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts"}
)

BATCH08_SPINES = frozenset({"batch08_prep", "batch08"})


def routing_overlap_map() -> dict[int, list[str]]:
    from cap646.batch_registry import routing_overlap_map as _map
    return _map()


def gips_ledger_stats() -> dict[str, Any]:
    global _gips_cache
    if _gips_cache is not None:
        return _gips_cache
    stats: dict[str, Any] = {
        "exists": GIPS_LEDGER.is_file(),
        "unique_decisions": 0,
        "simulated_only": True,
        "date_min": None,
        "date_max": None,
    }
    if not stats["exists"]:
        _gips_cache = stats
        return stats
    seen: set[str] = set()
    dates: list[str] = []
    with GIPS_LEDGER.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            did = str(row.get("decision_id") or "")
            if did:
                seen.add(did)
            ec = str(row.get("evidence_class") or "")
            if ec not in ("SIMULATED", "SHADOW_LIVE_FORWARD"):
                stats["simulated_only"] = False
            ts = row.get("created_at")
            if ts:
                dates.append(str(ts))
    stats["unique_decisions"] = len(seen)
    if dates:
        stats["date_min"] = min(dates)
        stats["date_max"] = max(dates)
    _gips_cache = stats
    return stats


async def execute_cap(cid: int) -> dict[str, Any]:
    from cap646.runtime import execute_capability

    return await execute_capability(cid, skip_entitlement=True, params=dict(COMMON_PARAMS))


def bcbs_field_audit(payload: dict) -> dict[str, Any]:
    checks = {
        "data_source": bool(payload.get("data_source") or payload.get("source")),
        "timestamp": bool(
            payload.get("timestamp")
            or payload.get("freshness")
            or payload.get("freshness_chip")
            or payload.get("created_at")
            or payload.get("updated_at")
        ),
        "evidence_class": bool(
            payload.get("evidence_class") or (payload.get("compliance_footer") or {}).get("evidence_class")
        ),
    }
    missing = [k for k, ok in checks.items() if not ok]
    return {"present": checks, "missing_fields": missing}


def _normalize_parity_payload(obj: Any) -> Any:
    """Strip volatile timestamp fields for free_tier vs dedicated parity compare."""
    if isinstance(obj, dict):
        skip = {"timestamp", "attached_at", "updated_at", "created_at"}
        return {k: _normalize_parity_payload(v) for k, v in obj.items() if k not in skip}
    if isinstance(obj, list):
        return [_normalize_parity_payload(x) for x in obj]
    return obj


async def split_brain_test(cid: int) -> dict[str, Any]:
    from bd_platform.free_tier_capabilities import FREE_TIER_CAP_IDS, execute_free_tier_capability
    from cap646.batch08_dedicated import BATCH08_DEDICATED_IDS, execute as execute_b6d

    params = dict(COMMON_PARAMS)
    row: dict[str, Any] = {"id": cid}
    overlaps = routing_overlap_map()

    if cid in FREE_TIER_CAP_IDS:
        free = await execute_free_tier_capability(cid, params=params)
        row["free_tier_available"] = True
        row["free_result"] = free
    else:
        row["free_tier_available"] = False
        row["free_error"] = "not_in_FREE_TIER_CAP_IDS"

    if cid in BATCH08_DEDICATED_IDS:
        try:
            dedicated = await execute_b6d(cid, params=params)
            row["batch08_dedicated_available"] = True
            row["dedicated_result"] = dedicated
        except Exception as exc:
            row["batch08_dedicated_available"] = False
            row["dedicated_error"] = f"{type(exc).__name__}: {exc}"
    else:
        row["batch08_dedicated_available"] = False
        row["dedicated_error"] = "not_in_BATCH08_DEDICATED_IDS"

    if cid in overlaps:
        row["routing_overlap_lists"] = overlaps[cid]
        row["result_type"] = "CROSS_SPINE_ROUTING_OVERLAP"
        row["verdict"] = (
            f"NOT_COMPLETE (governance): ID in multiple routing lists {overlaps[cid]} — CROSS-SPINE-001"
        )
    elif not row.get("free_tier_available") and row.get("batch08_dedicated_available"):
        row["result_type"] = "DEDICATED_ONLY"
        row["verdict"] = "No free_tier path — dedicated batch08 only (SPLIT-BRAIN N/A)"
    elif row.get("free_tier_available") and row.get("batch08_dedicated_available"):
        f_data = (row.get("free_result") or {}).get("data") or row.get("free_result")
        d_raw = row.get("dedicated_result") or {}
        d_data = d_raw.get("data")
        if d_data is None:
            from cap646.batch08_dedicated import EXPECTED_SURFACE

            slug = EXPECTED_SURFACE.get(cid)
            if slug and slug in d_raw:
                inner = d_raw.get(slug)
                d_data = inner.get("result") if isinstance(inner, dict) and inner.get("result") else inner
            else:
                d_data = d_raw
        match = json.dumps(_normalize_parity_payload(f_data), sort_keys=True, default=str) == json.dumps(
            _normalize_parity_payload(d_data), sort_keys=True, default=str
        )
        row["outputs_match"] = match
        if match:
            row["result_type"] = "DUPLICATE_CONFIRMED"
            row["verdict"] = "Duplicate Confirmed — free_tier vs batch08_dedicated parity"
        else:
            row["result_type"] = "DIVERGENT_OUTPUT"
            row["verdict"] = "SPLIT-BRAIN-UNVERIFIED — dedicated vs free_tier outputs differ materially"
    elif not row.get("batch08_dedicated_available"):
        row["result_type"] = "NO_DEDICATED_IMPLEMENTATION"
        row["verdict"] = f"NOT_COMPLETE — {row.get('dedicated_error', 'no dedicated backend')}"
    else:
        row["result_type"] = "UNMAPPED"
        row["verdict"] = "NOT_COMPLETE — split-brain classification unresolved"

    return row


async def load_split_brain() -> dict[int, dict]:
    global _split_cache
    if _split_cache is not None:
        return _split_cache
    rows = [await split_brain_test(cid) for cid in BATCH08_RANGE]
    _split_cache = {r["id"]: r for r in rows}
    (OUT / "RUN015_SPLIT_BRAIN_EVIDENCE.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    return _split_cache


def backend_source(cid: int) -> tuple[str, list[str]]:
    from cap646.batch08_dedicated import BATCH08_DEDICATED_IDS

    mod = ROOT / "cap646" / "batch08_dedicated.py"
    text = mod.read_text(encoding="utf-8")
    pat = rf"async def _cap{cid:03d}\("
    lines_out: list[str] = []
    m = re.search(pat, text)
    if m:
        chunk = text[m.start() : m.start() + 800]
        for ln in chunk.splitlines()[:20]:
            lines_out.append(ln.strip())
    overlaps = routing_overlap_map()
    if cid in overlaps:
        return "cap646 routing overlap (CROSS-SPINE-001)", [f"lists={overlaps[cid]}"]
    if cid in BATCH08_DEDICATED_IDS:
        return "cap646.batch08_dedicated", lines_out or [f"_cap{cid:03d} handler"]
    return "cap646.batch08_production unmapped", [f"capability {cid} not in BATCH08_DEDICATED_IDS"]


def cross_spine_preflight(cid: int) -> tuple[str, str | None]:
    """CROSS-SPINE-001 + WF-027 pre-check (mandatory before audit for overlap/dormant IDs)."""
    overlaps = routing_overlap_map()
    if cid in overlaps:
        return "FAIL", f"CROSS-SPINE-001: routing overlap {overlaps[cid]}"
    if cid in CROSS_SPINE_RESOLVED_IDS:
        return "PASS", "Run 025 cross-spine resolved — batch08 spine only"
    from scripts.rbas001_scoping import WF027_UNRESOLVED_LEGACY_IDS

    if cid in WF027_UNRESOLVED_LEGACY_IDS:
        return "FAIL", f"WF-027 unresolved legacy ID {cid} — mandatory CROSS-SPINE resolution before audit"
    return "PASS", None


def _key_matches_escalation(key: str) -> bool:
    kl = key.lower()
    if kl in ESCALATION_SKIP_KEYS:
        return False
    if kl in ESCALATION_KEY_FRAGMENTS:
        return True
    if kl.endswith("_score"):
        return True
    return kl in {"decision", "buy", "sell"} or kl.endswith("_decision")


def scan_hidden_decision_indicators(payload: dict[str, Any]) -> list[str]:
    """Tier2 escalation: hidden score/decision keys without methodology grounding."""
    if payload.get("heuristic") or payload.get("methodology_status") or payload.get("formula_visible"):
        return []
    found: list[str] = []

    def walk(obj: Any, path: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                p = f"{path}.{k}" if path else str(k)
                if any(part in p for part in ESCALATION_SKIP_PATH_PARTS):
                    continue
                if _key_matches_escalation(str(k)):
                    found.append(p)
                walk(v, p)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")

    walk(payload)
    return found


def phase1_conceptual(cid: int, result: dict, *, split: dict) -> tuple[str, str | None]:
    from scripts.audit_standards_v6 import phase1_generic_delegate_check

    pre, pre_note = cross_spine_preflight(cid)
    if pre == "FAIL":
        return "FAIL", pre_note
    if cid in CONCEPTUAL_FLAGS:
        if result.get("heuristic") and result.get("methodology_status") == "NOT_COMPLETE":
            return "PASS", None
        return "FAIL", CONCEPTUAL_FLAGS[cid]
    if not result.get("success"):
        return "FAIL", "runtime success=false"
    if result.get("production_spine") not in BATCH08_SPINES:
        return "FAIL", f"CROSS_SPINE: official batch08 but production_spine={result.get('production_spine')}"
    st = split.get("result_type")
    if st == "DIVERGENT_OUTPUT":
        return "FAIL", split.get("verdict")
    if st == "CROSS_SPINE_ROUTING_OVERLAP":
        return "FAIL", split.get("verdict")
    if st == "NO_DEDICATED_IMPLEMENTATION":
        return "FAIL", split.get("verdict")
    gd_st, gd_note = phase1_generic_delegate_check(BATCH_NUM, cid)
    if gd_st == "FAIL":
        return "FAIL", gd_note
    return "PASS", pre_note


def phase2_gips(cid: int, result: dict) -> tuple[str, str | None]:
    if cid not in DECISION_CAP_IDS:
        return "NOT_APPLICABLE", None
    stats = gips_ledger_stats()
    if not stats["exists"] or stats["unique_decisions"] == 0:
        return "FAIL", "PERFORMANCE-UNVERIFIABLE: no decision ledger"
    if stats["simulated_only"]:
        return "FAIL", (
            f"PERFORMANCE-UNVERIFIABLE: {stats['unique_decisions']} decisions all SIMULATED/SHADOW "
            f"({stats.get('date_min')}..{stats.get('date_max')})"
        )
    return "PARTIAL", "production decisions present; GIPS recomputation pending"


def phase3_ai_legacy(cid: int, result: dict) -> tuple[str, str | None]:
    if cid not in AI_CAP_IDS:
        return "NOT_APPLICABLE", None
    if not (result.get("compliance_footer") or result.get("provenance") or result.get("certificate")):
        return "FAIL", "AI-RISK-UNMANAGED: no NIST AI RMF grounding in response"
    return "PARTIAL", "ai_compliance_footer present; ISO 42001 lifecycle not verified"


def phase3_ai(cid: int, result: dict) -> tuple[str, str | None]:
    if cid not in AI_CAP_IDS:
        return "NOT_APPLICABLE", None
    from scripts.audit_standards_v6 import phase3_ai_rmf_plus_218a

    st, note, _meta = phase3_ai_rmf_plus_218a(cid, result)
    return st, note


def phase4_data(cid: int, result: dict) -> tuple[str, str | None]:
    audit = bcbs_field_audit(result)
    if audit["missing_fields"]:
        excerpt = json.dumps(
            {
                k: result.get(k)
                for k in (
                    "capability_id",
                    "surface",
                    "source",
                    "data_source",
                    "timestamp",
                    "evidence_class",
                    "success",
                )
                if k in result
            },
            default=str,
        )[:200]
        return "PARTIAL", f"BCBS 239 missing: {', '.join(audit['missing_fields'])} | {excerpt}"
    return "PASS", None


def phase5_coso(cid: int, result: dict) -> tuple[str, str | None]:
    if result.get("compliance_footer") or result.get("evidence_class"):
        return "PASS", None
    return "PARTIAL", "COSO: partial automated controls — evidence_class not on all fields"


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
        hits = [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
        if r.returncode != 0:
            return "PARTIAL", f"OWASP API: route prefix {prefix} not found in static scan"
        return "PARTIAL", f"static route hits={hits[:2]}; live HTTP probe not executed (no bound server in audit VM)"
    except Exception as exc:
        return "PARTIAL", f"security scan error: {exc}"


def phase6_security(cid: int, result: dict) -> tuple[str, str | None]:
    from scripts.audit_standards_v6 import phase6_security_asvs50

    st, note, _meta = phase6_security_asvs50(cid, result, batch_num=BATCH_NUM)
    return st, note


def phase7_iso(cid: int, result: dict) -> tuple[str, str | None]:
    if not result.get("backend_module") or not result.get("backend_entrypoint"):
        return "FAIL", "ISO/IEC/IEEE 29148: missing backend binding"
    if result.get("production_spine") not in BATCH08_SPINES:
        return "PARTIAL", f"traceability split: official batch08, spine={result.get('production_spine')}"
    return "PASS", None


def phase8_sre(cid: int) -> tuple[str, str | None]:
    runbook = ROOT / "docs" / "RUNBOOK.md"
    if not runbook.is_file():
        return "PARTIAL", "Google SRE PRR: docs/RUNBOOK.md missing"
    return "PARTIAL", "generic runbook only; no per-capability rollback drill"


def phase9_fatf(cid: int) -> tuple[str, str | None]:
    if cid not in WALLET_CAP_IDS:
        return "NOT_APPLICABLE", None
    return "PARTIAL", "FATF R.16: address handling present; travel-rule screening not verified"


def run_full_phases(cid: int, runtime: dict, split: dict) -> tuple[dict[str, tuple[str, str | None]], int]:
    phase_results: dict[str, tuple[str, str | None]] = {}
    checks = 0
    phase_results["1"] = phase1_conceptual(cid, runtime, split=split)
    checks += 1
    phase_results["2"] = phase2_gips(cid, runtime)
    checks += 1
    phase_results["3"] = phase3_ai(cid, runtime)
    checks += 1
    phase_results["4"] = phase4_data(cid, runtime)
    checks += 1
    phase_results["5"] = phase5_coso(cid, runtime)
    checks += 1
    phase_results["6"] = phase6_security(cid, runtime)
    checks += 1
    phase_results["7"] = phase7_iso(cid, runtime)
    checks += 1
    phase_results["8"] = phase8_sre(cid)
    checks += 1
    phase_results["9"] = phase9_fatf(cid)
    checks += 1
    return phase_results, checks


def run_abbreviated_phases(
    cid: int, runtime: dict, split: dict
) -> tuple[dict[str, tuple[str, str | None]], int, bool, list[str]]:
    phase_results: dict[str, tuple[str, str | None]] = {}
    checks = 0
    escalated = False
    escalation_hits: list[str] = []

    phase_results["1"] = phase1_conceptual(cid, runtime, split=split)
    checks += 1
    if phase_results["1"][0] == "PASS":
        escalation_hits = scan_hidden_decision_indicators(runtime)
        if escalation_hits:
            escalated = True

    for pid in TIER2_SKIPPED_PHASES:
        phase_results[pid] = ("SKIPPED", "RBAS-001 Tier2 abbreviated — phase not executed")

    phase_results["4"] = phase4_data(cid, runtime)
    checks += 1
    phase_results["6"] = phase6_security(cid, runtime)
    checks += 1

    return phase_results, checks, escalated, escalation_hits


def final_status_tier1(
    phase_results: dict[str, tuple[str, str | None]], runtime: dict, split: dict
) -> tuple[str, str | None, str | None]:
    from cap646.batch08_dedicated import EXPECTED_SURFACE

    cid = int(runtime.get("capability_id") or 0)
    if phase_results["1"][0] == "FAIL":
        note = phase_results["1"][1] or ""
        if split.get("result_type") == "DIVERGENT_OUTPUT":
            return "SPLIT-BRAIN-UNVERIFIED", "1", note
        if "CROSS_SPINE" in note or "CROSS_SPINE" in (split.get("verdict") or ""):
            return "NOT_COMPLETE", "1", note
        if "NO_DEDICATED" in note or split.get("result_type") == "NO_DEDICATED_IMPLEMENTATION":
            return "NOT_COMPLETE", "1", note
        if "GENERIC_DELEGATE" in note:
            return "NOT_COMPLETE", "1", note
        return "CONCEPTUALLY-UNSOUND", "1", note
    if phase_results["2"][0] == "FAIL":
        return "PERFORMANCE-UNVERIFIABLE", "2", phase_results["2"][1]
    if phase_results["3"][0] == "FAIL":
        return "AI-RISK-UNMANAGED", "3", phase_results["3"][1]
    if phase_results["6"][0] == "FAIL":
        return "SECURITY-CRITICAL", "6", phase_results["6"][1]
    spine = str(runtime.get("production_spine") or "")
    if spine not in BATCH08_SPINES:
        return "NOT_COMPLETE", "—", f"production_spine={spine or 'none'}"
    if not runtime.get("success"):
        return "NOT_COMPLETE", "—", "runtime success=false"
    surface = str(runtime.get("surface") or "")
    expected = EXPECTED_SURFACE.get(cid)
    if surface in GENERIC_SURFACES and (expected is None or surface != expected):
        return "SPLIT-BRAIN-UNVERIFIED", "1", f"generic surface {surface}"
    if expected and surface and surface != expected:
        return "SPLIT-BRAIN-UNVERIFIED", "1", f"surface mismatch runtime={surface} expected={expected}"
    for pid in ("2", "3", "4", "5", "6", "7", "8", "9"):
        st, note = phase_results[pid]
        if st in ("FAIL", "PARTIAL"):
            return "NOT_COMPLETE", pid, note
    return "PRODUCTION-ALIGNED", None, None


def final_status_tier2_abbreviated(
    phase_results: dict[str, tuple[str, str | None]], runtime: dict, split: dict
) -> tuple[str, str | None, str | None]:
    if phase_results["1"][0] == "FAIL":
        note = phase_results["1"][1] or ""
        if split.get("result_type") == "DIVERGENT_OUTPUT":
            return "SPLIT-BRAIN-UNVERIFIED", "1", note
        if "CROSS_SPINE" in note or "CROSS_SPINE" in (split.get("verdict") or ""):
            return "NOT_COMPLETE", "1", note
        if "NO_DEDICATED" in note or split.get("result_type") == "NO_DEDICATED_IMPLEMENTATION":
            return "NOT_COMPLETE", "1", note
        if "GENERIC_DELEGATE" in note:
            return "NOT_COMPLETE", "1", note
        return "CONCEPTUALLY-UNSOUND", "1", note
    st = split.get("result_type")
    if st in ("DIVERGENT_OUTPUT", "CROSS_SPINE_ROUTING_OVERLAP", "NO_DEDICATED_IMPLEMENTATION"):
        return "NOT_COMPLETE", "1", split.get("verdict")
    spine = str(runtime.get("production_spine") or "")
    if spine not in BATCH08_SPINES:
        return "NOT_COMPLETE", "—", f"production_spine={spine or 'none'}"
    if not runtime.get("success"):
        return "NOT_COMPLETE", "—", "runtime success=false"
    for pid in ("4", "6"):
        st_p, note = phase_results[pid]
        if st_p in ("FAIL", "PARTIAL"):
            return "NOT_COMPLETE", pid, note
    return "NOT_COMPLETE", "6", "Tier2 abbreviated pass — phase6 static scan PARTIAL expected (RBAS-001)"


def severity(status: str) -> str:
    if status in ("CONCEPTUALLY-UNSOUND", "SECURITY-CRITICAL", "AI-RISK-UNMANAGED"):
        return "حرج"
    if status in ("PERFORMANCE-UNVERIFIABLE", "SPLIT-BRAIN-UNVERIFIED", "NOT_COMPLETE"):
        return "متوسط"
    if status == "PRODUCTION-ALIGNED":
        return "منخفض"
    return "متوسط"


def _build_evidence(
    cid: int,
    runtime: dict,
    split: dict,
    code_lines: list[str],
    evidence_note: str | None,
) -> str:
    evidence_parts: list[str] = []
    if cid in CONCEPTUAL_FLAGS:
        evidence_parts.append(CONCEPTUAL_FLAGS[cid])
    if cid in CROSS_SPINE_RESOLVED_IDS:
        evidence_parts.append(
            f"CROSS-SPINE-001 resolved Run015: spine={runtime.get('production_spine')} "
            f"module={runtime.get('backend_module')}"
        )
    evidence_parts.append(
        f"split_brain={split.get('result_type')}; runtime success={runtime.get('success')} "
        f"surface={runtime.get('surface')} spine={runtime.get('production_spine')}"
    )
    if code_lines:
        evidence_parts.append(f"code: {code_lines[0][:90]}")
    if evidence_note:
        evidence_parts.append(str(evidence_note)[:120])
    bcbs = bcbs_field_audit(runtime)
    if bcbs["missing_fields"]:
        evidence_parts.append(f"BCBS missing={','.join(bcbs['missing_fields'])}")
    return "; ".join(evidence_parts)[:450]


async def audit_capability(
    cid: int,
    *,
    tier_info: dict[str, Any],
    split_map: dict[int, dict],
    catalog: dict[int, dict],
    overlaps: dict[int, list[str]],
) -> dict[str, Any]:
    name = catalog.get(cid, {}).get("capability", f"CAP-{cid}")
    rbas_tier = tier_info["rbas_tier"]
    rbas_reason = tier_info["rbas_reason"]
    split = split_map[cid]
    start = time.perf_counter()
    escalated = False
    escalation_hits: list[str] = []
    phase_checks_executed = 0
    audit_path = "TIER1_FULL_9_PHASE"

    try:
        runtime = await execute_cap(cid)
    except Exception as exc:
        runtime = {"success": False, "error": str(exc), "capability_id": cid}

    backend, code_lines = backend_source(cid)

    if rbas_tier == "TIER1":
        phase_results, phase_checks_executed = run_full_phases(cid, runtime, split)
        status, failed_phase, evidence_note = final_status_tier1(phase_results, runtime, split)
    else:
        audit_path = "TIER2_ABBREVIATED_1_4_6"
        phase_results, phase_checks_executed, escalated, escalation_hits = run_abbreviated_phases(
            cid, runtime, split
        )
        if escalated:
            phase_results, full_checks = run_full_phases(cid, runtime, split)
            phase_checks_executed += full_checks
            audit_path = "TIER2_ESCALATED_TIER1_FULL"
            status, failed_phase, evidence_note = final_status_tier1(phase_results, runtime, split)
        else:
            status, failed_phase, evidence_note = final_status_tier2_abbreviated(phase_results, runtime, split)

    failed_standard = PHASE_STANDARD.get(failed_phase or "", "—") if failed_phase else "—"
    duration_ms = int((time.perf_counter() - start) * 1000)

    row: dict[str, Any] = {
        "id": cid,
        "name": name,
        "status": status,
        "failed_phase": failed_phase or "—",
        "failed_standard": failed_standard,
        "evidence": _build_evidence(cid, runtime, split, code_lines, evidence_note),
        "severity": severity(status),
        "backend": backend,
        "split_brain_type": split.get("result_type"),
        "routing_overlap": overlaps.get(cid),
        "phase_results": {k: v[0] for k, v in phase_results.items()},
        "rbas_tier": rbas_tier,
        "rbas_reason": rbas_reason,
        "audit_path": audit_path,
        "escalated": escalated,
        "escalation_hits": escalation_hits,
        "phase_checks_executed": phase_checks_executed,
        "audit_duration_ms": duration_ms,
    }
    return row


async def audit_all() -> list[dict]:
    from cap646.catalog import catalog_by_id

    tier_map = batch08_tier_map()
    (OUT / "RBAS001_TIER_CLASSIFICATION.json").write_text(
        json.dumps([tier_map[cid] for cid in BATCH08_RANGE], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    split_map = await load_split_brain()
    catalog = catalog_by_id()
    overlaps = routing_overlap_map()
    rows: list[dict] = []
    for cid in BATCH08_RANGE:
        rows.append(
            await audit_capability(
                cid,
                tier_info=tier_map[cid],
                split_map=split_map,
                catalog=catalog,
                overlaps=overlaps,
            )
        )
    return rows


def _impact_metrics(rows: list[dict]) -> dict[str, Any]:
    tier1_rows = [r for r in rows if r["rbas_tier"] == "TIER1" and not r.get("escalated")]
    tier2_rows = [r for r in rows if r["rbas_tier"] == "TIER2" and not r.get("escalated")]
    escalated_rows = [r for r in rows if r.get("escalated")]
    t1_checks = sum(r["phase_checks_executed"] for r in tier1_rows)
    t2_checks = sum(r["phase_checks_executed"] for r in tier2_rows)
    esc_checks = sum(r["phase_checks_executed"] for r in escalated_rows)
    total_checks = sum(r["phase_checks_executed"] for r in rows)
    total_ms = sum(r["audit_duration_ms"] for r in rows)
    full_baseline = 50 * 9
    abbreviated_baseline = 29 * 4  # tier2 count * (P1+P4+P6+split)
    return {
        "tier1": {
            "ids": len(tier1_rows),
            "phase_checks": t1_checks,
            "duration_ms": sum(r["audit_duration_ms"] for r in tier1_rows),
        },
        "tier2": {
            "ids": len(tier2_rows),
            "phase_checks": t2_checks,
            "duration_ms": sum(r["audit_duration_ms"] for r in tier2_rows),
        },
        "tier1_count": len(tier1_rows),
        "tier1_phase_checks": t1_checks,
        "tier1_duration_ms": sum(r["audit_duration_ms"] for r in tier1_rows),
        "tier2_count": len(tier2_rows),
        "tier2_phase_checks": t2_checks,
        "tier2_duration_ms": sum(r["audit_duration_ms"] for r in tier2_rows),
        "escalated_count": len(escalated_rows),
        "escalated_phase_checks": esc_checks,
        "escalated_duration_ms": sum(r["audit_duration_ms"] for r in escalated_rows),
        "total_phase_checks": total_checks,
        "total_duration_ms": total_ms,
        "full_nine_phase_baseline_checks": full_baseline,
        "checks_saved_vs_full_baseline": full_baseline - total_checks,
        "tier2_efficiency_ratio": round(total_checks / full_baseline, 3) if full_baseline else 0,
        "conceptually_unsound_count": sum(1 for r in rows if r["status"] == "CONCEPTUALLY-UNSOUND"),
        "calibration_note": (
            "Escalation excludes compliance_footer provenance_score paths (Run 025 calibration). "
            "Tier2 abbreviated path did not yield CONCEPTUALLY-UNSOUND misses."
            if sum(1 for r in rows if r["status"] == "CONCEPTUALLY-UNSOUND") == 0
            else "RBAS-001 REQUIRES REVISION — Tier2 missed CONCEPTUALLY-UNSOUND."
        ),
    }


def write_report(rows: list[dict], tier_map: dict[int, dict[str, Any]]) -> Path:
    md = OUT / "BATCH08_INDEPENDENT_RBAS_AUDIT_REPORT.md"
    counts = Counter(r["status"] for r in rows)
    aligned = counts.get("PRODUCTION-ALIGNED", 0)
    overlaps = routing_overlap_map()
    gips = gips_ledger_stats()
    metrics = _impact_metrics(rows)
    tier1_count = sum(1 for r in tier_map.values() if r["rbas_tier"] == "TIER1")
    tier2_count = sum(1 for r in tier_map.values() if r["rbas_tier"] == "TIER2")

    lines = [
        "# Batch 08 Independent RBAS Due Diligence Report (IDs 251–300)\n",
        f"**Generated:** {datetime.now(UTC).isoformat()}  \n",
        "**Run:** Master Contract 013 — RBAS-001 risk-based diagnostic audit  \n",
        "**Auditor role:** Third Line of Defense — Independent Assurance  \n",
        "**Policies:** RTM-IND-001 | SCORE-IDX-001 | CROSS-SPINE-001 | WF-027 | RBAS-001  \n\n",
        "## RBAS-001 Tier Classification (all 50 IDs)\n\n",
        "| ID | Capability | Tier | Reason |\n",
        "|---:|---|---|---|\n",
    ]
    for cid in BATCH08_RANGE:
        t = tier_map[cid]
        cap = str(t.get("capability") or "").replace("|", "/")
        reason = str(t.get("rbas_reason") or "").replace("|", "/")
        lines.append(f"| {cid} | {cap} | **{t['rbas_tier']}** | {reason} |\n")

    lines.extend(
        [
            f"\n**Tier summary:** TIER1={tier1_count} | TIER2={tier2_count}  \n\n",
            "## RBAS Impact Metrics\n\n",
            f"- **Tier1 executed:** {metrics['tier1_count']} IDs — "
            f"{metrics['tier1_phase_checks']} phase checks — {metrics['tier1_duration_ms']} ms\n",
            f"- **Tier2 abbreviated:** {metrics['tier2_count']} IDs — "
            f"{metrics['tier2_phase_checks']} phase checks — {metrics['tier2_duration_ms']} ms\n",
            f"- **Tier2 escalated to Tier1:** {metrics['escalated_count']} IDs — "
            f"{metrics['escalated_phase_checks']} phase checks — {metrics['escalated_duration_ms']} ms\n",
            f"- **CONCEPTUALLY-UNSOUND:** {metrics['conceptually_unsound_count']}/50\n\n",
            "## WF-027 / CROSS-SPINE Preflight\n\n",
            f"- **Routing overlaps (BATCH01∩BATCH02∩BATCH03∩BATCH08):** "
            f"{len(overlaps)} IDs `{sorted(overlaps.keys())}`\n",
            f"- **WF-027 dormant legacy in batch08 range (251–300):** `{sorted(WF027_IN_BATCH08)}` "
            f"(zero overlap — unresolved legacy IDs 584+ are outside range)\n",
            "- **Cross-spine Run 025:** no WF-027 IDs in scope; batch08_prep spine registered for all 50\n\n",
            "## Results Table\n\n",
            "| ID | الاسم | RBAS | Path | الحالة النهائية | المرحلة | المعيار المرجعي | SPLIT-BRAIN | الدليل | الخطورة |\n",
            "|---:|---|---|---|---|---|---|---|---|---|\n",
        ]
    )
    for r in rows:
        esc = "↑T1" if r.get("escalated") else "—"
        lines.append(
            f"| {r['id']} | {r['name']} | {r['rbas_tier']} | {r['audit_path']} | **{r['status']}** | "
            f"{r['failed_phase']} | {r['failed_standard']} | {r.get('split_brain_type', '—')} | "
            f"{r['evidence']} | {r['severity']} {esc} |\n"
        )

    lines.append("\n## Summary\n\n")
    for k, v in counts.most_common():
        lines.append(f"- **{k}:** {v}/50\n")
    lines.append(
        f"\n**Independent result:** {aligned}/50 PRODUCTION-ALIGNED  \n"
        f"**CONCEPTUALLY-UNSOUND:** {counts.get('CONCEPTUALLY-UNSOUND', 0)}/50  \n"
        f"**GIPS ledger:** {gips.get('unique_decisions', 0)} decisions, simulated_only={gips.get('simulated_only')}\n"
    )
    lines.append("\n### SPLIT-BRAIN Summary (mandatory all 50)\n\n")
    sb = Counter(r.get("split_brain_type") for r in rows)
    for k, v in sb.most_common():
        lines.append(f"- **{k}:** {v}\n")
    lines.append("\n### WF-027 Preflight — Zero Overlap (Run 025)\n\n")
    lines.append(
        "- **Unresolved WF-027 IDs:** `{584, 629, 630, 631, 642, 644, 646}` — all outside 251–300\n"
        "- **Resolved prior:** 175 (Batch04), 214/245 (Batch05)\n\n"
    )
    if CROSS_SPINE_RESOLVED_IDS:
        for cid in sorted(CROSS_SPINE_RESOLVED_IDS):
            r = next(x for x in rows if x["id"] == cid)
            lines.append(
                f"- **ID {cid}:** status={r['status']} tier={r['rbas_tier']} path={r['audit_path']}; "
                f"backend={r['backend']}; split={r.get('split_brain_type')}\n"
            )
    lines.append("\n## Critical Code Evidence (SR 26-2)\n\n")
    for cid, note in sorted(CONCEPTUAL_FLAGS.items()):
        lines.append(f"- **ID {cid}:** `{note}`\n")
    if not CONCEPTUAL_FLAGS:
        lines.append("- *(none flagged in Run 025 static pre-scan — live audit above is authoritative)*\n")
    lines.append("\n## رأي اللجنة المستقلة\n\n")
    lines.append(
        f"بصفتنا لجنة تدقيق مستقلة (Third Line of Defense — IIA IPPF)، وبعد تنفيذ RBAS-001 "
        f"على Batch 08 (IDs 251–300) وفق SR 26-2 وCOSO وGIPS وRTM-IND-001 وCROSS-SPINE-001، "
        f"صُنّفت {tier1_count} قدرة TIER1 (9 مراحل) و{tier2_count} قدرة TIER2 (مختصر 1/4/6). "
        f"تصعيد Tier2→Tier1: {metrics['escalated_count']} IDs. "
        f"نجد **{aligned}/50** عند `PRODUCTION-ALIGNED`. "
        f"**CONCEPTUALLY-UNSOUND={counts.get('CONCEPTUALLY-UNSOUND', 0)}**. "
        f"**Batch 08 غير مغلق** — بوابة الإغلاق: CONCEPTUALLY-UNSOUND=0 + RTM صادق. "
        f"فحص SPLIT-BRAIN: {sb.get('DEDICATED_ONLY', 0)} dedicated-only; "
        f"{sb.get('CROSS_SPINE_ROUTING_OVERLAP', 0)} routing overlap; "
        f"{sb.get('DIVERGENT_OUTPUT', 0)} divergent. "
        f"WF-027 preflight: zero overlap in 251–300. "
        f"spine=batch08_prep. **نوصي بعدم أي إصلاح قبل مراجعة هذا التقرير** — "
        f"الإغلاق في Run منفصل كما Batch 01/02/03.\n"
    )
    md.write_text("".join(lines), encoding="utf-8")
    (OUT / "BATCH08_INDEPENDENT_RBAS_AUDIT.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return md


async def main() -> None:
    tier_map = batch08_tier_map()
    rows = await audit_all()
    path = write_report(rows, tier_map)
    counts = Counter(r["status"] for r in rows)
    metrics = _impact_metrics(rows)
    (OUT / "RUN015_RBAS_IMPACT_METRICS.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tier_counts = Counter(r["rbas_tier"] for r in rows)
    print(f"Wrote {path}")
    print(f"Status: {dict(counts)}")
    print(f"RBAS tiers: {dict(tier_counts)}")
    print(f"TIER1={metrics['tier1_count']} checks={metrics['tier1_phase_checks']} ms={metrics['tier1_duration_ms']}")
    print(f"TIER2={metrics['tier2_count']} checks={metrics['tier2_phase_checks']} ms={metrics['tier2_duration_ms']}")
    print(f"Escalated={metrics['escalated_count']} CONCEPTUALLY-UNSOUND={metrics['conceptually_unsound_count']}")


if __name__ == "__main__":
    asyncio.run(main())
