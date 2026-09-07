"""Canonical Batch15 (701–750) membership — dispatcher facades."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

BATCH15_IDS = list(range(701, 751))
CANONICAL_DUPLICATE_IDS = list(BATCH15_IDS)
CANONICAL_OFFSET = 267
CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {
    701: 434,
    702: 435,
    703: 436,
    704: 437,
    705: 438,
    706: 439,
    707: 440,
    708: 441,
    709: 442,
    710: 443,
    711: 444,
    712: 445,
    713: 446,
    714: 447,
    715: 448,
    716: 449,
    717: 450,
    718: 451,
    719: 452,
    720: 453,
    721: 454,
    722: 455,
    723: 456,
    724: 457,
    725: 458,
    726: 459,
    727: 460,
    728: 461,
    729: 462,
    730: 463,
    731: 464,
    732: 465,
    733: 466,
    734: 467,
    735: 468,
    736: 469,
    737: 470,
    738: 471,
    739: 472,
    740: 473,
    741: 474,
    742: 475,
    743: 476,
    744: 477,
    745: 478,
    746: 479,
    747: 480,
    748: 481,
    749: 482,
    750: 483,
}
SHARED_LAYER_MODULE = "bd_platform.batch15_defi_risk_data_facade_layer"
SHARED_ENTRYPOINT = "execute_batch15_facade"


def verify_membership() -> dict[str, object]:
    bindings = discover_bindings()
    errors: list[str] = []
    if len(BATCH15_IDS) != 50:
        errors.append("batch_not_50")
    for cid in BATCH15_IDS:
        mod, fn = bindings.get(cid, ("", ""))
        if mod != SHARED_LAYER_MODULE or fn != SHARED_ENTRYPOINT:
            errors.append(f"binding_{cid}")
    return {"ok": not errors, "errors": errors, "canonical_reuse_count": len(CANONICAL_DUPLICATE_TARGETS)}
