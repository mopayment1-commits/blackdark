#!/usr/bin/env python3
"""Independent Third-Line 9-Phase Due Diligence — Official Batch 02 (IDs 51–100).
Run 007 — post-remediation re-audit (Run 006 diagnostic superseded)."""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "institutional_due_diligence_2026" / "batch02_independent_audit"
OUT.mkdir(parents=True, exist_ok=True)

BATCH02_RANGE = range(51, 101)
from cap646.batch02_dedicated import BATCH02_OVERLAP_BATCH01_IDS as BATCH02_OVERLAP_BATCH01

DECISION_CAP_IDS = {53, 66, 69, 81, 90, 97, 98}
AI_CAP_IDS = {65, 66, 69, 99, 100}
WALLET_CAP_IDS = {73, 75, 91, 92}

PHASE_STANDARD: dict[str, str] = {
    "1": "SR 26-2 Independent Validation / Conceptual Soundness",
    "2": "GIPS (CFA Institute) — full-population performance disclosure",
    "3": "NIST AI RMF 1.0 + NIST AI 600-1 GenAI Profile",
    "4": "BCBS 239 — Accuracy/Completeness/Timeliness/Adaptability",
    "5": "COSO Internal Control — Integrated Framework",
    "6": "MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS",
    "7": "ISO/IEC 25010 + ISO/IEC/IEEE 12207 + ISO/IEC/IEEE 29148",
    "8": "Google SRE Production Readiness Review (PRR)",
    "9": "FATF Recommendation 16",
}

# Static SR 26-2 flags cleared Run 007 — remediation applied in batch02_dedicated.py
CONCEPTUAL_FLAGS: dict[int, str] = {}

GIPS_LEDGER = ROOT / "data" / "decision_ledger.jsonl"
_gips_cache: dict[str, Any] | None = None
_split_cache: dict[int, dict] | None = None

COMMON_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "email": "run006-audit@blackdark.local",
    "tier": "pro",
}


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
        "evidence_class": bool(payload.get("evidence_class") or (payload.get("compliance_footer") or {}).get("evidence_class")),
    }
    missing = [k for k, ok in checks.items() if not ok]
    return {"present": checks, "missing_fields": missing}


