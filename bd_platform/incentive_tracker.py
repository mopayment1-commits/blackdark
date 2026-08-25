"""
Incentive Tracker Module — Feature #203 (Sprint 2).

Tracks airdrop and incentive programs with mandatory source/status,
Fee DB (#130) integration, non-hideable disclaimer, and timeline visibility.

NOT displayed as an "opportunity" — factual program tracker only.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.IncentiveTracker")

_FEATURE_ID = 203
_STORE_PATH = Path("data/incentive_tracker.json")
_SEED_PATH = Path("data/incentive_programs_seed.json")
_DISCLAIMER = "Incentives subject to change. Impermanent loss possible."
_DISCLAIMER_AR = "الحوافز عرضة للتغيير. خسارة غير دائمة محتملة."
_MIN_PROTOCOL_COVERAGE = 50

Status = Literal["active", "ended", "upcoming"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_store() -> dict[str, Any]:
    if not _STORE_PATH.is_file():
        return _bootstrap_store()
    try:
        return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _bootstrap_store()


def _bootstrap_store() -> dict[str, Any]:
    programs: dict[str, Any] = {}
    if _SEED_PATH.is_file():
        try:
            rows = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
            for row in rows:
                programs[row["id"]] = {**row, "updated_at": _utcnow()}
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("incentive seed load failed: %s", exc)
    store = {"programs": programs, "updated_at": _utcnow()}
    _save_store(store)
    return store


def _save_store(blob: dict[str, Any]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    blob["updated_at"] = _utcnow()
    _STORE_PATH.write_text(json.dumps(blob, indent=2, ensure_ascii=False), encoding="utf-8")


def _infer_status(start: str, end: str) -> Status:
    today = date.today()
    try:
        s = date.fromisoformat(start)
        e = date.fromisoformat(end)
    except ValueError:
        return "active"
    if today < s:
        return "upcoming"
    if today > e:
        return "ended"
    return "active"


def _fee_db_context(program: dict[str, Any]) -> dict[str, Any]:
    """Fee DB (#130) — mandatory cost context for incentive surfaces."""
    try:
        from fee_matrix import maker_fee, taker_fee

        ex = "binance"
        maker = maker_fee(ex)
        taker = taker_fee(ex)
        return {
            "fee_db_feature_id": 130,
            "estimated_taker_fee_pct": round((taker or 0.001) * 100, 4),
            "estimated_maker_fee_pct": round((maker or 0.001) * 100, 4),
            "hidden_spread_note": "Add spread + IL via Fee DB for full cost",
            "fee_db_available": maker is not None and taker is not None,
        }
    except Exception:
        return {
            "fee_db_feature_id": 130,
            "fee_db_available": False,
            "note": "Fee DB unavailable — cost estimate omitted",
        }


def _format_display(program: dict[str, Any]) -> str:
    apy = program.get("apy_pct", 0)
    risk = program.get("risk_score", 5)
    name = program.get("program_name") or program.get("protocol")
    return f"Incentive Program: {name} | APY: {apy}% | Risk: {risk}/10"


def _format_timeline(program: dict[str, Any]) -> str:
    tl = program.get("timeline") or {}
    return (
        f"Start: {tl.get('start', 'N/A')} | End: {tl.get('end', 'N/A')} | "
        f"Cliff: {tl.get('cliff_days', 0)} days"
    )


def _enrich_program(row: dict[str, Any]) -> dict[str, Any]:
    tl = row.get("timeline") or {}
    status = row.get("status") or _infer_status(str(tl.get("start", "")), str(tl.get("end", "")))
    enriched = {
        **row,
        "status": status,
        "source_line": f"Source: {row.get('source', 'Unknown')} | Status: {status.title()}",
        "display": _format_display(row),
        "timeline_display": _format_timeline(row),
        "disclaimer": _DISCLAIMER,
        "disclaimer_ar": _DISCLAIMER_AR,
        "disclaimer_hideable": False,
        "not_an_opportunity": True,
        "fee_context": _fee_db_context(row),
    }
    return enriched


def list_incentive_programs(
    *,
    status: Status | None = None,
    protocol: str | None = None,
    chain: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    store = _load_store()
    rows = [_enrich_program(p) for p in store.get("programs", {}).values()]

    if status:
        rows = [r for r in rows if r.get("status") == status]
    if protocol:
        rows = [r for r in rows if protocol.lower() in str(r.get("protocol", "")).lower()]
    if chain:
        rows = [r for r in rows if str(r.get("chain", "")).lower() == chain.lower()]

    rows.sort(key=lambda r: (r.get("status") != "active", r.get("protocol", "")))
    protocol_count = len({r.get("protocol") for r in store.get("programs", {}).values()})

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "count": len(rows[:limit]),
        "protocol_coverage": protocol_count,
        "min_protocol_target": _MIN_PROTOCOL_COVERAGE,
        "coverage_met": protocol_count >= _MIN_PROTOCOL_COVERAGE,
        "programs": rows[:limit],
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }


def get_incentive_program(program_id: str) -> dict[str, Any]:
    store = _load_store()
    row = store.get("programs", {}).get(program_id)
    if not row:
        return {"ok": False, "error": "program_not_found"}
    program = _enrich_program(row)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "program": program,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }


def incentive_tracker_status() -> dict[str, Any]:
    store = _load_store()
    programs = list(store.get("programs", {}).values())
    protocols = {p.get("protocol") for p in programs}
    statuses = {}
    for p in programs:
        st = p.get("status") or _infer_status(
            str((p.get("timeline") or {}).get("start", "")),
            str((p.get("timeline") or {}).get("end", "")),
        )
        statuses[st] = statuses.get(st, 0) + 1

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "module": "Incentive Tracker",
        "program_count": len(programs),
        "protocol_count": len(protocols),
        "min_protocol_target": _MIN_PROTOCOL_COVERAGE,
        "coverage_met": len(protocols) >= _MIN_PROTOCOL_COVERAGE,
        "status_breakdown": statuses,
        "source_status_visible": True,
        "fee_db_integrated": True,
        "fee_db_feature_id": 130,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "not_displayed_as_opportunity": True,
        "timestamp": _utcnow(),
    }
