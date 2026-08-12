"""
BLACKDARK — F9 Sealed Desk Duel.

Two parties seal simultaneous predictions for the same window; public reveal board.
No gambling — accountability duel for analysts/funds.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("sealed_desk_duels.jsonl")
_DATA_BASE = Path(__file__).resolve().parent / "data"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _append(row: dict[str, Any]) -> None:
    path = ensure_under(_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with path.open("a", encoding="utf-8") as fh:  # NOSONAR pythonsecurity:S2083
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read_all() -> list[dict[str, Any]]:
    if not _PATH.exists():
        return []
    rows = []
    for line in _PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _rewrite(rows: list[dict[str, Any]]) -> None:
    path = ensure_under(_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")  # NOSONAR pythonsecurity:S2083


def _commitment(desk: str, verdict: str, nonce: str) -> str:
    return hashlib.sha256(f"{desk}|{verdict}|{nonce}".encode()).hexdigest()


def create_duel(
    *,
    asset: str = "BTC",
    window_minutes: int = 60,
    host_desk: str = "Desk A",
    host_verdict: str = "WAIT",
    invitee_desk: str = "Desk B",
) -> dict[str, Any]:
    now = _utcnow()
    reveal_at = now + timedelta(minutes=max(5, int(window_minutes)))
    nonce_a = secrets.token_hex(8)
    duel = {
        "duel_id": f"duel_{secrets.token_hex(6)}",
        "asset": asset.upper(),
        "window_minutes": int(window_minutes),
        "created_at": now.isoformat(),
        "reveal_at": reveal_at.isoformat(),
        "status": "awaiting_challenger",
        "host": {
            "desk": host_desk,
            "verdict": host_verdict.upper(),
            "nonce": nonce_a,
            "commitment": _commitment(host_desk, host_verdict.upper(), nonce_a),
        },
        "challenger": {
            "desk": invitee_desk,
            "verdict": None,
            "nonce": None,
            "commitment": None,
        },
        "gambling": False,
        "scoring": "sealed_simultaneous_reveal_v1",
    }
    _append(duel)
    return public_duel_view(duel)


def accept_duel(duel_id: str, *, desk: str, verdict: str) -> dict[str, Any]:
    rows = _read_all()
    target = None
    for r in rows:
        if r.get("duel_id") == duel_id:
            target = r
            break
    if not target:
        raise ValueError("duel_not_found")
    if target.get("status") not in {"awaiting_challenger", "sealed"}:
        raise ValueError("duel_not_open")
    nonce = secrets.token_hex(8)
    v = verdict.upper()
    target["challenger"] = {
        "desk": desk,
        "verdict": v,
        "nonce": nonce,
        "commitment": _commitment(desk, v, nonce),
    }
    target["status"] = "sealed"
    target["sealed_at"] = _utcnow().isoformat()
    _rewrite(rows)
    return public_duel_view(target)


def reveal_duel(duel_id: str, *, force: bool = False) -> dict[str, Any]:
    rows = _read_all()
    target = None
    for r in rows:
        if r.get("duel_id") == duel_id:
            target = r
            break
    if not target:
        raise ValueError("duel_not_found")
    reveal_at = datetime.fromisoformat(str(target["reveal_at"]))
    if reveal_at.tzinfo is None:
        reveal_at = reveal_at.replace(tzinfo=UTC)
    if not force and _utcnow() < reveal_at:
        return {
            **public_duel_view(target),
            "revealed": False,
            "message": "Window not elapsed — commitments visible, verdicts sealed",
        }
    target["status"] = "revealed"
    target["revealed_at"] = _utcnow().isoformat()
    host_v = (target.get("host") or {}).get("verdict")
    chal_v = (target.get("challenger") or {}).get("verdict")
    target["result"] = {
        "agree": bool(host_v and chal_v and host_v == chal_v),
        "host_verdict": host_v,
        "challenger_verdict": chal_v,
    }
    _rewrite(rows)
    return public_duel_view(target, reveal=True)


def public_duel_view(row: dict[str, Any], *, reveal: bool = False) -> dict[str, Any]:
    status = row.get("status")
    show = reveal or status == "revealed"
    host = row.get("host") or {}
    chal = row.get("challenger") or {}
    return {
        "duel_id": row.get("duel_id"),
        "asset": row.get("asset"),
        "window_minutes": row.get("window_minutes"),
        "created_at": row.get("created_at"),
        "reveal_at": row.get("reveal_at"),
        "status": status,
        "host": {
            "desk": host.get("desk"),
            "commitment": host.get("commitment"),
            "verdict": host.get("verdict") if show else None,
        },
        "challenger": {
            "desk": chal.get("desk"),
            "commitment": chal.get("commitment"),
            "verdict": chal.get("verdict") if show else None,
        },
        "result": row.get("result") if show else None,
        "gambling": False,
    }


def build_duel_board(*, limit: int = 20) -> dict[str, Any]:
    rows = _read_all()
    if not rows:
        d = create_duel(host_desk="Black Desk", host_verdict="WAIT", invitee_desk="Rival Desk")
        accept_duel(d["duel_id"], desk="Rival Desk", verdict="ACT")
        rows = _read_all()
    views = [public_duel_view(r, reveal=(r.get("status") == "revealed")) for r in rows[-limit:]]
    views.reverse()
    share = (
        f"BLACKDARK Sealed Desk Duel · {len(views)} bouts · "
        f"simultaneous sealed calls, public reveal · /desk-duel · Not gambling · Not financial advice"
    )
    return {
        "feature_id": "F9",
        "surface": "sealed_desk_duel",
        "product_complete": False,
        "generated_at": _utcnow().isoformat(),
        "duels": views,
        "count": len(views),
        "headline": "Sealed Desk Duel — argue with a hash, not a hot take",
        "doctrine": "No Twitter noise — simultaneous sealed predictions, then public reveal",
        "share_text": share,
        "share_urls": {
            "x": f"https://twitter.com/intent/tweet?text={quote(share)}",
            "whatsapp": f"https://wa.me/?text={quote(share)}",
        },
        "page": "/desk-duel",
        "api": "/api/desk-duel",
        "create_api": "POST /api/desk-duel",
        "accept_api": "POST /api/desk-duel/accept",
        "reveal_api": "POST /api/desk-duel/reveal",
    }
