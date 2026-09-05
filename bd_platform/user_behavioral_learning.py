"""
User Behavioral Learning (#105) — opt-in, privacy-first, rule-based personalization.

Wave 2 scope: NO complex ML. Simple interest scoring from page/surface visits.
Example rule: user opened 5 Solana pages → rank Solana first in suggestions.

Privacy:
- Explicit opt-in required (default OFF)
- Sensitive event payloads encrypted at rest (Fernet via secrets_vault)
- Personal-only — never public aggregates tied to identity
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_DATA_BASE = Path(__file__).resolve().parent.parent / "data"
_PREFS_PATH = safe_data_file("user_behavioral_prefs.json")
_EVENTS_PATH = safe_data_file("user_behavioral_events.enc.jsonl")
_MEMORY_PREFS: dict[str, dict[str, Any]] = {}
_TOPIC_COUNTS: dict[str, dict[str, int]] = {}
_MIN_VISITS_FOR_BOOST = 5


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _user_key(user_id: str) -> str:
    raw = (user_id or "anonymous").strip().lower() or "anonymous"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _normalize_topic(topic: str) -> str:
    t = (topic or "").strip().upper()
    aliases = {
        "SOLANA": "SOL",
        "BITCOIN": "BTC",
        "ETHEREUM": "ETH",
    }
    return aliases.get(t, t)[:32]


def _load_prefs() -> dict[str, dict[str, Any]]:
    global _MEMORY_PREFS
    if _MEMORY_PREFS:
        return _MEMORY_PREFS
    path = ensure_under(_PREFS_PATH, _DATA_BASE)
    if path.exists():
        try:
            _MEMORY_PREFS = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            _MEMORY_PREFS = {}
    else:
        _MEMORY_PREFS = {}
    return _MEMORY_PREFS


def _save_prefs() -> None:
    path = ensure_under(_PREFS_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_MEMORY_PREFS, indent=2), encoding="utf-8")


def _encrypt_payload(payload: dict[str, Any]) -> str:
    from secrets_vault import encrypt_secret

    plain = json.dumps(payload, ensure_ascii=False, default=str)
    return encrypt_secret(plain)


def _decrypt_payload(token: str) -> dict[str, Any] | None:
    from secrets_vault import decrypt_secret

    try:
        plain = decrypt_secret(token)
        row = json.loads(plain)
        return row if isinstance(row, dict) else None
    except Exception:
        return None


def _append_encrypted_event(row: dict[str, Any]) -> None:
    path = ensure_under(_EVENTS_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    enc = _encrypt_payload(row)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"enc": enc, "ts": _utcnow()}) + "\n")


def _rebuild_topic_counts(user_hash: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    path = ensure_under(_EVENTS_PATH, _DATA_BASE)
    if not path.exists():
        return counts
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-2000:]
    except OSError:
        return counts
    for line in lines:
        if not line.strip():
            continue
        try:
            wrapper = json.loads(line)
            row = _decrypt_payload(str(wrapper.get("enc") or ""))
        except json.JSONDecodeError:
            continue
        if not row or row.get("user_hash") != user_hash:
            continue
        topic = _normalize_topic(str(row.get("topic") or ""))
        if topic:
            counts[topic] = counts.get(topic, 0) + 1
    return counts


def opt_in_behavioral_learning(*, user_id: str) -> dict[str, Any]:
    """Explicit opt-in — required before any behavioral tracking."""
    key = _user_key(user_id)
    with _LOCK:
        prefs = _load_prefs()
        prefs[key] = {
            "user_hash": key,
            "opted_in": True,
            "opted_in_at": _utcnow(),
            "privacy_notice_ack": True,
        }
        _save_prefs()
    return {
        "ok": True,
        "feature": "#105",
        "opted_in": True,
        "user_hash": key,
        "message": "Behavioral learning enabled. You can opt out anytime.",
        "private": True,
    }


def opt_out_behavioral_learning(user_id: str, *, purge_events: bool = False) -> dict[str, Any]:
    key = _user_key(user_id)
    with _LOCK:
        prefs = _load_prefs()
        prefs[key] = {
            "user_hash": key,
            "opted_in": False,
            "opted_out_at": _utcnow(),
        }
        _save_prefs()
        _TOPIC_COUNTS.pop(key, None)
        if purge_events:
            path = ensure_under(_EVENTS_PATH, _DATA_BASE)
            if path.exists():
                kept: list[str] = []
                try:
                    for line in path.read_text(encoding="utf-8").splitlines():
                        if not line.strip():
                            continue
                        wrapper = json.loads(line)
                        row = _decrypt_payload(str(wrapper.get("enc") or ""))
                        if row and row.get("user_hash") == key:
                            continue
                        kept.append(line)
                    path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
                except (OSError, json.JSONDecodeError):
                    pass
    return {
        "ok": True,
        "feature": "#105",
        "opted_in": False,
        "purged": purge_events,
        "private": True,
    }


def behavioral_learning_status(*, user_id: str) -> dict[str, Any]:
    key = _user_key(user_id)
    prefs = _load_prefs().get(key) or {}
    return {
        "ok": True,
        "feature": "#105",
        "user_hash": key,
        "opted_in": bool(prefs.get("opted_in")),
        "opted_in_at": prefs.get("opted_in_at"),
        "rule_engine": "visit_count_v1",
        "min_visits_for_boost": _MIN_VISITS_FOR_BOOST,
        "private": True,
        "timestamp": _utcnow(),
    }


def record_behavior_event(
    *,
    user_id: str,
    topic: str,
    surface: str = "page",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a page/surface visit — only when user has opted in."""
    key = _user_key(user_id)
    prefs = _load_prefs().get(key) or {}
    if not prefs.get("opted_in"):
        return {
            "ok": False,
            "feature": "#105",
            "error": "opt_in_required",
            "opted_in": False,
            "private": True,
        }

    norm_topic = _normalize_topic(topic)
    if not norm_topic:
        return {"ok": False, "feature": "#105", "error": "topic_required", "private": True}

    row = {
        "event_id": f"ubl_{uuid4().hex[:16]}",
        "user_hash": key,
        "topic": norm_topic,
        "surface": (surface or "page")[:64],
        "meta": {k: str(v)[:120] for k, v in (meta or {}).items()},
        "recorded_at": _utcnow(),
        "private": True,
    }
    with _LOCK:
        _append_encrypted_event(row)
        counts = _TOPIC_COUNTS.setdefault(key, _rebuild_topic_counts(key))
        counts[norm_topic] = counts.get(norm_topic, 0) + 1

    return {
        "ok": True,
        "feature": "#105",
        "event_id": row["event_id"],
        "topic": norm_topic,
        "visit_count": counts[norm_topic],
        "boosted": counts[norm_topic] >= _MIN_VISITS_FOR_BOOST,
        "private": True,
    }


