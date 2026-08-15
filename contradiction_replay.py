"""
BLACKDARK — Contradiction Replay Clip (U1).

15-second shareable card: why we WAITED when dimensions conflicted.
Viral atom: survival story > profit screenshot.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

_DATA = Path(__file__).resolve().parent / "data" / "contradiction_replays.jsonl"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _clip_id(symbol: str, bullish: list[Any], bearish: list[Any]) -> str:
    raw = f"{symbol}|{sorted(map(str, bullish))}|{sorted(map(str, bearish))}|{int(time.time()) // 60}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _snapshot_conflict_meta(symbol: str, score: float | None) -> tuple[dict[str, Any], float | None]:
    try:
        from ai_oracle import get_latest_oracle_snapshot

        snap = get_latest_oracle_snapshot(symbol) or {}
        bd = snap.get("breakdown") or {}
        conflicts = bd.get("conflicts") or {}
        meta = {
            "severity": conflicts.get("severity") or "none",
            "bullish": conflicts.get("bullish") or [],
            "bearish": conflicts.get("bearish") or [],
            "message": conflicts.get("message") or "",
            "veto": bool(conflicts.get("severity") == "severe"),
            "action": "WAIT" if conflicts.get("severity") in ("severe", "mild") else "CLEAR",
        }
        if score is None:
            score = float(snap.get("score") or 0)
        return meta, score
    except Exception:
        return {
            "severity": "severe",
            "bullish": ["technical"],
            "bearish": ["sentiment", "macro"],
            "message": "Demo conflict — technical buy vs fear + macro drag",
            "veto": True,
            "action": "WAIT",
        }, score


def _conflict_meta(symbol: str, conflict: dict[str, Any] | None, score: float | None) -> tuple[dict[str, Any], float | None]:
    meta = dict(conflict or {})
    if meta:
        return meta, score
    return _snapshot_conflict_meta(symbol, score)


def _replay_frames(symbol: str, bullish: list[Any], bearish: list[Any], action: str, severity: str) -> list[dict[str, Any]]:
    return [
        {"t": 0, "label": "Signal noise", "text": f"{symbol}: conflicting dimensions detected"},
        {
            "t": 5,
            "label": "Bullish side",
            "text": ", ".join(map(str, bullish)) or "none",
        },
        {
            "t": 10,
            "label": "Bearish side",
            "text": ", ".join(map(str, bearish)) or "none",
        },
        {
            "t": 15,
            "label": "Decision",
            "text": f"{action} — Contradiction Veto ({severity})",
        },
    ]


def _persist_wait_replay(
    card: dict[str, Any],
    cid: str,
    symbol: str,
    bullish: list[Any],
    bearish: list[Any],
    meta: dict[str, Any],
) -> None:
    try:
        from kill_rate_board import record_kill

        record_kill(
            "contradiction_veto",
            f"{meta.get('severity')}:{symbol}",
            meta={"clip_id": cid, "bullish": bullish, "bearish": bearish},
        )
    except Exception:
        pass
    try:
        _DATA.parent.mkdir(parents=True, exist_ok=True)
        with _DATA.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(card, ensure_ascii=False) + "\n")
    except OSError:
        pass


def build_contradiction_replay(
    *,
    symbol: str = "BTC",
    conflict: dict[str, Any] | None = None,
    score: float | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Build a 15s WAIT replay card from conflict meta or live oracle breakdown."""
    meta, score = _conflict_meta(symbol, conflict, score)

    bullish = list(meta.get("bullish") or [])
    bearish = list(meta.get("bearish") or [])
    severity = str(meta.get("severity") or "none")
    action = str(meta.get("action") or ("I_DONT_KNOW" if severity in ("mild", "severe") else "CLEAR"))
    cid = _clip_id(symbol, bullish, bearish)

    share_text = (
        f"BLACKDARK I DON'T KNOW replay on {symbol}: "
        f"{', '.join(map(str, bullish)) or '—'} vs {', '.join(map(str, bearish)) or '—'} → {action}. "
        f"We publish the refusal. /contradiction-replay?id={cid}"
    )

    card = {
        "surface": "contradiction_replay_clip",
        "clip_id": cid,
        "generated_at": _utcnow(),
        "duration_seconds": 15,
        "symbol": symbol.upper(),
        "action": action,
        "severity": severity,
        "score": score,
        "bullish": bullish,
        "bearish": bearish,
        "message": meta.get("message") or "Dimensions disagreed — system refused the trade.",
        "frames": _replay_frames(symbol, bullish, bearish, action, severity),
        "headline": f"Why we said I DON'T KNOW on {symbol.upper()}",
        "share_text": share_text,
        "share_urls": {
            "x": f"https://twitter.com/intent/tweet?text={quote(share_text)}",
            "whatsapp": f"https://wa.me/?text={quote(share_text)}",
            "telegram": f"https://t.me/share/url?url={quote('https://blackdark.io/contradiction-replay')}&text={quote(share_text)}",
        },
        "verify_url": f"/contradiction-replay?id={cid}",
        "api": "/api/contradiction-replay",
        "disclaimer": "Not financial advice. I DON'T KNOW is a transparency product, not a profit guarantee.",
    }

    if persist and action in {"WAIT", "I_DONT_KNOW"}:
        _persist_wait_replay(card, cid, symbol, bullish, bearish, meta)

    return card


def get_replay(clip_id: str) -> dict[str, Any] | None:
    if not _DATA.exists() or not clip_id:
        return None
    try:
        for line in reversed(_DATA.read_text(encoding="utf-8").splitlines()):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("clip_id") == clip_id:
                return row
    except OSError:
        return None
    return None


def list_recent_replays(limit: int = 20) -> list[dict[str, Any]]:
    if not _DATA.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in reversed(_DATA.read_text(encoding="utf-8").splitlines()):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(rows) >= limit:
                break
    except OSError:
        return []
    return rows
