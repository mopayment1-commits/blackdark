"""
Launch-57 Phase 7 — shared edge + UI spine consuming Phase 1–3 layers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from launch57.decision_common import attach_decision_envelope, load_decision_spine, stale_gate_body, stamp_decision_batch

_LAUNCH57_REGISTER = Path(__file__).resolve().parents[1] / "governance/launch57/LAUNCH57_REGISTER.json"

# Launch-57 scope only — home/library must never surface IDs outside 1..57.
LAUNCH57_SCOPE_IDS: frozenset[int] = frozenset(range(1, 58))

_ALLOWED_HOME_STATUSES: frozenset[str] = frozenset({"PASS_ENGINEERING"})

_EXCLUDED_HOME_STATUSES: frozenset[str] = frozenset(
    {
        "PARKED",
        "NO_LINKED_CANONICAL",
        "NOT_LINKED",
        "STUB",
        "PHANTOM",
    }
)

_FREE_HISTORY_LIMIT = 10

_MVRV_LICENSED_SOURCE_NOTE = (
    "Licensed LookIntoBitcoin/Glassnode MVRV feed not configured — "
    "local proxy compute only; reference links provided without LIVE licensed values."
)


def attach_edge_ui_envelope(
    body: dict[str, Any],
    *,
    spine: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from launch57.b11_personal_history_bridge import finalize_b11_personal_history_surface
    from launch57.personal_history_timing_common import B11_LAUNCH_NUMBERS

    out = attach_decision_envelope(body, spine=spine)
    out["edge_ui_layer"] = {
        "phase": "7_EDGE_UI",
        "data_spine_consumed": (spine or {}).get("data_spine"),
        "freshness_state": (spine or {}).get("freshness_state"),
        "live_eligible": (spine or {}).get("live_eligible"),
        "evidence_class_visible": out.get("evidence_class_visible"),
    }
    launch_id = int(out.get("launch_item_id") or 0)
    if launch_id in B11_LAUNCH_NUMBERS:
        p = dict(params or {})
        out = finalize_b11_personal_history_surface(
            out,
            payload=p,
            spine=spine,
            display_timezone=p.get("display_timezone"),
        )
    return out


def free_tier_history_limit() -> int:
    return _FREE_HISTORY_LIMIT


def mvrv_source_blocker_note() -> str:
    return _MVRV_LICENSED_SOURCE_NOTE


async def gated_edge_ui(
    *,
    capability_id: int | None,
    launch_item_id: int,
    surface: str,
    entrypoint: str,
    symbol: str,
    params: dict[str, Any],
    module: str,
    binding: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    spine = await load_decision_spine(symbol, params)
    if not spine["live_eligible"]:
        body = stamp_decision_batch(
            stale_gate_body(
                capability_id=capability_id or 0,
                launch_item_id=launch_item_id,
                surface=surface,
                symbol=spine["symbol"],
                spine=spine,
                entrypoint=entrypoint,
            ),
            capability_id=capability_id or 0,
            launch_item_id=launch_item_id,
            entrypoint=entrypoint,
            batch_module=module,
            binding_source=binding,
        )
        return attach_edge_ui_envelope(body, spine=spine, params=params), None
    return None, spine


def launch57_home_eligible_ids() -> frozenset[int]:
    """PASS_ENGINEERING launch items only — excludes PARKED / unlinked."""
    if not _LAUNCH57_REGISTER.exists():
        return frozenset()
    register = json.loads(_LAUNCH57_REGISTER.read_text(encoding="utf-8"))
    eligible: set[int] = set()
    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if not isinstance(ln, int) or ln not in LAUNCH57_SCOPE_IDS:
            continue
        status = str(item.get("current_engineering_status") or "")
        if status in _EXCLUDED_HOME_STATUSES:
            continue
        if status in _ALLOWED_HOME_STATUSES:
            eligible.add(ln)
    return frozenset(eligible)


def launch57_library_entries(*, query: str | None = None) -> list[dict[str, Any]]:
    """Secondary capability library — all 57 Launch-57 entries (spec §2, §5)."""
    from launch57.capability_library_common import load_canonical_library_entries, search_library

    if query:
        searched = search_library(query=query)
        return searched.get("results") or []
    return load_canonical_library_entries()


def read_decision_history_rows(*, limit: int, tier: str = "free") -> list[dict[str, Any]]:
    from decision_ledger import _PATH  # noqa: PLC2701

    cap = limit if tier != "free" else min(limit, _FREE_HISTORY_LIMIT)
    if not _PATH.exists():
        return []
    try:
        lines = _PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(rows) >= cap:
            break
    return rows
