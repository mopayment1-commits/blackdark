"""
BLACKDARK — Since You Left Top-3 (U5).

On return: the three most important changes since the user's last visit.
Habit loop for Proof Pass / Pro — not a seventh hero button.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_DATA = Path(__file__).resolve().parent / "data" / "since_you_left.json"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_store() -> dict[str, Any]:
    if not _DATA.exists():
        return {"users": {}}
    try:
        return json.loads(_DATA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"users": {}}


def _save_store(store: dict[str, Any]) -> None:
    _DATA.parent.mkdir(parents=True, exist_ok=True)
    _DATA.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def capture_market_snapshot() -> dict[str, Any]:
    """Point-in-time facts used to compute Top-3 deltas."""
    snap: dict[str, Any] = {"captured_at": _utcnow(), "ts": time.time()}

    try:
        from kill_rate_board import build_kill_rate_board

        k = build_kill_rate_board()
        snap["kill_rate_percent"] = float(k["metrics"].get("kill_rate_percent") or 0)
        snap["total_kills"] = int(k["metrics"].get("total_kills") or 0)
    except Exception:
        snap["kill_rate_percent"] = 0.0
        snap["total_kills"] = 0

    try:
        from net_edge_truth import net_edge_truth_status

        t = net_edge_truth_status()
        snap["net_edge_reject_rate"] = float(t.get("reject_rate") or 0)
        snap["net_edge_evaluated"] = int(t.get("evaluated") or 0)
    except Exception:
        snap["net_edge_reject_rate"] = 0.0
        snap["net_edge_evaluated"] = 0

    try:
        from oracle_track_record import public_track_record

        tr = public_track_record() or {}
        snap["accuracy_hit_rate"] = float(
            tr.get("hit_rate_percent") or tr.get("direction_hit_rate_percent") or 0
        )
        snap["accuracy_samples"] = int(tr.get("resolved_count") or tr.get("n") or 0)
    except Exception:
        snap["accuracy_hit_rate"] = 0.0
        snap["accuracy_samples"] = 0

    try:
        from locked_predictions import list_locked_predictions

        locked = list_locked_predictions(limit=50) or []
        snap["locked_count"] = len(locked)
        snap["locked_open"] = sum(
            1 for r in locked if str(r.get("status") or "").lower() in {"open", "sealed", "locked", ""}
        )
    except Exception:
        snap["locked_count"] = 0
        snap["locked_open"] = 0

    try:
        from opportunity_tracker import get_active_durations

        active = get_active_durations(limit=5) or []
        snap["active_opps"] = len(active)
        snap["hottest_asset"] = (active[0].get("asset") if active else None) or None
    except Exception:
        snap["active_opps"] = 0
        snap["hottest_asset"] = None

    try:
        from signal_registry import registry_stats

        reg = registry_stats()
        snap["registry_labeled"] = int(reg.get("labeled") or 0)
        snap["registry_total"] = int(reg.get("total_in_memory") or 0)
    except Exception:
        snap["registry_labeled"] = 0
        snap["registry_total"] = 0

    # Best-effort oracle action for BTC
    try:
        from ai_oracle import get_latest_oracle_snapshot

        o = get_latest_oracle_snapshot("BTC") or {}
        snap["btc_action"] = str(o.get("action") or o.get("verdict") or o.get("decision") or "—")
        snap["btc_score"] = o.get("score")
    except Exception:
        snap["btc_action"] = "—"
        snap["btc_score"] = None

    return snap


def _delta_items(prev: dict[str, Any], cur: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    if prev.get("btc_action") and cur.get("btc_action") and prev["btc_action"] != cur["btc_action"]:
        items.append(
            {
                "id": "oracle_flip",
                "rank_score": 100,
                "title": "Oracle flipped",
                "detail": f"BTC {prev['btc_action']} → {cur['btc_action']}",
                "href": "/dashboard?lens=prove#decide",
            }
        )

    dk = float(cur.get("kill_rate_percent") or 0) - float(prev.get("kill_rate_percent") or 0)
    if abs(dk) >= 0.1 or int(cur.get("total_kills") or 0) > int(prev.get("total_kills") or 0):
        items.append(
            {
                "id": "kill_rate",
                "rank_score": 90 + min(9, abs(dk)),
                "title": "Kill-Rate moved",
                "detail": (
                    f"{prev.get('kill_rate_percent', 0)}% → {cur.get('kill_rate_percent', 0)}% "
                    f"({prev.get('total_kills', 0)} → {cur.get('total_kills', 0)} refusals)"
                ),
                "href": "/kill-rate",
            }
        )

    ds = int(cur.get("accuracy_samples") or 0) - int(prev.get("accuracy_samples") or 0)
    if ds != 0:
        items.append(
            {
                "id": "ledger_growth",
                "rank_score": 80 + min(9, abs(ds)),
                "title": "Public ledger grew",
                "detail": f"{ds:+d} resolved samples · hit-rate {cur.get('accuracy_hit_rate', 0)}%",
                "href": "/oracle-accuracy",
            }
        )

    dl = int(cur.get("locked_count") or 0) - int(prev.get("locked_count") or 0)
    if dl != 0:
        items.append(
            {
                "id": "locked_preds",
                "rank_score": 75,
                "title": "Locked predictions changed",
                "detail": f"{dl:+d} sealed/listed · {cur.get('locked_open', 0)} open",
                "href": "/oracle-accuracy#locked",
            }
        )

    dr = int(cur.get("registry_labeled") or 0) - int(prev.get("registry_labeled") or 0)
    if dr != 0:
        items.append(
            {
                "id": "corpus",
                "rank_score": 70,
                "title": "Labeled corpus grew",
                "detail": f"{dr:+d} labeled signals · total labeled {cur.get('registry_labeled', 0)}",
                "href": "/corpus-passport",
            }
        )

    if cur.get("hottest_asset") and cur.get("active_opps", 0) > 0:
        if cur.get("hottest_asset") != prev.get("hottest_asset") or cur.get("active_opps") != prev.get(
            "active_opps"
        ):
            items.append(
                {
                    "id": "half_life_heat",
                    "rank_score": 65,
                    "title": "Desk heat changed",
                    "detail": f"{cur.get('active_opps')} live edges · hottest {cur.get('hottest_asset')}",
                    "href": "/dashboard?lens=desk#half-life-clock",
                }
            )

    if not items:
        items = [
            {
                "id": "stable_oracle",
                "rank_score": 50,
                "title": "Oracle stance steady",
                "detail": f"BTC still {cur.get('btc_action', '—')} — no material flip since last visit",
                "href": "/",
            },
            {
                "id": "kill_board",
                "rank_score": 40,
                "title": "Kill-Rate board live",
                "detail": f"Public refusal rate {cur.get('kill_rate_percent', 0)}%",
                "href": "/kill-rate",
            },
            {
                "id": "arena",
                "rank_score": 30,
                "title": "Proof Arena waiting",
                "detail": "Human vs Oracle weekly — place or review your pick",
                "href": "/proof-arena",
            },
        ]

    items.sort(key=lambda x: float(x.get("rank_score") or 0), reverse=True)
    # Always return exactly Top-3 (pad with stable continuity cards)
    pads = [
        {
            "id": "kill_board",
            "rank_score": 20,
            "title": "Kill-Rate board live",
            "detail": "Public refusal rate — verify honesty anytime",
            "href": "/kill-rate",
        },
        {
            "id": "miss_feed",
            "rank_score": 15,
            "title": "Miss Feed open",
            "detail": "We publish misses first — brand by courage",
            "href": "/miss-feed",
        },
        {
            "id": "coverage",
            "rank_score": 10,
            "title": "Coverage Honesty",
            "detail": "Live venues only — planned never sold as live",
            "href": "/coverage-honesty",
        },
    ]
    out = items[:3]
    for p in pads:
        if len(out) >= 3:
            break
        if p["id"] not in {x.get("id") for x in out}:
            out.append(p)
    return out[:3]


def build_since_you_left(user_key: str = "anon", *, touch: bool = True) -> dict[str, Any]:
    key = (user_key or "anon").strip() or "anon"
    store = _load_store()
    users = store.setdefault("users", {})
    prev_entry = users.get(key) or {}
    prev_snap = prev_entry.get("snapshot") or {}
    cur = capture_market_snapshot()

    first_visit = not bool(prev_snap)
    top3 = (
        [
            {
                "id": "welcome",
                "rank_score": 100,
                "title": "Welcome — baseline sealed",
                "detail": "Next visit will show your Top-3 deltas vs this moment",
                "href": "/",
            },
            {
                "id": "ledger",
                "rank_score": 90,
                "title": "Verify the public ledger",
                "detail": f"Samples {cur.get('accuracy_samples', 0)} · hit-rate {cur.get('accuracy_hit_rate', 0)}%",
                "href": "/oracle-accuracy",
            },
            {
                "id": "kill",
                "rank_score": 80,
                "title": "See what we refuse",
                "detail": f"Kill-Rate {cur.get('kill_rate_percent', 0)}%",
                "href": "/kill-rate",
            },
        ]
        if first_visit
        else _delta_items(prev_snap, cur)
    )

    away_seconds = None
    if prev_entry.get("last_seen_ts"):
        away_seconds = max(0, int(time.time() - float(prev_entry["last_seen_ts"])))

    if touch:
        users[key] = {
            "last_seen": _utcnow(),
            "last_seen_ts": time.time(),
            "snapshot": cur,
            "visit_count": int(prev_entry.get("visit_count") or 0) + 1,
        }
        _save_store(store)

    return {
        "surface": "since_you_left_top3",
        "generated_at": _utcnow(),
        "user_key": key[:64],
        "first_visit": first_visit,
        "away_seconds": away_seconds,
        "previous_visit_at": prev_entry.get("last_seen"),
        "top3": top3,
        "headline": "Since you left — Top 3",
        "current_snapshot": cur,
        "api": "/api/since-you-left",
        "page": "/since-you-left",
        "tier_surface": "proof_pass_pro",
        "disclaimer": "Continuity digest — not financial advice.",
    }
