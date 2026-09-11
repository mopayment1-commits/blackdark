#!/usr/bin/env python3
"""Independent Third-Line 9-Phase Due Diligence — Official Batch 01 (IDs 1–50).
Audit-only; does not modify product code."""
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
OUT = ROOT / "institutional_due_diligence_2026" / "batch01_independent_audit"
OUT.mkdir(parents=True, exist_ok=True)

DECISION_CAP_IDS = {17, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 41, 60}
AI_CAP_IDS = {24, 25, 26, 34, 59}
WALLET_CAP_IDS = {2, 3, 10, 11, 12, 13, 14, 18, 19, 20, 22, 23, 629}
FREE_TIER_BACKEND_IDS = {1, 2, 3, 4, 10, 21, 38, 39, 45}

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

CONCEPTUAL_FLAGS: dict[int, str] = {
    8: "batch01_dedicated.py:382 top10_proxy_pct=min(95,max(locked_pct,(total-circ)/total*100)) — proxy not holder data",
    9: "batch01_dedicated.py:405 distribution_score=100-locked_pct*0.6+(ls_ratio-1)*10 — no cited methodology",
    33: "batch01_dedicated.py:1362 score=len(alerts)*12.5 — arbitrary linear scaling",
    34: "batch01_dedicated.py:1206 verdict=params.get('verdict') or 'Neutral' — user-supplied input",
}

GIPS_LEDGER = ROOT / "data" / "decision_ledger.jsonl"
_gips_cache: dict[str, Any] | None = None


def gips_ledger_stats() -> dict[str, Any]:
    global _gips_cache
    if _gips_cache is not None:
        return _gips_cache
    stats: dict[str, Any] = {
        "exists": GIPS_LEDGER.is_file(),
        "lines": 0,
        "unique_decisions": 0,
        "with_outcome": 0,
        "simulated_only": True,
        "actions": Counter(),
        "sources": Counter(),
        "date_min": None,
        "date_max": None,
    }
    if not stats["exists"]:
        _gips_cache = stats
        return stats
    seen: set[str] = set()
    with_outcome: set[str] = set()
    dates: list[str] = []
    with GIPS_LEDGER.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            stats["lines"] += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            did = str(row.get("decision_id") or "")
            if did:
                seen.add(did)
            if row.get("outcome_id"):
                with_outcome.add(did)
            ec = str(row.get("evidence_class") or "")
            if ec not in ("SIMULATED", "SHADOW_LIVE_FORWARD"):
                stats["simulated_only"] = False
            stats["actions"][str(row.get("decision_action") or "?")] += 1
            stats["sources"][str(row.get("source") or "?")] += 1
            ts = row.get("created_at")
            if ts:
                dates.append(str(ts))
    stats["unique_decisions"] = len(seen)
    stats["with_outcome"] = len(with_outcome)
    if dates:
        stats["date_min"] = min(dates)
        stats["date_max"] = max(dates)
    _gips_cache = stats
    return stats


async def execute_cap(cid: int) -> dict[str, Any]:
    from cap646.runtime import execute_capability

    return await execute_capability(
        cid,
        skip_entitlement=True,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "email": "independent-audit@blackdark.local",
            "tier": "pro",
        },
    )


def backend_source(cid: int) -> tuple[str, list[str]]:
    from cap646.batch01_dedicated import BATCH01_DEDICATED_IDS

    lines_out: list[str] = []
    if cid in BATCH01_DEDICATED_IDS:
        mod = ROOT / "cap646" / "batch01_dedicated.py"
        text = mod.read_text(encoding="utf-8")
        pat = rf"async def _cap{cid:03d}_"
        m = re.search(pat, text)
        if m:
            chunk = text[m.start() : m.start() + 1200]
            for ln in chunk.splitlines()[:25]:
                lines_out.append(ln.strip())
        return "cap646.batch01_dedicated", lines_out
    if cid in FREE_TIER_BACKEND_IDS:
        return "bd_platform.free_tier_capabilities (via batch01_production._BATCH01_FREE_TIER)", [
            "batch01_production.py:76-79 execute_free_tier_capability(capability_id)",
        ]
    handlers = {
        5: "cap646.handlers.onchain",
        47: "cap646.handlers.market",
        48: "cap646.handlers.derivatives",
        49: "cap646.handlers.verified",
    }
    h = handlers.get(cid, "cap646.batch01_production unmapped branch")
    return h, [f"handler route for cap {cid} in batch01_production.py"]


