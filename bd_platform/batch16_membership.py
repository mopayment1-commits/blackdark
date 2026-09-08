"""Canonical Batch16 (751–800) membership — dispatcher facades."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

BATCH16_IDS = list(range(751, 801))
CANONICAL_OFFSET = 267
CANONICAL_DUPLICATE_IDS = list(BATCH16_IDS)
CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {
    cid: cid - CANONICAL_OFFSET for cid in BATCH16_IDS
}
SHARED_LAYER_MODULE = "bd_platform.batch16_market_delivery_facade_layer"
SHARED_ENTRYPOINT = "execute_batch16_facade"


def verify_membership() -> dict[str, object]:
    bindings = discover_bindings()
    errors = [
        f"binding_{cid}"
        for cid in BATCH16_IDS
        if bindings.get(cid) != (SHARED_LAYER_MODULE, SHARED_ENTRYPOINT)
    ]
    if len(BATCH16_IDS) != 50:
        errors.append("batch_not_50")
    return {"ok": not errors, "errors": errors, "canonical_reuse_count": len(CANONICAL_DUPLICATE_TARGETS)}
