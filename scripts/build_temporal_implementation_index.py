#!/usr/bin/env python3
"""Build Temporal implementation index — requirement → module/test traceability."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bd_platform import temporal_source_driven_engineering as temporal  # noqa: E402

MATRIX = ROOT / "docs/BATCH13_TEMPORAL_IMPLEMENTATION_MATRIX.json"
OUT = ROOT / "docs/TEMPORAL_IMPLEMENTATION_INDEX.json"

DOMAIN_TESTS = {
    "event_store": ["tests/test_temporal_source_driven_engineering.py", "tests/test_batch13_temporal_spine.py"],
    "pit_leakage": ["tests/test_batch13_temporal_spine.py", "tests/test_temporal_source_driven_engineering.py"],
    "contamination": ["tests/test_batch13_temporal_spine.py"],
    "replay_walk_forward": ["tests/test_batch16_three_spec_foundations.py", "tests/test_batch13_temporal_spine.py"],
    "reproducibility": ["tests/test_batch13_temporal_spine.py"],
    "signal_trace": ["tests/test_temporal_source_driven_engineering.py"],
    "decision_trace": ["tests/test_temporal_source_driven_engineering.py"],
    "outcome_factory": ["tests/test_temporal_source_driven_engineering.py"],
    "evidence_ledger": ["tests/test_temporal_source_driven_engineering.py"],
    "failure_surprise_abstention": ["tests/test_temporal_source_driven_engineering.py"],
    "regime": ["tests/test_batch15_three_spec_foundations.py", "tests/test_temporal_source_driven_engineering.py"],
    "evidence_class": ["tests/test_batch13_temporal_spine.py"],
    "champion_challenger": ["tests/test_temporal_source_driven_engineering.py"],
    "forward_shadow": ["tests/test_temporal_source_driven_engineering.py"],
    "calibration_promotion": ["tests/test_temporal_source_driven_engineering.py"],
    "controlled_learning": ["tests/test_temporal_source_driven_engineering.py"],
    "cross_cutting": ["tests/test_temporal_source_driven_engineering.py"],
    "maturity_prerequisite": ["tests/test_temporal_source_driven_engineering.py"],
}

MODULE_ALIASES = {"backend_registry.py": "cap646/backend_registry.py"}


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    bindings = {}
    for row in matrix["rows"]:
        uid = row["canonical_requirement_id"]
        domain = temporal.resolve_closure_domain(row)
        paths = [
            "bd_platform/temporal_source_driven_engineering.py",
            "bd_platform/temporal_persistent_registries.py",
        ]
        if row.get("canonical_implementation"):
            paths.insert(0, MODULE_ALIASES.get(row["canonical_implementation"], row["canonical_implementation"]))
        cls = row.get("classification", "UNKNOWN")
        bindings[uid] = {
            "unique_id": uid,
            "domain": domain,
            "source_classification": cls,
            "implementation_intended": cls in temporal.BUILDABLE_CLASSIFICATIONS,
            "enforcement_tier": "MATURITY_GATED"
            if uid in temporal.MATURITY_GATED_IDS or cls == "EXPLICITLY_LATER_BY_SOURCE"
            else ("REJECT" if cls in temporal.BUILDABLE_CLASSIFICATIONS else "DOCUMENT_ONLY"),
            "module_paths": list(dict.fromkeys(paths)),
            "test_paths": DOMAIN_TESTS.get(domain, ["tests/test_temporal_source_driven_engineering.py"]),
            "source_aliases": row.get("source_aliases") or [],
        }
    payload = {
        "artifact": "TEMPORAL_IMPLEMENTATION_INDEX",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_head": git_head(),
        "binding_count": len(bindings),
        "bindings": bindings,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(OUT), "bindings": len(bindings)}, indent=2))


if __name__ == "__main__":
    main()