def phase1_conceptual(cid: int, result: dict, *, static_backend: str) -> tuple[str, str | None]:
    if cid in CONCEPTUAL_FLAGS:
        return "FAIL", CONCEPTUAL_FLAGS[cid]
    if not result.get("success"):
        return "FAIL", "runtime success=false"
    if cid in FREE_TIER_BACKEND_IDS or "free_tier" in static_backend:
        return "FAIL", (
            "SPLIT routing: RTM claims batch01 dedicated backend but code routes via "
            "batch01_production._BATCH01_FREE_TIER → execute_free_tier_capability "
            "(batch01_production.py:76-79)"
        )
    return "PASS", None


def phase2_gips(cid: int, result: dict) -> tuple[str, str | None]:
    if cid not in DECISION_CAP_IDS:
        return "NOT_APPLICABLE", None
    stats = gips_ledger_stats()
    if not stats["exists"] or stats["unique_decisions"] == 0:
        return "FAIL", "PERFORMANCE-UNVERIFIABLE: no decision ledger for GIPS full-population analysis"
    if stats["simulated_only"]:
        return "FAIL", (
            f"PERFORMANCE-UNVERIFIABLE: ledger {stats['unique_decisions']} decisions "
            f"({stats['date_min']}..{stats['date_max']}) all SIMULATED/SHADOW — "
            f"GIPS prohibits cherry-picked QA metrics as production performance"
        )
    outcome_rate = stats["with_outcome"] / max(stats["unique_decisions"], 1)
    return "PARTIAL", (
        f"ledger={stats['unique_decisions']} decisions, outcome_linked={stats['with_outcome']} "
        f"({outcome_rate:.0%}); independent accuracy recomputation not executed per cap {cid}"
    )


def phase3_ai(cid: int, result: dict) -> tuple[str, str | None]:
    if cid not in AI_CAP_IDS:
        return "NOT_APPLICABLE", None
    footer = result.get("compliance_footer") or {}
    prov = result.get("provenance") or result.get("certificate")
    if not footer and not prov:
        return "FAIL", "AI-RISK-UNMANAGED: no NIST AI RMF grounding/provenance in response"
    return "PARTIAL", "ai_compliance_footer present; ISO/IEC 42001 lifecycle register not verified"


def phase4_data(cid: int, result: dict) -> tuple[str, str | None]:
    src = result.get("data_source") or result.get("source")
    if result.get("error") and not src:
        return "FAIL", "BCBS 239: no provenance on error path"
    if not src and not result.get("metrics_snapshot"):
        return "PARTIAL", "BCBS 239: source/timeliness stamp missing on some payloads"
    return "PASS", None


def phase5_coso(cid: int, result: dict) -> tuple[str, str | None]:
    if result.get("compliance_footer") or result.get("evidence_class"):
        return "PASS", None
    if cid in {1, 2, 3, 4, 5}:
        return "PARTIAL", "COSO Monitoring: free-tier path lacks explicit evidence_class on all fields"
    return "PARTIAL", "COSO Control Activities: partial automated controls only"


