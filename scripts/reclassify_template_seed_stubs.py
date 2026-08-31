#!/usr/bin/env python3
"""Reclassify TEMPLATE-SEED-STUB capabilities to WRAPPER-ONLY-UNVERIFIED in all audit artifacts."""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REASON = (
    "WRAPPER-ONLY-UNVERIFIED: TEMPLATE-SEED-STUB — generated _base()+_metric() surface; "
    "static metric from data/legal_retail_commercial_seed.json cap_{id}; no unique domain logic; "
    "production /api/cap646 uses cap646 backend_registry handlers, not this template binding."
)

STUBS_BY_BATCH: dict[int, list[int]] = {
    3: [
        262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 273, 275, 276, 277, 278, 280, 281, 282,
        283, 284, 285, 286, 287, 289, 290, 291, 292, 293, 294, 295, 296, 298,
    ],
    4: [
        301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 317, 318, 319,
        320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 331, 332, 333, 334, 335, 336, 337, 338,
        340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 357, 358,
        359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376,
        377, 383, 384, 385, 386, 387, 388, 389, 391, 392, 394, 395, 397, 398, 399, 400,
    ],
    5: [
        401, 402, 403, 404, 405, 406, 407, 408, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419,
        420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 438,
        439, 440, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457,
        459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476,
        477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494,
        495, 496, 497, 498, 499, 500,
    ],
    6: [
        501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 518, 519,
        520, 521, 522, 523, 524, 526, 527, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539,
        540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557,
        558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 570, 571, 572, 573, 574, 575,
        576, 577, 579, 580, 581, 582, 583, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595,
        596, 597, 598, 599, 600,
    ],
}

ALL_STUBS = frozenset(i for ids in STUBS_BY_BATCH.values() for i in ids)
assert len(ALL_STUBS) == 311, len(ALL_STUBS)

EVIDENCE_FILES = {
    3: ROOT / "data/hero_batch_03_201_300_evidence.jsonl",
    4: ROOT / "data/hero_batch_04_301_400_evidence.jsonl",
    5: ROOT / "data/hero_batch_05_401_500_evidence.jsonl",
    6: ROOT / "data/hero_batch_06_501_600_evidence.jsonl",
}

AUDIT_FILES = {
    3: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_03_201_300.json",
    4: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_04_301_400.json",
    5: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_05_401_500.json",
    6: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_06_501_600.json",
}


def _reason_for(cid: int) -> str:
    batch = next(b for b, ids in STUBS_BY_BATCH.items() if cid in ids)
    layer = {
        3: "bd_platform.derivatives_onchain_intelligence_layer",
        4: "bd_platform.charting_market_intelligence_layer",
        5: "bd_platform.defi_yield_intelligence_layer",
        6: "bd_platform.institutional_delivery_intelligence_layer",
    }[batch]
    return f"{REASON} batch={batch:02d}; layer={layer}; cap_{cid} seed metric."


def _patch_evidence(path: Path) -> int:
    if not path.is_file():
        return 0
    changed = 0
    out_lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        cid = int(row["capability_id"])
        if cid not in ALL_STUBS:
            out_lines.append(json.dumps(row, ensure_ascii=False))
            continue
        row["deep_audit_classification"] = "WRAPPER-ONLY-UNVERIFIED"
        row["implementation_class"] = "wrapper_only_unverified"
        row["template_seed_stub"] = True
        row["reclassification_reason"] = _reason_for(cid)
        row["reclassified_at"] = datetime.now(UTC).isoformat()
        notes = str(row.get("notes") or "")
        if "WRAPPER-ONLY-UNVERIFIED" not in notes:
            row["notes"] = (notes + " — WRAPPER-ONLY-UNVERIFIED (TEMPLATE-SEED-STUB)").strip(" —")
        changed += 1
        out_lines.append(json.dumps(row, ensure_ascii=False))
    path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return changed


