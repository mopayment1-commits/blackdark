#!/usr/bin/env python3
from pathlib import Path
import json, hashlib, sys

ROOT=Path(__file__).resolve().parent
errors=[]; warnings=[]

EXIT_OK=0
EXIT_GATE_FAIL=3
EXIT_INPUT_ERROR=4

def load(name, required=True):
    p=ROOT/name
    if not p.exists():
        if required: errors.append(f"MISSING:{name}")
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"INVALID_JSON:{name}:{e}")
        return None

owner=load("OWNER_ACCEPTANCE_RECORD.json")
resume=load("RESUME_STATE.json")
freeze=load("DISCOVERY_FREEZE.json")
procedures=load("PROCEDURES.json", required=False) or []
evidence=load("EVIDENCE_INDEX.json", required=False) or []

# OWNER ACCEPTANCE: must originate from owner evidence, not agent assertion.
owner_gate=False
if owner:
    status=owner.get("acceptance_status")
    if status not in ("ACCEPTED","PARTIAL","REJECTED"):
        errors.append("OWNER_ACCEPTANCE_STATUS_NOT_RECORDED")
    if status=="ACCEPTED":
        for k in ("owner_name","scope_version","accepted_at_utc","acceptance_source_type",
                  "acceptance_source_artifact_path","acceptance_source_sha256"):
            if not owner.get(k): errors.append(f"OWNER_ACCEPTANCE_MISSING:{k}")
        src=owner.get("acceptance_source_artifact_path")
        h=owner.get("acceptance_source_sha256")
        if src and h:
            p=ROOT/src
            if not p.exists(): errors.append("OWNER_ACCEPTANCE_SOURCE_ARTIFACT_MISSING")
            else:
                actual=hashlib.sha256(p.read_bytes()).hexdigest()
                if actual.lower()!=h.lower(): errors.append("OWNER_ACCEPTANCE_SOURCE_HASH_MISMATCH")
        if not owner.get("accepted_scope") or not owner.get("accepted_limitations"):
            errors.append("OWNER_ACCEPTANCE_INCOMPLETE")
        owner_gate=not any(x.startswith("OWNER_ACCEPTANCE") for x in errors)

# DISCOVERY FREEZE: permit only documented LOW residual <=1%.
freeze_gate=False
if freeze:
    for k in ("freeze_id","canonical_sha","freeze_timestamp_utc"):
        if not freeze.get(k): errors.append(f"DISCOVERY_FREEZE_MISSING:{k}")
    if freeze.get("status")=="FROZEN":
        if freeze.get("unclassified_material_objects",0)!=0:
            errors.append("FREEZE_WITH_UNCLASSIFIED_MATERIAL_OBJECTS")
        low_pct=float(freeze.get("unclassified_low_residual_percent",0) or 0)
        max_pct=float(freeze.get("max_allowed_low_residual_percent",1.0) or 1.0)
        if low_pct>max_pct:
            errors.append(f"LOW_RESIDUAL_EXCEEDS_LIMIT:{low_pct}>{max_pct}")
        if low_pct>0 and not freeze.get("residual_items_path"):
            errors.append("LOW_RESIDUAL_WITHOUT_REGISTER")
        if freeze.get("unresolved_population_mismatches",0)!=0:
            errors.append("FREEZE_WITH_POPULATION_MISMATCH")
        freeze_gate=not any(x.startswith("FREEZE_") or x.startswith("LOW_RESIDUAL") for x in errors)

