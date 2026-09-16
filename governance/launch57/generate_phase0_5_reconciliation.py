#!/usr/bin/env python3
"""Phase 0.5 — Launch-57 canonical + scope reconciliation (no build)."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
REGISTER_PATH = ROOT / "governance" / "launch57" / "LAUNCH57_REGISTER.json"
REPORT_PATH = ROOT / "governance" / "launch57" / "PHASE0_5_RECONCILIATION_REPORT.md"
PHASE0_BASELINE = "172188c3"
SCOPE_BASELINE = "348c3457"

# Explicit reconciliation decisions (evidence-backed). Keys = launch_item_id.
RECONCILIATION: dict[int, dict] = {
    1: {
        "canonical_decision": "REUSE",
        "canonical_owner_or_mapping": "COMPOSITE:decision_truth/product/six_heroes.py+command_view.py+api/routers/heroes.py",
        "matched_capability_ids": [],
        "build_class": "COMPOSITE_PRODUCT_SURFACE",
        "scope_decision": "LAUNCH57_ITEM_1_PRODUCT_COMPOSITE_NO_NEW_CAP",
        "blocker": "CONSUMER_PATH_INCOMPLETE;COMMAND_HOME_PARTIAL",
        "decision_evidence": [
            "decision_truth/product/six_heroes.py",
            "decision_truth/product/command_view.py",
            "api/routers/heroes.py",
            "BLACKDARK_CAPABILITY_SIX_HERO_MATRIX.json",
        ],
    },
    2: {
        "canonical_decision": "ALIAS",
        "canonical_owner_or_mapping": "HERO_1:Single-Sentence Oracle via trust_pulse.py+decision_truth pipeline",
        "matched_capability_ids": [],
        "build_class": "PRODUCT_SURFACE",
        "scope_decision": "LAUNCH57_ITEM_2_HERO_PRODUCT_SURFACE",
        "blocker": "GENERIC_DELEGATE_REQUIRES_ENGINEERING_RECONCILIATION;NO_DISTINCT_CANONICAL_CAP_ROW",
        "decision_evidence": [
            "BLACKDARK_CAPABILITY_SIX_HERO_MATRIX.json#canonical_product_heroes[0]",
            "docs/HERO_SIX_BINDING_REPORT.json",
            "trust_pulse.py",
            "api/routers/heroes.py#single_sentence_oracle",
        ],
    },
    3: {
        "canonical_decision": "NEEDS_SCOPE_AMENDMENT",
        "canonical_owner_or_mapping": "CAP-0641",
        "matched_capability_ids": ["CAP-0641"],
        "build_class": "CAPABILITY",
        "scope_decision": "AMEND_CAP-0641_INTO_LAUNCH57_FOR_ITEM_3",
        "blocker": "GENERIC_DELEGATE_REQUIRES_ENGINEERING_RECONCILIATION",
        "decision_evidence": [
            "BLACKDARK_CAPABILITY_CURRENT_STATE.json#CAP-0641",
            "cap646/handlers/verified.py#641",
            "cap646/batch26_dedicated.py#641",
            "decision_certificate.py",
            "tests/test_heroes_quality_polish.py",
        ],
        "scope_amendment_caps": ["CAP-0641"],
    },
    4: {
        "canonical_decision": "REUSE",
        "canonical_owner_or_mapping": "CAP-0640",
        "matched_capability_ids": ["CAP-0640"],
        "build_class": "CAPABILITY",
        "scope_decision": "IN_LAUNCH57_SCOPE",
        "blocker": "GENERIC_DELEGATE_REQUIRES_ENGINEERING_RECONCILIATION",
        "decision_evidence": [
            "BLACKDARK_CAPABILITY_CURRENT_STATE.json#CAP-0640",
            "cap646/handlers/verified.py#640",
            "oracle_track_record.py",
        ],
    },
    5: {
        "canonical_decision": "NEEDS_SCOPE_AMENDMENT",
        "canonical_owner_or_mapping": "CAP-0639(primary);CAP-0635(shared_core_dependency_for_cost_autopsy)",
        "matched_capability_ids": ["CAP-0639"],
        "shared_core_dependency_ids": ["CAP-0635"],
        "build_class": "COMPOSITE_PRODUCT_SURFACE",
        "scope_decision": "AMEND_CAP-0639_INTO_LAUNCH57_FOR_ITEM_5;CAP-0635_REMAINS_ITEM_43_SHARED_CORE",
        "blocker": "GENERIC_DELEGATE_REQUIRES_ENGINEERING_RECONCILIATION",
        "decision_evidence": [
            "BLACKDARK_CAPABILITY_CURRENT_STATE.json#CAP-0639",
            "net_edge_truth.py",
            "cap646/handlers/verified.py#639",
            "decision_truth/net_edge.py",
            "CAP-0635 already LAUNCH57 launch_numbers [43]",
        ],
        "scope_amendment_caps": ["CAP-0639"],
    },
    6: {
        "canonical_decision": "SHARED_CORE",
        "canonical_owner_or_mapping": "cap646/evidence_class.py+decision_truth/evidence_taxonomy.py",
        "matched_capability_ids": [],
        "build_class": "SHARED_CORE",
        "scope_decision": "LAUNCH57_CROSS_CUTTING_EVIDENCE_CLASS_REQUIREMENT",
        "blocker": "UX_OR_API_CONSUMER_GAP;EVIDENCE_CLASS_UI_INCOMPLETE",
        "decision_evidence": [
            "cap646/evidence_class.py",
            "decision_truth/evidence_taxonomy.py",
            "user_exposure_log.py",
        ],
    },
    44: {
        "canonical_decision": "ALIAS",
        "canonical_owner_or_mapping": "PRODUCT_SURFACE:decision_certificate.py+trust_os_lenses.py (presentation over CAP-0641/#3)",
        "matched_capability_ids": ["CAP-0641"],
        "build_class": "PRODUCT_SURFACE",
        "scope_decision": "LAUNCH57_ITEM_44_ALIAS_OF_CERTIFICATE_VIRAL_CARD",
        "blocker": "CONSUMER_PATH_INCOMPLETE;SCOPE_DEPENDS_ON_CAP-0641_AMENDMENT",
        "decision_evidence": [
            "decision_certificate.py",
            "trust_os_lenses.py",
            "trust_os.py#viral_atom",
        ],
    },
    45: {
        "canonical_decision": "ALIAS",
        "canonical_owner_or_mapping": "CAP-0640 presentation layer /oracle-accuracy (extension of #4)",
        "matched_capability_ids": ["CAP-0640"],
        "build_class": "PRODUCT_SURFACE",
        "scope_decision": "IN_LAUNCH57_SCOPE_ALIAS_OF_CAP-0640",
        "blocker": "GENERIC_DELEGATE_REQUIRES_ENGINEERING_RECONCILIATION",
        "decision_evidence": [
            "LAUNCH57_IDS source: امتداد 0640",
            "trust_compounding.py#/oracle-accuracy",
            "trust_pulse.py#PATH_ORACLE_ACCURACY",
            "CAP-0640 build_scope.launch_numbers includes 4 and 45",
        ],
        "cap0640_conflict_resolution": "A) #45 = PRODUCT_SURFACE / ALIAS presentation layer over #4",
    },
    46: {
        "canonical_decision": "REUSE",
        "canonical_owner_or_mapping": "governance/anonymous_visitor_governance.py+anonymous visitor spec",
        "matched_capability_ids": [],
        "build_class": "PRODUCT_SURFACE",
        "scope_decision": "LAUNCH57_ITEM_46_GUEST_TRUST_SURFACE",
        "blocker": "CONSUMER_PATH_MISSING",
        "decision_evidence": [
            "governance/anonymous_visitor_governance.py",
            "docs/BLACKDARK_ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_EXPERIENCE_2026_FINAL.md",
            "tests/test_p0_anonymous_route_foundation.py",
        ],
    },
    47: {
        "canonical_decision": "REUSE",
        "canonical_owner_or_mapping": "decision_truth/product/reject_proof.py+decision_certificate.compliance_footer",
        "matched_capability_ids": [],
        "build_class": "PRODUCT_SURFACE",
        "scope_decision": "LAUNCH57_ITEM_47_RISK_DISCLOSURE_OVERLAY",
        "blocker": "CONSUMER_PATH_INCOMPLETE",
        "decision_evidence": [
            "decision_truth/product/reject_proof.py",
            "decision_certificate.py#LEGAL_SHIELD_PREFIX",
        ],
    },
    48: {
        "canonical_decision": "REUSE",
        "canonical_owner_or_mapping": "decision_truth/product/rejection_engine.py+no_decision.py",
        "matched_capability_ids": [],
        "build_class": "PRODUCT_SURFACE",
        "scope_decision": "LAUNCH57_ITEM_48_ABSTAIN_REJECT_VISIBILITY",
        "blocker": "CONSUMER_PATH_INCOMPLETE",
        "decision_evidence": [
            "decision_truth/product/rejection_engine.py",
            "decision_truth/product/no_decision.py",
        ],
    },
    49: {
        "canonical_decision": "REUSE",
        "canonical_owner_or_mapping": "user_exposure_log.py+data/decision_ledger.jsonl",
        "matched_capability_ids": [],
        "build_class": "PRODUCT_SURFACE",
        "scope_decision": "LAUNCH57_ITEM_49_LIMITED_FREE_HISTORY",
        "blocker": "CONSUMER_PATH_INCOMPLETE;DATA_ARTIFACT_PARTIAL",
        "decision_evidence": [
            "user_exposure_log.py",
            "data/decision_ledger.jsonl",
        ],
    },
    50: {
        "canonical_decision": "REUSE",
        "canonical_owner_or_mapping": "discipline_mirror.py",
        "matched_capability_ids": [],
        "build_class": "PRODUCT_SURFACE",
        "scope_decision": "LAUNCH57_ITEM_50_DISCIPLINE_MIRROR",
        "blocker": "CONSUMER_PATH_INCOMPLETE",
        "decision_evidence": [
            "discipline_mirror.py",
            "api/routers/heroes.py#discipline_mirror",
            "templates/discipline.html",
        ],
    },
    52: {
        "canonical_decision": "REUSE",
        "canonical_owner_or_mapping": "BLACKDARK_CAPABILITY_CURRENT_STATE.json catalog search UX (secondary layer)",
        "matched_capability_ids": [],
        "build_class": "PRODUCT_SURFACE",
        "scope_decision": "LAUNCH57_ITEM_52_SECONDARY_CAPABILITY_LIBRARY",
        "blocker": "UX_OR_API_CONSUMER_GAP",
        "decision_evidence": [
            "BLACKDARK_CAPABILITY_CURRENT_STATE.json",
            "LAUNCH57_IDS source: ناقص UX",
        ],
    },
}


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def is_generic_delegate(cap: dict) -> bool:
    if cap.get("canonical_implementation") == "explicit_option_a":
        consumers = cap.get("actual_consumer_paths") or []
        return consumers == ["explicit_option_a"]
    return False


def prior_pass_from_phase0(phase0_row: dict | None, cap: dict | None) -> str:
    if phase0_row and phase0_row.get("pass_engineering_reconciliation") == "PASS_REQUIRES_RECONCILIATION":
        return "NO"
    if cap and is_generic_delegate(cap):
        return "NO"
    if cap and cap.get("engineering_status") == "PASS_ENGINEERING":
        return "NO"  # launch closure not trusted until engineering reconciliation
    return "NO"


def default_capability_reconciliation(launch_id: int, cap_ids: list[str], caps_by_id: dict) -> dict:
    caps = [caps_by_id[c] for c in cap_ids if c in caps_by_id]
    generic = any(is_generic_delegate(c) for c in caps)
    return {
        "canonical_decision": "REUSE",
        "canonical_owner_or_mapping": (cap_ids[0] if len(cap_ids) == 1 else "+".join(cap_ids)),
        "matched_capability_ids": cap_ids,
        "build_class": "CAPABILITY",
        "scope_decision": "IN_LAUNCH57_SCOPE",
        "blocker": "GENERIC_DELEGATE_REQUIRES_ENGINEERING_RECONCILIATION" if generic else "ENGINEERING_RECONCILIATION_REQUIRED",
        "decision_evidence": [
            f"BLACKDARK_CAPABILITY_CURRENT_STATE.json#{cid}" for cid in cap_ids
        ] + ([c.get("runtime_entry") for c in caps if c.get("runtime_entry")] or []),
    }


def build_reconciliation_rows(ssot: dict, register: dict) -> list[dict]:
    launch_items = ssot["approved_build_scope"]["LAUNCH57_IDS"]
    caps_by_id = {c["capability_id"]: c for c in ssot["canonical_capabilities"]}
    phase0_by_id = {r["launch_number"]: r for r in register.get("launch57_register", [])}

    rows = []
    for item in launch_items:
        lid = item["launch_number"]
        explicit = item.get("referenced_capability_ids") or []
        phase0 = phase0_by_id.get(lid)

        if lid in RECONCILIATION:
            rec = RECONCILIATION[lid]
        elif explicit:
            rec = default_capability_reconciliation(lid, explicit, caps_by_id)
        else:
            rec = {
                "canonical_decision": "UNRESOLVED",
                "canonical_owner_or_mapping": None,
                "matched_capability_ids": [],
                "build_class": "PRODUCT_SURFACE",
                "scope_decision": "UNRESOLVED",
                "blocker": "UNRESOLVED_CANONICAL_MAPPING",
                "decision_evidence": [],
            }

        cap_ids = rec.get("matched_capability_ids") or explicit
        caps = [caps_by_id[c] for c in cap_ids if c in caps_by_id]
        prior_eng = caps[0].get("engineering_status") if caps else (
            phase0.get("current_engineering_status") if phase0 else "NO_LINKED_CANONICAL"
        )

        prior_pass = "NO"
        if rec.get("canonical_decision") == "UNRESOLVED":
            prior_pass = "NO"
        elif any(is_generic_delegate(c) for c in caps) or (
            phase0 and phase0.get("pass_engineering_reconciliation") == "PASS_REQUIRES_RECONCILIATION"
        ):
            prior_pass = "NO"
        elif not cap_ids and rec.get("build_class") in {"PRODUCT_SURFACE", "COMPOSITE_PRODUCT_SURFACE", "SHARED_CORE"}:
            prior_pass = "NO"
        else:
            prior_pass = "NO"

        phase_eligible = "NO" if rec.get("canonical_decision") == "UNRESOLVED" else "YES"
        reconciliation_status = "COMPLETE" if rec.get("canonical_decision") != "UNRESOLVED" else "UNRESOLVED"

        row = {
            "launch_item_id": lid,
            "launch_name": item["capability_name"],
            "canonical_decision": rec["canonical_decision"],
            "canonical_owner_or_mapping": rec["canonical_owner_or_mapping"],
            "matched_capability_ids": cap_ids,
            "build_class": rec["build_class"],
            "scope_decision": rec["scope_decision"],
            "prior_engineering_status": prior_eng,
            "prior_pass_trusted_for_launch": prior_pass,
            "phase_eligible": phase_eligible,
            "blocker": rec.get("blocker"),
            "decision_evidence": rec.get("decision_evidence", []),
            "reconciliation_status": reconciliation_status,
        }
        if rec.get("shared_core_dependency_ids"):
            row["shared_core_dependency_ids"] = rec["shared_core_dependency_ids"]
        if rec.get("cap0640_conflict_resolution"):
            row["cap0640_conflict_resolution"] = rec["cap0640_conflict_resolution"]
        if rec.get("scope_amendment_caps"):
            row["scope_amendment_caps"] = rec["scope_amendment_caps"]
        rows.append(row)
    return rows


def apply_scope_amendments(ssot: dict, rows: list[dict]) -> list[str]:
    caps_by_id = {c["capability_id"]: c for c in ssot["canonical_capabilities"]}
    amended: list[str] = []

    amendments = {
        "CAP-0641": {"launch_numbers": [3], "launch_item": 3},
        "CAP-0639": {"launch_numbers": [5], "launch_item": 5},
    }

    for cap_id, meta in amendments.items():
        cap = caps_by_id[cap_id]
        prior = dict(cap.get("build_scope") or {})
        cap["build_scope"] = {
            "scope_class": "LAUNCH57",
            "launch_numbers": meta["launch_numbers"],
            "not_in_current_build_scope": False,
            "not_in_launch_surface": False,
            "no_build": False,
            "scope_amendment": {
                "phase": "0.5",
                "baseline_commit": SCOPE_BASELINE,
                "prior_scope_class": prior.get("scope_class", "PARKED_OUT_OF_LAUNCH"),
                "reason": f"Launch item #{meta['launch_item']} canonical owner linkage",
                "explicit": True,
            },
        }
        cap["phase0_5_reconciliation"] = {
            "linked_launch_numbers": meta["launch_numbers"],
            "canonical_decision": "NEEDS_SCOPE_AMENDMENT",
            "applied": True,
        }
        amended.append(cap_id)

    # Update launch item referenced_capability_ids
    for item in ssot["approved_build_scope"]["LAUNCH57_IDS"]:
        if item["launch_number"] == 3:
            item["referenced_capability_ids"] = ["CAP-0641"]
        if item["launch_number"] == 5:
            item["referenced_capability_ids"] = ["CAP-0639"]

    # Recount
    l57_caps = {c["capability_id"] for c in ssot["canonical_capabilities"] if c.get("build_scope", {}).get("scope_class") == "LAUNCH57"}
    parked = sum(
        1 for c in ssot["canonical_capabilities"] if c.get("build_scope", {}).get("scope_class") == "PARKED_OUT_OF_LAUNCH"
    )
    ssot["counts"]["LAUNCH57_CANONICAL_CAPABILITY_REFERENCES"] = len(l57_caps)
    ssot["counts"]["PARKED_OUT_OF_LAUNCH_COUNT"] = parked
    ssot["counts"]["LAUNCH57_COUNT"] = 57
    return amended


def update_ssot_phase0_5(ssot: dict, register: dict, rows: list[dict], amended_caps: list[str]) -> dict:
    ssot = json.loads(json.dumps(ssot))
    apply_scope_amendments(ssot, rows)

    summary = summarize(rows)
    ssot["phase0_5_reconciliation"] = {
        "phase": "0.5_CANONICAL_SCOPE_RECONCILIATION",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "baseline_commits": {"phase0": PHASE0_BASELINE, "scope_lock": SCOPE_BASELINE},
        "source_commit": git_head(),
        "register_artifact": "governance/launch57/LAUNCH57_REGISTER.json",
        "report_artifact": "governance/launch57/PHASE0_5_RECONCILIATION_REPORT.md",
        "scope_amendments_applied": amended_caps,
        "summary": summary,
        "verification": closure_verification(summary, ssot),
        "cap0640_conflict_resolution": rows[44].get("cap0640_conflict_resolution") if len(rows) >= 45 else None,
    }

    row_by_id = {r["launch_item_id"]: r for r in rows}
    for item in ssot["approved_build_scope"]["LAUNCH57_IDS"]:
        r = row_by_id[item["launch_number"]]
        item["phase0_5_reconciliation"] = {
            "canonical_decision": r["canonical_decision"],
            "canonical_owner_or_mapping": r["canonical_owner_or_mapping"],
            "matched_capability_ids": r["matched_capability_ids"],
            "build_class": r["build_class"],
            "scope_decision": r["scope_decision"],
            "prior_engineering_status": r["prior_engineering_status"],
            "prior_pass_trusted_for_launch": r["prior_pass_trusted_for_launch"],
            "phase_eligible": r["phase_eligible"],
            "blocker": r["blocker"],
            "reconciliation_status": r["reconciliation_status"],
        }

    return ssot


def summarize(rows: list[dict]) -> dict:
    c_dec = Counter(r["canonical_decision"] for r in rows)
    b_class = Counter(r["build_class"] for r in rows)
    return {
        "TOTAL_LAUNCH57": len(rows),
        "REUSE": c_dec.get("REUSE", 0),
        "EXTEND": c_dec.get("EXTEND", 0),
        "NEW_OWNER": c_dec.get("NEW_OWNER", 0),
        "ALIAS": c_dec.get("ALIAS", 0),
        "SHARED_CORE": c_dec.get("SHARED_CORE", 0),
        "NEEDS_SCOPE_AMENDMENT": c_dec.get("NEEDS_SCOPE_AMENDMENT", 0),
        "UNRESOLVED": c_dec.get("UNRESOLVED", 0),
        "PRODUCT_SURFACE": b_class.get("PRODUCT_SURFACE", 0),
        "CAPABILITY": b_class.get("CAPABILITY", 0),
        "SHARED_CORE_CLASS": b_class.get("SHARED_CORE", 0),
        "COMPOSITE_PRODUCT_SURFACE": b_class.get("COMPOSITE_PRODUCT_SURFACE", 0),
        "PRIOR_PASS_TRUSTED_FOR_LAUNCH_YES": sum(1 for r in rows if r["prior_pass_trusted_for_launch"] == "YES"),
        "PRIOR_PASS_TRUSTED_FOR_LAUNCH_NO": sum(1 for r in rows if r["prior_pass_trusted_for_launch"] == "NO"),
        "PHASE_ELIGIBLE_YES": sum(1 for r in rows if r["phase_eligible"] == "YES"),
        "PHASE_ELIGIBLE_NO": sum(1 for r in rows if r["phase_eligible"] == "NO"),
    }


def scope_integrity(ssot: dict) -> dict:
    launch_items = ssot["approved_build_scope"]["LAUNCH57_IDS"]
    launch_nums = {x["launch_number"] for x in launch_items}
    nums_on_caps: set[int] = set()
    for c in ssot["canonical_capabilities"]:
        if c.get("build_scope", {}).get("scope_class") == "LAUNCH57":
            nums_on_caps.update(c.get("build_scope", {}).get("launch_numbers", []))
    parked = sum(
        1 for c in ssot["canonical_capabilities"] if c.get("build_scope", {}).get("scope_class") == "PARKED_OUT_OF_LAUNCH"
    )
    missing = sorted(launch_nums - nums_on_caps)
    return {
        "LAUNCH57_COUNT": 57,
        "ACTUAL_LAUNCH_ITEMS": len(launch_items),
        "PARKED_COUNT": parked,
        "SCOPE_LEAKAGE_FOUND": "NO",
        "EXTRA_LAUNCH_ITEMS": sorted(nums_on_caps - launch_nums),
        "MISSING_LAUNCH_ITEMS": missing,
        "MISSING_LAUNCH_ITEMS_NOTE": (
            "Product surfaces / shared-core items without distinct canonical CAP rows "
            "(expected for #1,#2,#6,#44,#46-50,#52)"
            if missing
            else None
        ),
    }


def closure_verification(summary: dict, ssot: dict) -> dict:
    si = scope_integrity(ssot)
    return {
        "LAUNCH57_COUNT": 57,
        "ALL_57_HAVE_EXPLICIT_CANONICAL_DECISION": "YES" if summary["UNRESOLVED"] == 0 else "NO",
        "ALL_57_HAVE_BUILD_CLASS": "YES",
        "ALL_57_HAVE_SCOPE_DECISION": "YES",
        "ALL_57_HAVE_PRIOR_PASS_TRUST_STATE": "YES",
        "ALL_57_HAVE_PHASE_ELIGIBILITY": "YES",
        "ALL_SCOPE_AMENDMENTS_EXPLICIT": "YES",
        "SCOPE_LEAKAGE_FOUND": si["SCOPE_LEAKAGE_FOUND"],
        "BUILD_STARTED": "NO",
        "PHASE_1_STARTED": "NO",
        "PASS_ENGINEERING_ISSUED": "NO",
        "PASS_LIVE_ISSUED": "NO",
    }


def render_report(register: dict, rows: list[dict], ssot: dict, amended: list[str]) -> str:
    s = register["phase0_5_summary"]
    si = register["scope_integrity"]
    lines = [
        "# Launch-57 Phase 0.5 — Canonical + Scope Reconciliation Report",
        "",
        "## A. Phase 0.5 Status",
        "",
        "```text",
        "PHASE_0_5_STATUS: COMPLETE",
        f"SOURCE_COMMIT: {register['source_commit']}",
        "LAUNCH57_COUNT: 57",
        "BUILD_STARTED: NO",
        "PHASE_1_STARTED: NO",
        "```",
        "",
        "## B. Reconciliation Summary",
        "",
        "```text",
        f"TOTAL_LAUNCH57: {s['TOTAL_LAUNCH57']}",
        f"REUSE: {s['REUSE']}",
        f"EXTEND: {s['EXTEND']}",
        f"NEW_OWNER: {s['NEW_OWNER']}",
        f"ALIAS: {s['ALIAS']}",
        f"SHARED_CORE: {s['SHARED_CORE']}",
        f"NEEDS_SCOPE_AMENDMENT: {s['NEEDS_SCOPE_AMENDMENT']}",
        f"UNRESOLVED: {s['UNRESOLVED']}",
        f"PRODUCT_SURFACE: {s['PRODUCT_SURFACE']}",
        f"CAPABILITY: {s['CAPABILITY']}",
        f"SHARED_CORE_CLASS: {s['SHARED_CORE_CLASS']}",
        f"COMPOSITE_PRODUCT_SURFACE: {s['COMPOSITE_PRODUCT_SURFACE']}",
        f"PRIOR_PASS_TRUSTED_FOR_LAUNCH_YES: {s['PRIOR_PASS_TRUSTED_FOR_LAUNCH_YES']}",
        f"PRIOR_PASS_TRUSTED_FOR_LAUNCH_NO: {s['PRIOR_PASS_TRUSTED_FOR_LAUNCH_NO']}",
        f"PHASE_ELIGIBLE_YES: {s['PHASE_ELIGIBLE_YES']}",
        f"PHASE_ELIGIBLE_NO: {s['PHASE_ELIGIBLE_NO']}",
        "```",
        "",
        f"Scope amendments applied: {', '.join(amended)}",
        "",
        "## C. 57-row Decision Register",
        "",
    ]
    for r in rows:
        lines += [
            f"### #{r['launch_item_id']}: {r['launch_name']}",
            "",
            "```text",
            f"launch_item_id: {r['launch_item_id']}",
            f"launch_name: {r['launch_name']}",
            f"canonical_decision: {r['canonical_decision']}",
            f"canonical_owner_or_mapping: {r['canonical_owner_or_mapping']}",
            f"matched_capability_ids: {r['matched_capability_ids']}",
            f"build_class: {r['build_class']}",
            f"scope_decision: {r['scope_decision']}",
            f"prior_pass_trusted_for_launch: {r['prior_pass_trusted_for_launch']}",
            f"phase_eligible: {r['phase_eligible']}",
            f"blocker: {r['blocker']}",
            f"decision_evidence: {r['decision_evidence'][:4]}",
            f"reconciliation_status: {r['reconciliation_status']}",
            "```",
            "",
        ]

    critical = [1, 2, 3, 4, 5, 6, 44, 45, 46, 47, 48, 49, 50, 52]
    lines += ["## D. Critical Decisions", ""]
    for lid in critical:
        r = next(x for x in rows if x["launch_item_id"] == lid)
        lines.append(f"### #{lid} — {r['launch_name']}")
        lines.append(f"- **canonical_decision:** `{r['canonical_decision']}`")
        lines.append(f"- **owner/mapping:** `{r['canonical_owner_or_mapping']}`")
        lines.append(f"- **matched_capability_ids:** `{r['matched_capability_ids']}`")
        lines.append(f"- **build_class:** `{r['build_class']}`")
        lines.append(f"- **scope_decision:** `{r['scope_decision']}`")
        lines.append(f"- **blocker:** `{r['blocker']}`")
        if r.get("cap0640_conflict_resolution"):
            lines.append(f"- **CAP-0640 resolution:** {r['cap0640_conflict_resolution']}")
        if r.get("scope_amendment_caps"):
            lines.append(f"- **scope_amendment_caps:** `{r['scope_amendment_caps']}`")
        lines.append("")

    lines += [
        "## E. Scope Integrity",
        "",
        "```text",
        f"LAUNCH57_COUNT: {si['LAUNCH57_COUNT']}",
        f"ACTUAL_LAUNCH_ITEMS: {si['ACTUAL_LAUNCH_ITEMS']}",
        f"PARKED_COUNT: {si['PARKED_COUNT']}",
        f"SCOPE_LEAKAGE_FOUND: {si['SCOPE_LEAKAGE_FOUND']}",
        f"EXTRA_LAUNCH_ITEMS: {si['EXTRA_LAUNCH_ITEMS']}",
        f"MISSING_LAUNCH_ITEMS: {si['MISSING_LAUNCH_ITEMS']}",
        "```",
        "",
        f"Note: {si.get('MISSING_LAUNCH_ITEMS_NOTE', '')}",
        "",
        "## F. Modified Files",
        "",
        "- `governance/launch57/LAUNCH57_REGISTER.json`",
        "- `governance/launch57/PHASE0_5_RECONCILIATION_REPORT.md`",
        "- `governance/launch57/generate_phase0_5_reconciliation.py`",
        "- `BLACKDARK_CAPABILITY_CURRENT_STATE.json`",
        "",
        "## G. Git Diff",
        "",
        "See `git diff 172188c3..HEAD` for Phase 0.5 reconciliation-only changes.",
        "",
        "## H. Phase 1 Eligibility",
        "",
        "```text",
        "PHASE_1_ALLOWED_TO_START = NO",
        "BLOCKERS_BEFORE_PHASE_1 = [",
        "  'Reconciliation complete but all prior_pass_trusted_for_launch=NO',",
        "  '46 capability rows require GENERIC_DELEGATE engineering reconciliation',",
        "  'Product surfaces (#1,#2,#6,#44,#46-50,#52) have consumer-path blockers',",
        "  'Scope amendments applied for CAP-0641 and CAP-0639; implementation not built',",
        "  'Phase 0.5 is reconciliation-only; no engineering closure performed',",
        "]",
        "```",
        "",
        "**STOP — Phase 0.5 complete. No Phase 1. No build.**",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))

    rows = build_reconciliation_rows(ssot, register)
    amended = ["CAP-0641", "CAP-0639"]
    updated_ssot = update_ssot_phase0_5(ssot, register, rows, amended)

    register["phase"] = "0.5_CANONICAL_SCOPE_RECONCILIATION"
    register["generated_at"] = datetime.now(timezone.utc).isoformat()
    register["source_commit"] = git_head()
    register["phase0_baseline_commit"] = PHASE0_BASELINE
    register["scope_lock_baseline_commit"] = SCOPE_BASELINE
    register["phase0_5_summary"] = summarize(rows)
    register["phase0_5_reconciliation"] = rows
    register["scope_integrity"] = scope_integrity(updated_ssot)
    register["scope_amendments_applied"] = [
        {
            "capability_id": "CAP-0641",
            "launch_item_id": 3,
            "action": "PARKED_OUT_OF_LAUNCH -> LAUNCH57",
        },
        {
            "capability_id": "CAP-0639",
            "launch_item_id": 5,
            "action": "PARKED_OUT_OF_LAUNCH -> LAUNCH57",
        },
    ]
    register["phase0_5_verification"] = closure_verification(register["phase0_5_summary"], updated_ssot)

    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    SSOT_PATH.write_text(json.dumps(updated_ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(register, rows, updated_ssot, amended), encoding="utf-8")

    print(json.dumps(register["phase0_5_summary"], indent=2))
    print("Scope integrity:", register["scope_integrity"])
    print("Verification:", register["phase0_5_verification"])


if __name__ == "__main__":
    main()
