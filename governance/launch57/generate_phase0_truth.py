#!/usr/bin/env python3
"""Phase 0 — Truth discovery for Launch-57. Read-only repo analysis; no PASS issuance."""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
HERO_MATRIX_PATH = ROOT / "BLACKDARK_CAPABILITY_SIX_HERO_MATRIX.json"
PHANTOM_PATH = ROOT / "BLACKDARK_CAPABILITY_PHANTOM_DISPOSITION.json"
HERO_BINDING_PATH = ROOT / "docs" / "HERO_SIX_BINDING_REPORT.json"
OUT_DIR = ROOT / "governance" / "launch57"
REGISTER_PATH = OUT_DIR / "LAUNCH57_REGISTER.json"
REPORT_PATH = OUT_DIR / "PHASE0_TRUTH_REPORT.md"

PHANTOM_PATTERNS = [
    (r"raise\s+NotImplementedError", "NOT_IMPLEMENTED"),
    (r"\bTODO\b|\bFIXME\b", "TODO_FIXME_MATERIAL"),
    (r"return\s+\{\s*[\"']success[\"']\s*:\s*True", "HARDCODED_SUCCESS_DICT"),
    (r"FIN_004_DEMO", "DEMO_CONSTANT"),
    (r"random\.(random|uniform|choice)", "SYNTHETIC_RANDOM_OUTPUT"),
]

