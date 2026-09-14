#!/usr/bin/env python3
"""True v6 institutional audit — governing file aligned, no inflated PASS claims."""

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

OUT = ROOT / "V6_TRUE_INSTITUTIONAL_AUDIT_REPORT.json"
SUMMARY = ROOT / "V6_TRUE_INSTITUTIONAL_AUDIT_SUMMARY.json"
MD_OUT = ROOT / "BLACKDARK_V6_TRUE_INSTITUTIONAL_AUDIT_AR_2026.md"


async def _audit_one(cap_id: int) -> dict:
    from cap646.v6_true_institutional_dod import verify_v6_true_institutional

    try:
        return await verify_v6_true_institutional(cap_id)
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
    from cap646.batch_constants import official_batch_name

    return official_batch_name(cid)


def _write_markdown(rows: list[dict], summary: dict) -> None:
    lines = [
        "# تقرير التدقيق المؤسسي الحقيقي — 826 قدرة (v6)",
        "",
        f"**التاريخ:** {summary['generated_at'][:10]}",
        "**المرجع الحاكم:** `BLACKDARK_Institutional_Capability_Standard_2026_v6(1).md`",
        "",
        "> **تنبيه:** هذا التقرير يلغي ادعاء 826/826 السابق. التدقيق السابق (`v6_strict_dod`) كان سطحيًا.",
        "",
        "## الحكم الصادق",
        "",
        f"| المؤشر | القيمة |",
        f"|--------|--------|",
        f"| PASS_ENGINEERING (v6 حقيقي) | **{summary['pass_engineering']}/826** |",
        f"| NOT_COMPLETE | **{summary['not_complete']}/826** |",
        f"| CANONICALLY_COVERED | {summary['canonically_covered']} |",
        f"| EXTERNAL_BLOCKED | {summary['external_blocked']} |",
        f"| نسبة الاكتمال الحقيقي | **{summary['pass_pct']}%** |",
        f"| اكتمال عبر ربط keyword/semantic سطحي | {summary['superficial_binding_pass']} |",
        f"| جاهز لتقديم لجنة (ادّعاء اكتمال كامل) | **لا** |",
        "",
        "## لماذا التقرير السابق مرفوض",
        "",
        "1. معظم البوابات (G06/G08/G11) كانت `True` تلقائيًا بدون دليل.",
        "2. `capability_keyword` و`semantic_track_*` يمرّران 585+ قدرة على 26 backend مشترك فقط.",
        "3. v6 §1170–1171 يمنع أن تكون القدرات أسماء/metadata فوق سلوك واحد.",
        "4. v6 §139.5: 826 صفًا أخضر ≠ 826 قدرة محسومة دلاليًا.",
        "",
        "## أكثر البوابات الفاشلة",
        "",
    ]
    for gate, count in summary.get("top_failed_gates", [])[:10]:
        lines.append(f"- `{gate}`: {count} قدرة")
    lines.extend(["", "## حسب الدفعة", ""])
    for batch, data in sorted(summary.get("by_batch", {}).items()):
        lines.append(f"- **{batch}**: {data['pass']}/{data['total']} PASS ({data['pct']}%)")
    lines.extend(
        [
            "",
            "## أمر التحقق",
            "```bash",
            "python3 scripts/v6_true_institutional_audit_826.py",
            "```",
        ]
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows = asyncio.run(_audit_all(concurrency=2))
    OUT.write_text(json.dumps({"capabilities": rows}, indent=2, ensure_ascii=False), encoding="utf-8")

    pass_eng = sum(1 for r in rows if r.get("PASS_ENGINEERING"))
    superficial_pass = sum(
        1 for r in rows if r.get("PASS_ENGINEERING") and r.get("superficial_binding")
    )
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
        "methodology": "v6 governing file §2.1 + §34 + §1170–1171 — rejects keyword/semantic bulk routing",
        "pass_engineering": pass_eng,
        "not_complete": sum(1 for r in rows if r.get("verdict") == "NOT_COMPLETE"),
        "canonically_covered": sum(1 for r in rows if r.get("verdict") == "CANONICALLY_COVERED"),
        "external_blocked": sum(1 for r in rows if r.get("verdict") == "EXTERNAL_BLOCKED"),
        "pass_pct": round(pass_eng / 826 * 100, 2),
        "superficial_binding_pass": superficial_pass,
        "committee_ready_full_completion_claim": False,
        "prior_superficial_audit_retracted": True,
        "top_failed_gates": failed_gates.most_common(12),
        "by_batch": by_batch,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown(rows, summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    sys.exit(main())
