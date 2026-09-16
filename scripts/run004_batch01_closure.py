#!/usr/bin/env python3
"""Master Contract Run 004 — Batch 01 closure procedures (items 2-6)."""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "institutional_due_diligence_2026" / "batch01_independent_audit"
OUT.mkdir(parents=True, exist_ok=True)

SPLIT_BRAIN_IDS = [1, 2, 3, 4, 10, 21, 38, 39, 45]
BCBS_IDS = [5, 6, 7, 11, 12, 13, 14, 15, 16, 18, 19, 20, 22, 23, 36, 37, 40, 42, 43, 44, 46, 47, 48, 49, 50]
GIPS_IDS = [17, 24, 25, 26, 27, 28, 29, 30, 31, 32, 35, 41]
LEDGER = ROOT / "data" / "decision_ledger.jsonl"

COMMON_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "email": "run004-audit@blackdark.local",
    "tier": "pro",
    "tx_hash": "0xabc123def4567890abcdef1234567890abcdef1234567890abcdef1234567890",
}


def _json_excerpt(obj: Any, max_len: int = 280) -> str:
    s = json.dumps(obj, ensure_ascii=False, default=str)
    return s[:max_len] + ("…" if len(s) > max_len else "")


async def test_split_brain() -> list[dict]:
    from bd_platform.free_tier_capabilities import execute_free_tier_capability
    from cap646.batch01_dedicated import execute as execute_dedicated

    rows = []
    for cid in SPLIT_BRAIN_IDS:
        params = dict(COMMON_PARAMS)
        free = await execute_free_tier_capability(cid, params=params)
        dedicated_error = None
        dedicated = None
        try:
            dedicated = await execute_dedicated(cid, params=params)
        except Exception as exc:
            dedicated_error = f"{type(exc).__name__}: {exc}"

        if dedicated_error:
            result_type = "NO_DEDICATED_IMPLEMENTATION"
            verdict = (
                "NOT_COMPLETE (governance): RTM implies dedicated batch01 backend but "
                f"batch01_dedicated has no handler — only free_tier path exists. Error: {dedicated_error}"
            )
            match = False
        else:
            free_data = free.get("data") or free
            ded_data = dedicated or {}
            match = json.dumps(free_data, sort_keys=True, default=str) == json.dumps(
                ded_data, sort_keys=True, default=str
            )
            if match:
                result_type = "DUPLICATE_CONFIRMED"
                verdict = "Duplicate Confirmed — functional parity; RTM documentation should cite free_tier backend"
            else:
                result_type = "DIVERGENT_OUTPUT"
                verdict = (
                    "NOT_COMPLETE (real): dedicated vs free_tier outputs differ materially — "
                    "production path may not use dedicated logic"
                )

        rows.append(
            {
                "id": cid,
                "result_type": result_type,
                "dedicated_available": dedicated_error is None,
                "dedicated_error": dedicated_error,
                "free_tier_backend": free.get("backend_module"),
                "free_surface": free.get("surface"),
                "outputs_match": match if dedicated_error is None else None,
                "verdict": verdict,
                "free_excerpt": _json_excerpt(free.get("data") or free, 200),
                "dedicated_excerpt": _json_excerpt(dedicated, 200) if dedicated else None,
            }
        )
    return rows


def bcbs_field_audit(payload: dict) -> dict:
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


async def test_bcbs239() -> list[dict]:
    from cap646.runtime import execute_capability

    rows = []
    for cid in BCBS_IDS:
        result = await execute_capability(cid, skip_entitlement=True, params=dict(COMMON_PARAMS))
        audit = bcbs_field_audit(result)
        rows.append(
            {
                "id": cid,
                "missing_fields": audit["missing_fields"],
                "present": audit["present"],
                "payload_excerpt": _json_excerpt(
                    {
                        k: result.get(k)
                        for k in (
                            "capability_id",
                            "surface",
                            "data_source",
                            "source",
                            "timestamp",
                            "freshness",
                            "evidence_class",
                            "success",
                        )
                        if k in result
                    },
                    320,
                ),
            }
        )
    return rows


