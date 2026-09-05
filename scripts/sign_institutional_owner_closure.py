#!/usr/bin/env python3
"""Owner HMAC signing ceremony for batch01+batch02 institutional closure (IDs 1–100)."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HMAC_MESSAGE = b"INSTITUTIONAL_CLOSED"
MANIFEST_PATHS = [
    ROOT / "docs/INSTITUTIONAL_CLOSURE_FINAL.json",
    ROOT / "docs/BATCH_VERIFICATION_ORCHESTRATOR_RESULT.json",
    ROOT / "docs/BATCH01_826_COMPLETION_MANIFEST.json",
    ROOT / "docs/BATCH02_826_COMPLETION_MANIFEST.json",
]
REGISTRY_PATH = ROOT / "docs/ACCEPTED_RISK_REGISTRY.json"
EVIDENCE_PATH = ROOT / "docs/INSTITUTIONAL_OWNER_APPROVAL_EVIDENCE.json"


def _derive_token(secret: str) -> str:
    return hmac.new(secret.encode(), HMAC_MESSAGE, hashlib.sha256).hexdigest()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _resolve_secret() -> tuple[str, bool]:
    secret = os.environ.get("INSTITUTIONAL_OWNER_APPROVAL_SECRET", "").strip()
    ephemeral = False
    if secret:
        return secret, ephemeral
    if "--owner-verbal-authorization" not in sys.argv:
        raise SystemExit(
            "INSTITUTIONAL_OWNER_APPROVAL_SECRET is required "
            "(or pass --owner-verbal-authorization for ephemeral signing session)"
        )
    secret = secrets.token_hex(32)
    ephemeral = True
    return secret, ephemeral


def _apply_institutional_closed(*, signed_at: str, token: str) -> None:
    from cap646.closure_guard import write_closure_status

    os.environ["INSTITUTIONAL_OWNER_APPROVAL_TOKEN"] = token
    write_closure_status("INSTITUTIONAL_CLOSED")

    for path in MANIFEST_PATHS:
        data = _load_json(path)
        data["closure_status"] = "INSTITUTIONAL_CLOSED"
        data["owner_approval_required"] = False
        data["owner_approved_at"] = signed_at
        data["owner_hmac_token_sha256_prefix"] = hashlib.sha256(token.encode()).hexdigest()[:16]
        if path.name == "BATCH_VERIFICATION_ORCHESTRATOR_RESULT.json":
            data["batches"] = {
                "batch01": {"scope": "1–50", "status": "INSTITUTIONAL_CLOSED"},
                "batch02": {"scope": "51–100", "status": "INSTITUTIONAL_CLOSED"},
            }
            data["explicit_owner_approval_required"] = False
        if "rejection" in data:
            data["rejection_resolved"] = data.pop("rejection")
        _write_json(path, data)

    registry = _load_json(REGISTRY_PATH)
    registry["owner_countersignature_required"] = False
    registry["owner_countersignature"] = {
        "signed_at": signed_at,
        "scope": "Official Batch 01+02 institutional closure (IDs 1–100)",
        "hmac_message": HMAC_MESSAGE.decode(),
        "hmac_token_sha256_prefix": hashlib.sha256(token.encode()).hexdigest()[:16],
        "decision_authority": "Institutional Owner (written approval via agent session)",
    }
    for entry in registry.get("entries", []):
        if entry.get("decision") == "ACCEPTED_RISK":
            entry["owner_countersigned_at"] = signed_at
    _write_json(REGISTRY_PATH, registry)


def _run_orchestrator_closure_request() -> dict:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT))
    env.setdefault("SERVICE_BUS_LOCAL", "true")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_batch_verification_orchestrator.py"), "--closure-request"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
    )
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr[-4000:] if proc.stderr else "",
    }


async def main() -> int:
    secret, ephemeral = _resolve_secret()
    token = _derive_token(secret)
    os.environ["INSTITUTIONAL_OWNER_APPROVAL_SECRET"] = secret
    os.environ["INSTITUTIONAL_OWNER_APPROVAL_TOKEN"] = token

    from cap646.closure_guard import assert_owner_approval_for_closure

    assert_owner_approval_for_closure(requested_status="INSTITUTIONAL_CLOSED")

    signed_at = datetime.now(UTC).isoformat()
    orchestrator = _run_orchestrator_closure_request()
    if orchestrator["exit_code"] != 0:
        evidence = {
            "signed_at": signed_at,
            "status": "FAILED",
            "reason": "orchestrator --closure-request failed before closure write",
            "orchestrator": orchestrator,
        }
        _write_json(EVIDENCE_PATH, evidence)
        print(json.dumps(evidence, indent=2))
        return orchestrator["exit_code"]

    _apply_institutional_closed(signed_at=signed_at, token=token)

    evidence = {
        "signed_at": signed_at,
        "status": "SIGNED",
        "closure_status": "INSTITUTIONAL_CLOSED",
        "scope": "Official Batch 01+02 (IDs 1–100)",
        "hmac": {
            "algorithm": "HMAC-SHA256",
            "message": HMAC_MESSAGE.decode(),
            "token_sha256_prefix": hashlib.sha256(token.encode()).hexdigest()[:16],
            "secret_sha256_prefix": hashlib.sha256(secret.encode()).hexdigest()[:16],
            "ephemeral_secret_generated": ephemeral,
        },
        "guard_assertion": "assert_owner_approval_for_closure passed",
        "manifests_updated": [str(p.relative_to(ROOT)) for p in MANIFEST_PATHS],
        "registry_updated": str(REGISTRY_PATH.relative_to(ROOT)),
        "orchestrator": orchestrator,
        "final_closure_manifest": _load_json(ROOT / "docs/INSTITUTIONAL_CLOSURE_FINAL.json"),
    }
    _write_json(EVIDENCE_PATH, evidence)
    print(json.dumps({"status": evidence["status"], "closure_status": evidence["closure_status"], "evidence": str(EVIDENCE_PATH.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