def ranked_topics_for_user(
    *,
    user_id: str,
    candidates: list[str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Rule-based ranking: topics with >=5 visits surface first.
    Returns honest scores — no fabricated ML confidence.
    """
    key = _user_key(user_id)
    prefs = _load_prefs().get(key) or {}
    if not prefs.get("opted_in"):
        return {
            "ok": True,
            "feature": "#105",
            "opted_in": False,
            "ranked": [],
            "headline": None,
            "private": True,
        }

    with _LOCK:
        counts = _TOPIC_COUNTS.get(key) or _rebuild_topic_counts(key)
        _TOPIC_COUNTS[key] = counts

    pool = [_normalize_topic(t) for t in (candidates or list(counts.keys())) if t]
    pool = list(dict.fromkeys(pool))

    scored = []
    for topic in pool:
        visits = counts.get(topic, 0)
        scored.append(
            {
                "topic": topic,
                "visit_count": visits,
                "boosted": visits >= _MIN_VISITS_FOR_BOOST,
                "score": visits,
            }
        )
    scored.sort(key=lambda x: (-x["score"], x["topic"]))
    top = scored[: max(1, min(limit, 50))]

    headline = None
    boosted = [r for r in top if r["boosted"]]
    if boosted:
        lead = boosted[0]
        headline = (
            f"Based on your recent activity, {lead['topic']} ranked first "
            f"({lead['visit_count']} visits)"
        )

    return {
        "ok": True,
        "feature": "#105",
        "opted_in": True,
        "ranked": top,
        "headline": headline,
        "rule_engine": "visit_count_v1",
        "accuracy_note": "Rule-based interest ranking — not ML prediction",
        "latency_target_ms": 2000,
        "private": True,
        "timestamp": _utcnow(),
    }


def behavioral_learning_module_status() -> dict[str, Any]:
    prefs = _load_prefs()
    opted_in = sum(1 for p in prefs.values() if p.get("opted_in"))
    return {
        "ok": True,
        "surface": "user_behavioral_learning",
        "feature": "#105",
        "wave": 2,
        "opt_in_users": opted_in,
        "encryption": "fernet_at_rest",
        "rule_engine": "visit_count_v1",
        "default_opt_in": False,
        "timestamp": _utcnow(),
    }
