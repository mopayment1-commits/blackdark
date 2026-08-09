"""
BLACKDARK — ML Experience Log.

Persistent journal of every training cycle, flywheel run, and model improvement.
This is the project's "learning memory" for acquirer due diligence.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any, Literal

import config
from path_safety import ensure_under

logger = logging.getLogger("BLACKDARK.MLExperience")

ExperienceEvent = Literal[
    "flywheel_cycle",
    "labeling_batch",
    "training_run",
    "model_deployed",
    "prediction_logged",
    "ensemble_trained",
]

EXPERIENCE_LOG_PATH = config.DATA_DIR / "ml_experience_log.jsonl"
SUMMARY_PATH = config.DATA_DIR / "ml_experience_summary.json"


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def append_experience(
    event_type: ExperienceEvent,
    payload: dict[str, Any],
    *,
    notes: str | None = None,
) -> dict[str, Any]:
    entry = {
        "timestamp": _utcnow_iso(),
        "event_type": event_type,
        "payload": payload,
        "notes": notes,
    }
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    log_path = ensure_under(EXPERIENCE_LOG_PATH, config.DATA_DIR)
    with log_path.open("a", encoding="utf-8") as handle:  # NOSONAR pythonsecurity:S2083
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    _refresh_summary(entry)
    logger.info("ML experience logged | type=%s", event_type)
    return entry


def _refresh_summary(latest: dict[str, Any]) -> None:
    stats = load_experience_summary()
    stats["total_events"] = int(stats.get("total_events") or 0) + 1
    stats["last_event"] = latest
    stats["last_updated"] = _utcnow_iso()
    by_type = stats.setdefault("events_by_type", {})
    event_type = str(latest.get("event_type") or "unknown")
    by_type[event_type] = int(by_type.get(event_type) or 0) + 1
    if event_type == "training_run" and latest.get("payload", {}).get("trained"):
        stats["total_training_runs"] = int(stats.get("total_training_runs") or 0) + 1
        metrics = latest.get("payload", {}).get("metrics") or {}
        best = float(stats.get("best_accuracy") or 0)
        accuracy = float(metrics.get("accuracy") or 0)
        if accuracy > best:
            stats["best_accuracy"] = accuracy
            stats["best_model_version"] = latest.get("payload", {}).get("model_version")
    if event_type == "flywheel_cycle":
        stats["total_flywheel_cycles"] = int(stats.get("total_flywheel_cycles") or 0) + 1
        labeled = (latest.get("payload") or {}).get("export", {}).get("exported")
        if labeled is not None:
            stats["last_labeled_export_count"] = labeled
    ensure_under(SUMMARY_PATH, config.DATA_DIR).write_text(  # NOSONAR pythonsecurity:S2083
        json.dumps(stats, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_experience_summary() -> dict[str, Any]:
    if not SUMMARY_PATH.exists():
        return {
            "total_events": 0,
            "total_training_runs": 0,
            "total_flywheel_cycles": 0,
            "best_accuracy": 0.0,
            "created_at": _utcnow_iso(),
        }
    try:
        return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"total_events": 0, "parse_error": True}


def fetch_recent_experiences(*, limit: int = 50) -> list[dict[str, Any]]:
    if not EXPERIENCE_LOG_PATH.exists():
        return []
    lines = EXPERIENCE_LOG_PATH.read_text(encoding="utf-8").splitlines()
    records: list[dict[str, Any]] = []
    for raw_line in lines[-limit:]:
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            records.append(json.loads(stripped))
        except json.JSONDecodeError:
            continue
    return list(reversed(records))


def public_experience_block() -> dict[str, Any]:
    summary = load_experience_summary()
    recent = fetch_recent_experiences(limit=10)
    return {
        "summary": {
            "total_events": summary.get("total_events", 0),
            "total_training_runs": summary.get("total_training_runs", 0),
            "total_flywheel_cycles": summary.get("total_flywheel_cycles", 0),
            "best_accuracy": summary.get("best_accuracy", 0),
            "best_model_version": summary.get("best_model_version"),
            "last_labeled_export_count": summary.get("last_labeled_export_count", 0),
        },
        "recent_events": [
            {
                "timestamp": row.get("timestamp"),
                "event_type": row.get("event_type"),
                "highlights": _event_highlights(row),
            }
            for row in recent
        ],
    }


def _event_highlights(row: dict[str, Any]) -> dict[str, Any]:
    payload = row.get("payload") or {}
    event_type = row.get("event_type")
    if event_type == "training_run":
        return {
            "trained": payload.get("trained"),
            "accuracy": (payload.get("metrics") or {}).get("accuracy"),
            "samples": (payload.get("metrics") or {}).get("samples_total"),
            "version": payload.get("model_version"),
        }
    if event_type == "flywheel_cycle":
        return {
            "resolved": (payload.get("labeling") or {}).get("resolved_24h"),
            "exported": (payload.get("export") or {}).get("exported"),
            "trained": (payload.get("training") or {}).get("trained"),
        }
    return {"keys": list(payload.keys())[:5]}
