"""Build the fixed Requirements Baseline from governing sources and catalogs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cap646.catalog import matrix_by_id as matrix646_by_id
from cap978.catalog import catalog_by_id as catalog978_by_id, is_duplicate, is_external
from rvm.governing import load_governing_sources
from rvm.models import RVMEntry

_ROOT = Path(__file__).resolve().parent.parent
_BASELINE_OUT = _ROOT / "docs" / "rvm" / "REQUIREMENTS_BASELINE.json"

PLATFORM_STAGES: list[tuple[str, str, str]] = [
    ("PLT-RAW", "platform_chain_e2e", "Raw market/on-chain data ingested with provenance"),
    ("PLT-DERIVED", "platform_chain_e2e", "Normalized derived metrics available for downstream use"),
    ("PLT-ENTITY", "platform_chain_e2e", "Entity/event library records market events"),
    ("PLT-FEATURE", "platform_chain_e2e", "Feature engineering produces model-ready features"),
    ("PLT-SIGNAL", "platform_chain_e2e", "Signal registry emits traceable signals"),
    ("PLT-PREDICTION", "platform_chain_e2e", "Prediction/decision engine produces auditable decisions"),
    ("PLT-CONFIDENCE", "platform_chain_e2e", "Confidence scoring attached to predictions"),
    ("PLT-EXPOSURE", "platform_chain_e2e", "User exposure logged with tier gating"),
    ("PLT-OUTCOME", "platform_chain_e2e", "Outcome feedback linked to predictions"),
    ("PLT-EVIDENCE", "platform_chain_e2e", "Evidence pack and failure corpus updated"),
    ("PLT-LEARNING", "platform_chain_e2e", "Experience log captures learning events"),
    ("PLT-MODEL", "platform_chain_e2e", "Model version tracked in registry"),
]

CONTROL_OUTCOMES: dict[str, str] = {
    "GOV-001": "Governance documents adopted and accessible",
    "GOV-002": "RBAC role matrix enforced with single ownership",
    "GOV-003": "Fail-closed financial and stale-price guards active",
    "ARC-001": "Architecture due diligence score meets threshold",
    "ARC-002": "Loose coupling via service bus",
    "QUA-001": "Automated test suite present and runnable",
    "SEC-001": "Login rate limiting enforced",
    "SEC-002": "API key encryption guard active",
    "SEC-003": "Security headers middleware deployed",
    "SEC-004": "MFA enrollment path available",
    "SEC-005": "Session hardening and CSRF protection",
    "SEC-006": "Enterprise SSO (OIDC/SAML) operational with real IdP",
    "SEC-007": "Secrets manager integration",
    "SEC-008": "Independent third-party penetration test attestation",
    "SEC-009": "SOC2/ISO certification from accredited auditor",
    "DAT-001": "Data lake hot/cold tier operational",
    "DAT-002": "Provenance scoring on all data paths",
    "DAT-003": "Quarantine on data disagreement",
    "DAT-004": "No mock/demo as sole production proof",
    "REL-001": "Health checks and uptime probes",
    "REL-002": "Signed multi-worker HA load evidence",
    "REL-003": "Chaos/failure injection resilience",
    "REL-004": "Backup and recovery path documented",
    "REL-005": "Observability stack operational",
    "QA-001": "Evidence room with reproducible artifacts",
    "QA-002": "Zero-defect gate in CI",
    "QA-003": "Regression test coverage on critical paths",
    "QA-004": "Production vs demo path separation",
    "AI-001": "AI provenance footer on all oracle outputs",
    "AI-002": "Model card published",
    "AI-003": "Overclaim denylist enforced",
    "AI-004": "Oracle audit chain immutable",
    "AI-005": "Confidence calibration tracked",
    "FIN-001": "Net edge truth fail-closed",
    "FIN-002": "Fee/slippage modeling in arbitrage",
    "FIN-003": "Billing tier entitlements enforced",
    "FIN-004": "No unsupported ROI claims",
    "PRV-001": "Privacy policy and consent flows",
    "PRV-002": "Data retention and deletion paths",
    "UX-001": "25-locale i18n with RTL support",
    "UX-002": "Trust OS lens navigation",
    "UX-003": "Accessibility baseline on core journeys",
}

COMMERCIAL_GATES: list[tuple[str, str]] = [
    ("COM-P0-EXT", "All P0 external evidence items closed (644, 645, SEC-006, SEC-008, REL-002)"),
    ("COM-BILLING", "Live payment processor with subscription lifecycle"),
    ("COM-KYC", "KYC/AML pathway for institutional tier"),
    ("COM-MSA", "Master Service Agreement and DPA templates executed"),
    ("COM-SLA", "Published SLA with uptime commitments"),
    ("COM-SUPPORT", "Tiered support with escalation paths"),
]

INSTITUTIONAL_GATES: list[tuple[str, str]] = [
    ("INS-SSOT", "Single Requirements Verification Matrix governs all status"),
    ("INS-EVIDENCE", "Evidence room with re-verifiable artifacts per requirement"),
    ("INS-TENANT", "Multi-tenant org isolation with Postgres production path"),
    ("INS-DATAROOM", "Institutional data room with audit trail"),
    ("INS-B2B", "B2B API gateway with partner onboarding"),
    ("INS-SOFT-LAUNCH", "Soft launch shadow-forward mode operational"),
]


def _cap_intended_outcome(name: str, track: str) -> str:
    return f"User/institution achieves '{name}' outcome on track {track} with evidence-backed results"


def build_capability_entries() -> list[RVMEntry]:
    entries: list[RVMEntry] = []
    catalog = catalog978_by_id()
    matrix646 = matrix646_by_id()
    for cid, row in sorted(catalog.items()):
        name = row.get("capability", "")
        track = row.get("track", "")
        scope = row.get("scope", "base_646")
        gap_status = None
        if cid <= 646:
            gap_status = matrix646.get(cid, {}).get("final_classification")
        source = "GOV-SRC-001"
        if is_external(cid):
            intended = f"Capability '{name}' operational with contracted external data/vendor rights"
        elif is_duplicate(cid):
            intended = f"Capability '{name}' delivered via canonical implementation without duplicate logic"
        else:
            intended = _cap_intended_outcome(name, track)
        entries.append(
            RVMEntry(
                id=f"CAP-{cid}",
                kind="capability",
                source=source,
                requirement=f"{name} (ID {cid}, {scope}, {track})",
                intended_outcome=intended,
                verification_method="execute_capability + backend binding + compliance footer + static binding audit",
                validation_method="functional_dod domain check + user journey / operational outcome proof",
                gap_matrix_status=gap_status,
            )
        )
    return entries


def build_control_entries() -> list[RVMEntry]:
    return [
        RVMEntry(
            id=ctl_id,
            kind="control",
            source="GOV-SRC-002",
            requirement=f"Institutional control {ctl_id}",
            intended_outcome=outcome,
            verification_method="verify_control executable check",
            validation_method="institutional operational proof — not code existence alone",
        )
        for ctl_id, outcome in CONTROL_OUTCOMES.items()
    ]


def build_platform_entries() -> list[RVMEntry]:
    return [
        RVMEntry(
            id=stage_id,
            kind="platform",
            source="GOV-SRC-002",
            requirement=f"Platform data chain stage: {stage_id}",
            intended_outcome=outcome,
            verification_method="platform_chain_e2e stage execution",
            validation_method="compounding chain produces traceable downstream artifacts",
        )
        for stage_id, _module, outcome in PLATFORM_STAGES
    ]


def build_commercial_entries() -> list[RVMEntry]:
    return [
        RVMEntry(
            id=com_id,
            kind="commercial",
            source="GOV-SRC-002",
            requirement=f"Commercial readiness gate: {com_id}",
            intended_outcome=outcome,
            verification_method="commercial_launch_checklist + billing/KYC module audit",
            validation_method="procurement-ready operational proof",
        )
        for com_id, outcome in COMMERCIAL_GATES
    ]


def build_institutional_entries() -> list[RVMEntry]:
    return [
        RVMEntry(
            id=ins_id,
            kind="institutional",
            source="GOV-SRC-002",
            requirement=f"Institutional readiness gate: {ins_id}",
            intended_outcome=outcome,
            verification_method="institutional module audit + RVM self-check",
            validation_method="institutional buyer operational acceptance",
        )
        for ins_id, outcome in INSTITUTIONAL_GATES
    ]


def build_baseline() -> dict[str, Any]:
    gov = load_governing_sources()
    entries = (
        build_capability_entries()
        + build_control_entries()
        + build_platform_entries()
        + build_commercial_entries()
        + build_institutional_entries()
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline_version": gov.get("baseline_version", "blackdark-rvm-v1"),
        "governing_sources": gov,
        "total_requirements": len(entries),
        "counts_by_kind": {
            kind: sum(1 for e in entries if e.kind == kind)
            for kind in ("capability", "control", "platform", "commercial", "institutional")
        },
        "requirements": [e.to_dict() for e in entries],
        "methodology": {
            "verification": "Proves implementation conforms to specified requirement",
            "validation": "Proves final implementation achieves intended user/institutional purpose",
            "final_status_values": ["PASS", "FAIL", "EXTERNAL_EVIDENCE_REQUIRED"],
        },
    }


def write_baseline() -> dict[str, Any]:
    data = build_baseline()
    _BASELINE_OUT.parent.mkdir(parents=True, exist_ok=True)
    _BASELINE_OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def load_baseline() -> dict[str, Any]:
    if not _BASELINE_OUT.is_file():
        return write_baseline()
    return json.loads(_BASELINE_OUT.read_text(encoding="utf-8"))
