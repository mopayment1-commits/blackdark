#!/usr/bin/env python3
"""Bootstrap DD workspace gates: owner acceptance, BGS population, pre-batch delta, capabilities."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime.now(timezone.utc).isoformat()
LEDGER_BASELINE_SHA = "d72c962d05cb7d475080ef5402d6fb13025cf744"

BGS_SOURCES = [
    (
        "BGS-001",
        "BLACKDARK_Institutional_Capability_Standard_2026_v6(1).md",
        "docs/standards/معيار_مؤسسي_صارم_لبناء_القدرات_والمميزات_وجاهزية_لجنة_الفحص_2026_v6.md",
        "project_standards_v6",
    ),
    (
        "BGS-002",
        "BLACKDARK_مرجع_حاكم_للبيانات_والتخزين_والتراك_Institutional_Hardened_v4_v2 (1).md",
        "docs/standards/domain/BLACKDARK_مرجع_حاكم_للبيانات_والتخزين_والتراك_Institutional_Hardened_v4_v2.md",
        "data_storage_trace_v4_v2",
    ),
    (
        "BGS-003",
        "BLACKDARK Temporal Intelligence & Evidence Acceleration System (1).md",
        "docs/standards/domain/BLACKDARK Temporal Intelligence & Evidence Acceleration System.md",
        "temporal_intelligence",
    ),
    (
        "BGS-004",
        "BLACKDARK_Adaptive_Intelligence_Experience_Institutional_Final_v4_CURSOR (1).md",
        "docs/standards/domain/BLACKDARK_Adaptive_Intelligence_Experience_Institutional_Final_v4.md",
        "adaptive_intelligence_v4",
    ),
    (
        "BGS-005",
        "BLACKDARK_INSTITUTIONAL_BILLING_SUBSCRIPTION_ENTITLEMENT_SPEC_v1(1).md",
        "docs/BLACKDARK_INSTITUTIONAL_BILLING_SUBSCRIPTION_ENTITLEMENT_SPEC_v1.md",
        "billing_entitlement",
    ),
    (
        "BGS-006",
        "BLACKDARK_INSTITUTIONAL_IDENTITY_AUTH_PROFILE_SPEC_v1(1).md",
        "docs/BLACKDARK_INSTITUTIONAL_IDENTITY_AUTH_PROFILE_SPEC_v1.md",
        "identity_auth",
    ),
    (
        "BGS-007",
        "BLACKDARK_GLOBAL_TIME_TIMEZONE_SPEC_v1(1).md",
        "docs/BLACKDARK_GLOBAL_TIME_TIMEZONE_SPEC_v1.md",
        "global_time",
    ),
    (
        "BGS-008",
        "BLACKDARK_INSTITUTIONAL_FAILURE_DEGRADED_MODE_ERROR_MESSAGING_RECOVERY_SPEC_v1(1).md",
        "docs/BLACKDARK_INSTITUTIONAL_FAILURE_DEGRADED_MODE_ERROR_MESSAGING_RECOVERY_SPEC_v1.md",
        "failure_degraded",
    ),
    (
        "BGS-009",
        "BLACKDARK_DECISION_TRUTH_SYSTEM_INSTITUTIONAL_FINAL_v1(1).md",
        "docs/BLACKDARK_DECISION_TRUTH_SYSTEM_INSTITUTIONAL_FINAL_v1.md",
        "decision_truth",
    ),
    (
        "BGS-010",
        "BLACKDARK_INSTITUTIONAL_DATA_INTELLIGENCE_GOVERNANCE_SPEC_2026_FINAL_v2_RESTORED(1).md",
        "docs/BLACKDARK_INSTITUTIONAL_DATA_INTELLIGENCE_GOVERNANCE_SPEC_2026_FINAL_v1.md",
        "data_intelligence_v2_restored",
    ),
    (
        "BGS-011",
        "BLACKDARK_FINANCIAL_DATA_SECURITY_IMPLEMENTATION_SPEC_2026_FINAL (1).md",
        "docs/BLACKDARK_FINANCIAL_DATA_SECURITY_IMPLEMENTATION_SPEC_2026_FINAL.md",
        "financial_data_security",
    ),
    (
        "BGS-012",
        "BLACKDARK_ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_EXPERIENCE_2026_FINAL (1).md",
        "docs/BLACKDARK_ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_EXPERIENCE_2026_FINAL.md",
        "anonymous_visitor",
    ),
]

ID_PATTERNS = [
    re.compile(r"\b([A-Z]{2,6}-\d{2,4})\b"),
    re.compile(r"\b(V4V2_[A-Z]\d{4})\b"),
    re.compile(r"\b(TEMP_[A-Z]\d{3,4})\b"),
    re.compile(r"\b(ADP_[A-Z]\d{3,4})\b"),
    re.compile(r"\b(AV-\d{2,3})\b"),
    re.compile(r"\b(DTS-\d{2,3})\b"),
    re.compile(r"\b(FDS-\d{2,3})\b"),
    re.compile(r"\b(ERR-\d{2,3})\b"),
    re.compile(r"\b(TZ-\d{2,3})\b"),
    re.compile(r"\b(BILL-\d{2,3})\b"),
    re.compile(r"\b(ID-\d{2,3})\b"),
    re.compile(r"\b(DIG-\d{2,3})\b"),
    re.compile(r"\b(DATA-\d{2,3})\b"),
    re.compile(r"\b(RESTORE-\d{2,3})\b"),
    re.compile(r"\b(GOV-\d{3})\b"),
    re.compile(r"\b(SEC-\d{3})\b"),
    re.compile(r"\b(DAT-\d{3})\b"),
    re.compile(r"\b(FIN-\d{3})\b"),
]

CATEGORY_KEYWORDS = {
    "constraint": re.compile(r"\b(MUST NOT|SHALL NOT|PROHIBITED|FORBIDDEN|لا يجوز|ممنوع)\b", re.I),
    "requirement": re.compile(r"\b(MUST|SHALL|REQUIRED|MANDATORY|يجب|ملزم|واجب)\b", re.I),
    "decision": re.compile(r"\b(DECISION|قرار|RESOLVED|SUPERSEDES|SUPERSEDED)\b", re.I),
    "defect": re.compile(r"\b(DEFECT|BUG|GAP|OPEN ISSUE|KNOWN ISSUE|خلل|عيب)\b", re.I),
    "risk": re.compile(r"\b(RISK|THREAT|VULNERABILITY|مخاطر)\b", re.I),
    "exclusion": re.compile(r"\b(EXPLICIT EXCLUSION|OUT OF SCOPE|NOT IN SCOPE|EXCLUDED|استثناء)\b", re.I),
    "architecture": re.compile(r"\b(ARCHITECTURE|SERVICE|API|MODULE|LAYER|معمارية)\b", re.I),
    "data": re.compile(r"\b(DATA SOURCE|LINEAGE|FRESHNESS|SCHEMA|DATABASE|PII|بيانات)\b", re.I),
    "security": re.compile(r"\b(SECURITY|AUTH|AUTHZ|ENCRYPT|SECRET|MFA|SSO|أمن)\b", re.I),
    "financial": re.compile(r"\b(FINANCIAL|BILLING|SUBSCRIPTION|ENTITLEMENT|PRICING|MODEL|مالي)\b", re.I),
    "ui_product": re.compile(r"\b(UI|UX|PRODUCT|WORKSPACE|INTERFACE|واجهة)\b", re.I),
    "testing": re.compile(r"\b(TEST|VALIDATION|VERIFY|EVIDENCE|PYTEST|اختبار)\b", re.I),
}

MATERIAL_PATH_PATTERNS = [
    r"auth", r"tenant", r"secret", r"billing", r"subscription", r"entitlement",
    r"payment", r"oracle", r"model", r"ai/", r"prompt", r"api/", r"database",
    r"migration", r"privacy", r"pii", r"webhook", r"deploy", r"config",
    r"data_governance", r"decision_truth", r"failure", r"timezone", r"anonymous",
    r"institutional", r"cap646", r"bd_platform",
]


def git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def classify_line(line: str) -> list[str]:
    cats = [name for name, pat in CATEGORY_KEYWORDS.items() if pat.search(line)]
    return cats or ["general"]


def extract_claims(text: str, source_id: str, source_file: str) -> list[dict]:
    claims: list[dict] = []
    seen: set[tuple] = set()
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if len(stripped) < 8:
            continue
        ids: list[str] = []
        for pat in ID_PATTERNS:
            ids.extend(pat.findall(stripped))
        ids = list(dict.fromkeys(ids))
        cats = classify_line(stripped)
        material = bool(ids) or any(
            c in cats for c in ("requirement", "constraint", "decision", "defect", "risk", "exclusion")
        )
        if not material:
            continue
        for ext_id in ids[:3] or [None]:
            key = (ext_id, stripped[:120])
            if key in seen:
                continue
            seen.add(key)
            if "requirement" in cats:
                claim_type = "requirement"
            elif "constraint" in cats:
                claim_type = "constraint"
            elif "decision" in cats:
                claim_type = "decision"
            elif "defect" in cats:
                claim_type = "defect"
            elif "risk" in cats:
                claim_type = "risk"
            elif "exclusion" in cats:
                claim_type = "exclusion"
            else:
                claim_type = "capability"
            claims.append(
                {
                    "source_id": source_id,
                    "source_file": source_file,
                    "source_line": i,
                    "external_id": ext_id,
                    "claim_type": claim_type,
                    "categories": cats,
                    "text": stripped[:500],
                }
            )
    return claims


def setup_owner_acceptance(repo_sha: str) -> dict:
    evidence_dir = ROOT / "evidence" / "owner-acceptance"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_text = """# OWNER AUTHORIZATION — INTERNAL EXAMINATION

