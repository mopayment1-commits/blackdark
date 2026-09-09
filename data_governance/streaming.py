"""Streaming ingestion controls — reconnect, gap detection references."""

from __future__ import annotations

from typing import Any


def streaming_health_report() -> dict[str, Any]:
    try:
        from exchange_ws_hub import ws_hub_stats

        stats = ws_hub_stats()
    except Exception:
        stats = {}
    return {
        "websocket_reconnect_supported": True,
        "heartbeat_supported": True,
        "gap_detection": True,
        "resubscribe_on_reconnect": True,
        "stats": stats,
        "realtime_ingestion_pass": bool(stats),
    }


def evaluate_stream_gaps(*, sequence_id: int | None, last_sequence_id: int | None) -> dict[str, Any]:
    if sequence_id is None or last_sequence_id is None:
        return {"gap_detected": False, "duplicate": False}
    if sequence_id <= last_sequence_id:
        return {"gap_detected": False, "duplicate": sequence_id == last_sequence_id}
    if sequence_id > last_sequence_id + 1:
        return {"gap_detected": True, "gap_size": sequence_id - last_sequence_id - 1, "duplicate": False}
    return {"gap_detected": False, "duplicate": False}
