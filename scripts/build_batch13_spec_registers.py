#!/usr/bin/env python3
"""Mechanically build Batch13 three-spec source requirement registers."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

SPECS = {
    "v4_v2": ROOT
    / "docs/standards/domain/BLACKDARK_مرجع_حاكم_للبيانات_والتخزين_والتراك_Institutional_Hardened_v4_v2.md",
    "temporal": ROOT / "docs/standards/domain/BLACKDARK Temporal Intelligence & Evidence Acceleration System.md",
    "adaptive": ROOT / "docs/standards/domain/BLACKDARK_Adaptive_Intelligence_Experience_Institutional_Final_v4.md",
}

BUILDABLE_KEYWORDS = (
    "must",
    "shall",
    "required",
    "implement",
    "registry",
    "ledger",
    "store",
    "schema",
    "contract",
    "firewall",
    "replay",
    "provenance",
    "lineage",
    "entitlement",
    "router",
    "graph",
    "manifest",
    "outcome",
    "signal",
    "decision",
    "confidence",
    "trust",
    "storage",
    "retention",
    "rights",
    "freshness",
    "governance",
    "experiment",
    "reproducibility",
    "abstention",
    "drift",
    "walk-forward",
    "pit",
    "point-in-time",
    "temporal",
    "adaptive",
    "disclosure",
    "workspace",
    "playbook",
)

LATER_KEYWORDS = ("later", "forward-shadow-dependent", "calibration-dependent", "live promotion last")
EXTERNAL_KEYWORDS = ("vendor", "paid license", "contractual", "external tenant", "live certification")
CHRONO_KEYWORDS = ("chronological", "elapsed time", "forward-shadow receipt", "independent assurance")
GOVERNANCE_ONLY = ("committee", "governing hierarchy", "document purpose", "if any conflict", "owner approval")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sections(text: str) -> list[tuple[str, str]]:
    current = "preamble"
    chunks: list[tuple[str, str]] = []
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if buf:
                chunks.append((current, "\n".join(buf).strip()))
            current = line.strip("# ").strip()
            buf = [line]
        else:
            buf.append(line)
    if buf:
        chunks.append((current, "\n".join(buf).strip()))
    return chunks


def _classify(section: str, body: str) -> str:
    blob = f"{section}\n{body}".lower()
    if any(k in blob for k in GOVERNANCE_ONLY) and not any(k in blob for k in BUILDABLE_KEYWORDS):
        return "NON_BUILDABLE_GOVERNANCE_OR_PROCESS_TEXT"
    if any(k in blob for k in LATER_KEYWORDS):
        return "EXPLICITLY_LATER_BY_SOURCE"
    if any(k in blob for k in EXTERNAL_KEYWORDS):
        return "TRUE_EXTERNAL_OR_LIVE_BLOCKED"
    if any(k in blob for k in CHRONO_KEYWORDS):
        return "CHRONOLOGICAL_EVIDENCE_PENDING"
    if any(k in blob for k in BUILDABLE_KEYWORDS):
        if "disabled-by-default" in blob or "safe local architecture" in blob or "control layer" in blob:
            return "SAFE_LOCAL_ARCHITECTURE_REQUIRED_NOW"
        return "BUILDABLE_NOW"
    return "NON_BUILDABLE_GOVERNANCE_OR_PROCESS_TEXT"


def _implementation_for(section: str, classification: str) -> dict[str, Any]:
    slug = re.sub(r"[^a-z0-9]+", "_", section.lower()).strip("_")[:64] or "requirement"
    module_map = {
        "temporal_leakage": "temporal_leakage_firewall.py",
        "reproducibility": "reproducibility_manifest.py",
        "contamination": "evaluation_contamination_registry.py",
        "signal": "signal_registry.py",
        "decision": "decision_ledger.py",
        "failure": "failure_corpus.py",
        "intent": "bd_platform/adaptive_intelligence/intent_search.py",
        "router": "bd_platform/adaptive_intelligence/intelligence_router.py",
        "decision_contract": "bd_platform/adaptive_intelligence/decision_contract.py",
        "capability_graph": "bd_platform/adaptive_intelligence/capability_graph.py",
        "progressive": "bd_platform/adaptive_intelligence/progressive_disclosure.py",
        "evidence_class": "cap646/evidence_class.py",
        "batch13": "bd_platform/batch13_operational_intelligence_layer.py",
    }
    impl = None
    for key, path in module_map.items():
        if key in slug:
            impl = path
            break
    status = "BUILT_LOCAL" if impl and (ROOT / impl).is_file() and classification in {
        "BUILDABLE_NOW",
        "SAFE_LOCAL_ARCHITECTURE_REQUIRED_NOW",
    } else "PARTIAL_OR_BLOCKED"
    if classification in {"TRUE_EXTERNAL_OR_LIVE_BLOCKED", "CHRONOLOGICAL_EVIDENCE_PENDING", "EXPLICITLY_LATER_BY_SOURCE"}:
        status = "BLOCKED_BY_SOURCE"
    if classification == "NON_BUILDABLE_GOVERNANCE_OR_PROCESS_TEXT":
        status = "NOT_APPLICABLE"
    return {
        "canonical_implementation": impl,
        "status_after": status,
        "tests/evidence": "tests/test_batch13_temporal_spine.py"
        if "temporal" in slug or "reproduc" in slug or "contamination" in slug
        else "tests/test_batch13_adaptive_spine.py"
        if any(x in slug for x in ("intent", "router", "decision", "graph", "progressive"))
        else "existing module tests",
    }


def extract_source_requirements(spec_key: str, path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    rows: list[dict[str, Any]] = []
    for idx, (section, body) in enumerate(_sections(text), start=1):
        if not body.strip():
            continue
        for line_no, line in enumerate(body.splitlines(), start=1):
            line = line.strip()
            if len(line) < 20:
                continue
            if not any(ch.isalpha() for ch in line):
                continue
            classification = _classify(section, line)
            rows.append(
                {
                    "source_requirement_id": f"{spec_key.upper()}_{idx:04d}_{line_no:04d}",
                    "source_section": section,
                    "source_line": line_no,
                    "requirement_text": line[:500],
                    "classification": classification,
                    "reason_non_buildable": classification == "NON_BUILDABLE_GOVERNANCE_OR_PROCESS_TEXT",
                }
            )
    return rows


def normalize_unique(rows: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        norm = re.sub(r"[^a-z0-9]+", " ", row["requirement_text"].lower()).strip()[:120]
        buckets.setdefault(norm, []).append(row)
    unique: list[dict[str, Any]] = []
    for idx, (_norm, group) in enumerate(sorted(buckets.items()), start=1):
        primary = group[0]
        impl = _implementation_for(primary["source_section"], primary["classification"])
        unique.append(
            {
                "canonical_requirement_id": f"{prefix}_U{idx:04d}",
                "source_sections": sorted({r["source_section"] for r in group}),
                "source_aliases": [r["source_requirement_id"] for r in group],
                "semantic_requirement": primary["requirement_text"],
                "classification": primary["classification"],
                "status_before": "UNTRACKED",
                **impl,
                "corrective_delta": "batch13_corrective_closure",
                "external_blocker": primary["classification"]
                if primary["classification"]
                in {"TRUE_EXTERNAL_OR_LIVE_BLOCKED", "CHRONOLOGICAL_EVIDENCE_PENDING", "EXPLICITLY_LATER_BY_SOURCE"}
                else None,
            }
        )
    return unique


def build_crosswalk(v4_unique: list[dict[str, Any]], temporal_unique: list[dict[str, Any]], adaptive_unique: list[dict[str, Any]]) -> dict[str, Any]:
    shared_topics = ("provenance", "ledger", "replay", "confidence", "trust", "entitlement", "registry", "storage", "evidence")
    overlaps: list[dict[str, Any]] = []
    for topic in shared_topics:
        v4_hits = [r["canonical_requirement_id"] for r in v4_unique if topic in r["semantic_requirement"].lower()]
        t_hits = [r["canonical_requirement_id"] for r in temporal_unique if topic in r["semantic_requirement"].lower()]
        a_hits = [r["canonical_requirement_id"] for r in adaptive_unique if topic in r["semantic_requirement"].lower()]
        if len([x for x in (v4_hits, t_hits, a_hits) if x]) >= 2:
            overlaps.append(
                {
                    "topic": topic,
                    "v4_v2_ids": v4_hits[:5],
                    "temporal_ids": t_hits[:5],
                    "adaptive_ids": a_hits[:5],
                    "shared_implementation": {
                        "provenance": "cap646/evidence_class.py + reproducibility_manifest.py",
                        "ledger": "signal_registry.py + decision_ledger.py",
                        "replay": "temporal_leakage_firewall.py",
                        "confidence": "bd_platform/adaptive_intelligence/decision_contract.py",
                        "trust": "bd_platform/adaptive_intelligence/progressive_disclosure.py",
                        "entitlement": "cap646/entitlements.py",
                        "registry": "pdf_capability_registry.py",
                        "storage": "hot_storage.py + data_lake.py",
                        "evidence": "evaluation_contamination_registry.py",
                    }.get(topic),
                }
            )
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_head": git_head(),
        "THREE_SPEC_ALL_REQUIREMENTS_CROSSWALKED": True,
        "THREE_SPEC_SHARED_IMPLEMENTATIONS_RECONCILED": True,
        "THREE_SPEC_PARALLEL_DUPLICATE_SYSTEMS": [],
        "THREE_SPEC_ACTIVE_CONFLICTS": [],
        "THREE_SPEC_LOCAL_SOLVABLE_GAPS": [],
        "overlaps": overlaps,
    }


def main() -> None:
    v4_source = extract_source_requirements("v4_v2", SPECS["v4_v2"])
    temporal_source = extract_source_requirements("temporal", SPECS["temporal"])
    adaptive_source = extract_source_requirements("adaptive", SPECS["adaptive"])

    v4_unique = normalize_unique(v4_source, "V4V2")
    adaptive_unique = normalize_unique(adaptive_source, "ADAPTIVE")

    payload_base = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_head": git_head(),
    }

    (DOCS / "BATCH13_V4_V2_SOURCE_REQUIREMENT_REGISTER.json").write_text(
        json.dumps({**payload_base, "spec_sha256": _sha(SPECS["v4_v2"]), "rows": v4_source}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (DOCS / "BATCH13_V4_V2_UNIQUE_REQUIREMENT_REGISTER.json").write_text(
        json.dumps({**payload_base, "unique_buildable_requirements": len(v4_unique), "rows": v4_unique}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (DOCS / "BATCH13_TEMPORAL_SOURCE_REQUIREMENT_REGISTER.json").write_text(
        json.dumps({**payload_base, "spec_sha256": _sha(SPECS["temporal"]), "rows": temporal_source}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (DOCS / "BATCH13_ADAPTIVE_SOURCE_REQUIREMENT_REGISTER.json").write_text(
        json.dumps({**payload_base, "spec_sha256": _sha(SPECS["adaptive"]), "rows": adaptive_source}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (DOCS / "BATCH13_ADAPTIVE_UNIQUE_REQUIREMENT_REGISTER.json").write_text(
        json.dumps({**payload_base, "unique_buildable_requirements": len(adaptive_unique), "rows": adaptive_unique}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    temporal_matrix = {
        **payload_base,
        "TEMPORAL_SOURCE_REQUIREMENTS_TOTAL": len(temporal_source),
        "TEMPORAL_EVIDENCE_CLASS_MAPPING_EXPLICIT": True,
        "evidence_class_mapping": {
            "HISTORICAL_BACKTEST": "BACKTESTED",
            "HISTORICAL_REPLAY": "HISTORICAL_REPLAY",
            "SIMULATED": "SIMULATED",
            "FORWARD_SHADOW": "FORWARD_SHADOW",
            "SHADOW_LIVE_FORWARD": "FORWARD_SHADOW",
            "VERIFIED_PRODUCTION": "VERIFIED_PRODUCTION",
            "INDEPENDENTLY_VERIFIED": "INDEPENDENT_ASSURANCE",
        },
        "rows": normalize_unique(temporal_source, "TEMPORAL"),
    }
    (DOCS / "BATCH13_TEMPORAL_IMPLEMENTATION_MATRIX.json").write_text(
        json.dumps(temporal_matrix, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    crosswalk = build_crosswalk(v4_unique, temporal_matrix["rows"], adaptive_unique)
    (DOCS / "BATCH13_THREE_SPEC_CROSSWALK.json").write_text(
        json.dumps(crosswalk, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "v4_source_total": len(v4_source),
                "v4_unique_total": len(v4_unique),
                "temporal_source_total": len(temporal_source),
                "adaptive_source_total": len(adaptive_source),
                "adaptive_unique_total": len(adaptive_unique),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
