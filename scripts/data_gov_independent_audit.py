#!/usr/bin/env python3
"""Independent second-pass audit of DATA/RESTORE requirement extraction."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "governing-sources-population/BLACKDARK_INSTITUTIONAL_DATA_INTELLIGENCE_GOVERNANCE_SPEC_2026_FINAL_v2_RESTORED.md"
OUT_DIR = ROOT / "institutional_due_diligence_2026/DATA_GOV_COMPLIANCE"


def _extract_spec_ids(text: str) -> set[str]:
    data_ids = set(re.findall(r"\bDATA-\d{3}\b", text))
    restore_ids = set(re.findall(r"\bRESTORE-\d{3}\b", text))
    return data_ids | restore_ids


def main() -> int:
    spec_text = SPEC.read_text(encoding="utf-8")
    spec_ids = _extract_spec_ids(spec_text)
    primary = json.loads((OUT_DIR / "DATA_GOV_PRIMARY_REQUIREMENTS.json").read_text(encoding="utf-8"))
    mapping = json.loads((OUT_DIR / "DATA_GOV_PRIMARY_TO_ATOMIC_MAPPING.json").read_text(encoding="utf-8"))
    atomic = json.loads((OUT_DIR / "DATA_GOV_ATOMIC_REQUIREMENTS.json").read_text(encoding="utf-8"))

    extracted_ids = {p["requirement_id"] for p in primary["primary_requirements"]}
    missing_from_extract = sorted(spec_ids - extracted_ids)
    extra_in_extract = sorted(extracted_ids - spec_ids)

    atomic_ids = {o["atomic_id"] for o in atomic["obligations"]}
    mapped_ids = {m["atomic_id"] for m in mapping["mapping"]}
    unmapped_atomic = sorted(atomic_ids - mapped_ids)
    orphan_mapped = sorted(mapped_ids - atomic_ids)

    must_count = len(re.findall(r"\bMUST\b", spec_text))
    must_not_count = len(re.findall(r"\bMUST NOT\b", spec_text))

    report = {
        "audit_pass": (
            not missing_from_extract
            and not extra_in_extract
            and not unmapped_atomic
            and not orphan_mapped
            and mapping["UNMAPPED_ATOMIC_REQUIREMENTS"] == 0
            and mapping["SILENTLY_MERGED_REQUIREMENTS"] == 0
            and mapping["OMITTED_NORMATIVE_REQUIREMENTS"] == 0
        ),
        "spec_parent_ids_found": len(spec_ids),
        "extracted_parent_ids": len(extracted_ids),
        "missing_from_extract": missing_from_extract,
        "extra_in_extract": extra_in_extract,
        "atomic_obligations": len(atomic_ids),
        "mapped_atomic": len(mapped_ids),
        "unmapped_atomic": unmapped_atomic,
        "orphan_mapped": orphan_mapped,
        "spec_must_clauses": must_count,
        "spec_must_not_clauses": must_not_count,
        "UNMAPPED_ATOMIC_REQUIREMENTS": len(unmapped_atomic),
        "SILENTLY_MERGED_REQUIREMENTS": mapping.get("SILENTLY_MERGED_REQUIREMENTS", 0),
        "OMITTED_NORMATIVE_REQUIREMENTS": len(missing_from_extract),
        "UNEXPLAINED_REQUIREMENT_DELTA": len(extra_in_extract),
    }
    (OUT_DIR / "DATA_GOV_INDEPENDENT_AUDIT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["audit_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
