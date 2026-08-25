"""
Analyst Notes Feed — Feature #206 (Sprint 2 lightweight).

NOT a consensus engine — curated analyst views with mandatory attribution.
Messari Pro import style + manual curation. Divergence shown as counts, not averages.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.AnalystNotes")

_FEATURE_ID = 206
_STORE_PATH = Path("data/analyst_notes.json")
_SEED_PATH = Path("data/analyst_notes_seed.json")
_DISCLAIMER = "Analyst views are opinions, not facts."
_DISCLAIMER_AR = "آراء المحللين هي آراء وليست حقائق."
_MERGED_FEATURE = 206  # lightweight feed, not Wave 3 consensus engine

View = Literal["bullish", "neutral", "bearish"]


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
    notes: dict[str, Any] = {}
    if _SEED_PATH.is_file():
        try:
            rows = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
            for row in rows:
                notes[row["id"]] = {**row, "updated_at": _utcnow()}
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("analyst notes seed load failed: %s", exc)
    store = {"notes": notes, "updated_at": _utcnow()}
    _save_store(store)
    return store


def _save_store(blob: dict[str, Any]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    blob["updated_at"] = _utcnow()
    _STORE_PATH.write_text(json.dumps(blob, indent=2, ensure_ascii=False), encoding="utf-8")


def _attribution_line(note: dict[str, Any]) -> str:
    analyst = note.get("analyst") or note.get("contributor") or "Unknown"
    firm = note.get("firm") or "Independent"
    date = note.get("published_date") or note.get("timestamp", "")[:10]
    return f"Analyst: {analyst} | Firm: {firm} | Date: {date}"


def _view_display(note: dict[str, Any]) -> str:
    view = str(note.get("view") or "neutral").title()
    conf = note.get("confidence_pct", 50)
    return f"Analyst View: {view} | Confidence: {conf}%"


def _enrich_note(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "attribution_line": _attribution_line(row),
        "display": _view_display(row),
        "source_line": f"Source: {row.get('source', 'Manual Curation')} | Imported: {row.get('imported_at', row.get('published_date', ''))}",
        "not_a_prediction": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_ar": _DISCLAIMER_AR,
        "disclaimer_hideable": False,
    }


def _compute_divergence(notes: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"bullish": 0, "neutral": 0, "bearish": 0}
    for n in notes:
        v = str(n.get("view") or "neutral").lower()
        if v in counts:
            counts[v] += 1
    total = sum(counts.values()) or 1
    display = (
        f"{total} analysts: {counts['bullish']} Bullish | "
        f"{counts['neutral']} Neutral | {counts['bearish']} Bearish"
    )
    return {
        "total": total,
        "bullish": counts["bullish"],
        "neutral": counts["neutral"],
        "bearish": counts["bearish"],
        "display": display,
        "no_average_score": True,
    }


def list_analyst_notes(
    *,
    asset: str | None = None,
    firm: str | None = None,
    view: View | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    store = _load_store()
    rows = [_enrich_note(n) for n in store.get("notes", {}).values()]

    if asset:
        sym = asset.upper()
        rows = [r for r in rows if sym in [a.upper() for a in (r.get("assets") or [])]]
    if firm:
        rows = [r for r in rows if firm.lower() in str(r.get("firm", "")).lower()]
    if view:
        rows = [r for r in rows if str(r.get("view", "")).lower() == view]

    rows.sort(key=lambda r: r.get("published_date") or "", reverse=True)
    divergence = _compute_divergence(rows)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "mode": "analyst_notes_feed",
        "consensus_engine": False,
        "count": len(rows[:limit]),
        "notes": rows[:limit],
        "divergence": divergence,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }


def get_analyst_note(note_id: str) -> dict[str, Any]:
    store = _load_store()
    row = store.get("notes", {}).get(note_id)
    if not row:
        return {"ok": False, "error": "note_not_found"}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "note": _enrich_note(row),
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }


def get_asset_analyst_summary(asset: str) -> dict[str, Any]:
    """Asset-level analyst divergence — counts only, no consensus average."""
    feed = list_analyst_notes(asset=asset, limit=200)
    notes = feed.get("notes") or []
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "asset": asset.upper(),
        "divergence": feed.get("divergence"),
        "note_count": len(notes),
        "sample_notes": notes[:5],
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }


def analyst_notes_status() -> dict[str, Any]:
    store = _load_store()
    notes = list(store.get("notes", {}).values())
    firms = {n.get("firm") for n in notes}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "module": "Analyst Notes Feed",
        "consensus_engine": False,
        "wave_3_consensus_deferred": True,
        "note_count": len(notes),
        "firm_count": len(firms),
        "contributor_attribution_required": True,
        "divergence_as_counts": True,
        "no_average_score": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "import_sources": ["Messari Pro (style)", "Manual Curation"],
        "timestamp": _utcnow(),
    }
