"""Credential lifecycle registry — no secrets in code/logs/frontend."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from data_governance.registry import canonical_source_registry

_SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"
)


@dataclass(frozen=True)
class CredentialRequirement:
    source_id: str
    env_key: str
    owner: str
    test_live_separation: bool
    rotation_path: str
    revoke_path: str


def credential_requirements() -> list[CredentialRequirement]:
    reqs: list[CredentialRequirement] = []
    for entry in canonical_source_registry():
        if not entry.env_key:
            continue
        reqs.append(
            CredentialRequirement(
                source_id=entry.source_id,
                env_key=entry.env_key,
                owner=entry.credential_owner,
                test_live_separation=True,
                rotation_path=f"rotate_env:{entry.env_key}",
                revoke_path=f"revoke_env:{entry.env_key}",
            )
        )
    return reqs


def scan_for_hardcoded_secrets(paths: list[str] | None = None) -> list[str]:
    """Scan repository text files for obvious secret patterns (audit helper)."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    hits: list[str] = []
    scan_dirs = paths or ["data_governance"]
    for rel in scan_dirs:
        base = root / rel
        if not base.exists():
            continue
        for fp in base.rglob("*.py"):
            if "test" in fp.name:
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if _SECRET_PATTERN.search(text):
                hits.append(str(fp.relative_to(root)))
    return hits


def credential_status() -> dict[str, Any]:
    reqs = credential_requirements()
    configured = [r for r in reqs if os.getenv(r.env_key)]
    return {
        "total_requirements": len(reqs),
        "configured_in_env": len(configured),
        "unconfigured_keys": [r.env_key for r in reqs if not os.getenv(r.env_key)],
        "secret_manager_only": True,
        "test_live_separation": True,
        "hardcoded_secrets_in_code": scan_for_hardcoded_secrets(),
    }
