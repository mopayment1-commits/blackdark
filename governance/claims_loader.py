"""Load numbered requirements from BUILD_GOVERNANCE_EXTRACTED_CLAIMS.json."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_CLAIMS = _ROOT / "BUILD_GOVERNANCE_EXTRACTED_CLAIMS.json"


@lru_cache(maxsize=1)
def load_claims() -> list[dict[str, Any]]:
    if not _CLAIMS.exists():
        return []
    return json.loads(_CLAIMS.read_text(encoding="utf-8")).get("claims") or []


def claims_by_prefix(prefix: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in load_claims():
        eid = str(row.get("external_id") or "")
        if eid.startswith(prefix):
            out[eid] = row
    return out


def ordered_ids(prefix: str, *, max_num: int | None = None) -> list[str]:
    by = claims_by_prefix(prefix)
    nums = []
    for eid in by:
        m = re.search(r"-(\d+)$", eid)
        if m:
            nums.append(int(m.group(1)))
    nums.sort()
    if max_num:
        nums = [n for n in nums if n <= max_num]
    return [f"{prefix}{n:03d}" for n in nums]
