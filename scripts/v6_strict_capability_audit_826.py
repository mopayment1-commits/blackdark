#!/usr/bin/env python3
"""Strict v6 audit of all 826 capabilities — institutional committee evidence."""

from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "V6_STRICT_826_AUDIT_REPORT.json"
SUMMARY = ROOT / "V6_STRICT_826_AUDIT_SUMMARY.json"
MD_OUT = ROOT / "BLACKDARK_V6_STRICT_826_INSTITUTIONAL_AUDIT_AR_2026.md"


async def _audit_one(cap_id: int) -> dict:
    from cap646.v6_strict_dod import verify_v6_strict

    try:
        return await verify_v6_strict(cap_id)
    except Exception as exc:
        return {
            "capability_id": cap_id,
            "verdict": "AUDIT_ERROR",
            "PASS_ENGINEERING": False,
            "error": str(exc)[:200],
        }


async def _audit_all(concurrency: int = 2) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)

    async def _guarded(cid: int) -> dict:
        async with sem:
            return await _audit_one(cid)

    return await asyncio.gather(*[_guarded(i) for i in range(1, 827)])


def _batch_name(cid: int) -> str:
    return f"batch{(cid - 1) // 50 + 1:02d}"


def _write_markdown(rows: list[dict], summary: dict) -> None:
    lines = [
        "# تقرير التدقيق المؤسسي الصارم — 826 قدرة (v6)",
        "",
        f"**التاريخ:** {summary['generated_at'][:10]}",
        f"**المرجع الحاكم:** BLACKDARK Institutional Capability Standard 2026 v6 §2.1",
        "",
        "## الحكم النهائي",
        "",
        f"| المؤشر | القيمة |",
        f"|--------|--------|",
        f"| PASS_ENGINEERING (صارم v6) | **{summary['pass_engineering']}/826** |",
        f"| NOT_COMPLETE | **{summary['not_complete']}/826** |",
        f"| CANONICALLY_COVERED | {summary['canonically_covered']} |",
        f"| EXTERNAL_BLOCKED | {summary['external_blocked']} |",
        f"| نسبة الاكتمال الصارم | **{summary['pass_pct']}%** |",
        f"| جاهز لتقديم لجنة (ادّعاء اكتمال كامل) | **{'لا' if summary['pass_engineering'] < 826 else 'نعم'}** |",
        "",
        "> **قاعدة v6:** لا PASS_ENGINEERING بدون إثبات الهدف التصميمي + 13 بوابة.",
        "",
        "## أكثر البوابات الفاشلة",
        "",
    ]
    for gate, count in summary.get("top_failed_gates", [])[:8]:
        lines.append(f"- `{gate}`: {count} قدرة")
    lines.extend(["", "## حسب الدفعة (batch)", ""])
    for batch, data in sorted(summary.get("by_batch", {}).items()):
        lines.append(f"- **{batch}**: {data['pass']}/{data['total']} PASS ({data['pct']}%)")
    lines.extend(
        [
            "",
            "## مستثنى من النطاق",
            "- نشر Railway",
            "- pentest/SOC2 خارجي",
            "- موافقة بشرية",
            "",
            "## أمر التحقق",
            "```bash",
            "python3 scripts/v6_strict_capability_audit_826.py",
            "```",
        ]
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows = asyncio.run(_audit_all(concurrency=2))
    OUT.write_text(json.dumps({"capabilities": rows}, indent=2, ensure_ascii=False), encoding="utf-8")

    verdicts = Counter(r.get("verdict") for r in rows)
    pass_eng = sum(1 for r in rows if r.get("PASS_ENGINEERING"))
    binding = Counter(r.get("binding_source") for r in rows if not r.get("PASS_ENGINEERING"))
    failed_gates: Counter[str] = Counter()
    for r in rows:
        for g in r.get("failed_gates") or []:
            failed_gates[g] += 1

    by_batch: dict[str, dict] = {}
    for r in rows:
        b = _batch_name(r["capability_id"])
        by_batch.setdefault(b, {"pass": 0, "total": 0})
        by_batch[b]["total"] += 1
        if r.get("PASS_ENGINEERING"):
            by_batch[b]["pass"] += 1
    for b in by_batch:
        t = by_batch[b]["total"]
        by_batch[b]["pct"] = round(by_batch[b]["pass"] / t * 100, 1) if t else 0

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology": "v6 §2.1 thirteen gates — no catalog inflation",
        "pass_engineering": pass_eng,
        "not_complete": verdicts.get("NOT_COMPLETE", 0) + verdicts.get("AUDIT_ERROR", 0),
        "canonically_covered": verdicts.get("CANONICALLY_COVERED", 0),
        "external_blocked": verdicts.get("EXTERNAL_BLOCKED", 0),
        "pass_pct": round(pass_eng / 826 * 100, 2),
        "committee_ready_full_completion_claim": pass_eng >= 826,
        "top_failed_gates": failed_gates.most_common(15),
        "top_binding_sources_failed": binding.most_common(10),
        "by_batch": by_batch,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown(rows, summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["committee_ready_full_completion_claim"] else 1


if __name__ == "__main__":
    sys.exit(main())
