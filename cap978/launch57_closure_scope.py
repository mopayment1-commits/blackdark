"""Launch-57 accountable closure scope — separate from CAP978 extension catalog (647–978).

Governing scope lock (launch **items** 1..57, not capability id 1..57):
- ``governance/launch57/LAUNCH57_57_CAPABILITY_ADAPTIVE_RECONCILIATION.json`` → ``scope_lock.LAUNCH57_IDS``
- ``scope_lock.EVERYTHING_ELSE`` = ``PARKED_OUT_OF_LAUNCH``

Extension catalog tiers (capability ids) are documented in ``cap978/catalog.py`` and
``docs/cap978/INSTITUTIONAL_CLOSURE.md`` (978 full gate vs 826 delivery vs 678 CI sample).
Those documents do **not** redefine Launch-57 launch-item scope; they govern the 978 PDF catalog.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from launch57.dispatch_isolation import launch57_bound_capability_ids

_ROOT = Path(__file__).resolve().parent.parent
_SCOPE_ARTIFACT = _ROOT / "governance" / "launch57" / "LAUNCH57_57_CAPABILITY_ADAPTIVE_RECONCILIATION.json"

EXTENSION_PARKED_MIN_ID = 647
EXTENSION_PARKED_MAX_ID = 978


@lru_cache(maxsize=1)
def launch57_launch_item_ids() -> frozenset[int]:
    data = json.loads(_SCOPE_ARTIFACT.read_text(encoding="utf-8"))
    raw = (data.get("scope_lock") or {}).get("LAUNCH57_IDS") or []
    return frozenset(int(x) for x in raw)


def launch57_accountable_capability_ids() -> frozenset[int]:
    """Capability IDs bound to Launch-57 handlers (engineering dispatch isolation SSOT)."""
    return launch57_bound_capability_ids()


def is_launch57_accountable_capability(capability_id: int) -> bool:
    return capability_id in launch57_accountable_capability_ids()


def is_extension_parked_outside_launch57(capability_id: int) -> bool:
    """647–978 extension rows outside Launch-57 dispatch binding (informational for PR)."""
    if capability_id < EXTENSION_PARKED_MIN_ID:
        return False
    return capability_id not in launch57_accountable_capability_ids()


def governing_scope_summary() -> dict[str, Any]:
    lock = {}
    try:
        data = json.loads(_SCOPE_ARTIFACT.read_text(encoding="utf-8"))
        lock = dict(data.get("scope_lock") or {})
    except Exception:
        pass
    return {
        "launch57_launch_items": sorted(launch57_launch_item_ids()),
        "launch57_launch_item_count": len(launch57_launch_item_ids()),
        "everything_else": lock.get("EVERYTHING_ELSE", "PARKED_OUT_OF_LAUNCH"),
        "accountable_capability_count": len(launch57_accountable_capability_ids()),
        "accountable_capability_ids": sorted(launch57_accountable_capability_ids()),
        "extension_parked_id_range": f"{EXTENSION_PARKED_MIN_ID}..{EXTENSION_PARKED_MAX_ID}",
        "governing_artifact": str(_SCOPE_ARTIFACT.relative_to(_ROOT)),
        "cap978_catalog_tiers": "cap978/catalog.py + docs/cap978/INSTITUTIONAL_CLOSURE.md",
    }
