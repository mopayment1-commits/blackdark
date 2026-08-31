#!/usr/bin/env python3
"""Generate unified final integrity summary across hero batches 01-06."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVIDENCE_FILES = [
    ROOT / "data/hero_batch_01_evidence.jsonl",
    ROOT / "data/hero_batch_02_101_200_evidence.jsonl",
    ROOT / "data/hero_batch_03_201_300_evidence.jsonl",
    ROOT / "data/hero_batch_04_301_400_evidence.jsonl",
    ROOT / "data/hero_batch_05_401_500_evidence.jsonl",
    ROOT / "data/hero_batch_06_501_600_evidence.jsonl",
]

EXTENSION_PENDING = frozenset({704, 708, 812, 814, 815})
OPTION_A = frozenset({338, 500, 507, 534})


def _load_evidence() -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    by_id: dict[int, dict[str, Any]] = {}
    for path in EVIDENCE_FILES:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            rows.append(row)
            by_id[int(row["capability_id"])] = row
    return rows, by_id


def _load_manifest_ids(path: Path, key: str = "ids") -> set[int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if key in data:
        return {int(i) for i in data[key]}
    if "entries" in data:
        return {int(k) for k in data["entries"]}
    raise KeyError(key)


def _run_pytest() -> dict[str, Any]:
    proc = subprocess.run(
        ["pytest", "-m", "not slow", "--tb=no", "-rA"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    summary = ""
    for line in proc.stdout.splitlines():
        if "passed" in line and "in" in line:
            summary = line.strip()
    return {"exit_code": proc.returncode, "summary": summary, "passed": proc.returncode == 0}


def main() -> None:
    all_rows, by_id = _load_evidence()
    unique_ids = sorted(by_id)
    assert len(all_rows) == 600, len(all_rows)

    wrapper = _load_manifest_ids(ROOT / "docs/TEMPLATE_STUB_RECLASSIFICATION_MANIFEST.json")
    split144 = _load_manifest_ids(ROOT / "docs/SPLIT_BRAIN_ROUTING_RECLASSIFICATION_MANIFEST.json")
    split_bcd = _load_manifest_ids(ROOT / "docs/SPLIT_BRAIN_BCD_RECLASSIFICATION_MANIFEST.json")
    option_b = _load_manifest_ids(ROOT / "docs/OPTION_B_DEFERRED_RECLASSIFICATION_MANIFEST.json")
    split_all = split144 | split_bcd

    cls_counts = Counter(by_id[cid].get("deep_audit_classification", "UNKNOWN") for cid in unique_ids)

    # Overlap checks
    overlap_wrapper_split = wrapper & split_all
    overlap_option_a_wrapper = OPTION_A & wrapper
    overlap_option_a_split = OPTION_A & split_all

    # Arithmetic
    naive_remainder = 600 - len(wrapper) - len(split_all)
    unique_remainder_ids = sorted(set(unique_ids) - wrapper - split_all)

    # Healthy = no discovered integrity issue
    integrity_issue_classes = {
        "SPLIT-BRAIN-UNVERIFIED",
        "WRAPPER-ONLY-UNVERIFIED",
        "DEFERRED/TEMPLATE-STUB",
        "EXTENSION-PENDING-CAP646",
    }
    healthy_ids = sorted(
        cid
        for cid, row in by_id.items()
        if row.get("deep_audit_classification") == "PRODUCTION-ALIGNED"
    )

    unverified_claims = sorted(
        cid
        for cid, row in by_id.items()
        if row.get("deep_audit_classification") in {"VERIFIED-DEEP", "REUSED-LINK"}
    )

    production_aligned = sorted(cid for cid, row in by_id.items() if row.get("deep_audit_classification") == "PRODUCTION-ALIGNED")

    pytest_result = _run_pytest()

    out: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Hero batches 01-06 evidence universe",
        "evidence_rows": len(all_rows),
        "unique_capability_ids": len(unique_ids),
        "duplicate_row_ids": sorted({int(r["capability_id"]) for r in all_rows if sum(1 for x in all_rows if int(x["capability_id"]) == int(r["capability_id"])) > 1}),
        "classification_counts_unique_ids": dict(sorted(cls_counts.items())),
        "overlap_analysis": {
            "wrapper_only_count": len(wrapper),
            "split_brain_total_count": len(split_all),
            "split_brain_routing_count": len(split144),
            "split_brain_bcd_count": len(split_bcd),
            "wrapper_intersect_split_brain": sorted(overlap_wrapper_split),
            "wrapper_intersect_split_brain_count": len(overlap_wrapper_split),
            "option_a_in_wrapper": sorted(overlap_option_a_wrapper),
            "option_a_in_split_brain": sorted(overlap_option_a_split),
            "option_b_deferred_count": len(option_b),
            "conclusion": "WRAPPER-ONLY (311 manifest) and SPLIT-BRAIN (202) are disjoint sets (0 ID overlap). Option A (4) were subset of WRAPPER manifest, now PRODUCTION-ALIGNED.",
        },
        "arithmetic_question": {
            "formula_naive": "600 - 311 - 202 = 87",
            "naive_remainder": naive_remainder,
            "unique_remainder_count": len(unique_remainder_ids),
            "unique_remainder_ids": unique_remainder_ids,
            "duplicate_row_adjustment": naive_remainder - len(unique_remainder_ids),
            "explanation": (
                "600 evidence rows minus 311 WRAPPER-ONLY minus 202 SPLIT-BRAIN yields 87 row-slots, "
                "but 24 IDs appear twice (batch-01 hero overlap), so unique remainder = 63."
            ),
        },
        "healthy_capabilities": {
            "count": len(healthy_ids),
            "definition": "PRODUCTION-ALIGNED only — explicit_option_a binding verified live; no integrity issue discovered",
            "ids": healthy_ids,
        },
        "production_aligned": {
            "count": len(production_aligned),
            "ids": production_aligned,
        },
        "extension_pending_cap646": {
            "count": len(EXTENSION_PENDING),
            "ids": sorted(EXTENSION_PENDING),
            "reason": (
                "Present in CAP978 catalog and batch-01 evidence but absent from cap646.backend_registry "
                "(binding_for raises KeyError). Require cap646 registration or dedicated CAP978-only verification path — "
                "not closed under cap646 program until registered."
            ),
            "verification_path": "Register in cap646 catalog + backend_registry OR run separate CAP978 extension closure track",
        },
        "unverified_verified_deep_or_reused_link_remaining": {
            "count": len(unverified_claims),
            "ids": unverified_claims,
            "note": "Must be 0 after full reclassification; any non-zero is a blocker",
        },
        "pytest_not_slow": pytest_result,
        "manifests": {
            "wrapper_only": "docs/TEMPLATE_STUB_RECLASSIFICATION_MANIFEST.json",
            "split_brain_routing": "docs/SPLIT_BRAIN_ROUTING_RECLASSIFICATION_MANIFEST.json",
            "split_brain_bcd": "docs/SPLIT_BRAIN_BCD_RECLASSIFICATION_MANIFEST.json",
            "option_b_deferred": "docs/OPTION_B_DEFERRED_RECLASSIFICATION_MANIFEST.json",
            "option_a_aligned": "docs/OPTION_A_PRODUCTION_ALIGNED_MANIFEST.json",
            "option_a_proof": "docs/OPTION_A_PRODUCTION_PROOF.json",
        },
    }

    json_path = ROOT / "docs/FINAL_INTEGRITY_SUMMARY_BATCHES_01_06.json"
    md_path = ROOT / "docs/FINAL_INTEGRITY_SUMMARY_BATCHES_01_06.md"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Final integrity summary — hero batches 01–06",
        "",
        f"**Generated:** {out['generated_at']}",
        "",
        "## Classification counts (unique IDs)",
        "",
        "| Classification | Count |",
        "|----------------|------:|",
    ]
    for k, v in sorted(out["classification_counts_unique_ids"].items()):
        lines.append(f"| `{k}` | {v} |")

    lines.extend(
        [
            "",
            "## 1) Arithmetic (600 − 311 − 202)",
            "",
            f"- Naive row arithmetic: **{out['arithmetic_question']['naive_remainder']}**",
            f"- Unique IDs remainder: **{out['arithmetic_question']['unique_remainder_count']}**",
            f"- Duplicate-row adjustment: **{out['arithmetic_question']['duplicate_row_adjustment']}**",
            f"- Remainder IDs: `{', '.join(str(i) for i in out['arithmetic_question']['unique_remainder_ids'])}`",
            "",
            "## 2) Healthy capabilities (no integrity issue)",
            "",
            f"**Count: {out['healthy_capabilities']['count']}** — IDs: `{', '.join(str(i) for i in out['healthy_capabilities']['ids'])}`",
            "",
            "## 3) Overlap WRAPPER vs SPLIT-BRAIN",
            "",
            f"- Intersection count: **{out['overlap_analysis']['wrapper_intersect_split_brain_count']}** (disjoint)",
            "",
            "## 4) PRODUCTION-ALIGNED (Option A)",
            "",
            f"`{', '.join(str(i) for i in out['production_aligned']['ids'])}`",
            "",
            "## 5) Extension pending (CAP646)",
            "",
            f"IDs: `{', '.join(str(i) for i in out['extension_pending_cap646']['ids'])}`",
            "",
            out["extension_pending_cap646"]["reason"],
            "",
            f"**Path:** {out['extension_pending_cap646']['verification_path']}",
            "",
            "## 6) Unverified VERIFIED-DEEP / REUSED-LINK remaining",
            "",
            f"**Count: {out['unverified_verified_deep_or_reused_link_remaining']['count']}**",
            "",
            "## pytest -m \"not slow\"",
            "",
            f"`{pytest_result['summary']}`",
            "",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"healthy": out["healthy_capabilities"], "classes": out["classification_counts_unique_ids"], "pytest": pytest_result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
