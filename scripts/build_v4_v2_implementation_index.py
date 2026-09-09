#!/usr/bin/env python3
"""Build v4_v2 implementation index — source requirement → module/test traceability."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys_path = ROOT
import sys

sys.path.insert(0, str(ROOT))

from bd_platform import v4_v2_phase1_engineering_spine as phase1  # noqa: E402

UNIQUE_PATH = ROOT / "docs/BATCH13_V4_V2_UNIQUE_REQUIREMENT_REGISTER.json"
CLOSURE_MAP = ROOT / "docs/V4_V2_PHASE1_CLOSURE_MAP.json"
MATRIX_PATH = ROOT / "docs/BATCH13_V4_V2_IMPLEMENTATION_MATRIX.json"
OUT = ROOT / "docs/V4_V2_IMPLEMENTATION_INDEX.json"

MODULE_PATH_ALIASES = {
    "backend_registry.py": "cap646/backend_registry.py",
    "runtime.py": "cap646/runtime.py",
}


def _normalize_module_path(path: str) -> str:
    if not path:
        return path
    return MODULE_PATH_ALIASES.get(path, path)


DOMAIN_TESTS: dict[str, list[str]] = {
    "storage_foundation": ["tests/test_batch13_temporal_spine.py", "tests/test_v4_v2_source_driven_engineering.py"],
    "provenance": ["tests/test_batch13_temporal_spine.py", "tests/test_brand_coverage_radical_closure.py"],
    "source_rights": ["tests/test_v4_v2_source_driven_engineering.py"],
    "source_quality": ["tests/test_v4_v2_source_driven_engineering.py"],
    "lineage": ["tests/test_v4_v2_source_driven_engineering.py"],
    "pit_temporal": ["tests/test_batch13_temporal_spine.py", "tests/test_v4_v2_source_driven_engineering.py"],
    "correction_revision": ["tests/test_v4_v2_source_driven_engineering.py"],
    "registry": ["tests/test_signal_registry_public.py", "tests/test_v4_v2_source_driven_engineering.py"],
    "data_quality": ["tests/test_brand_coverage_radical_closure.py"],
    "evidence": ["tests/test_batch13_temporal_spine.py", "tests/test_v4_v2_source_driven_engineering.py"],
    "decision_signal": ["tests/test_batch13_adaptive_spine.py", "tests/test_v4_v2_source_driven_engineering.py"],
    "audit_retention": ["tests/test_v4_v2_source_driven_engineering.py"],
    "reliability": ["tests/test_v4_v2_source_driven_engineering.py"],
    "privacy_security": ["tests/test_v4_v2_source_driven_engineering.py"],
    "runtime_enforcement": ["tests/test_batch17_extension_suite.py"],
    "replay_runtime": ["tests/test_batch13_temporal_spine.py", "tests/test_batch16_three_spec_foundations.py"],
    "evaluation": ["tests/test_batch17_three_spec_foundations.py"],
    "capability_coupled": ["tests/test_batch17_extension_suite.py"],
    "cross_cutting": ["tests/test_v4_v2_source_driven_engineering.py"],
    "maturity_prerequisite": ["tests/test_v4_v2_source_driven_engineering.py"],
}


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _ledger_shaped(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": row.get("canonical_requirement_id"),
        "requirement_type": "PLATFORM",
        "implementation_nature": "OTHER_WITH_JUSTIFICATION",
        "shared_canonical_implementation": row.get("canonical_implementation"),
        "maturity_gate": row.get("canonical_requirement_id") in phase1.MATURITY_GATED_REQUIREMENT_IDS,
    }


def main() -> None:
    unique = json.loads(UNIQUE_PATH.read_text(encoding="utf-8"))
    closure_rows = {}
    if CLOSURE_MAP.is_file():
        closure_rows = {
            r["requirement_id"]: r for r in json.loads(CLOSURE_MAP.read_text(encoding="utf-8")).get("rows", [])
        }
    matrix_modules: dict[str, str] = {}
    if MATRIX_PATH.is_file():
        for row in json.loads(MATRIX_PATH.read_text(encoding="utf-8")).get("rows", []):
            matrix_modules[row["requirement_id"]] = row.get("canonical_implementation")

    bindings: dict[str, Any] = {}
    for row in unique.get("rows", []):
        uid = row["canonical_requirement_id"]
        domain = phase1.resolve_closure_domain(_ledger_shaped(row))
        closure = closure_rows.get(uid, {})
        module_paths = list(
            dict.fromkeys(
                _normalize_module_path(p)
                for p in (
                    [p for p in (closure.get("implementation_paths") or []) if p]
                    + ([row["canonical_implementation"]] if row.get("canonical_implementation") else [])
                    + [
                        "bd_platform/v4_v2_source_driven_engineering.py",
                        "bd_platform/v4_v2_persistent_registries.py",
                        "bd_platform/v4_v2_phase1_engineering_spine.py",
                    ]
                )
            )
        )
        classification = row.get("classification", "UNKNOWN")
        intended = classification in {"BUILDABLE_NOW", "SAFE_LOCAL_ARCHITECTURE_REQUIRED_NOW"}
        tier = "MATURITY_GATED" if uid in phase1.MATURITY_GATED_REQUIREMENT_IDS else ("REJECT" if intended else "DOCUMENT_ONLY")
        bindings[uid] = {
            "unique_id": uid,
            "domain": domain,
            "source_classification": classification,
            "implementation_intended": intended,
            "enforcement_tier": tier,
            "module_paths": module_paths,
            "implementation_paths": module_paths,
            "test_paths": DOMAIN_TESTS.get(domain, ["tests/test_v4_v2_source_driven_engineering.py"]),
            "source_aliases": row.get("source_aliases") or [],
            "semantic_requirement": (row.get("semantic_requirement") or "")[:200],
        }

    payload = {
        "artifact": "V4_V2_IMPLEMENTATION_INDEX",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_head": git_head(),
        "binding_count": len(bindings),
        "bindings": bindings,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(OUT), "bindings": len(bindings)}, indent=2))


if __name__ == "__main__":
    main()