def phase6_security(cid: int) -> tuple[str, str | None]:
    from cap646.ui_pages import user_surface_for

    surf = user_surface_for(cid)
    if not surf or not surf.get("api_path"):
        return "PARTIAL", "no user-facing API path — internal/surface-only capability"
    path = str(surf["api_path"])
    try:
        r = subprocess.run(
            ["rg", "-l", re.escape(path.split("{")[0]), "api/", "dashboard.py", "platform_api.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode != 0:
            return "PARTIAL", f"OWASP API: route prefix for {path} not confirmed in static scan"
    except Exception as exc:
        return "PARTIAL", f"security scan error: {exc}"
    return "PASS", None


def phase7_iso(cid: int, result: dict) -> tuple[str, str | None]:
    if not result.get("backend_module") or not result.get("backend_entrypoint"):
        return "FAIL", "ISO/IEC/IEEE 29148: missing backend binding in runtime result"
    return "PASS", None


def phase8_sre(cid: int) -> tuple[str, str | None]:
    runbook = ROOT / "docs" / "RUNBOOK.md"
    if not runbook.is_file():
        return "PARTIAL", "Google SRE PRR: docs/RUNBOOK.md missing"
    text = runbook.read_text(encoding="utf-8", errors="replace")
    if str(cid) not in text and "batch01" not in text.lower():
        return "PARTIAL", "Google SRE PRR: no per-capability runbook/rollback drill evidence"
    return "PARTIAL", "Google SRE PRR: generic runbook only; no independent rollback drill per cap"


def phase9_fatf(cid: int) -> tuple[str, str | None]:
    if cid not in WALLET_CAP_IDS:
        return "NOT_APPLICABLE", None
    return "PARTIAL", "FATF R.16: wallet/address handling present; travel-rule screening not verified"


PHASES = [
    ("1", None),  # handled separately — needs static_backend
    ("2", phase2_gips),
    ("3", phase3_ai),
    ("4", phase4_data),
    ("5", phase5_coso),
    ("6", lambda cid, r: phase6_security(cid)),
    ("7", phase7_iso),
    ("8", lambda cid, r: phase8_sre(cid)),
    ("9", lambda cid, r: phase9_fatf(cid)),
]


def final_status(phase_results: dict[str, tuple[str, str | None]], runtime: dict) -> tuple[str, str | None, str | None]:
    from cap646.batch01_dedicated import EXPECTED_SURFACE

    cid = int(runtime.get("capability_id") or 0)
    if phase_results["1"][0] == "FAIL":
        note = phase_results["1"][1] or ""
        if "free_tier" in note or "SPLIT routing" in note:
            return "SPLIT-BRAIN-UNVERIFIED", "1", note
        return "CONCEPTUALLY-UNSOUND", "1", note
    if phase_results["2"][0] == "FAIL":
        return "PERFORMANCE-UNVERIFIABLE", "2", phase_results["2"][1]
    if phase_results["3"][0] == "FAIL":
        return "AI-RISK-UNMANAGED", "3", phase_results["3"][1]
    if phase_results["6"][0] == "FAIL":
        return "SECURITY-CRITICAL", "6", phase_results["6"][1]
    if runtime.get("production_spine") != "batch01" or not runtime.get("success"):
        return "NOT_COMPLETE", "—", "runtime spine/success failure"
    surface = str(runtime.get("surface") or "")
    expected = EXPECTED_SURFACE.get(cid)
    generic_surfaces = {"onchain_intelligence", "market_data", "ai_decision_intelligence"}
    if surface in generic_surfaces and (expected is None or surface != expected):
        return "SPLIT-BRAIN-UNVERIFIED", "1", f"generic surface {surface} vs expected {expected}"
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

    catalog = catalog_by_id()
    rows: list[dict] = []
    for cid in range(1, 51):
        name = catalog.get(cid, {}).get("capability", f"CAP-{cid}")
        try:
            runtime = await execute_cap(cid)
        except Exception as exc:
            runtime = {"success": False, "error": str(exc), "capability_id": cid}
        backend, code_lines = backend_source(cid)
        phase_results: dict[str, tuple[str, str | None]] = {}
        phase_results["1"] = phase1_conceptual(cid, runtime, static_backend=backend)
        for pid, fn in PHASES[1:]:
            phase_results[pid] = fn(cid, runtime)  # type: ignore[operator]
        status, failed_phase, evidence_note = final_status(phase_results, runtime)
        failed_standard = PHASE_STANDARD.get(failed_phase or "", "—") if failed_phase else "—"
        evidence_parts: list[str] = []
        if cid in CONCEPTUAL_FLAGS:
            evidence_parts.append(CONCEPTUAL_FLAGS[cid])
        if cid in FREE_TIER_BACKEND_IDS:
            evidence_parts.append("backend=free_tier via batch01_production.py:76-79")
        evidence_parts.append(
            f"runtime success={runtime.get('success')} surface={runtime.get('surface')} "
            f"spine={runtime.get('production_spine')} backend={runtime.get('backend_module')}"
        )
        if code_lines:
            evidence_parts.append(f"code: {code_lines[0][:100]}")
        if evidence_note:
            evidence_parts.append(evidence_note[:120])
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
                "phase_results": {k: v[0] for k, v in phase_results.items()},
            }
        )
    return rows


