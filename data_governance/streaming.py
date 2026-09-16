"""Streaming ingestion controls — reconnect, gap detection, ordered application."""

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
        return {
            "gap_detected": False,
            "duplicate": False,
            "out_of_order": False,
            "accepted": True,
        }
    if sequence_id == last_sequence_id:
        return {
            "gap_detected": False,
            "duplicate": True,
            "out_of_order": False,
            "accepted": False,
        }
    if sequence_id < last_sequence_id:
        return {
            "gap_detected": False,
            "duplicate": False,
            "out_of_order": True,
            "accepted": False,
        }
    if sequence_id > last_sequence_id + 1:
        return {
            "gap_detected": True,
            "gap_size": sequence_id - last_sequence_id - 1,
            "duplicate": False,
            "out_of_order": False,
            "accepted": True,
        }
    return {
        "gap_detected": False,
        "duplicate": False,
        "out_of_order": False,
        "accepted": True,
    }


def evaluate_event_time_order(
    *,
    event_time: float | None,
    last_event_time: float | None,
) -> dict[str, Any]:
    """Event-time ordering when sequence/version is unavailable."""
    if event_time is None or last_event_time is None:
        return {"duplicate": False, "out_of_order": False, "accepted": True}
    if event_time == last_event_time:
        return {"duplicate": True, "out_of_order": False, "accepted": False}
    if event_time < last_event_time:
        return {"duplicate": False, "out_of_order": True, "accepted": False}
    return {"duplicate": False, "out_of_order": False, "accepted": True}


def apply_ordered_stream_event(
    state: dict[str, Any],
    *,
    sequence_id: int | None = None,
    event_time: float | None = None,
    payload: dict[str, Any] | None = None,
    replay: bool = False,
) -> dict[str, Any]:
    """
    Canonical ordered stream application.

    - newer sequence/event_time -> accepted and state advances
    - duplicate / out-of-order -> rejected without canonical-state mutation
    - replay=True -> isolated evaluation; live state unchanged
    """
    live = {
        "last_sequence_id": state.get("last_sequence_id"),
        "last_event_time": state.get("last_event_time"),
        "canonical_payload": state.get("canonical_payload"),
    }
    working = dict(live)
    evaluation: dict[str, Any]

    if sequence_id is not None:
        evaluation = evaluate_stream_gaps(
            sequence_id=sequence_id,
            last_sequence_id=working.get("last_sequence_id"),
        )
    else:
        evaluation = evaluate_event_time_order(
            event_time=event_time,
            last_event_time=working.get("last_event_time"),
        )

    if not evaluation.get("accepted"):
        return {
            **evaluation,
            "state": live,
            "replay": replay,
            "mutated": False,
        }

    if sequence_id is not None:
        working["last_sequence_id"] = sequence_id
    if event_time is not None:
        working["last_event_time"] = event_time
    if payload is not None:
        working["canonical_payload"] = dict(payload)

    if replay:
        return {
            **evaluation,
            "state": live,
            "replay_state": working,
            "replay": True,
            "mutated": False,
        }

    return {
        **evaluation,
        "state": working,
        "replay": False,
        "mutated": True,
    }
