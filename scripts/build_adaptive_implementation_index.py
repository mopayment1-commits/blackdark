#!/usr/bin/env python3
"""Build Adaptive implementation index — requirement → module/test traceability."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bd_platform import adaptive_source_driven_engineering as adaptive  # noqa: E402

MATRIX = ROOT / "docs/BATCH13_ADAPTIVE_UNIQUE_REQUIREMENT_REGISTER.json"
OUT = ROOT / "docs/ADAPTIVE_IMPLEMENTATION_INDEX.json"

DOMAIN_TESTS = {
    "intelligence_router": ["tests/test_adaptive_source_driven_engineering.py", "tests/test_batch13_adaptive_spine.py"],
    "decision_boundary": ["tests/test_batch13_adaptive_spine.py", "tests/test_adaptive_source_driven_engineering.py"],
    "confidence_trust": ["tests/test_adaptive_source_driven_engineering.py"],
    "progressive_disclosure": ["tests/test_batch13_adaptive_spine.py"],
    "capability_graph": ["tests/test_batch13_adaptive_spine.py"],
    "intent_search": ["tests/test_batch13_adaptive_spine.py"],
    "universal_command": ["tests/test_adaptive_source_driven_engineering.py"],
    "taxonomy_discovery": ["tests/test_adaptive_source_driven_engineering.py"],
    "contextual_recommendations": ["tests/test_adaptive_source_driven_engineering.py"],
    "workspace_playbook_mystack": ["tests/test_adaptive_source_driven_engineering.py"],
    "data_room_institutional": ["tests/test_adaptive_source_driven_engineering.py"],
    "human_validation": ["tests/test_adaptive_source_driven_engineering.py"],
    "controlled_learning": ["tests/test_adaptive_source_driven_engineering.py"],
    "entitlement_role_tenant": ["tests/test_adaptive_source_driven_engineering.py"],
    "accessibility_usability": ["tests/test_adaptive_source_driven_engineering.py"],
    "six_heroes_disposition": ["tests/test_adaptive_source_driven_engineering.py"],
    "cross_cutting": ["tests/test_adaptive_source_driven_engineering.py"],
    "maturity_prerequisite": ["tests/test_adaptive_source_driven_engineering.py"],
}

MODULE_ALIASES = {"backend_registry.py": "cap646/backend_registry.py"}


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    bindings = {}
    for row in matrix["rows"]:
        uid = row["canonical_requirement_id"]
        domain = adaptive.resolve_closure_domain(row)
        paths = [
            "bd_platform/adaptive_source_driven_engineering.py",
            "bd_platform/adaptive_persistent_registries.py",
        ]
        if row.get("canonical_implementation"):
            paths.insert(0, MODULE_ALIASES.get(row["canonical_implementation"], row["canonical_implementation"]))
        cls = row.get("classification", "UNKNOWN")
        bindings[uid] = {
            "unique_id": uid,
            "domain": domain,
            "source_classification": cls,
            "implementation_intended": cls in adaptive.BUILDABLE_CLASSIFICATIONS,
            "enforcement_tier": "MATURITY_GATED"
            if uid in adaptive.MATURITY_GATED_IDS or cls == "EXPLICITLY_LATER_BY_SOURCE"
            else ("REJECT" if cls in adaptive.BUILDABLE_CLASSIFICATIONS else "DOCUMENT_ONLY"),
            "module_paths": list(dict.fromkeys(paths)),
            "test_paths": DOMAIN_TESTS.get(domain, ["tests/test_adaptive_source_driven_engineering.py"]),
            "source_aliases": row.get("source_aliases") or [],
        }
    payload = {
        "artifact": "ADAPTIVE_IMPLEMENTATION_INDEX",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_head": git_head(),
        "binding_count": len(bindings),
        "bindings": bindings,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(OUT), "bindings": len(bindings)}, indent=2))


if __name__ == "__main__":
    main()
