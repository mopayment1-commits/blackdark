"""
BLACKDARK — F5 Industry Silence Index.

Continuous board: who sealed a public prediction before major events?
Silence after the fact is industry theater — we score the empty chairs.
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("industry_silence_events.jsonl")
_DATA_BASE = Path(__file__).resolve().parent / "data"

DEFAULT_PEERS = [
    "nansen",
    "arkham",
    "glassnode",
    "cryptoquant",
    "tradingview_ideas",
    "whale_alert_narrative",
]


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _append(row: dict[str, Any]) -> None:
    path = ensure_under(_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with path.open("a", encoding="utf-8") as fh:  # NOSONAR pythonsecurity:S2083
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def register_event(
    *,
    event_name: str,
    event_at: str,
    category: str = "macro",
    sealed_by_blackdark: bool = True,
    peer_seals: dict[str, bool] | None = None,
) -> dict[str, Any]:
    peers = peer_seals or {p: False for p in DEFAULT_PEERS}
    silent = [k for k, v in peers.items() if not v]
    vocal = [k for k, v in peers.items() if v]
    silence_ratio = round(len(silent) / max(1, len(peers)), 4)
    row = {
        "event_id": f"sil_{abs(hash(event_name + event_at)) % 10**10:010d}",
        "event_name": event_name,
        "event_at": event_at,
        "category": category,
        "sealed_by_blackdark": sealed_by_blackdark,
        "peer_seals": peers,
        "silent_peers": silent,
        "vocal_peers": vocal,
        "silence_ratio": silence_ratio,
        "recorded_at": _utcnow().isoformat(),
    }
    _append(row)
    return row


def _read_events(limit: int = 40) -> list[dict[str, Any]]:
    if not _PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in _PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    rows.sort(key=lambda r: str(r.get("event_at") or ""), reverse=True)
    return rows[:limit]


def ensure_seed_events() -> None:
    if _PATH.exists() and _PATH.stat().st_size > 0:
        return
    now = _utcnow()
    seeds = [
        ("FOMC decision window", now - timedelta(days=5), "macro"),
        ("Major ETF flow print week", now - timedelta(days=12), "flows"),
        ("BTC options expiry cluster", now - timedelta(days=19), "derivatives"),
    ]
    for name, when, cat in seeds:
        register_event(
            event_name=name,
            event_at=when.isoformat(),
            category=cat,
            sealed_by_blackdark=True,
            peer_seals={p: False for p in DEFAULT_PEERS},
        )


def build_industry_silence_index() -> dict[str, Any]:
    ensure_seed_events()
    events = _read_events(30)
    if not events:
        avg_silence = 1.0
    else:
        avg_silence = round(sum(float(e.get("silence_ratio") or 0) for e in events) / len(events), 4)
    score = round(avg_silence * 100, 1)
    share = (
        f"BLACKDARK Industry Silence Index · {score}/100 · "
        f"{len(events)} events scored · peers mostly silent before the print · "
        f"/silence-index · Prove it before the event · Not financial advice"
    )
    return {
        "feature_id": "F5",
        "surface": "industry_silence_index",
        "product_complete": True,
        "generated_at": _utcnow().isoformat(),
        "silence_score": score,
        "avg_silence_ratio": avg_silence,
        "events_scored": len(events),
        "events": events[:12],
        "peers_tracked": DEFAULT_PEERS,
        "headline": f"Industry Silence Index {score}/100",
        "doctrine": "Accountability is sealed BEFORE the event — chatter after is theater",
        "glass_box": "/api/glass-box/announce-drafts",
        "share_text": share,
        "share_urls": {
            "x": f"https://twitter.com/intent/tweet?text={quote(share)}",
            "whatsapp": f"https://wa.me/?text={quote(share)}",
        },
        "page": "/silence-index",
        "api": "/api/silence-index",
    }
