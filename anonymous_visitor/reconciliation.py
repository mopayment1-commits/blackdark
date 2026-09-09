"""Reconciliation artifact SHA semantics — separate from traceability matrix."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def reconciliation_semantics_valid(*, artifact_path: str | Path | None = None) -> dict[str, Any]:
    head = _git_head()
    rec_path = Path(artifact_path or "docs/ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_FINAL_RECONCILIATION.json")
    if not rec_path.is_file():
        return {"valid": False, "reason": "missing_artifact", "head": head}
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    impl = rec.get("implementation_sha")
    material = rec.get("material_sha")
    evidence_from = rec.get("evidence_generated_from_sha") or rec.get("reconciliation_generated_from_sha")
    artifact = rec.get("artifact_commit_sha") or rec.get("reconciliation_sha")
    stale: list[str] = []
    if impl and impl != head:
        stale.append("implementation_sha")
    if material and material != head:
        stale.append("material_sha")
    if evidence_from and evidence_from != head:
        stale.append("evidence_generated_from_sha")
    self_ref = bool(
        impl
        and artifact
        and impl == artifact
        and material
        and evidence_from
        and len({x for x in (impl, artifact, material, evidence_from) if x}) == 1
    )
    semantics_valid = bool(impl) and impl == head and not stale and not self_ref
    return {
        "valid": semantics_valid,
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
