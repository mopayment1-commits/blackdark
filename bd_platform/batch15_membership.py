"""Canonical Batch15 (701–750) membership — dispatcher facades."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

BATCH15_IDS = list(range(701, 751))
CANONICAL_OFFSET = 267
SPECIAL_CANONICAL: dict[int, int] = {725: 458}
CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {
    cid: SPECIAL_CANONICAL.get(cid, cid - CANONICAL_OFFSET) for cid in BATCH15_IDS
}
CANONICAL_DUPLICATE_IDS = list(BATCH15_IDS)
SHARED_LAYER_MODULE = "bd_platform.batch15_defi_risk_data_facade_layer"
SHARED_ENTRYPOINT = "execute_batch15_facade"


def verify_membership() -> dict[str, object]:
    bindings = discover_bindings()
    errors = [
        f"binding_{cid}"
        for cid in BATCH15_IDS
        if bindings.get(cid) != (SHARED_LAYER_MODULE, SHARED_ENTRYPOINT)
    ]
    if len(BATCH15_IDS) != 50:
        errors.append("batch_not_50")
    return {"ok": not errors, "errors": errors, "canonical_reuse_count": len(CANONICAL_DUPLICATE_TARGETS)}
