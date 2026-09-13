"""Provenance lineage contract (DIG-004, DIG-019, DIG-044)."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def attach_provenance(payload: dict[str, Any], *, surface: str) -> dict[str, Any]:
    out = dict(payload)
    chain = dict(out.get("provenance_chain") or out.get("provenance") or {})
    chain.setdefault("surface", surface)
    chain.setdefault("source_id", out.get("source_id") or out.get("source") or "internal_cache")
    body = json.dumps(chain, sort_keys=True, default=str)
    chain["lineage_hash"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    out["provenance_chain"] = chain
    return out
