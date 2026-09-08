"""Canonical Batch17 (801–826) membership — dispatcher facades."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

BATCH17_IDS = list(range(801, 827))
CANONICAL_OFFSET = 267
CANONICAL_DUPLICATE_IDS = list(BATCH17_IDS)
CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {
    801: 534,
    802: 535,
    803: 536,
    804: 537,
    805: 538,
    806: 539,
    807: 540,
    808: 541,
    809: 542,
    810: 543,
    811: 544,
    812: 545,
    813: 546,
    814: 547,
    815: 548,
    816: 549,
    817: 550,
    818: 551,
    819: 552,
    820: 553,
    821: 554,
    822: 555,
    823: 556,
    824: 557,
    825: 558,
    826: 559,
}
SHARED_LAYER_MODULE = "bd_platform.batch17_final_program_facade_layer"
SHARED_ENTRYPOINT = "execute_batch17_facade"


def verify_membership() -> dict[str, object]:
    bindings = discover_bindings()
    errors = [
        f"binding_{cid}"
        for cid in BATCH17_IDS
        if bindings.get(cid) != (SHARED_LAYER_MODULE, SHARED_ENTRYPOINT)
    ]
    if len(BATCH17_IDS) != 26:
        errors.append("batch_not_26")
    return {"ok": not errors, "errors": errors, "canonical_reuse_count": len(CANONICAL_DUPLICATE_TARGETS)}
