#!/usr/bin/env python3
"""Local verification orchestrator — runs batch proof scripts; NOT a CI gate.

This script coordinates local proof generation for batch01/batch02 audits.
It does NOT replace independent CI gates (critical, gate-full, SonarCloud).
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ORCHESTRATED_SCRIPTS: list[dict[str, str]] = [
    {
        "script": "audit_official_batch01_rtm.py",
        "verifies": "RTM audit: 50/50 official batch01 IDs classified PRODUCTION-ALIGNED vs NOT_COMPLETE",
    },
    {
        "script": "audit_official_batch02_rtm.py",
        "verifies": "RTM audit: 50/50 official batch02 IDs including OVERLAP_BATCH01 routing",
    },
    {
        "script": "verify_batch01_production.py",
        "verifies": "Production spine execution for all batch01 IDs (module import + execute)",
    },
    {
        "script": "verify_batch01_http_all50.py",
        "verifies": "HTTP GET /api/cap646/{id} for IDs 1–50 with status 200",
    },
    {
        "script": "verify_batch01_http_11_fixed.py",
        "verifies": "HTTP regression subset: 11 formerly NOT_COMPLETE batch01 IDs",
    },
    {
        "script": "verify_entitlement_gateway_proof.py",
        "verifies": "Entitlement gateway path for batch01 sample IDs (no skip_entitlement)",
    },
    {
        "script": "verify_official_batch02_production.py",
        "verifies": "HTTP GET /api/cap646/{id} for IDs 51–100 with status 200",
    },
    {
        "script": "verify_entitlement_batch02_gateway_proof.py",
        "verifies": "Entitlement gateway path for batch02 sample IDs (no skip_entitlement)",
    },
]


def _owner_approval_ok() -> tuple[bool, str]:
    """FFIEC separation-of-duties: require signed owner token when approval flag set."""
    token = os.environ.get("INSTITUTIONAL_OWNER_APPROVAL_TOKEN", "")
    secret = os.environ.get("INSTITUTIONAL_OWNER_APPROVAL_SECRET", "")
    if not secret:
        return False, "INSTITUTIONAL_OWNER_APPROVAL_SECRET not set"
    if not token:
        return False, "INSTITUTIONAL_OWNER_APPROVAL_TOKEN not set"
    expected = hmac.new(secret.encode(), b"INSTITUTIONAL_CLOSED", hashlib.sha256).hexdigest()
    if not hmac.compare_digest(token, expected):
        return False, "owner approval token mismatch"
    return True, "owner approval token valid"


def _run(script: str, *, attempts: int = 2) -> dict:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT))
    env.setdefault("SERVICE_BUS_LOCAL", "true")
    last: dict | None = None
    for attempt in range(1, attempts + 1):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script)],
            capture_output=True,
            text=True,
            cwd=ROOT,
            env=env,
            timeout=600,
        )
        last = {
            "script": script,
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr[-2000:] if proc.stderr else "",
            "attempt": attempt,
        }
        if proc.returncode == 0:
            return last
    assert last is not None
    return last


async def _bootstrap_db() -> None:
    """Fresh CI runners need sqlite schema before RTM/HTTP audits touch database-backed caps."""
    import database

    await database.init_db()


async def main() -> None:
    await _bootstrap_db()
    closure_request = "--closure-request" in sys.argv
    if closure_request:
        approval_ok, approval_reason = _owner_approval_ok()
        if not approval_ok:
            print(json.dumps({"owner_approval_required": True, "reason": approval_reason}, indent=2))
            raise SystemExit(
                "Governance gate: owner approval token required for closure declaration "
                "(INSTITUTIONAL_OWNER_APPROVAL_SECRET + INSTITUTIONAL_OWNER_APPROVAL_TOKEN)"
            )

    results = [_run(entry["script"]) for entry in ORCHESTRATED_SCRIPTS]
    failed = [r for r in results if r["exit_code"] != 0]

    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "orchestrator": "scripts/run_batch_verification_orchestrator.py",
        "note": "Local proof orchestrator only — not an institutional CI gate",
        "closure_status": "PENDING_CLOSURE",
        "batches": {
            "batch01": {"scope": "1–50", "status": "PENDING_CLOSURE"},
            "batch02": {"scope": "51–100", "status": "PENDING_CLOSURE"},
        },
        "orchestrated_scripts": [
            {**entry, **next(r for r in results if r["script"] == entry["script"])}
            for entry in ORCHESTRATED_SCRIPTS
        ],
        "all_verified": len(failed) == 0,
        "explicit_owner_approval_required": True,
    }
    path = ROOT / "docs/BATCH_VERIFICATION_ORCHESTRATOR_RESULT.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Back-compat path — always PENDING_CLOSURE until owner approves
    legacy = ROOT / "docs/INSTITUTIONAL_CLOSURE_FINAL.json"
    legacy.write_text(
        json.dumps(
            {
                "verified_at": out["verified_at"],
                "closure_status": "PENDING_CLOSURE",
                "rejection": "CLOSURE-REJECT-02",
                "owner_approval_required": True,
                "merge_does_not_imply_closure": True,
                "orchestrator_result": "docs/BATCH_VERIFICATION_ORCHESTRATOR_RESULT.json",
                "scripts": results,
                "all_verified": out["all_verified"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"all_verified": out["all_verified"], "failed": [f["script"] for f in failed]}, indent=2))
    print(f"Wrote {path}")
    if failed:
        for item in failed:
            print(f"--- FAILURE: {item['script']} (exit {item['exit_code']}) ---", file=sys.stderr)
            if item.get("stdout"):
                print(item["stdout"], file=sys.stderr)
            if item.get("stderr"):
                print(item["stderr"], file=sys.stderr)
        raise SystemExit(f"Orchestrator failed: {[f['script'] for f in failed]}")


if __name__ == "__main__":
    asyncio.run(main())