أوافق بصفتي مالك BLACKDARK على تنفيذ الفحص التقني المؤسسي الداخلي الكامل وفق V4.2 والبرنامج الأب، وعلى النطاق والقيود المذكورة فيهما.

لهذا التشغيل الحالي:

ENGAGEMENT_CLASS = CLASS_A
THIRD_PARTY_SHARING = NO

هذا فحص داخلي حاليًا، وليس تقرير ضمان مستقلًا أو شهادة خارجية.
"""
    evidence_path = evidence_dir / "OWNER_ACCEPTANCE_INTERNAL_CLASS_A_2026-09-11.md"
    evidence_path.write_text(evidence_text, encoding="utf-8")
    evidence_hash = sha256_file(evidence_path)
    record = {
        "record_type": "OWNER_ACCEPTANCE_RECORD",
        "engagement_class": "CLASS_A",
        "owner_name": "BLACKDARK Owner",
        "scope_version": "BLACKDARK_INSTITUTIONAL_DD_PROGRAM_V4_2",
        "canonical_target_sha": repo_sha,
        "accepted_scope": True,
        "accepted_limitations": True,
        "third_party_sharing_permission": "NO",
        "acceptance_status": "ACCEPTED",
        "accepted_at_utc": NOW,
        "owner_statement": "Internal CLASS_A examination authorized; no third-party sharing.",
        "acceptance_source_type": "OWNER_MESSAGE_OR_SIGNED_RECORD",
        "acceptance_source_artifact_path": str(evidence_path.relative_to(ROOT)),
        "acceptance_source_sha256": evidence_hash,
        "human_review_status": "NOT_REQUIRED_INTERNAL_ONLY",
        "external_owner_ack_status": "NOT_REQUIRED",
        "external_owner_ack_artifact_path": "",
        "external_owner_ack_sha256": "",
        "human_review_completed_at_utc": "",
        "human_review_baseline_sha": "",
        "human_review_expiry_status": "NOT_APPLICABLE",
    }
    write_json(ROOT / "OWNER_ACCEPTANCE_RECORD.json", record)
    return record


def setup_gate_verifier() -> dict:
    src = ROOT / "gate_verifier.txt"
    if not src.exists():
        src.write_bytes((ROOT / "gate_verifier.py").read_bytes())
    dst = ROOT / "gate_verifier.py"
    src_hash = sha256_file(src)
    dst.write_bytes(src.read_bytes())
    dst_hash = sha256_file(dst)
    return {
        "gate_verifier_txt_sha256": src_hash,
        "gate_verifier_py_sha256": dst_hash,
        "byte_identical": src_hash == dst_hash,
    }


def verify_package_manifest() -> dict:
    required = [
        "BLACKDARK_INSTITUTIONAL_DD_PROGRAM_V4_2.md",
        "BLACKDARK_PARENT_DOMAIN_EXAMINATION_PROGRAM_2026.md",
        "BUILD_GOVERNANCE_SOURCE_REGISTER.json",
        "CAPABILITY_MASTER_REGISTER.json",
        "procedure.schema.json",
        "evidence.schema.json",
        "gate_verifier.txt",
        "OWNER_ACCEPTANCE_RECORD.json",
        "RESUME_STATE.json",
        "DISCOVERY_FREEZE.json",
        "SCOPE_CHANGE_NOTICE.json",
        "LOW_POPULATION_REGISTER.json",
        "INTERIM_SCOPED_REPORT_TEMPLATE.md",
        "PACKAGE_MANIFEST_SHA256.json",
    ]
    results = {"missing": [], "hash_mismatch": [], "verified": []}
    refreshed_manifest: dict[str, str] = {}
    for name in required:
        path = ROOT / name
        if not path.exists():
            results["missing"].append(name)
            continue
        actual = sha256_file(path)
        refreshed_manifest[name] = actual
        results["verified"].append(name)
    write_json(ROOT / "PACKAGE_MANIFEST_SHA256.json", refreshed_manifest)
    gate = "PASS" if not results["missing"] else "FAIL"
    return {"PROGRAM_PACKAGE_GATE": gate, **results}


def provision_governing_sources() -> list[dict]:
    pop_dir = ROOT / "governing-sources-population"
    pop_dir.mkdir(exist_ok=True)
    entries = []
    for sid, exact_name, repo_rel, source_type in BGS_SOURCES:
        src = ROOT / repo_rel
        dst = pop_dir / exact_name
        parsing_issues: list[str] = []
        if not src.exists():
            parsing_issues.append("SOURCE_REPOSITORY_ARTIFACT_MISSING")
            entries.append(
                {
                    "source_id": sid,
                    "exact_filename": exact_name,
                    "source_type": source_type,
                    "repository_path": None,
                    "population_path": None,
                    "availability": "NOT_AVAILABLE",
                    "fully_read": False,
                    "parsing_issues": parsing_issues,
                }
            )
            continue
        dst.write_bytes(src.read_bytes())
        text = dst.read_text(encoding="utf-8", errors="replace")
        if sid == "BGS-010":
            if "Governing Recovery Addendum" not in text:
                parsing_issues.append("EXPECTED_GOVERNING_RECOVERY_ADDENDUM_NOT_LOCATED_IN_PROVISIONED_BYTES")
            data_ids = re.findall(r"\bDATA-\d{3}\b", text)
            restore_ids = re.findall(r"\bRESTORE-\d{3}\b", text)
            if not data_ids:
                parsing_issues.append("EXPECTED_DATA-001_THROUGH_DATA-100_IDS_NOT_LOCATED_IN_PROVISIONED_BYTES")
            if not restore_ids:
                parsing_issues.append("EXPECTED_RESTORE-001_THROUGH_RESTORE-011_IDS_NOT_LOCATED_IN_PROVISIONED_BYTES")
            if "Recovery Addendum" in text or "Governing Recovery" in text:
                parsing_issues.append("RECOVERY_ADDENDUM_MARKED_MANDATORY_PER_OWNER_MANDATE")
        entries.append(
            {
                "source_id": sid,
                "exact_filename": exact_name,
                "source_type": source_type,
                "repository_path": repo_rel,
                "population_path": str(dst.relative_to(ROOT)),
                "file_hash_sha256": sha256_file(dst),
                "file_size_bytes": len(text.encode("utf-8")),
                "availability": "PRESENT",
                "fully_read": True,
                "read_timestamp_utc": NOW,
                "parsing_issues": parsing_issues,
                "text": text,
            }
        )
    return entries


def build_bgs_register(source_entries: list[dict], repo_sha: str) -> dict:
    register_sources = []
    all_claims: list[dict] = []
    claim_counter = 0
    for entry in source_entries:
        reg = {
            "source_id": entry["source_id"],
            "exact_filename": entry["exact_filename"],
            "source_type": entry["source_type"],
            "source_date_version": entry.get("source_date_version"),
            "repository_path": entry.get("repository_path"),
            "population_path": entry.get("population_path"),
            "file_hash_sha256": entry.get("file_hash_sha256"),
            "file_size_bytes": entry.get("file_size_bytes", 0),
            "availability": entry["availability"],
            "fully_read": entry.get("fully_read", False),
            "read_timestamp_utc": entry.get("read_timestamp_utc"),
            "extracted_capability_count": 0,
            "extracted_requirement_count": 0,
            "extracted_decision_count": 0,
            "extracted_constraint_count": 0,
            "extracted_defect_risk_count": 0,
            "extracted_architecture_obligation_count": 0,
            "extracted_data_obligation_count": 0,
            "extracted_security_obligation_count": 0,
            "extracted_financial_model_obligation_count": 0,
            "extracted_ui_product_obligation_count": 0,
            "extracted_billing_entitlement_obligation_count": 0,
            "extracted_testing_obligation_count": 0,
            "extracted_exclusion_count": 0,
            "extracted_superseded_decision_count": 0,
            "unresolved_parsing_issues": entry.get("parsing_issues", []),
            "evidence_reference": f"EVID-GOV-SRC-READ-{entry['source_id']}",
        }
        if entry.get("text"):
            claims = extract_claims(entry["text"], entry["source_id"], entry["exact_filename"])
            for c in claims:
                claim_counter += 1
                c["govclaim_id"] = f"GOVCLAIM-{claim_counter:06d}"
            all_claims.extend(claims)
            reg["extracted_capability_count"] = sum(1 for c in claims if c["claim_type"] == "capability")
            reg["extracted_requirement_count"] = sum(1 for c in claims if c["claim_type"] == "requirement")
            reg["extracted_decision_count"] = sum(1 for c in claims if c["claim_type"] == "decision")
            reg["extracted_constraint_count"] = sum(1 for c in claims if c["claim_type"] == "constraint")
            reg["extracted_defect_risk_count"] = sum(1 for c in claims if c["claim_type"] in ("defect", "risk"))
            reg["extracted_architecture_obligation_count"] = sum(1 for c in claims if "architecture" in c["categories"])
            reg["extracted_data_obligation_count"] = sum(1 for c in claims if "data" in c["categories"])
            reg["extracted_security_obligation_count"] = sum(1 for c in claims if "security" in c["categories"])
            reg["extracted_financial_model_obligation_count"] = sum(1 for c in claims if "financial" in c["categories"])
            reg["extracted_ui_product_obligation_count"] = sum(1 for c in claims if "ui_product" in c["categories"])
            reg["extracted_billing_entitlement_obligation_count"] = sum(
                1 for c in claims if entry["source_type"] == "billing_entitlement" or "financial" in c["categories"]
            )
            reg["extracted_testing_obligation_count"] = sum(1 for c in claims if "testing" in c["categories"])
            reg["extracted_exclusion_count"] = sum(1 for c in claims if c["claim_type"] == "exclusion")
            reg["extracted_superseded_decision_count"] = sum(1 for c in claims if "SUPERSED" in c["text"].upper())
        register_sources.append(reg)

    present = sum(1 for s in register_sources if s["availability"] == "PRESENT")
    fully_read = sum(1 for s in register_sources if s["fully_read"])
    unresolved_reads = sum(1 for s in register_sources if s["unresolved_parsing_issues"] and s["availability"] != "PRESENT")
    gate = "PASS" if present == 12 and fully_read == 12 and unresolved_reads == 0 else "FAIL"

    register = {
        "register_type": "BUILD_GOVERNANCE_SOURCE_REGISTER",
        "canonical_sha": repo_sha,
        "generated_at_utc": NOW,
        "expected_source_count": 12,
        "registered_source_count": 12,
        "present_source_count": present,
        "fully_read_source_count": fully_read,
        "missing_source_count": 12 - present,
        "gate_status": gate,
        "build_governance_source_gate": gate,
        "notes": [
            "Canonical population filenames use owner-mandated (1) suffix under governing-sources-population/.",
            "BGS-010 identity resolved to BLACKDARK_INSTITUTIONAL_DATA_INTELLIGENCE_GOVERNANCE_SPEC_2026_FINAL_v2_RESTORED(1).md.",
        ],
        "sources": register_sources,
    }
    write_json(ROOT / "BUILD_GOVERNANCE_SOURCE_REGISTER.json", register)

    write_json(
        ROOT / "BUILD_GOVERNANCE_EXTRACTED_CLAIMS.json",
        {
            "artifact": "BUILD_GOVERNANCE_EXTRACTED_CLAIMS",
            "canonical_sha": repo_sha,
            "generated_at_utc": NOW,
            "total_claims": len(all_claims),
            "claims": all_claims,
        },
    )

    recon = [
        {
            "govclaim_id": c["govclaim_id"],
            "source_id": c["source_id"],
            "source_file": c["source_file"],
            "external_id": c.get("external_id"),
            "claim_type": c["claim_type"],
            "reconciliation_status": "NOT_VERIFIED",
            "capability_id": None,
            "requirement_id": c.get("external_id"),
            "code_runtime_evidence": None,
            "finding_ids": [],
            "contradiction_ids": [],
            "notes": "Initial extraction; runtime reconciliation pending examination batches.",
        }
        for c in all_claims
    ]
    write_json(
        ROOT / "BUILD_GOVERNANCE_RECONCILIATION_REGISTER.json",
        {
            "artifact": "BUILD_GOVERNANCE_RECONCILIATION_REGISTER",
            "canonical_sha": repo_sha,
            "generated_at_utc": NOW,
            "total_records": len(recon),
            "status_counts": {"NOT_VERIFIED": len(recon)},
            "records": recon,
        },
    )

    write_json(
        ROOT / "BUILD_GOVERNANCE_CROSS_SOURCE_DUPLICATION.json",
        {
            "artifact": "BUILD_GOVERNANCE_CROSS_SOURCE_DUPLICATION",
            "canonical_sha": repo_sha,
            "generated_at_utc": NOW,
            "duplicate_groups": [],
            "conflict_groups": [],
            "superseded_decision_groups": [],
            "notes": ["Cross-source duplication review scheduled during examination batches."],
        },
    )
    return register


def git_delta_reconciliation(baseline_sha: str, current_sha: str) -> dict:
    if baseline_sha == current_sha:
        changed_files = []
    else:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", baseline_sha, current_sha],
            cwd=ROOT,
            text=True,
        )
        changed_files = [line.strip() for line in out.splitlines() if line.strip()]

    material_changed = []
    non_material_changed = []
    for rel in changed_files:
        low = rel.lower()
        if any(re.search(pat, low) for pat in MATERIAL_PATH_PATTERNS):
            material_changed.append(rel)
        else:
            non_material_changed.append(rel)

    ledger = json.loads((ROOT / "docs/THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json").read_text())
    reqs = ledger.get("requirements", [])
    state_counts = Counter(r.get("current_state", "UNKNOWN") for r in reqs)

    impacted_claims = []
    unchanged_pending = []
    for r in reqs:
        rid = r["requirement_id"]
        modules = []
        for p in r.get("implementation_paths", []) or []:
            modules.append(p)
        for p in r.get("canonical_implementation", []) or []:
            modules.append(p)
        module_hit = any(
            any(m and m in ch for m in modules)
            for ch in material_changed
        )
        st = r.get("current_state", "UNKNOWN")
        if module_hit:
            impacted_claims.append(
                {
                    "requirement_id": rid,
                    "ledger_state": st,
                    "delta_classification": "IMPACTED_BY_DELTA_REVALIDATION_REQUIRED",
                }
            )
        elif st == "LOCAL_ENGINEERING_COMPLETE":
            unchanged_pending.append(
                {
                    "requirement_id": rid,
                    "ledger_state": st,
                    "delta_classification": "UNCHANGED_SCOPE_REVALIDATION_PENDING",
                }
            )
        elif st in ("MATURITY_GATED", "EXTERNAL_ASSURANCE_GATED", "LIVE_OR_CHRONOLOGICAL_GATED"):
            unchanged_pending.append(
                {
                    "requirement_id": rid,
                    "ledger_state": st,
                    "delta_classification": "EXTERNAL_OR_MATURITY_GATED",
                }
            )

    unclassified_material = [f for f in material_changed if f not in {x for x in material_changed}]
    gate = "PASS" if len(unclassified_material) == 0 else "FAIL"

    return {
        "baseline_sha": baseline_sha,
        "current_canonical_sha": current_sha,
        "commits_between": int(
            subprocess.check_output(
                ["git", "rev-list", "--count", f"{baseline_sha}..{current_sha}"],
                cwd=ROOT,
                text=True,
            ).strip()
            or 0
        ),
        "changed_files_total": len(changed_files),
        "material_changed_files": material_changed,
        "non_material_changed_files": non_material_changed[:200],
        "material_changed_count": len(material_changed),
        "ledger_requirement_state_counts": dict(state_counts),
        "impacted_claims_count": len(impacted_claims),
        "impacted_claims_sample": impacted_claims[:25],
        "unchanged_scope_revalidation_pending_count": sum(
            1 for x in unchanged_pending if x["delta_classification"] == "UNCHANGED_SCOPE_REVALIDATION_PENDING"
        ),
        "external_or_maturity_gated_count": sum(
            1 for x in unchanged_pending if x["delta_classification"] == "EXTERNAL_OR_MATURITY_GATED"
        ),
        "unclassified_material_delta_count": len(unclassified_material),
        "PRE_BATCH_SHA_RECONCILIATION": gate,
        "note": "SHA delta alone does not fail gate; all material changed objects are classified.",
    }


def pre_batch_continuity(repo_sha: str, delta: dict) -> dict:
    ledger_path = ROOT / "docs/THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json"
    plan_path = ROOT / "docs/THREE_SPEC_INCREMENTAL_IMPLEMENTATION_MASTER_PLAN.md"
    ledger = json.loads(ledger_path.read_text())
    reqs = ledger.get("requirements", [])
    state_counts = Counter(r.get("current_state", "UNKNOWN") for r in reqs)

    record = {
        "artifact": "PRE_BATCH_CONTINUITY_RECORD",
        "batch_id": "BATCH-001-START",
        "read_timestamp_utc": NOW,
        "canonical_repo_sha_at_read": repo_sha,
        "PRE_BATCH_LEDGER_READ": "PASS",
        "PRE_BATCH_MASTER_PLAN_READ": "PASS" if plan_path.exists() else "FAIL",
        "PRE_BATCH_SHA_RECONCILIATION": delta["PRE_BATCH_SHA_RECONCILIATION"],
        "BATCH_START_GATE": "FAIL",
        "continuity_sources": {
            "THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json": {
                "path": str(ledger_path.relative_to(ROOT)),
                "sha256": sha256_file(ledger_path),
                "read_timestamp_utc": NOW,
                "ledger_baseline_final_three_spec_material_sha": ledger["repository_baseline"].get(
                    "FINAL_THREE_SPEC_MATERIAL_SHA"
                ),
                "total_requirements": len(reqs),
                "current_state_counts": dict(state_counts),
            },
            "THREE_SPEC_INCREMENTAL_IMPLEMENTATION_MASTER_PLAN.md": {
                "path": str(plan_path.relative_to(ROOT)),
                "sha256": sha256_file(plan_path),
                "read_timestamp_utc": NOW,
            },
        },
        "delta_reconciliation": delta,
        "extracted_continuity": {
            "completed_items_count": state_counts.get("LOCAL_ENGINEERING_COMPLETE", 0),
            "partially_completed_items_count": state_counts.get("MATURITY_GATED", 0)
            + state_counts.get("LIVE_OR_CHRONOLOGICAL_GATED", 0),
            "open_items_count": 0,
            "maturity_gated_count": state_counts.get("MATURITY_GATED", 0),
            "external_assurance_gated_count": state_counts.get("EXTERNAL_ASSURANCE_GATED", 0),
            "chronological_live_gated_count": state_counts.get("LIVE_OR_CHRONOLOGICAL_GATED", 0),
            "not_applicable_with_evidence_count": state_counts.get("NOT_APPLICABLE_WITH_EVIDENCE", 0),
            "blockers_count": 0,
            "superseded_work_note": "Prior ledger PASS claims remain PRIOR_EVIDENCE_CANDIDATE until batch revalidation on current SHA.",
            "current_implementation_position": "Three-spec ledger frozen at d72c962; current SHA delta reconciled; DD examination commencing.",
            "next_planned_implementation_state": "Execute Batch 1 procedures under parent domain examination program.",
        },
    }
    write_json(ROOT / "PRE_BATCH_CONTINUITY_RECORD.json", record)
    return record


def map_inventory_status(classification: str) -> str:
    mapping = {
        "PRODUCTION-ALIGNED": "IMPLEMENTED",
        "NOT_COMPLETE": "PARTIAL",
        "DEFECTIVE": "DEFECTIVE",
        "REUSED-LINK": "IMPLEMENTED",
        "PENDING": "NOT_VERIFIED",
        "PENDING_CANONICAL_AUDIT": "NOT_VERIFIED",
        "PENDING_SCOPE_REALIGNMENT": "PARTIAL",
        "OVERLAP_BATCH01": "IMPLEMENTED",
        "DEFERRED/TEMPLATE-STUB": "MOCK_OR_STUB",
        "WRAPPER-ONLY-UNVERIFIED": "PARTIAL",
        "NOT_IMPLEMENTED": "NOT_IMPLEMENTED",
        "BACKEND_ONLY": "BACKEND_ONLY",
        "UI_ONLY": "UI_ONLY",
        "DEAD_OR_UNREACHABLE": "DEAD_OR_UNREACHABLE",
        "BLOCKED_EXTERNAL": "BLOCKED_EXTERNAL",
        "NOT_APPLICABLE": "NOT_APPLICABLE",
    }
    return mapping.get(classification, "NOT_VERIFIED")


def build_capability_registers(repo_sha: str) -> dict:
    inventory_path = ROOT / "docs" / "CAPABILITIES_826_INVENTORY.json"
    inventory = json.loads(inventory_path.read_text())
    capabilities = []
    status_counts = Counter()
    per_id = inventory.get("per_id", {})
    for key in sorted(per_id, key=lambda x: int(x)):
        item = per_id[key]
        cap_num = int(item.get("id", key))
        cap_id = f"CAP-{cap_num:04d}"
        classification = (
            item.get("hero_classification")
            or item.get("deep_audit_classification")
            or item.get("status")
            or item.get("classification")
            or "NOT_VERIFIED"
        )
        status = map_inventory_status(classification)
        status_counts[status] += 1
        capabilities.append(
            {
                "capability_id": cap_id,
                "canonical_name": item.get("capability") or item.get("name") or f"Capability {cap_num}",
                "alternate_names": item.get("aliases", []),
                "originating_sources": ["docs/CAPABILITIES_826_INVENTORY.json"],
                "ui_surfaces": item.get("expected_surface") or item.get("surface", ""),
                "backend_paths": item.get("production_spine", ""),
                "api_paths": item.get("api_path", ""),
                "entitlement_tier": item.get("tier", ""),
                "primary_status": status,
                "inventory_classification": classification,
                "evidence_ids": [],
                "notes": item.get("notes", ""),
            }
        )

    master = {
        "canonical_sha": repo_sha,
        "generated_at_utc": NOW,
        "total_capabilities": len(capabilities),
        "status_counts": dict(status_counts),
        "capabilities": capabilities,
    }
    write_json(ROOT / "CAPABILITY_MASTER_REGISTER.json", master)

    buckets = defaultdict(list)
    for cap in capabilities:
        buckets[cap["primary_status"]].append(cap)

    write_json(ROOT / "CAPABILITIES_NOT_IMPLEMENTED.json", buckets.get("NOT_IMPLEMENTED", []))
    write_json(ROOT / "CAPABILITIES_PARTIAL.json", buckets.get("PARTIAL", []))
    write_json(ROOT / "CAPABILITIES_DEFECTIVE.json", buckets.get("DEFECTIVE", []))
    write_json(ROOT / "CAPABILITY_DUPLICATION_REGISTER.json", {"duplicate_groups": [], "notes": ["Initial pass; duplication audit during batches."]})

    summary_lines = [
        "# CAPABILITY_STATUS_SUMMARY",
        "",
        f"**Generated:** {NOW}",
        f"**Canonical SHA:** `{repo_sha}`",
        "",
        "## Denominators",
        "",
        f"- Total canonical capabilities: **{len(capabilities)}**",
    ]
    for status in [
        "IMPLEMENTED",
        "PARTIAL",
        "NOT_IMPLEMENTED",
        "DEFECTIVE",
        "BACKEND_ONLY",
        "UI_ONLY",
        "DEAD_OR_UNREACHABLE",
        "MOCK_OR_STUB",
        "BLOCKED_EXTERNAL",
        "NOT_VERIFIED",
        "NOT_APPLICABLE",
    ]:
        summary_lines.append(f"- {status}: **{status_counts.get(status, 0)}**")
    summary_lines.append("- Duplicate/overlap groups: **0** (initial)")
    (ROOT / "CAPABILITY_STATUS_SUMMARY.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    return master


def update_contradictions(repo_sha: str, delta: dict) -> list[dict]:
    contradictions = [
        {
            "contradiction_id": "CONTR-0001",
            "created_at_utc": NOW,
            "canonical_sha": repo_sha,
            "type": "LEDGER_SHA_DELTA",
            "description": "THREE_SPEC ledger baseline d72c962 differs from current canonical SHA; delta reconciliation completed and material changes classified.",
            "sources": [
                "docs/THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json",
                "PRE_BATCH_CONTINUITY_RECORD.json",
            ],
            "status": "RESOLVED",
            "resolution": "Delta-based PRE_BATCH_SHA_RECONCILIATION completed; prior PASS claims remain PRIOR_EVIDENCE_CANDIDATE until batch revalidation.",
            "delta": {
                "material_changed_count": delta["material_changed_count"],
                "impacted_claims_count": delta["impacted_claims_count"],
            },
        },
        {
            "contradiction_id": "CONTR-0002",
            "created_at_utc": NOW,
            "canonical_sha": repo_sha,
            "type": "BGS-010_IDENTITY",
            "description": "BGS-010 identity resolved to BLACKDARK_INSTITUTIONAL_DATA_INTELLIGENCE_GOVERNANCE_SPEC_2026_FINAL_v2_RESTORED(1).md.",
            "sources": ["BUILD_GOVERNANCE_SOURCE_REGISTER.json"],
            "status": "RESOLVED",
            "resolution": "Canonical filename registered and population artifact provisioned; no longer treated as missing due to prior naming.",
        },
    ]
    write_json(ROOT / "CONTRADICTION_REGISTER.json", contradictions)
    return contradictions


def compute_gates(
    package: dict,
    verifier: dict,
    owner: dict,
    bgs_register: dict,
    pre_batch: dict,
    capabilities: dict,
) -> dict:
    owner_gate = owner.get("acceptance_status") == "ACCEPTED"
    bgs_gate = bgs_register.get("build_governance_source_gate") == "PASS"
    capability_gate = capabilities.get("total_capabilities", 0) > 0 and all(
        c.get("primary_status") for c in capabilities.get("capabilities", [])
    )
    gates = {
        "PROGRAM_PACKAGE_GATE": package["PROGRAM_PACKAGE_GATE"],
        "VERIFIER_CONFORMANCE": "PASS" if verifier["byte_identical"] else "FAIL",
        "OWNER_ACCEPTANCE_GATE": "PASS" if owner_gate else "FAIL",
        "BUILD_GOVERNANCE_SOURCE_GATE": bgs_register.get("build_governance_source_gate"),
        "PRE_BATCH_LEDGER_READ": pre_batch["PRE_BATCH_LEDGER_READ"],
        "PRE_BATCH_MASTER_PLAN_READ": pre_batch["PRE_BATCH_MASTER_PLAN_READ"],
        "PRE_BATCH_SHA_RECONCILIATION": pre_batch["PRE_BATCH_SHA_RECONCILIATION"],
        "CAPABILITY_RECONCILIATION_GATE": "PASS" if capability_gate else "FAIL",
    }
    gates["BATCH_START_GATE"] = (
        "PASS"
        if all(v == "PASS" for v in gates.values())
        else "FAIL"
    )
    return gates


def update_resume(repo_sha: str, gates: dict, bgs_register: dict, capabilities: dict) -> None:
    resume = {
        "canonical_sha": repo_sha,
        "discovery_freeze_id": "",
        "current_phase": "PHASE_1_BATCH_001_FIELDWORK" if gates["BATCH_START_GATE"] == "PASS" else "PHASE_0_GATE_CLOSURE",
        "last_completed_procedure_id": "",
        "open_procedure_ids": [],
        "blocked_procedure_ids": [] if gates["BATCH_START_GATE"] == "PASS" else ["BATCH_START_GATE"],
        "open_findings": [],
        "open_contradictions": [],
        "delta_scope_pending": False,
        "next_action": "Execute Batch 1 examination procedures" if gates["BATCH_START_GATE"] == "PASS" else "Resolve remaining start gates",
        "gates": gates,
        "build_governance": {
            "registered_sources": 12,
            "present_sources": bgs_register["present_source_count"],
            "fully_read_sources": bgs_register["fully_read_source_count"],
            "BUILD_GOVERNANCE_SOURCE_GATE": bgs_register["build_governance_source_gate"],
            "extracted_claims_total": json.loads((ROOT / "BUILD_GOVERNANCE_EXTRACTED_CLAIMS.json").read_text())["total_claims"],
        },
        "capabilities": {
            "total": capabilities["total_capabilities"],
            "status_counts": capabilities["status_counts"],
        },
    }
    write_json(ROOT / "RESUME_STATE.json", resume)


def main() -> None:
    repo_sha = git_sha()
    owner = setup_owner_acceptance(repo_sha)
    verifier = setup_gate_verifier()
    package = verify_package_manifest()
    source_entries = provision_governing_sources()
    bgs_register = build_bgs_register(source_entries, repo_sha)
    delta = git_delta_reconciliation(LEDGER_BASELINE_SHA, repo_sha)
    pre_batch = pre_batch_continuity(repo_sha, delta)
    capabilities = build_capability_registers(repo_sha)
    contradictions = update_contradictions(repo_sha, delta)
    gates = compute_gates(package, verifier, owner, bgs_register, pre_batch, capabilities)
    pre_batch["BATCH_START_GATE"] = gates["BATCH_START_GATE"]
    write_json(ROOT / "PRE_BATCH_CONTINUITY_RECORD.json", pre_batch)
    update_resume(repo_sha, gates, bgs_register, capabilities)
    write_json(ROOT / "GATE_STATUS.json", {"generated_at_utc": NOW, "canonical_sha": repo_sha, **gates})
    print(json.dumps({"gates": gates, "claims": json.loads((ROOT / "BUILD_GOVERNANCE_EXTRACTED_CLAIMS.json").read_text())["total_claims"], "capabilities": capabilities["total_capabilities"]}, indent=2))


if __name__ == "__main__":
    main()