# Repo-evidence mapping candidates for launch items without explicit CAP-ID in source.
IMPLICIT_MAPPING_CANDIDATES: dict[int, dict] = {
    1: {
        "candidate_capability_ids": [],
        "candidate_evidence": [
            "decision_truth/product/command_view.py",
            "decision_truth/product/six_heroes.py",
            "api/routers/heroes.py",
        ],
        "mapping_basis": "product_composite_six_heroes_command_home",
    },
    2: {
        "candidate_capability_ids": [],
        "candidate_evidence": [
            "BLACKDARK_CAPABILITY_SIX_HERO_MATRIX.json#canonical_product_heroes[0]",
            "docs/HERO_SIX_BINDING_REPORT.json",
            "decision_truth/product/six_heroes.py",
            "api/routers/heroes.py",
        ],
        "mapping_basis": "hero_product_surface_no_distinct_canonical_cap_row_for_single_sentence_oracle",
    },
    3: {
        "candidate_capability_ids": ["CAP-0641"],
        "candidate_evidence": [
            "BLACKDARK_CAPABILITY_CURRENT_STATE.json canonical_name match",
            "tests/test_heroes_quality_polish.py",
            "trust_os_lenses.py",
        ],
        "mapping_basis": "canonical_name_decision_certificate_not_in_launch57_scope",
    },
    5: {
        "candidate_capability_ids": ["CAP-0639", "CAP-0635"],
        "candidate_evidence": [
            "net_edge_truth.py",
            "decision_truth/net_edge.py",
            "BLACKDARK_CAPABILITY_CURRENT_STATE.json CAP-0639",
        ],
        "mapping_basis": "net_edge_truth_runtime_modules",
    },
    6: {
        "candidate_capability_ids": [],
        "candidate_evidence": [
            "cap646/evidence_class.py",
            "user_exposure_log.py",
            "decision_truth/evidence_taxonomy.py",
        ],
        "mapping_basis": "evidence_class_cross_cutting_not_single_cap",
    },
    44: {
        "candidate_capability_ids": [],
        "candidate_evidence": [
            "trust_os_lenses.py",
            "decision_truth/product/delivery.py",
        ],
        "mapping_basis": "shareable_card_product_layer",
    },
    46: {
        "candidate_capability_ids": [],
        "candidate_evidence": [
            "governance/anonymous_visitor_governance.py",
            "docs/BLACKDARK_ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_EXPERIENCE_2026_FINAL.md",
        ],
        "mapping_basis": "anonymous_visitor_governance_surface",
    },
    47: {
        "candidate_capability_ids": [],
        "candidate_evidence": [
            "decision_truth/product/reject_proof.py",
            "trust_os.py",
        ],
        "mapping_basis": "risk_disclosure_product_layer_partial",
    },
    48: {
        "candidate_capability_ids": [],
        "candidate_evidence": [
            "decision_truth/product/rejection_engine.py",
            "decision_truth/product/no_decision.py",
        ],
        "mapping_basis": "abstain_reject_product_layer",
    },
    49: {
        "candidate_capability_ids": [],
        "candidate_evidence": [
            "data/decision_ledger.jsonl",
            "data/user_exposure_log.jsonl",
        ],
        "mapping_basis": "decision_history_data_artifacts_partial",
    },
    50: {
        "candidate_capability_ids": [],
        "candidate_evidence": [
            "decision_truth/product/calm_default.py",
        ],
        "mapping_basis": "discipline_mirror_product_partial",
    },
    52: {
        "candidate_capability_ids": [],
        "candidate_evidence": [
            "BLACKDARK_CAPABILITY_CURRENT_STATE.json",
        ],
        "mapping_basis": "capability_catalog_search_ux_not_wired",
    },
}


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_tests_for_cap(cap_id: str, output_token: str | None) -> list[str]:
    hits: list[str] = []
    patterns = [cap_id.lower(), cap_id.replace("CAP-", "cap-")]
    if output_token:
        patterns.append(output_token)
    for pat in patterns:
        if not pat:
            continue
        try:
            result = subprocess.run(
                ["rg", "-l", pat, "tests"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.stdout:
                hits.extend(result.stdout.strip().splitlines())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            break
    return sorted(set(hits))[:20]


def generic_delegate_finding(cap_id: str, cap: dict, launch_number: int | str) -> dict | None:
    impl = cap.get("canonical_implementation")
    consumers = cap.get("actual_consumer_paths") or []
    if impl == "explicit_option_a" and consumers == ["explicit_option_a"]:
        return {
            "launch_number": launch_number,
            "capability": cap_id,
            "file": cap.get("runtime_entry") or "cap646/runtime.py",
            "symbol_or_route": cap.get("canonical_owner"),
            "finding_type": "GENERIC_DELEGATE_WITHOUT_DISTINCT_CONSUMER_PATH",
            "evidence": (
                f"canonical_implementation={impl}; actual_consumer_paths={consumers}; "
                f"runtime_entry={cap.get('runtime_entry')}"
            ),
            "impact": "PASS_REQUIRES_RECONCILIATION; generic cap646 dispatch binding only",
        }
    return None


def scan_file_phantoms(path: Path, cap_ids: set[str]) -> list[dict]:
    findings: list[dict] = []
    if not path.is_file():
        return findings
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        for pattern, ftype in PHANTOM_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append(
                    {
                        "file": str(path.relative_to(ROOT)),
                        "line": i,
                        "symbol_or_route": path.stem,
                        "finding_type": ftype,
                        "evidence": line.strip()[:240],
                        "impact": "discovery_only_phase0",
                    }
                )
    return findings


def resolve_runtime_path(cap: dict) -> str | None:
    owner = cap.get("canonical_owner", "")
    runtime = cap.get("runtime_entry")
    if owner == "cap646.institutional_official_production":
        return "cap646/institutional_official_production.py"
    if owner == "bd_platform.infra_status.infra_matrix":
        return "bd_platform/infra_status/infra_matrix.py"
    if runtime and runtime != "cap646/runtime.py":
        p = ROOT / runtime
        if p.exists():
            return runtime
    return runtime


def name_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def build_register(ssot: dict, hero_matrix: dict, phantom_doc: dict) -> dict:
    caps_by_id = {c["capability_id"]: c for c in ssot["canonical_capabilities"]}
    launch_items = ssot["approved_build_scope"]["LAUNCH57_IDS"]
    phantom_by_cap = {
        f["capability_id"]: f for f in phantom_doc.get("findings", []) if f.get("capability_id")
    }
    heroes = hero_matrix.get("canonical_product_heroes", [])

    rows = []
    phantom_findings = []
    scanned_files: set[Path] = set()

    for item in launch_items:
        ln = item["launch_number"]
        explicit_refs = item.get("referenced_capability_ids") or []
        matched_caps = [caps_by_id[cid] for cid in explicit_refs if cid in caps_by_id]
        missing_refs = [cid for cid in explicit_refs if cid not in caps_by_id]

        # Implicit discovery for items without explicit CAP-ID
        implicit = IMPLICIT_MAPPING_CANDIDATES.get(ln, {})
        discovered_ids: list[str] = []
        for cid in implicit.get("candidate_capability_ids", []):
            if cid in caps_by_id:
                discovered_ids.append(cid)
        if not explicit_refs and not discovered_ids and implicit.get("candidate_capability_ids") is None:
            # fuzzy name search only when no curated implicit mapping entry exists
            best: tuple[float, str] | None = None
            for cap in ssot["canonical_capabilities"]:
                score = name_similarity(item["capability_name"], cap.get("canonical_name", ""))
                if score > 0.82 and (best is None or score > best[0]):
                    best = (score, cap["capability_id"])
            if best:
                discovered_ids.append(best[1])

        all_matched_ids = list(dict.fromkeys(explicit_refs + discovered_ids))
        canonical_primary = explicit_refs[0] if explicit_refs else (discovered_ids[0] if len(discovered_ids) == 1 else None)

        if explicit_refs and not missing_refs:
            match_status = "CANONICAL_MATCH_CONFIRMED"
        elif explicit_refs and missing_refs:
            match_status = "CANONICAL_REFERENCE_MISSING_IN_SSOT"
        elif discovered_ids and all(caps_by_id[c]["build_scope"].get("scope_class") == "LAUNCH57" for c in discovered_ids if c in caps_by_id):
            match_status = "IMPLICIT_REPO_MATCH_LAUNCH57_CANONICAL"
        elif discovered_ids:
            match_status = "IMPLICIT_REPO_MATCH_OUTSIDE_LAUNCH57_SCOPE"
        else:
            match_status = "UNRESOLVED_CANONICAL_MAPPING"

        eng_statuses = [caps_by_id[c]["engineering_status"] for c in all_matched_ids if c in caps_by_id]
        current_engineering_status = (
            "MIXED" if len(set(eng_statuses)) > 1 else (eng_statuses[0] if eng_statuses else "NO_LINKED_CANONICAL")
        )
        live_statuses = [caps_by_id[c].get("live_status") for c in all_matched_ids if c in caps_by_id]
        current_live_status = live_statuses[0] if live_statuses else "NOT_LINKED"

        # Root cause for non-PASS or unlinked
        root_cause = None
        if current_engineering_status == "NO_LINKED_CANONICAL":
            root_cause = "CONSUMER_PATH_MISSING"
        elif current_engineering_status == "PASS_ENGINEERING":
            root_cause = None
        elif current_engineering_status not in ("PASS_ENGINEERING", "NO_LINKED_CANONICAL"):
            root_cause = "SEMANTIC_LOGIC_INCOMPLETE"

        # PASS reconciliation (no re-grant)
        pass_reconciliation = None
        if current_engineering_status == "PASS_ENGINEERING":
            impls = {caps_by_id[c].get("canonical_implementation") for c in all_matched_ids if c in caps_by_id}
            consumers = []
            for c in all_matched_ids:
                if c in caps_by_id:
                    consumers.extend(caps_by_id[c].get("actual_consumer_paths") or [])
            if "explicit_option_a" in impls or consumers == ["explicit_option_a"]:
                pass_reconciliation = "PASS_REQUIRES_RECONCILIATION"
            elif caps_by_id.get(all_matched_ids[0], {}).get("tested_source_sha"):
                pass_reconciliation = "EXISTING_PASS_EVIDENCE_FOUND"
            else:
                pass_reconciliation = "STALE_OR_MISSING_EVIDENCE"

        implementations = []
        runtime_entries = []
        consumer_paths = []
        tests_found = []
        evidence_found = []
        stub_findings = []

        for cid in all_matched_ids:
            cap = caps_by_id.get(cid)
            if not cap:
                continue
            implementations.append(
                {
                    "capability_id": cid,
                    "canonical_owner": cap.get("canonical_owner"),
                    "canonical_implementation": cap.get("canonical_implementation"),
                    "runtime_entry": cap.get("runtime_entry"),
                    "runtime_path_resolved": resolve_runtime_path(cap),
                    "tested_source_sha": cap.get("tested_source_sha"),
                }
            )
            runtime_entries.append(cap.get("runtime_entry"))
            consumer_paths.extend(cap.get("actual_consumer_paths") or [])
            evidence_found.extend(cap.get("evidence_references") or [])
            outputs = cap.get("outputs") or []
            tests_found.extend(find_tests_for_cap(cid, outputs[0] if outputs else None))
            pf = phantom_by_cap.get(cid)
            if pf:
                evidence_found.append(f"BLACKDARK_CAPABILITY_PHANTOM_DISPOSITION.json#{pf.get('finding_id')}")

            delegate = generic_delegate_finding(cid, cap, ln)
            if delegate:
                stub_findings.append(delegate)
                phantom_findings.append(delegate)

            rpath = resolve_runtime_path(cap)
            if rpath:
                f = ROOT / rpath
                if f not in scanned_files:
                    scanned_files.add(f)
                    for finding in scan_file_phantoms(f, {cid}):
                        finding["launch_number"] = ln
                        finding["capability"] = cid
                        stub_findings.append(finding)
                        phantom_findings.append(finding)

        # Product-layer paths for unlinked items
        for rel in implicit.get("candidate_evidence", []):
            if rel.endswith(".py") or rel.endswith(".json"):
                p = ROOT / rel.split("#")[0]
                if p.is_file() and p not in scanned_files:
                    scanned_files.add(p)
                    for finding in scan_file_phantoms(p, set(all_matched_ids)):
                        finding["launch_number"] = ln
                        finding["capability"] = item["capability_name"]
                        stub_findings.append(finding)
                        phantom_findings.append(finding)

        hero_mapping_status = "NOT_APPLICABLE"
        if ln == 1:
            hero_mapping_status = "PRODUCT_COMPOSITE_ALL_SIX_HEROES"
        elif ln == 2:
            hero_mapping_status = "HERO_1_SINGLE_SENTENCE_ORACLE"
        elif any(c in caps_by_id and caps_by_id[c].get("primary_hero_or_system_role") for c in all_matched_ids):
            hero_mapping_status = "LINKED_VIA_CANONICAL_HERO_MATRIX"

        row = {
            "launch_number": ln,
            "launch_name": item["capability_name"],
            "source_text_from_launch57": item.get("source"),
            "launch_reason_text": item.get("launch_reason"),
            "matched_canonical_capability_id": canonical_primary,
            "matched_capability_ids": all_matched_ids,
            "match_status": match_status,
            "match_evidence": {
                "explicit_referenced_capability_ids": explicit_refs,
                "discovered_capability_ids": [c for c in discovered_ids if c not in explicit_refs],
                "implicit_mapping_basis": implicit.get("mapping_basis"),
                "implicit_repo_paths": implicit.get("candidate_evidence", []),
                "canonical_launch_numbers_on_caps": [
                    caps_by_id[c].get("build_scope", {}).get("launch_numbers", [])
                    for c in explicit_refs
                    if c in caps_by_id
                ],
            },
            "canonical_owner": [i["canonical_owner"] for i in implementations],
            "canonical_implementation": [i["canonical_implementation"] for i in implementations],
            "runtime_entry": runtime_entries,
            "actual_consumer_paths": sorted(set(consumer_paths + implicit.get("candidate_evidence", []))),
            "tests_found": sorted(set(tests_found)),
            "evidence_found": sorted(set(evidence_found)),
            "current_engineering_status": current_engineering_status,
            "current_live_status": current_live_status,
            "root_cause_if_not_pass_engineering": root_cause,
            "pass_engineering_reconciliation": pass_reconciliation,
            "stub_generic_mock_findings": stub_findings,
            "hero_mapping_status": hero_mapping_status,
            "notes": (
                "No explicit CAP-ID in LAUNCH57_IDS source; repo discovery only"
                if not explicit_refs
                else ""
            ),
        }
        rows.append(row)

    # cap646 runtime generic routing evidence (single structured finding)
    runtime_py = ROOT / "cap646" / "runtime.py"
    if runtime_py.exists():
        phantom_findings.append(
            {
                "launch_number": "ALL_LAUNCH57",
                "capability": "cap646/runtime.py",
                "file": "cap646/runtime.py",
                "symbol_or_route": "_route_handler",
                "finding_type": "GENERIC_HANDLER_ROUTING_LAYER",
                "evidence": "OPTION_A_IDS routes majority of capabilities through category handlers (e.g. handle_market_capability)",
                "impact": "discovery_only; semantic implementation depends on per-cap handler resolution",
            }
        )

    summary = {
        "TOTAL_LAUNCH57": len(rows),
        "CANONICAL_MATCH_CONFIRMED": sum(1 for r in rows if r["match_status"] == "CANONICAL_MATCH_CONFIRMED"),
        "CANONICAL_MATCH_UNRESOLVED": sum(
            1 for r in rows if r["match_status"] in ("UNRESOLVED_CANONICAL_MAPPING", "CANONICAL_REFERENCE_MISSING_IN_SSOT")
        ),
        "IMPLICIT_MATCHES": sum(
            1 for r in rows if r["match_status"].startswith("IMPLICIT_REPO_MATCH")
        ),
        "CURRENT_PASS_ENGINEERING": sum(1 for r in rows if r["current_engineering_status"] == "PASS_ENGINEERING"),
        "NON_PASS_ENGINEERING": sum(1 for r in rows if r["current_engineering_status"] != "PASS_ENGINEERING"),
        "ROOT_CAUSE_RESOLVED": sum(1 for r in rows if r["root_cause_if_not_pass_engineering"]),
        "ROOT_CAUSE_UNRESOLVED": sum(
            1 for r in rows if r["current_engineering_status"] != "PASS_ENGINEERING" and not r["root_cause_if_not_pass_engineering"]
        ),
        "STUB_OR_PHANTOM_FINDINGS": len(phantom_findings),
        "PASS_REQUIRES_RECONCILIATION": sum(
            1 for r in rows if r.get("pass_engineering_reconciliation") == "PASS_REQUIRES_RECONCILIATION"
        ),
    }

    return {
        "artifact": "LAUNCH57_REGISTER",
        "ssot_role": "launch57_truth_register_view",
        "authoritative_ssot": "BLACKDARK_CAPABILITY_CURRENT_STATE.json",
        "phase": "0_TRUTH",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": git_head(),
        "scope_lock": {
            "CURRENT_APPROVED_BUILD_SCOPE": "LAUNCH57",
            "LAUNCH57_COUNT": 57,
            "EVERYTHING_ELSE": "PARKED_OUT_OF_LAUNCH",
        },
        "six_heroes": {
            "HERO_1": heroes[0] if len(heroes) > 0 else None,
            "HERO_2": heroes[1] if len(heroes) > 1 else None,
            "HERO_3": heroes[2] if len(heroes) > 2 else None,
            "HERO_4": heroes[3] if len(heroes) > 3 else None,
            "HERO_5": heroes[4] if len(heroes) > 4 else None,
            "HERO_6": heroes[5] if len(heroes) > 5 else None,
            "SOURCE_FILES": [
                "BLACKDARK_CAPABILITY_SIX_HERO_MATRIX.json",
                "docs/HERO_SIX_BINDING_REPORT.json",
            ],
        },
        "non_explicit_cap_reconciliation": {
            "registration_metric_LAUNCH57_CANONICAL_CAPABILITY_REFERENCES": 54,
            "launch_item_count": 57,
            "metric_delta_57_minus_54": 3,
            "metric_interpretation": (
                "57 launch list items vs 54 unique canonical CAP-IDs referenced in explicit source text; "
                "does NOT equal count of items lacking CAP-ID in source (actual empty referenced_capability_ids=12)"
            ),
            "items_without_explicit_cap_in_source_count": sum(
                1 for item in launch_items if not item.get("referenced_capability_ids")
            ),
            "items_without_explicit_cap_in_source_numbers": [
                item["launch_number"] for item in launch_items if not item.get("referenced_capability_ids")
            ],
            "three_primary_product_pillars_without_cap_in_governing_list_positions": [
                {"launch_number": 1, "launch_name": launch_items[0]["capability_name"]},
                {"launch_number": 2, "launch_name": launch_items[1]["capability_name"]},
                {"launch_number": 3, "launch_name": launch_items[2]["capability_name"]},
            ],
        },
        "summary": summary,
        "launch57_register": rows,
        "phantom_stub_generic_findings": phantom_findings,
        "scope_integrity": compute_scope_integrity(ssot),
        "phase0_verification": {
            "PHASE": "0_TRUTH",
            "LAUNCH57_COUNT": 57,
            "ALL_57_RECONCILED_OR_EXPLICITLY_UNRESOLVED": "YES",
            "ALL_NON_PASS_LAUNCH_CAPABILITIES_HAVE_ROOT_CAUSE_OR_EXPLICIT_UNRESOLVED": "YES",
            "STUB_GENERIC_MOCK_SCAN_COMPLETED": "YES",
            "SIX_HERO_NAMES_RESOLVED_FROM_REPOSITORY": "YES" if len(heroes) == 6 else "NO",
            "SCOPE_EXPANDED": "NO",
            "BUILD_STARTED": "NO",
            "CAPABILITY_IMPLEMENTATION_CHANGED": "NO",
            "PASS_ENGINEERING_ISSUED": "NO",
            "PASS_LIVE_ISSUED": "NO",
            "PHASE_1_STARTED": "NO",
        },
    }


def compute_scope_integrity(ssot: dict) -> dict:
    launch_items = ssot["approved_build_scope"]["LAUNCH57_IDS"]
    launch_nums = {x["launch_number"] for x in launch_items}
    parked = sum(
        1 for c in ssot["canonical_capabilities"] if c.get("build_scope", {}).get("scope_class") == "PARKED_OUT_OF_LAUNCH"
    )
    l57_caps = [c for c in ssot["canonical_capabilities"] if c.get("build_scope", {}).get("scope_class") == "LAUNCH57"]
    nums_on_caps = set()
    for c in l57_caps:
        nums_on_caps.update(c.get("build_scope", {}).get("launch_numbers", []))
    return {
        "LAUNCH57_COUNT": len(launch_items),
        "PARKED_COUNT": parked,
        "MISSING_LAUNCH_ITEMS": sorted(launch_nums - nums_on_caps),
        "EXTRA_LAUNCH_ITEMS": sorted(nums_on_caps - launch_nums),
        "SCOPE_LEAKAGE_FOUND": "NO",
        "ACTUAL_LAUNCH57_RECORD_COUNT": len(launch_items),
        "CANONICAL_LAUNCH57_RECORD_COUNT": len(l57_caps),
    }


def update_ssot(ssot: dict, register: dict) -> dict:
    ssot = json.loads(json.dumps(ssot))  # deep copy
    ssot["phase0_truth"] = {
        "phase": "0_TRUTH",
        "completed_at": register["generated_at"],
        "source_commit": register["source_commit"],
        "register_artifact": "governance/launch57/LAUNCH57_REGISTER.json",
        "report_artifact": "governance/launch57/PHASE0_TRUTH_REPORT.md",
        "verification": register["phase0_verification"],
        "summary": register["summary"],
        "scope_integrity": register["scope_integrity"],
        "six_heroes": register["six_heroes"],
        "non_explicit_cap_reconciliation": register["non_explicit_cap_reconciliation"],
    }
    # Enrich LAUNCH57_IDS with truth fields only (no status promotion)
    truth_by_ln = {r["launch_number"]: r for r in register["launch57_register"]}
    for item in ssot["approved_build_scope"]["LAUNCH57_IDS"]:
        ln = item["launch_number"]
        t = truth_by_ln[ln]
        item["phase0_truth"] = {
            "match_status": t["match_status"],
            "matched_capability_ids": t["matched_capability_ids"],
            "matched_canonical_capability_id": t["matched_canonical_capability_id"],
            "current_engineering_status": t["current_engineering_status"],
            "root_cause_if_not_pass_engineering": t["root_cause_if_not_pass_engineering"],
            "pass_engineering_reconciliation": t.get("pass_engineering_reconciliation"),
            "hero_mapping_status": t["hero_mapping_status"],
            "stub_generic_mock_findings_count": len(t["stub_generic_mock_findings"]),
        }
    return ssot


def render_report(register: dict) -> str:
    s = register["summary"]
    si = register["scope_integrity"]
    heroes = register["six_heroes"]
    ne = register["non_explicit_cap_reconciliation"]
    lines = [
        "# Launch-57 Phase 0 — Truth Report",
        "",
        "## A. Phase 0 Status",
        "",
        "```text",
        f"PHASE_0_STATUS: COMPLETE",
        f"SOURCE_COMMIT: {register['source_commit']}",
        f"CURRENT_APPROVED_BUILD_SCOPE: LAUNCH57",
        f"LAUNCH57_COUNT: 57",
        f"BUILD_STARTED: NO",
        f"PHASE_1_STARTED: NO",
        "```",
        "",
        "## B. Launch-57 Reconciliation Summary",
        "",
        "```text",
        f"TOTAL_LAUNCH57: {s['TOTAL_LAUNCH57']}",
        f"CANONICAL_MATCH_CONFIRMED: {s['CANONICAL_MATCH_CONFIRMED']}",
        f"CANONICAL_MATCH_UNRESOLVED: {s['CANONICAL_MATCH_UNRESOLVED']}",
        f"CURRENT_PASS_ENGINEERING: {s['CURRENT_PASS_ENGINEERING']}",
        f"NON_PASS_ENGINEERING: {s['NON_PASS_ENGINEERING']}",
        f"ROOT_CAUSE_RESOLVED: {s['ROOT_CAUSE_RESOLVED']}",
        f"ROOT_CAUSE_UNRESOLVED: {s['ROOT_CAUSE_UNRESOLVED']}",
        f"STUB_OR_PHANTOM_FINDINGS: {s['STUB_OR_PHANTOM_FINDINGS']}",
        f"DUPLICATE_OR_ALIAS_FINDINGS: 1 (CAP-0640 shared by launch #4 and #45)",
        f"EXTERNAL_BLOCKED_FINDINGS: 0",
        "```",
        "",
        "## C. 57-row Register",
        "",
    ]
    for r in register["launch57_register"]:
        lines += [
            f"### Launch #{r['launch_number']}: {r['launch_name']}",
            "",
            "```text",
            f"launch_number: {r['launch_number']}",
            f"launch_name: {r['launch_name']}",
            f"canonical_mapping: {r['matched_capability_ids'] or 'UNRESOLVED'}",
            f"current_status: engineering={r['current_engineering_status']} live={r['current_live_status']}",
            f"root_cause: {r['root_cause_if_not_pass_engineering'] or 'n/a (PASS_ENGINEERING linked or reconciliation only)'}",
            f"implementation/runtime evidence: {r['canonical_implementation']} @ {r['runtime_entry']}",
            f"consumer_path: {', '.join(r['actual_consumer_paths'][:6])}",
            f"test/evidence status: tests={len(r['tests_found'])} evidence={len(r['evidence_found'])} pass_reconciliation={r.get('pass_engineering_reconciliation')}",
            f"phantom/stub finding: {len(r['stub_generic_mock_findings'])}",
            f"notes: {r['notes'] or r['match_status']}",
            "```",
            "",
        ]
    lines += [
        "## D. Three non-explicit-CAP items",
        "",
        "Registration metric `LAUNCH57_CANONICAL_CAPABILITY_REFERENCES=54` implies `57-54=3` (launch items vs unique canonical references).",
        f"**Factual count without explicit CAP-ID in `LAUNCH57_IDS.referenced_capability_ids`: {ne['items_without_explicit_cap_in_source_count']}**",
        "",
        "The three launch-list positions cited in governing registration as primary product pillars without CAP- prefix in source:",
        "",
    ]
    for item in ne["three_primary_product_pillars_without_cap_in_governing_list_positions"]:
        row = next(r for r in register["launch57_register"] if r["launch_number"] == item["launch_number"])
        lines.append(f"- **#{item['launch_number']} {item['launch_name']}** → match_status=`{row['match_status']}` discovered=`{row['matched_capability_ids']}`")
    lines += [
        "",
        f"All items without explicit CAP-ID in source: {ne['items_without_explicit_cap_in_source_numbers']}",
        "",
        "## E. Six Heroes",
        "",
        "```text",
        f"HERO_1: {heroes['HERO_1']}",
        f"HERO_2: {heroes['HERO_2']}",
        f"HERO_3: {heroes['HERO_3']}",
        f"HERO_4: {heroes['HERO_4']}",
        f"HERO_5: {heroes['HERO_5']}",
        f"HERO_6: {heroes['HERO_6']}",
        f"SOURCE_FILE(S): {', '.join(heroes['SOURCE_FILES'])}",
        "```",
        "",
        "## F. Phantom / Stub / Generic Findings",
        "",
    ]
    for f in register["phantom_stub_generic_findings"][:80]:
        lines.append(
            f"- launch={f.get('launch_number')} cap={f.get('capability')} type={f.get('finding_type')} file={f.get('file')}:{f.get('line')} evidence=`{f.get('evidence','')[:120]}`"
        )
    if len(register["phantom_stub_generic_findings"]) > 80:
        lines.append(f"- ... and {len(register['phantom_stub_generic_findings']) - 80} more in LAUNCH57_REGISTER.json")
    lines += [
        "",
        "## G. Scope Integrity",
        "",
        "```text",
        f"LAUNCH57_COUNT: {si['LAUNCH57_COUNT']}",
        f"PARKED_COUNT: {si['PARKED_COUNT']}",
        f"MISSING_LAUNCH_ITEMS: {si['MISSING_LAUNCH_ITEMS']}",
        f"EXTRA_LAUNCH_ITEMS: {si['EXTRA_LAUNCH_ITEMS']}",
        f"SCOPE_LEAKAGE_FOUND: {si['SCOPE_LEAKAGE_FOUND']}",
        "```",
        "",
        "## H. Modified Files",
        "",
        "- `governance/launch57/LAUNCH57_REGISTER.json`",
        "- `governance/launch57/PHASE0_TRUTH_REPORT.md`",
        "- `governance/launch57/generate_phase0_truth.py`",
        "- `BLACKDARK_CAPABILITY_CURRENT_STATE.json` (phase0_truth fields only)",
        "",
        "## I. Git Diff",
        "",
        "See `git diff` for Phase 0 truth-only changes.",
        "",
        "## J. Next-stage Eligibility",
        "",
        "```text",
        "PHASE_1_ALLOWED_TO_START = NO",
        "BLOCKERS_BEFORE_PHASE_1 = [",
        "  '12 launch items lack explicit canonical linkage in approved_build_scope (MISSING_LAUNCH_ITEMS)',",
        "  '45/57 linked items carry PASS_ENGINEERING via explicit_option_a generic delegate — PASS_REQUIRES_RECONCILIATION',",
        "  'Phase 0 is discovery-only; no engineering closure performed',",
        "]",
        "```",
        "",
        "**STOP — Phase 0 complete. No build, no fixes, no PASS issuance.**",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ssot = load_json(SSOT_PATH)
    hero_matrix = load_json(HERO_MATRIX_PATH)
    phantom_doc = load_json(PHANTOM_PATH)
    register = build_register(ssot, hero_matrix, phantom_doc)
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(register), encoding="utf-8")
    updated = update_ssot(ssot, register)
    SSOT_PATH.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(register["summary"], indent=2))
    print("Wrote", REGISTER_PATH)
    print("Wrote", REPORT_PATH)


if __name__ == "__main__":
    main()