def analyze_gips_ledger() -> dict:
    stats: dict[str, Any] = {
        "ledger_path": str(LEDGER),
        "exists": LEDGER.is_file(),
        "total_lines": 0,
        "unique_decisions": 0,
        "with_outcome": 0,
        "by_evidence_class": {},
        "first_shadow_live_at": None,
        "first_simulated_at": None,
        "last_at": None,
        "date_span_hours": None,
        "decisions_per_day": {},
    }
    if not stats["exists"]:
        return stats

    seen: set[str] = set()
    with_outcome: set[str] = set()
    dates: list[str] = []
    shadow_dates: list[str] = []
    sim_dates: list[str] = []

    with LEDGER.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            stats["total_lines"] += 1
            row = json.loads(line)
            did = str(row.get("decision_id") or "")
            if did:
                seen.add(did)
            if row.get("outcome_id"):
                with_outcome.add(did)
            ec = str(row.get("evidence_class") or "UNKNOWN")
            stats["by_evidence_class"][ec] = stats["by_evidence_class"].get(ec, 0) + 1
            ts = str(row.get("created_at") or "")
            if ts:
                dates.append(ts)
                day = ts[:10]
                stats["decisions_per_day"][day] = stats["decisions_per_day"].get(day, 0) + 1
                if ec == "SHADOW_LIVE_FORWARD":
                    shadow_dates.append(ts)
                if ec == "SIMULATED":
                    sim_dates.append(ts)

    stats["unique_decisions"] = len(seen)
    stats["with_outcome"] = len(with_outcome)
    if dates:
        stats["first_at"] = min(dates)
        stats["last_at"] = max(dates)
        t0 = datetime.fromisoformat(min(dates).replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(max(dates).replace("Z", "+00:00"))
        stats["date_span_hours"] = round((t1 - t0).total_seconds() / 3600, 2)
    if shadow_dates:
        stats["first_shadow_live_at"] = min(shadow_dates)
    if sim_dates:
        stats["first_simulated_at"] = min(sim_dates)

    # GIPS minimum guidance (SR 26-2 / GIPS composite): typically 12mo or 30+ decisions for stable rate
    stats["gips_minimum_guidance"] = {
        "min_decisions_for_stable_accuracy_estimate": 30,
        "min_calendar_days_recommended": 90,
        "min_production_decisions_required": 30,
        "note": "GIPS requires full population over defined period; SHADOW/SIMULATED excluded per promotion_policy",
    }
    span_days = max(len(stats["decisions_per_day"]), 1)
    rate_per_day = stats["unique_decisions"] / span_days
    stats["accumulation_rate_per_day"] = round(rate_per_day, 2)
    need = max(0, 30 - stats["unique_decisions"])
    if rate_per_day > 0 and span_days < 90:
        stats["projected_days_to_30_decisions"] = round(need / rate_per_day, 1) if need else 0
        stats["projected_days_to_90_day_window"] = round(max(0, 90 - span_days), 1)
    else:
        stats["projected_days_to_30_decisions"] = None
        stats["projected_days_to_90_day_window"] = None

    prod_classes = {k: v for k, v in stats["by_evidence_class"].items() if k not in ("SIMULATED", "SHADOW_LIVE_FORWARD")}
    stats["has_production_decisions"] = sum(prod_classes.values()) > 0
    stats["reclassification"] = (
        "KEEP PERFORMANCE-UNVERIFIABLE"
        if not stats["has_production_decisions"]
        else "REVIEW — production decisions present"
    )
    stats["reclassification_reason"] = (
        "Project newness + shadow-only ledger (span "
        f"{stats.get('date_span_hours', '?')}h, {stats['unique_decisions']} decisions) — "
        "NOT a collection fault; promotion_policy correctly segregates SIMULATED/SHADOW. "
        "Insufficient calendar time for GIPS full-population accuracy."
        if not stats["has_production_decisions"]
        else "Production-class decisions detected — re-run GIPS recomputation"
    )
    return stats


async def test_cap34_three_inputs() -> list[dict]:
    from cap646.batch01_dedicated import execute as execute_dedicated

    cases = [
        {"label": "user_forces_Opportunity", "verdict": "Opportunity", "risk_score": 1.0},
        {"label": "user_forces_Risk", "verdict": "Risk", "risk_score": 9.5},
        {"label": "user_forces_Neutral", "verdict": "Neutral", "risk_score": 5.0},
    ]
    rows = []
    for case in cases:
        params = dict(COMMON_PARAMS)
        params["verdict"] = case["verdict"]
        params["risk_score"] = case["risk_score"]
        result = await execute_dedicated(34, params=params)
        answer = (result.get("clear_answer") or {})
        rows.append(
            {
                "input": case,
                "output_verdict": answer.get("verdict"),
                "output_risk_score": answer.get("risk_score"),
                "analysis_inputs": result.get("analysis_inputs"),
                "user_verdict_ignored": result.get("analysis_inputs", {}).get("user_verdict_ignored"),
                "one_line_en": (answer.get("one_line") or {}).get("en"),
            }
        )
    return rows


async def main() -> None:
    cap34 = await test_cap34_three_inputs()
    split = await test_split_brain()
    bcbs = await test_bcbs239()
    gips = analyze_gips_ledger()

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "run": "004",
        "item1_cap34_live_test": cap34,
        "item2_split_brain": split,
        "item3_bcbs239": bcbs,
        "item4_gips": gips,
    }
    path = OUT / "RUN004_BATCH01_CLOSURE_EVIDENCE.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {path}")
    print("Cap34 verdicts:", [r["output_verdict"] for r in cap34])
    print("Split-brain types:", {r["id"]: r["result_type"] for r in split})
    print("GIPS reclassification:", gips.get("reclassification"))


if __name__ == "__main__":
    asyncio.run(main())