def _recount(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        cls = row.get("classification") or row.get("deep_audit_classification") or "UNKNOWN"
        counts[cls] = counts.get(cls, 0) + 1
    return counts


def _patch_audit(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("rows") or []
    changed = 0
    for row in rows:
        cid = int(row["capability_id"])
        if cid not in ALL_STUBS:
            continue
        row["classification"] = "WRAPPER-ONLY-UNVERIFIED"
        row["prior_implementation_class"] = row.get("prior_implementation_class") or "verified_deep"
        row["template_seed_stub"] = True
        row["reclassification_reason"] = _reason_for(cid)
        row["reclassified_at"] = datetime.now(UTC).isoformat()
        changed += 1
    counts = _recount(rows)
    data["classification_counts"] = {
        k: counts.get(k, 0)
        for k in ("VERIFIED-DEEP", "REUSED-LINK", "WRAPPER-ONLY-UNVERIFIED", "DEFERRED/DELEGATED")
    }
    if "verified_deep_native_count" in data:
        data["verified_deep_native_count"] = counts.get("VERIFIED-DEEP", 0)
    if "wrapper_only_unverified_count" in data:
        data["wrapper_only_unverified_count"] = counts.get("WRAPPER-ONLY-UNVERIFIED", 0)
    if "verified_deep_honest_count" in data:
        data["verified_deep_honest_count"] = (
            counts.get("VERIFIED-DEEP", 0) + counts.get("REUSED-LINK", 0)
        )
    data["template_seed_stub_reclassified_count"] = changed
    data["template_seed_stub_reclassified_at"] = datetime.now(UTC).isoformat()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def _patch_retrospective_01_04() -> int:
    path = ROOT / "docs/RETROSPECTIVE_RECLASSIFICATION_BATCHES_01_04.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    per_batch: dict[str, dict[str, int]] = {}
    for row in data.get("rows", []):
        cid = int(row["capability_id"])
        batch = row.get("batch", "")
        per_batch.setdefault(batch, {})
        if cid in ALL_STUBS:
            row["classification"] = "WRAPPER-ONLY-UNVERIFIED"
            row["template_seed_stub"] = True
            row["reclassification_reason"] = _reason_for(cid)
            row["reclassified_at"] = datetime.now(UTC).isoformat()
            changed += 1
        cls = row["classification"]
        per_batch[batch][cls] = per_batch[batch].get(cls, 0) + 1
    data["per_batch_counts"] = {
        b: {
            "VERIFIED-DEEP": c.get("VERIFIED-DEEP", 0),
            "REUSED-LINK": c.get("REUSED-LINK", 0),
            "WRAPPER-ONLY-UNVERIFIED": c.get("WRAPPER-ONLY-UNVERIFIED", 0),
            "DEFERRED/DELEGATED": c.get("DEFERRED/DELEGATED", 0),
        }
        for b, c in per_batch.items()
    }
    totals = _recount(data["rows"])
    data["classification_counts"] = {
        k: totals.get(k, 0)
        for k in ("VERIFIED-DEEP", "REUSED-LINK", "WRAPPER-ONLY-UNVERIFIED", "DEFERRED/DELEGATED")
    }
    data["verified_deep_native_count"] = totals.get("VERIFIED-DEEP", 0)
    data["wrapper_only_unverified_count"] = totals.get("WRAPPER-ONLY-UNVERIFIED", 0)
    data["template_seed_stub_reclassified_count"] = changed
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def _patch_checklist() -> int:
    import pandas as pd

    path = ROOT / "capabilities_checklist.xlsx"
    df = pd.read_excel(path)
    id_col = "#"
    status_col = "الحالة"
    changed = 0
    for idx, row in df.iterrows():
        try:
            cid = int(row[id_col])
        except (TypeError, ValueError):
            continue
        if cid not in ALL_STUBS:
            continue
        old = str(row[status_col])
        marker = "WRAPPER-ONLY-UNVERIFIED — TEMPLATE-SEED-STUB"
        if marker in old:
            continue
        base = re.sub(r"\s*—\s*VERIFIED-DEEP.*$", "", old)
        base = re.sub(r"\s*—\s*مبني جزئيًا.*$", "", base)
        df.at[idx, status_col] = f"{base} — {marker}; {_reason_for(cid)}"
        changed += 1
    df.to_excel(path, index=False)
    completed_path = ROOT / "capabilities_checklist_completed.xlsx"
    if completed_path.is_file():
        df.to_excel(completed_path, index=False)
    return changed


def main() -> None:
    manifest = {
        "reclassified_at": datetime.now(UTC).isoformat(),
        "total": len(ALL_STUBS),
        "by_batch": {str(k): v for k, v in STUBS_BY_BATCH.items()},
        "reason_template": REASON,
        "entries": {str(cid): _reason_for(cid) for cid in sorted(ALL_STUBS)},
    }
    out = ROOT / "docs/TEMPLATE_STUB_RECLASSIFICATION_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ev = sum(_patch_evidence(p) for p in EVIDENCE_FILES.values())
    au = sum(_patch_audit(p) for p in AUDIT_FILES.values())
    retro = _patch_retrospective_01_04()
    xlsx = _patch_checklist()
    print(json.dumps({"evidence": ev, "audit": au, "retro": retro, "xlsx": xlsx, "total": len(ALL_STUBS)}, indent=2))


if __name__ == "__main__":
    main()
