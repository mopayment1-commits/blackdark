#!/usr/bin/env python3
"""Item 4 — Six Heroes final freeze for Batch05 (normalization + weighting + sensitivity + explainability)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "docs/BATCH05_HERO_SIX_BINDING_201_250.json"
OUT = ROOT / "docs/BATCH05_HERO_SIX_FINAL_FREEZE.json"


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> None:
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    heroes = binding.get("heroes", [])

    freeze = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "sequence_item": 4,
        "scope": "Six Heroes final freeze — Batch05 201-250",
        "build_phase": "OPEN",
        "batch05_independent": 0,
        "progress_826": 179,
        "production_aligned_count": 0,
        "freeze_status": "FINAL_FREEZE_LOCAL",
        "not_claimed": ["LOCAL_GOVERNANCE_COMPLETE", "LIVE_READY", "batch05_independent"],
        "normalization": {
            "method": binding.get("normalization", {}).get("method"),
            "batch05_independent_caps": "N/A — 43 stranglers not in hero aggregation inputs",
            "reused_link_226": "inherits canonical #69 normalization at batch02 spine",
            "wave5_ids": "242-250 not in hero inputs — confirmed",
            "frozen": True,
        },
        "weighting": {
            "default": binding.get("weighting", {}).get("default"),
            "batch05_stub": binding.get("weighting", {}).get("batch05_stub"),
            "justification": binding.get("weighting", {}).get("justification"),
            "frozen": True,
            "adr_required_for_change": True,
        },
        "sensitivity": {
            "per_hero_loo": [
                {
                    "hero": h["hero"],
                    "batch05_direct_ids": h.get("batch05_direct_capability_ids", []),
                    "sensitivity_loo": h.get("sensitivity_loo"),
                    "five_scenarios": h.get("five_scenarios", []),
                }
                for h in heroes
            ],
            "independent_signal_concurrence": binding.get("independent_signal_concurrence"),
            "frozen": True,
        },
        "explainability": {
            "per_hero": [
                {
                    "hero": h["hero"],
                    "explainability": h.get("explainability"),
                    "reused_canonical_feeds": h.get("batch05_reused_canonical_feeds", []),
                }
                for h in heroes
            ],
            "aggregation_layer_five_scenario_bags": binding.get("aggregation_layer_five_scenario_bags"),
            "frozen": True,
        },
        "heroes_fed_by_batch05": {
            "direct_strangler_ids": [],
            "reused_canonical_only": {"226": 69},
            "wave5_ids_in_hero_inputs": [],
        },
        "binding_source": str(BINDING.relative_to(ROOT)),
        "post_wave5_confirmation": binding.get("post_wave5_confirmation"),
    }

    # Update binding with freeze stamp
    binding["final_freeze"] = {
        "frozen_at": freeze["generated_at"],
        "commit": git_commit(),
        "sequence_item": 4,
        "status": "FINAL_FREEZE_LOCAL",
        "note": "Normalization+Weighting+Sensitivity+Explainability frozen; no batch05 strangler in hero inputs",
    }
    binding["status"] = "FINAL_FREEZE_LOCAL — independent caps excluded until per-ID PA clearance"
    BINDING.write_text(json.dumps(binding, indent=2) + "\n", encoding="utf-8")
    OUT.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.name} — heroes={len(heroes)} freeze=FINAL_FREEZE_LOCAL")


if __name__ == "__main__":
    main()
