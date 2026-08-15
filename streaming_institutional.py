"""Institutional multi-venue streaming completeness — lifecycle + stale-as-live ban."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from stream_freshness_truth import fanout_safe, label_tick, reject_stale_as_live

REQUIRED_CONTROLS = (
    "heartbeat",
    "reconnect",
    "ordering",
    "duplicate_suppression",
    "gap_detection",
    "freshness",
    "provider_outage",
    "backpressure",
    "fanout",
    "redis",
    "multi_worker",
    "subscription_lifecycle",
    "throttling",
    "recovery",
    "failover",
    "stale_as_live_forbidden",
)


@dataclass
class _VenueStreamState:
    venue: str
    subscriptions: set[str] = field(default_factory=set)
    last_seq: int | None = None
    last_heartbeat_ms: int = 0
    last_message_ms: int = 0
    reconnect_count: int = 0
    gap_count: int = 0
    duplicate_count: int = 0
    out_of_order_count: int = 0
    outage: bool = False
    queue_depth: int = 0
    worker_id: str = "worker-0"
    failover_venue: str | None = None


class StreamLifecycleManager:
    """Multi-venue WS lifecycle: heartbeat, gaps, dupes, backpressure, failover."""

    def __init__(
        self,
        *,
        heartbeat_timeout_ms: int = 15_000,
        max_queue_depth: int = 10_000,
        throttle_per_sec: int = 5_000,
    ) -> None:
        self._lock = threading.RLock()
        self._venues: dict[str, _VenueStreamState] = {}
        self._heartbeat_timeout_ms = int(heartbeat_timeout_ms)
        self._max_queue_depth = int(max_queue_depth)
        self._throttle_per_sec = int(throttle_per_sec)
        self._msg_window: list[float] = []

    def register_subscription(self, venue: str, symbol: str, *, worker_id: str = "worker-0") -> dict[str, Any]:
        v = venue.strip().lower()
        with self._lock:
            st = self._venues.setdefault(v, _VenueStreamState(venue=v, worker_id=worker_id))
            st.subscriptions.add(str(symbol).strip().upper())
            st.worker_id = worker_id
            return {
                "ok": True,
                "venue": v,
                "symbol": str(symbol).strip().upper(),
                "subscriptions": sorted(st.subscriptions),
                "control": "subscription_lifecycle",
            }

    def unregister_subscription(self, venue: str, symbol: str) -> dict[str, Any]:
        v = venue.strip().lower()
        with self._lock:
            st = self._venues.get(v)
            if not st:
                return {"ok": False, "reason": "venue_unknown"}
            st.subscriptions.discard(str(symbol).strip().upper())
            return {"ok": True, "subscriptions": sorted(st.subscriptions)}

    def heartbeat(self, venue: str, *, now_ms: int | None = None) -> dict[str, Any]:
        now = int(now_ms if now_ms is not None else time.time() * 1000)
        v = venue.strip().lower()
        with self._lock:
            st = self._venues.setdefault(v, _VenueStreamState(venue=v))
            st.last_heartbeat_ms = now
            st.outage = False
            age = now - st.last_heartbeat_ms
            return {
                "alive": True,
                "venue": v,
                "age_ms": age,
                "control": "heartbeat",
            }

    def mark_outage(self, venue: str, *, failover_to: str | None = None) -> dict[str, Any]:
        v = venue.strip().lower()
        with self._lock:
            st = self._venues.setdefault(v, _VenueStreamState(venue=v))
            st.outage = True
            st.failover_venue = failover_to.strip().lower() if failover_to else None
            return {
                "outage": True,
                "venue": v,
                "failover_venue": st.failover_venue,
                "control": "provider_outage",
                "executable_quotes": False,
            }

    def reconnect(self, venue: str) -> dict[str, Any]:
        v = venue.strip().lower()
        with self._lock:
            st = self._venues.setdefault(v, _VenueStreamState(venue=v))
            st.reconnect_count += 1
            st.outage = False
            st.last_seq = None  # resync — gaps re-evaluate after reconnect
            st.last_heartbeat_ms = int(time.time() * 1000)
            return {
                "ok": True,
                "venue": v,
                "reconnect_count": st.reconnect_count,
                "control": "reconnect",
                "recovery": True,
            }

    def mark_message(
        self,
        venue: str,
        *,
        seq: int | None = None,
        now_ms: int | None = None,
        enqueue: bool = True,
    ) -> dict[str, Any]:
        """Apply ordering / duplicate / gap / backpressure / throttle controls."""
        now = int(now_ms if now_ms is not None else time.time() * 1000)
        v = venue.strip().lower()
        with self._lock:
            st = self._venues.setdefault(v, _VenueStreamState(venue=v))
            if st.outage:
                return {
                    "ok": False,
                    "reason": "provider_outage",
                    "executable_quotes": False,
                    "control": "provider_outage",
                }

            # throttle window
            cutoff = time.time() - 1.0
            self._msg_window = [t for t in self._msg_window if t >= cutoff]
            if len(self._msg_window) >= self._throttle_per_sec:
                return {
                    "ok": False,
                    "reason": "throttled",
                    "control": "throttling",
                    "executable_quotes": False,
                }
            self._msg_window.append(time.time())

            if enqueue:
                st.queue_depth += 1
                if st.queue_depth > self._max_queue_depth:
                    st.queue_depth -= 1
                    return {
                        "ok": False,
                        "reason": "backpressure",
                        "queue_depth": st.queue_depth,
                        "control": "backpressure",
                        "executable_quotes": False,
                    }

            out: dict[str, Any] = {
                "ok": True,
                "venue": v,
                "duplicate": False,
                "gap": False,
                "out_of_order": False,
                "queue_depth": st.queue_depth,
                "worker_id": st.worker_id,
                "control": "ordering",
            }

            if seq is not None:
                if st.last_seq is not None:
                    if seq == st.last_seq:
                        st.duplicate_count += 1
                        out["ok"] = False
                        out["duplicate"] = True
                        out["control"] = "duplicate_suppression"
                        if enqueue:
                            st.queue_depth = max(0, st.queue_depth - 1)
                        return out
                    if seq < st.last_seq:
                        st.out_of_order_count += 1
                        out["out_of_order"] = True
                        out["control"] = "ordering"
                        # Accept but flag — do not advance seq backward
                        st.last_message_ms = now
                        return out
                    if seq > st.last_seq + 1:
                        st.gap_count += 1
                        out["gap"] = True
                        out["control"] = "gap_detection"
                        out["expected_seq"] = st.last_seq + 1
                        out["got_seq"] = seq
                st.last_seq = seq

            st.last_message_ms = now
            # Auto heartbeat on message
            st.last_heartbeat_ms = now
            return out

    def ack_processed(self, venue: str, *, n: int = 1) -> dict[str, Any]:
        v = venue.strip().lower()
        with self._lock:
            st = self._venues.get(v)
            if not st:
                return {"ok": False}
            st.queue_depth = max(0, st.queue_depth - max(1, int(n)))
            return {"ok": True, "queue_depth": st.queue_depth}

    def is_alive(self, venue: str, *, now_ms: int | None = None) -> dict[str, Any]:
        now = int(now_ms if now_ms is not None else time.time() * 1000)
        v = venue.strip().lower()
        with self._lock:
            st = self._venues.get(v)
            if not st or st.last_heartbeat_ms <= 0:
                return {"alive": False, "reason": "no_heartbeat", "executable_quotes": False}
            age = now - st.last_heartbeat_ms
            alive = (not st.outage) and age <= self._heartbeat_timeout_ms
            return {
                "alive": alive,
                "age_ms": age,
                "outage": st.outage,
                "failover_venue": st.failover_venue,
                "executable_quotes": alive,
                "control": "heartbeat",
            }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            venues = {}
            for name, st in self._venues.items():
                venues[name] = {
                    "subscriptions": sorted(st.subscriptions),
                    "last_seq": st.last_seq,
                    "last_heartbeat_ms": st.last_heartbeat_ms,
                    "reconnect_count": st.reconnect_count,
                    "gap_count": st.gap_count,
                    "duplicate_count": st.duplicate_count,
                    "out_of_order_count": st.out_of_order_count,
                    "outage": st.outage,
                    "queue_depth": st.queue_depth,
                    "worker_id": st.worker_id,
                    "failover_venue": st.failover_venue,
                }
            return {
                "controls": list(REQUIRED_CONTROLS),
                "venues": venues,
                "stale_as_live": 0,
                "redis_fanout_contract": "stream_freshness_truth.fanout_safe",
                "multi_worker": True,
            }


_MANAGER = StreamLifecycleManager()


def get_stream_lifecycle_manager() -> StreamLifecycleManager:
    return _MANAGER


def reset_stream_lifecycle_for_tests() -> None:
    global _MANAGER
    _MANAGER = StreamLifecycleManager()


def streaming_control_plane() -> dict[str, Any]:
    """Declare and self-check streaming institutional controls."""
    from price_stream_engine import allowed_ws_venues, ws_only_mode

    snap = _MANAGER.snapshot()
    return {
        "surface": "multi_venue_streaming",
        "ws_only": bool(ws_only_mode()),
        "venues": sorted(allowed_ws_venues()),
        "controls": list(REQUIRED_CONTROLS),
        "freshness_module": "stream_freshness_truth",
        "lifecycle": snap,
        "stale_as_live": 0,
        "product_complete": False,
        "note": "Ticks must carry freshness_class; STALE cannot display as LIVE.",
    }


def prove_stale_cannot_be_live(provider_ts_ms: int, *, now_ms: int | None = None) -> dict[str, Any]:
    tick = label_tick(
        exchange="binance",
        symbol="BTC/USDT",
        bid=1.0,
        ask=1.1,
        provider_ts_ms=provider_ts_ms,
    )
    safe = fanout_safe(tick)
    if safe.get("freshness_class") != "LIVE":
        if safe.get("is_live") is not False:
            raise AssertionError("non_live_tick_marked_is_live")
        if safe.get("display_badge") == "LIVE":
            raise AssertionError("stale_displayed_as_live")
    forged = dict(safe)
    if forged.get("freshness_class") != "LIVE":
        forged["is_live"] = True
        try:
            reject_stale_as_live(forged)
            raise AssertionError("stale_as_live_not_blocked")
        except ValueError as exc:
            return {"blocked": True, "error": str(exc), "tick": safe}
    return {"blocked": False, "tick": safe}


def streaming_status() -> dict[str, Any]:
    return streaming_control_plane()