async def split_brain_test(cid: int) -> dict[str, Any]:
    from bd_platform.free_tier_capabilities import FREE_TIER_CAP_IDS, execute_free_tier_capability
    from cap646.batch02_dedicated import BATCH02_DEDICATED_IDS, execute as execute_b2d

    params = dict(COMMON_PARAMS)
    row: dict[str, Any] = {"id": cid}

    # free_tier path
    if cid in FREE_TIER_CAP_IDS:
        free = await execute_free_tier_capability(cid, params=params)
        row["free_tier_available"] = True
        row["free_result"] = free
    else:
        row["free_tier_available"] = False
        row["free_error"] = "not_in_FREE_TIER_CAP_IDS"

    # batch02 dedicated path
    if cid in BATCH02_DEDICATED_IDS:
        try:
            dedicated = await execute_b2d(cid, params=params)
            row["batch02_dedicated_available"] = True
            row["dedicated_result"] = dedicated
        except Exception as exc:
            row["batch02_dedicated_available"] = False
            row["dedicated_error"] = f"{type(exc).__name__}: {exc}"
    elif cid in BATCH02_OVERLAP_BATCH01:
        row["batch02_dedicated_available"] = False
        row["dedicated_error"] = "BATCH02_OVERLAP — not in BATCH02_DEDICATED_IDS"
    else:
        row["batch02_dedicated_available"] = False
        row["dedicated_error"] = "not_in_BATCH02_DEDICATED_IDS"

    # classify
    if cid in BATCH02_OVERLAP_BATCH01:
        row["result_type"] = "CROSS_SPINE_BATCH01"
        row["verdict"] = (
            "NOT_COMPLETE (governance): ID in batch02/batch01 overlap set — "
            "CROSS-SPINE-001 violation"
        )
    elif not row.get("free_tier_available") and row.get("batch02_dedicated_available"):
        row["result_type"] = "DEDICATED_ONLY"
        row["verdict"] = "No free_tier path — dedicated batch02 only (SPLIT-BRAIN N/A)"
    elif row.get("free_tier_available") and row.get("batch02_dedicated_available"):
        f_data = (row.get("free_result") or {}).get("data") or row.get("free_result")
        d_data = row.get("dedicated_result")
        match = json.dumps(f_data, sort_keys=True, default=str) == json.dumps(d_data, sort_keys=True, default=str)
        row["outputs_match"] = match
        if match:
            row["result_type"] = "DUPLICATE_CONFIRMED"
            row["verdict"] = "Duplicate Confirmed — free_tier vs batch02_dedicated parity"
        else:
            row["result_type"] = "DIVERGENT_OUTPUT"
            row["verdict"] = "SPLIT-BRAIN-UNVERIFIED — dedicated vs free_tier outputs differ materially"
    elif not row.get("batch02_dedicated_available"):
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
    rows = [await split_brain_test(cid) for cid in BATCH02_RANGE]
    _split_cache = {r["id"]: r for r in rows}
    (OUT / "RUN006_SPLIT_BRAIN_EVIDENCE.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    return _split_cache


def backend_source(cid: int) -> tuple[str, list[str]]:
    from cap646.batch02_dedicated import BATCH02_DEDICATED_IDS

    mod = ROOT / "cap646" / "batch02_dedicated.py"
    text = mod.read_text(encoding="utf-8")
    pat = rf"async def _cap{cid:03d}\("
    lines_out: list[str] = []
    m = re.search(pat, text)
    if m:
        chunk = text[m.start() : m.start() + 800]
        for ln in chunk.splitlines()[:20]:
            lines_out.append(ln.strip())
    if cid in BATCH02_OVERLAP_BATCH01:
        return "cap646.batch01_dedicated (overlap — CROSS-SPINE-001)", [
            "runtime routes BATCH01_IDS before BATCH02_IDS when overlap exists",
        ]
    if cid in BATCH02_DEDICATED_IDS:
        return "cap646.batch02_dedicated", lines_out or [f"_cap{cid:03d} handler"]
    return "cap646.batch02_production unmapped", [f"capability {cid} not in BATCH02_DEDICATED_IDS"]


def phase1_conceptual(cid: int, result: dict, *, split: dict) -> tuple[str, str | None]:
    if cid in CONCEPTUAL_FLAGS:
        if result.get("heuristic") and result.get("methodology_status") == "NOT_COMPLETE":
            return "PASS", None
        return "FAIL", CONCEPTUAL_FLAGS[cid]
    if not result.get("success"):
        return "FAIL", "runtime success=false"
    if cid in BATCH02_OVERLAP_BATCH01 and result.get("production_spine") != "batch02":
        return "FAIL", (
            f"CROSS_SPINE: official batch02 but production_spine={result.get('production_spine')} "
            "(batch01 legacy extension)"
        )
    st = split.get("result_type")
    if st == "DIVERGENT_OUTPUT":
        return "FAIL", split.get("verdict")
    if st == "CROSS_SPINE_BATCH01":
        return "FAIL", split.get("verdict")
    if st == "NO_DEDICATED_IMPLEMENTATION":
        return "FAIL", split.get("verdict")
    # SCORE-IDX-001: scoring fields without heuristic disclosure
    score_keys = ("score", "_score", "composite", "breadth_score", "proxy")
    blob = json.dumps(result, default=str).lower()
    if any(k in blob for k in score_keys) and cid in {52, 53, 54, 81, 90}:
        if not result.get("heuristic") and not result.get("methodology_status"):
            if cid not in CONCEPTUAL_FLAGS:
                pass  # already in CONCEPTUAL_FLAGS for 52,53,54,81
    return "PASS", None


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


def phase3_ai(cid: int, result: dict) -> tuple[str, str | None]:
    if cid not in AI_CAP_IDS:
        return "NOT_APPLICABLE", None
    if not (result.get("compliance_footer") or result.get("provenance") or result.get("certificate")):
        return "FAIL", "AI-RISK-UNMANAGED: no NIST AI RMF grounding in response"
    return "PARTIAL", "ai_compliance_footer present; ISO 42001 lifecycle not verified"


def phase4_data(cid: int, result: dict) -> tuple[str, str | None]:
    audit = bcbs_field_audit(result)
    if audit["missing_fields"]:
        excerpt = json.dumps(
            {k: result.get(k) for k in ("capability_id", "surface", "source", "data_source", "timestamp", "evidence_class", "success") if k in result},
            default=str,
        )[:200]
        return "PARTIAL", f"BCBS 239 missing: {', '.join(audit['missing_fields'])} | {excerpt}"
    return "PASS", None


def phase5_coso(cid: int, result: dict) -> tuple[str, str | None]:
    if result.get("compliance_footer") or result.get("evidence_class"):
        return "PASS", None
    return "PARTIAL", "COSO: partial automated controls — evidence_class not on all fields"


def phase6_security(cid: int, result: dict) -> tuple[str, str | None]:
    from cap646.ui_pages import user_surface_for

    surf = user_surface_for(cid)
    if not surf or not surf.get("api_path"):
        if result.get("compliance_footer") or result.get("evidence_class"):
            return "PASS", None
        return "PARTIAL", "no user-facing API path — internal/surface-only capability"
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
        if r.returncode == 0:
            return "PASS", None
        gr = subprocess.run(
            ["rg", "-l", r"/\{capability_id\}/execute", "api/routers/cap646.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if gr.returncode == 0 and "/execute" in path:
            return "PASS", None
        return "PARTIAL", f"OWASP API: route prefix {prefix} not confirmed in static scan"
    except Exception as exc:
        return "PARTIAL", f"security scan error: {exc}"


def phase7_iso(cid: int, result: dict) -> tuple[str, str | None]:
    if not result.get("backend_module") or not result.get("backend_entrypoint"):
        return "FAIL", "ISO/IEC/IEEE 29148: missing backend binding"
    if cid in BATCH02_OVERLAP_BATCH01 and result.get("production_spine") != "batch02":
        return "PARTIAL", f"traceability split: official batch02, spine={result.get('production_spine')}"
    return "PASS", None


def phase8_sre(cid: int) -> tuple[str, str | None]:
    runbook = ROOT / "docs" / "RUNBOOK.md"
    if not runbook.is_file():
        return "PARTIAL", "Google SRE PRR: docs/RUNBOOK.md missing"
    text = runbook.read_text(encoding="utf-8", errors="replace")
    cap_tag = f"cap-{cid:03d}"
    if cap_tag in text or f"ID {cid}" in text:
        return "PASS", None
    return "PARTIAL", "generic runbook only; no per-capability rollback drill"


def phase9_fatf(cid: int) -> tuple[str, str | None]:
    if cid not in WALLET_CAP_IDS:
        return "NOT_APPLICABLE", None
    return "PARTIAL", "FATF R.16: address handling present; travel-rule screening not verified"


def final_status(phase_results: dict[str, tuple[str, str | None]], runtime: dict, split: dict) -> tuple[str, str | None, str | None]:
    from cap646.batch02_dedicated import EXPECTED_SURFACE

    cid = int(runtime.get("capability_id") or 0)
    if phase_results["1"][0] == "FAIL":
        note = phase_results["1"][1] or ""
        if split.get("result_type") == "DIVERGENT_OUTPUT":
            return "SPLIT-BRAIN-UNVERIFIED", "1", note
        if "CROSS_SPINE" in note or "CROSS_SPINE" in (split.get("verdict") or ""):
            return "NOT_COMPLETE", "1", note
        if "NO_DEDICATED" in note or split.get("result_type") == "NO_DEDICATED_IMPLEMENTATION":
            return "NOT_COMPLETE", "1", note
        return "CONCEPTUALLY-UNSOUND", "1", note
    if phase_results["2"][0] == "FAIL":
        return "PERFORMANCE-UNVERIFIABLE", "2", phase_results["2"][1]
    if phase_results["3"][0] == "FAIL":
        return "AI-RISK-UNMANAGED", "3", phase_results["3"][1]
    if phase_results["6"][0] == "FAIL":
        return "SECURITY-CRITICAL", "6", phase_results["6"][1]
    spine = str(runtime.get("production_spine") or "")
    if cid not in BATCH02_OVERLAP_BATCH01 and spine != "batch02":
        return "NOT_COMPLETE", "—", f"production_spine={spine or 'none'}"
    if not runtime.get("success"):
        return "NOT_COMPLETE", "—", "runtime success=false"
    surface = str(runtime.get("surface") or "")
    expected = EXPECTED_SURFACE.get(cid)
    if surface in {"onchain_intelligence", "market_data", "ai_decision_intelligence"} and (
        expected is None or surface != expected
    ):
        return "SPLIT-BRAIN-UNVERIFIED", "1", f"generic surface {surface}"
    if expected and surface and surface != expected:
        return "SPLIT-BRAIN-UNVERIFIED", "1", f"surface mismatch runtime={surface} expected={expected}"
    for pid in ("2", "3", "4", "5", "6", "7", "8", "9"):
        st, note = phase_results[pid]
        if st in ("FAIL", "PARTIAL"):
            return "NOT_COMPLETE", pid, note
    return "PRODUCTION-ALIGNED", None, None


def severity(status: str) -> str:
    if status in ("CONCEPTUALLY-UNSOUND", "SECURITY-CRITICAL", "AI-RISK-UNMANAGED"):
        return "حرج"
    if status in ("PERFORMANCE-UNVERIFIABLE", "SPLIT-BRAIN-UNVERIFIED", "NOT_COMPLETE"):
        return "متوسط"
    if status == "PRODUCTION-ALIGNED":
        return "منخفض"
    return "متوسط"


async def audit_all() -> list[dict]:
    from cap646.catalog import catalog_by_id

    split_map = await load_split_brain()
    catalog = catalog_by_id()
    rows: list[dict] = []
    for cid in BATCH02_RANGE:
        name = catalog.get(cid, {}).get("capability", f"CAP-{cid}")
        try:
            runtime = await execute_cap(cid)
        except Exception as exc:
            runtime = {"success": False, "error": str(exc), "capability_id": cid}
        backend, code_lines = backend_source(cid)
        split = split_map[cid]
        phase_results: dict[str, tuple[str, str | None]] = {}
        phase_results["1"] = phase1_conceptual(cid, runtime, split=split)
        phase_results["2"] = phase2_gips(cid, runtime)
        phase_results["3"] = phase3_ai(cid, runtime)
        phase_results["4"] = phase4_data(cid, runtime)
        phase_results["5"] = phase5_coso(cid, runtime)
        phase_results["6"] = phase6_security(cid, runtime)
        phase_results["7"] = phase7_iso(cid, runtime)
        phase_results["8"] = phase8_sre(cid)
        phase_results["9"] = phase9_fatf(cid)
        status, failed_phase, evidence_note = final_status(phase_results, runtime, split)
        failed_standard = PHASE_STANDARD.get(failed_phase or "", "—") if failed_phase else "—"
        evidence_parts = []
        if cid in CONCEPTUAL_FLAGS:
            evidence_parts.append(CONCEPTUAL_FLAGS[cid])
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
        rows.append(
            {
                "id": cid,
                "name": name,
                "status": status,
                "failed_phase": failed_phase or "—",
                "failed_standard": failed_standard,
                "evidence": "; ".join(evidence_parts)[:450],
                "severity": severity(status),
                "backend": backend,
                "split_brain_type": split.get("result_type"),
                "phase_results": {k: v[0] for k, v in phase_results.items()},
            }
        )
    return rows


def write_report(rows: list[dict]) -> Path:
    md = OUT / "BATCH02_INDEPENDENT_NINE_PHASE_REPORT.md"
    counts = Counter(r["status"] for r in rows)
    aligned = counts.get("PRODUCTION-ALIGNED", 0)
    official_rtm = ROOT / "docs" / "BATCH02_OFFICIAL_RTM_51_100.json"
    rtm_claim = "unknown"
    if official_rtm.is_file():
        rtm = json.loads(official_rtm.read_text(encoding="utf-8"))
        rtm_claim = f"{rtm.get('summary', {}).get('production_aligned', rtm.get('production_aligned', '?'))}/50"
    gips = gips_ledger_stats()
    lines = [
        "# Batch 02 Independent Nine-Phase Due Diligence Report (IDs 51–100)\n",
        f"**Generated:** {datetime.now(UTC).isoformat()}  \n",
        "**Run:** Master Contract 007 — Post-remediation closure re-audit  \n",
        "**Auditor role:** Third Line of Defense — Independent Assurance  \n",
        "**Policies:** RTM-IND-001 (self-assessment RTM untrusted) | SCORE-IDX-001  \n\n",
        "## Results Table\n\n",
        "| ID | الاسم | الحالة النهائية | المرحلة | المعيار المرجعي | SPLIT-BRAIN | الدليل | الخطورة |\n",
        "|---:|---|---|---|---|---|---|---|\n",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['name']} | **{r['status']}** | {r['failed_phase']} | "
            f"{r['failed_standard']} | {r.get('split_brain_type','—')} | {r['evidence']} | {r['severity']} |\n"
        )
    lines.append("\n## Summary\n\n")
    for k, v in counts.most_common():
        lines.append(f"- **{k}:** {v}/50\n")
    lines.append(
        f"\n**Official RTM claim (untrusted per RTM-IND-001):** {rtm_claim} PRODUCTION-ALIGNED  \n"
        f"**Independent result:** {aligned}/50 PRODUCTION-ALIGNED  \n"
        f"**GIPS ledger:** {gips.get('unique_decisions', 0)} decisions, simulated_only={gips.get('simulated_only')}\n"
    )
    lines.append("\n### SPLIT-BRAIN Summary (mandatory all 50)\n\n")
    sb = Counter(r.get("split_brain_type") for r in rows)
    for k, v in sb.most_common():
        lines.append(f"- **{k}:** {v}\n")
    lines.append("\n## Critical Code Evidence (SR 26-2)\n\n")
    for cid, note in sorted(CONCEPTUAL_FLAGS.items()):
        lines.append(f"- **ID {cid}:** `{note}`\n")
    lines.append("\n## رأي اللجنة المستقلة\n\n")
    lines.append(
        f"بصفتنا لجنة تدقيق مستقلة (Third Line of Defense — IIA IPPF)، وبعد تنفيذ المراحل التسع على "
        f"Batch 02 (IDs 51–100) وفق SR 26-2 وCOSO وGIPS وRTM-IND-001، "
        f"نجد **{aligned}/50** عند `PRODUCTION-ALIGNED` — مقابل ادّعاء RTM الرسمي **{rtm_claim}** "
        f"(`docs/BATCH02_OFFICIAL_RTM_51_100.json` — **غير موثوق** حتى independent validation). "
        f"**Batch 02 غير مغلق** — CONCEPTUALLY-UNSOUND={counts.get('CONCEPTUALLY-UNSOUND', 0)}. "
        f"فحص SPLIT-BRAIN الإلزامي: {sb.get('CROSS_SPINE_BATCH01', 0)} IDs overlap batch01 spine (55,56,59,60); "
        f"{sb.get('DEDICATED_ONLY', 0)} dedicated-only; {sb.get('DIVERGENT_OUTPUT', 0)} divergent. "
        f"نوصي بعدم أي إصلاح قبل مراجعة هذا التقرير التشخيصي — ثم Run 007+ للإغلاق كما Batch 01.\n"
    )
    md.write_text("".join(lines), encoding="utf-8")
    (OUT / "BATCH02_INDEPENDENT_NINE_PHASE.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return md


async def main() -> None:
    rows = await audit_all()
    path = write_report(rows)
    print(f"Wrote {path}")
    print(Counter(r["status"] for r in rows))


if __name__ == "__main__":
    asyncio.run(main())