# EVIDENCE + SHA AT EXECUTION
e_by_id={}
for e in evidence:
    eid=e.get("evidence_id")
    if not eid:
        errors.append("EVIDENCE_WITHOUT_ID"); continue
    e_by_id[eid]=e
    for k in ("artifact_path","artifact_sha256","observed_repo_sha_at_execution","canonical_sha"):
        if not e.get(k): errors.append(f"{eid}:MISSING:{k}")
    ap=e.get("artifact_path"); ah=e.get("artifact_sha256")
    if ap and ah:
        p=ROOT/ap
        if not p.exists(): errors.append(f"{eid}:ARTIFACT_MISSING:{ap}")
        else:
            actual=hashlib.sha256(p.read_bytes()).hexdigest()
            if actual.lower()!=str(ah).lower(): errors.append(f"{eid}:HASH_MISMATCH")
    if e.get("observed_repo_sha_at_execution") and e.get("canonical_sha"):
        if e["observed_repo_sha_at_execution"]!=e["canonical_sha"]:
            errors.append(f"{eid}:EXECUTION_SHA_DIFFERS_FROM_CANONICAL")
    if freeze and e.get("observed_repo_sha_at_execution") and freeze.get("canonical_sha"):
        if e["observed_repo_sha_at_execution"]!=freeze["canonical_sha"]:
            errors.append(f"{eid}:EXECUTION_SHA_DIFFERS_FROM_FREEZE")

# PROCEDURES
required_proc=("procedure_id","requirement_id","universe_ids","domain","risk_level",
               "applicability_status","execution_class","objective","population_denominator",
               "method","minimum_evidence_class","acceptance_criteria","failure_criteria","status")
for p in procedures:
    pid=p.get("procedure_id","<NO_ID>")
    for k in required_proc:
        if k not in p or p.get(k) in ("",None,[]):
            errors.append(f"{pid}:MISSING:{k}")
    st=p.get("status")
    if st=="PASS":
        ids=p.get("evidence_ids") or []
        if not ids: errors.append(f"{pid}:PASS_WITHOUT_EVIDENCE")
        for eid in ids:
            if eid not in e_by_id: errors.append(f"{pid}:PASS_REFERENCES_MISSING_EVIDENCE:{eid}")
        if p.get("risk_level") in ("CRITICAL","HIGH") and p.get("population_denominator") in (None,"",0):
            errors.append(f"{pid}:CRITICAL_HIGH_WITHOUT_DENOMINATOR")
    if st=="BLOCKED" and not p.get("blocker_id"):
        errors.append(f"{pid}:BLOCKED_WITHOUT_BLOCKER_ID")
    if st=="NOT_APPLICABLE" and not p.get("na_reason"):
        errors.append(f"{pid}:NA_WITHOUT_REASON")

# RESUME SHA INTEGRITY
if resume and freeze and resume.get("canonical_sha") and freeze.get("canonical_sha"):
    if resume["canonical_sha"]!=freeze["canonical_sha"]:
        errors.append("RESUME_SHA_DIFFERS_FROM_DISCOVERY_FREEZE")

# Sharing controls
sharing=(owner or {}).get("third_party_sharing_permission","NO")
human=(owner or {}).get("human_review_status","NOT_REQUIRED_INTERNAL_ONLY")
if sharing=="NO" and (ROOT/"BLACKDARK_TECHNICAL_DUE_DILIGENCE_EXTERNAL_SUMMARY.md").exists():
    errors.append("EXTERNAL_SHORT_FORM_PROHIBITED_WHEN_SHARING_NO")
if sharing in ("YES","WITH_CONDITIONS") and human!="COMPLETE":
    warnings.append("PENDING_HUMAN_REVIEW_BEFORE_EXTERNAL_SHARING")

result={
  "owner_acceptance_gate":"PASS" if owner_gate else "FAIL",
  "discovery_freeze_gate":"PASS" if freeze_gate else "FAIL",
  "evidence_hash_and_sha_gate":"PASS" if not any(("ARTIFACT_" in e or "HASH_" in e or "EXECUTION_SHA_" in e or "PASS_WITHOUT_EVIDENCE" in e) for e in errors) else "FAIL",
  "errors":errors,
  "warnings":warnings,
  "GATE_STATUS":"PASS" if not errors else "FAIL",
  "INTERIM_REPORT_ALLOWED": True,
  "FINAL_REPORT_ALLOWED": False if errors else True
}
print(json.dumps(result,indent=2))
sys.exit(EXIT_OK if not errors else EXIT_GATE_FAIL)
