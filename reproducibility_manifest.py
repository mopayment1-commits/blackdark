"""Reproducibility manifest — deterministic replay contract metadata."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_reproducibility_manifest(
    *,
    dataset_id: str,
    model_id: str | None = None,
    rule_id: str | None = None,
    seed: int = 0,
    evidence_class: str = "BACKTESTED",
    inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = {
        "dataset_id": dataset_id,
        "model_id": model_id,
        "rule_id": rule_id,
        "seed": seed,
        "evidence_class": evidence_class,
        "inputs": inputs or {},
        "created_at": datetime.now(UTC).isoformat(),
    }
    digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    return {"manifest_id": digest[:16], "digest_sha256": digest, **body}


def verify_manifest(manifest: dict[str, Any]) -> bool:
    payload = {k: v for k, v in manifest.items() if k not in ("manifest_id", "digest_sha256")}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return digest == manifest.get("digest_sha256")


def load_manifest(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