def write_report(rows: list[dict]) -> Path:
    md = OUT / "BATCH01_INDEPENDENT_NINE_PHASE_REPORT.md"
    lines = [
        "# Batch 01 Independent Nine-Phase Due Diligence Report (IDs 1–50)\n",
        f"**Generated:** {datetime.now(UTC).isoformat()}  \n",
        "**Auditor role:** Third Line of Defense — Independent Assurance  \n",
        "**Standards cited:** SR 26-2, GIPS, NIST AI RMF, BCBS 239, COSO, IIA IPPF, "
        "ISO 25010/12207/29148, OWASP API, MITRE ATLAS, FATF R.16, Google SRE PRR\n\n",
        "## Results Table\n\n",
        "| ID | الاسم | الحالة النهائية | المرحلة التي فشلت | المعيار المرجعي المخالَف | الدليل | مستوى الخطورة |\n",
        "|---:|---|---|---|---|---|---|\n",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['name']} | **{r['status']}** | {r['failed_phase']} | "
            f"{r['failed_standard']} | {r['evidence']} | {r['severity']} |\n"
        )
    counts = Counter(r["status"] for r in rows)
    aligned = counts.get("PRODUCTION-ALIGNED", 0)
    gips = gips_ledger_stats()
    lines.append("\n## Summary\n\n")
    for k, v in counts.most_common():
        lines.append(f"- **{k}:** {v}/50\n")
    lines.append(
        f"\n**GIPS ledger (global):** {gips.get('unique_decisions', 0)} unique decisions, "
        f"{gips.get('with_outcome', 0)} with outcome_id, simulated_only={gips.get('simulated_only')}\n"
    )
    lines.append("\n## رأي اللجنة المستقلة\n\n")
    lines.append(
        f"بصفتنا لجنة تدقيق مستقلة (Third Line of Defense — IIA IPPF)، وبعد تنفيذ المراحل التسع "
        f"حرفيًا على الدفعة الأولى (IDs 1–50) وفق SR 26-2 وCOSO وGIPS، "
        f"نجد **{aligned}/50** قدرة فقط عند `PRODUCTION-ALIGNED` — مقابل **50/50** في RTM الرسمي "
        f"(`docs/BATCH01_OFFICIAL_RTM_1_50.json`). "
        f"**هذه الدفعة لا تستوفي حد «جاهز للفحص الخارجي»** لأسباب قابلة للتحقق: "
        f"(1) **SR 26-2 Phase 1**: صيغ scoring بلا سند منهجي (IDs 8, 9, 33, 34) مع اقتباس سطور كود؛ "
        f"(2) **SPLIT-BRAIN**: IDs 1–4, 10, 21, 38, 39, 45 تُوجَّه عبر `free_tier_capabilities` "
        f"رغم تسجيل RTM كـ batch01 dedicated؛ "
        f"(3) **GIPS Phase 2**: `data/decision_ledger.jsonl` ({gips.get('unique_decisions', 0)} قرار) "
        f"كله SIMULATED/SHADOW — لا أداء إنتاجي قابل للتحقق لقرارات Oracle/Alerts؛ "
        f"(4) **Google SRE PRR Phase 8**: runbook عام بلا rollback drill per-capability. "
        f"نوصي بعدم استخدام RTM `PRODUCTION-ALIGNED` السابق كدليل acquisition دون independent validation خارجية.\n"
    )
    md.write_text("".join(lines), encoding="utf-8")
    (OUT / "BATCH01_INDEPENDENT_NINE_PHASE.json").write_text(
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
