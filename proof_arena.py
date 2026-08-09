"""
BLACKDARK — Proof Arena Lite (U4).

Weekly Human vs Oracle accuracy challenge — transparency game, not gambling.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

_DATA = Path(__file__).resolve().parent / "data" / "proof_arena.jsonl"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def week_id(now: datetime | None = None) -> str:
    dt = now or _utcnow()
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _week_bounds(wid: str) -> tuple[str, str]:
    year_s, week_s = wid.split("-W")
    year, week = int(year_s), int(week_s)
    # Monday of ISO week
    jan4 = datetime(year, 1, 4, tzinfo=UTC)
    start = jan4 - timedelta(days=jan4.weekday()) + timedelta(weeks=week - 1)
    end = start + timedelta(days=7)
    return start.isoformat(), end.isoformat()


def _load_picks() -> list[dict[str, Any]]:
    if not _DATA.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in _DATA.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return rows


def _save_pick(row: dict[str, Any]) -> None:
    _DATA.parent.mkdir(parents=True, exist_ok=True)
    with _DATA.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def oracle_week_score_safe() -> dict[str, Any]:
    try:
        from oracle_track_record import public_track_record

        tr = public_track_record() or {}
        return {
            "hit_rate_percent": float(
                tr.get("hit_rate_percent") or tr.get("direction_hit_rate_percent") or 0
            ),
            "samples": int(tr.get("resolved_count") or tr.get("n") or 0),
            "source": "oracle_track_record",
        }
    except Exception:
        return {"hit_rate_percent": 0.0, "samples": 0, "source": "empty"}


def submit_pick(
    *,
    user_key: str,
    symbol: str,
    direction: str,
    note: str = "",
) -> dict[str, Any]:
    """Human weekly pick: up / down / wait."""
    d = str(direction or "").strip().lower()
    if d not in {"up", "down", "wait"}:
        raise ValueError("direction must be up|down|wait")
    uk = (user_key or "").strip() or "anon"
    sym = (symbol or "BTC").strip().upper()
    wid = week_id()
    row = {
        "id": hashlib.sha256(f"{wid}|{uk}|{sym}|{time.time()}".encode()).hexdigest()[:16],
        "week_id": wid,
        "user_key_hash": hashlib.sha256(uk.encode()).hexdigest()[:24],
        "symbol": sym,
        "direction": d,
        "note": (note or "")[:240],
        "created_at": _utcnow().isoformat(),
        "resolved": False,
        "correct": None,
    }
    _save_pick(row)
    return {"ok": True, "pick": row, "week": build_week_board(wid)}


def build_week_board(wid: str | None = None) -> dict[str, Any]:
    wid = wid or week_id()
    start, end = _week_bounds(wid)
    picks = [p for p in _load_picks() if p.get("week_id") == wid]
    humans = len(picks)
    waits = sum(1 for p in picks if p.get("direction") == "wait")
    ups = sum(1 for p in picks if p.get("direction") == "up")
    downs = sum(1 for p in picks if p.get("direction") == "down")
    resolved = [p for p in picks if p.get("resolved")]
    human_correct = sum(1 for p in resolved if p.get("correct"))
    human_rate = round(100.0 * human_correct / len(resolved), 2) if resolved else None
    oracle = oracle_week_score_safe()

    leaderboard: dict[str, dict[str, Any]] = {}
    for p in picks:
        hk = str(p.get("user_key_hash") or "anon")
        bucket = leaderboard.setdefault(hk, {"picks": 0, "waits": 0, "correct": 0, "resolved": 0})
        bucket["picks"] += 1
        if p.get("direction") == "wait":
            bucket["waits"] += 1
        if p.get("resolved"):
            bucket["resolved"] += 1
            if p.get("correct"):
                bucket["correct"] += 1

    board = sorted(
        (
            {
                "user": k[:8] + "…",
                "picks": v["picks"],
                "waits": v["waits"],
                "hit_rate_percent": round(100.0 * v["correct"] / v["resolved"], 1)
                if v["resolved"]
                else None,
            }
            for k, v in leaderboard.items()
        ),
        key=lambda r: (r["hit_rate_percent"] is not None, r["hit_rate_percent"] or 0, r["picks"]),
        reverse=True,
    )[:25]

    return {
        "surface": "proof_arena_lite",
        "week_id": wid,
        "window": {"start": start, "end": end},
        "generated_at": _utcnow().isoformat(),
        "rules": {
            "game": "Human vs Oracle — weekly direction picks",
            "not": "Not gambling. No prizes. Transparency + discipline only.",
            "directions": ["up", "down", "wait"],
            "scoring": "Resolved against public ledger outcomes when available",
        },
        "human": {
            "picks": humans,
            "up": ups,
            "down": downs,
            "wait": waits,
            "resolved": len(resolved),
            "hit_rate_percent": human_rate,
        },
        "oracle": oracle,
        "matchup_line": (
            f"Week {wid}: Humans "
            f"{human_rate if human_rate is not None else '—'}% vs Oracle "
            f"{oracle.get('hit_rate_percent')}%"
        ),
        "leaderboard": board,
        "recent_picks": list(reversed(picks[-15:])),
        "share_line": (
            f"BLACKDARK Proof Arena {wid} — Human vs Oracle. "
            f"I play discipline, not hype. /proof-arena"
        ),
        "api": {"week": "/api/proof-arena/week", "pick": "POST /api/proof-arena/pick"},
        "page": "/proof-arena",
        "disclaimer": "Educational transparency challenge — not financial advice, not a contest of chance.",
    }
