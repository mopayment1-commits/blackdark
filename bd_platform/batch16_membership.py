"""Canonical Batch16 (751–800) membership — dispatcher facades."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

BATCH16_IDS = list(range(751, 801))
CANONICAL_OFFSET = 267
CANONICAL_DUPLICATE_IDS = list(BATCH16_IDS)
CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {
    751: 484,
    752: 485,
    753: 486,
    754: 487,
    755: 488,
    756: 489,
    757: 490,
    758: 491,
    759: 492,
    760: 493,
    761: 494,
    762: 495,
    763: 496,
    764: 497,
    765: 498,
    766: 499,
    767: 500,
    768: 501,
    769: 502,
    770: 503,
    771: 504,
    772: 505,
    773: 506,
    774: 507,
    775: 508,
    776: 509,
    777: 510,
    778: 511,
    779: 512,
    780: 513,
    781: 514,
    782: 515,
    783: 516,
    784: 517,
    785: 518,
    786: 519,
    787: 520,
    788: 521,
    789: 522,
    790: 523,
    791: 524,
    792: 525,
    793: 526,
    794: 527,
    795: 528,
    796: 529,
    797: 530,
    798: 531,
    799: 532,
    800: 533,
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
