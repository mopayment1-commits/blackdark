"""Reconciliation artifact SHA semantics — separate from traceability matrix."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _git_head(ref: str = "HEAD") -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", ref], text=True).strip()
    except Exception:
        return "unknown"


def _commit_touched_files(ref: str = "HEAD") -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", ref],
            text=True,
        )
        return [ln for ln in out.splitlines() if ln.strip()]
    except Exception:
        return []


def head_is_evidence_only_commit(ref: str = "HEAD") -> bool:
    files = _commit_touched_files(ref)
    if not files:
        return False
    allowed = {
        "docs/ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_FINAL_RECONCILIATION.json",
        "docs/ANONYMOUS_VISITOR_STRICT_EVIDENCE_RECONCILIATION.json",
        "docs/ANONYMOUS_BROWSER_E2E_EVIDENCE.json",
    }
    return set(files).issubset(allowed)


def reconciliation_semantics_valid(*, artifact_path: str | Path | None = None) -> dict[str, Any]:
    head = _git_head()
    evidence_only = head_is_evidence_only_commit()
    certified_head = _git_head("HEAD~1") if evidence_only else head
    rec_path = Path(artifact_path or "docs/ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_FINAL_RECONCILIATION.json")
    if not rec_path.is_file():
        return {
            "valid": False,
            "reason": "missing_artifact",
            "head": head,
            "RECONCILIATION_SHA_SEMANTICS_VALID": False,
        }
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    impl = rec.get("implementation_sha")
    material = rec.get("material_sha")
    evidence_from = rec.get("evidence_generated_from_sha") or rec.get("reconciliation_generated_from_sha")
    artifact = rec.get("artifact_commit_sha") or rec.get("reconciliation_sha")
    stale: list[str] = []
    expected_impl = certified_head
    if impl and impl != expected_impl:
        stale.append("implementation_sha")
    if material and material != expected_impl:
        stale.append("material_sha")
    if evidence_from and evidence_from != expected_impl:
        stale.append("evidence_generated_from_sha")
    self_ref = bool(
        impl
        and artifact
        and impl == artifact
        and material
        and evidence_from
        and len({x for x in (impl, artifact, material, evidence_from) if x}) == 1
    )
    semantics_valid = bool(impl) and not stale and not self_ref
    return {
        "valid": semantics_valid,
        "CURRENT_HEAD": head,
        "IMPLEMENTATION_SHA": impl,
        "EVIDENCE_GENERATED_FROM_SHA": evidence_from,
        "ARTIFACT_COMMIT_SHA": artifact,
        "HEAD_IS_EVIDENCE_ONLY_COMMIT": evidence_only,
        "CERTIFIED_CODE_SHA": expected_impl,
        "head": head,
        "implementation_sha": impl,
        "evidence_generated_from_sha": evidence_from,
        "artifact_commit_sha": artifact,
        "stale_fields": stale,
        "self_referential": self_ref,
        "RECONCILIATION_SHA_SEMANTICS_VALID": semantics_valid,
        "SELF_REFERENTIAL_COMMIT_HASH": self_ref,
        "STALE_RECONCILIATION_FIELDS": stale,
    }
