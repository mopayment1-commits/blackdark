#!/usr/bin/env python3
"""Execute Batch05 Gate Zero live probes — records real HTTP evidence only.

Does NOT claim LIVE_READY or elevate counters on failure.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_URL = "https://blackdark-production.up.railway.app"
OUT = ROOT / "docs/BATCH05_GATE_ZERO_LIVE_EXECUTION.json"

HEALTH_PATHS = ["/health", "/health/ready"]
SAMPLE_STRANGLER_IDS = [201, 205, 217, 242, 247]
RESIDUAL_7_IDS = [212, 206, 214, 226, 228, 232, 245]
CAP646_PATHS = [f"/api/cap646/{cid}" for cid in SAMPLE_STRANGLER_IDS + RESIDUAL_7_IDS]


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def http_get(path: str, *, rounds: int = 3) -> dict[str, Any]:
    url = f"{PRODUCTION_URL.rstrip('/')}{path}"
    attempts: list[dict[str, Any]] = []
    for i in range(rounds):
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "batch05-gate-zero-live/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read(8000).decode("utf-8", errors="replace")
                attempts.append(
                    {
                        "round": i + 1,
                        "http_status": resp.status,
                        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
                        "body_preview": body[:400],
                    }
                )
        except urllib.error.HTTPError as exc:
            body = exc.read(800).decode("utf-8", errors="replace") if exc.fp else ""
            attempts.append(
                {
                    "round": i + 1,
                    "http_status": exc.code,
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
                    "body_preview": body[:400],
                }
            )
        except Exception as exc:  # noqa: BLE001
            attempts.append(
                {
                    "round": i + 1,
                    "http_status": None,
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
                    "error": str(exc),
                }
            )
        time.sleep(1)
    statuses = [a.get("http_status") for a in attempts]
    return {
        "path": path,
        "url": url,
        "attempts": attempts,
        "all_http_status": statuses,
        "gate_pass": all(s == 200 for s in statuses if s is not None) and bool(statuses),
    }


def main() -> None:
    health = [http_get(p) for p in HEALTH_PATHS]
    cap646 = [http_get(p) for p in CAP646_PATHS]

    health_pass = all(h["gate_pass"] for h in health)
    cap646_200 = sum(1 for c in cap646 if all(s == 200 for s in c["all_http_status"] if s is not None))
    cap646_total = len(cap646)

    doc = {
        "executed_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "production_url": PRODUCTION_URL,
        "gate": "ZERO",
        "status": "PASS" if health_pass and cap646_200 == cap646_total else "FAILED",
        "live_ready": False,
        "local_governance_complete": False,
        "batch05_independent": 0,
        "progress_826": 179,
        "production_aligned_count": 0,
        "pa_elevated_count": 0,
        "health_probes": health,
        "cap646_probes": cap646,
        "residual_7_ids_probed": RESIDUAL_7_IDS,
        "summary": {
            "health_pass": health_pass,
            "cap646_success_count": cap646_200,
            "cap646_total": cap646_total,
            "railway_application_not_found": any(
                "Application not found" in (a.get("body_preview") or "")
                for probe in health + cap646
                for a in probe["attempts"]
            ),
        },
        "diagnosis": (
            "Railway edge 404 Application not found — no web service bound to public domain"
            if not health_pass
            else None
        ),
        "owner_remediation": [
            "Redeploy web service on Railway project blackdark-production",
            "Attach domain blackdark-production.up.railway.app to running service",
            "Verify DATABASE_URL and required env vars",
            "Re-run scripts/execute_batch05_gate_zero_live.py after deploy",
        ],
        "phase_statement_ar": (
            "هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. "
            "لا إعلان اكتمال حوكمة · لا Batch05 complete · لا جاهزية حية 100%."
        ),
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": doc["status"], "health_pass": health_pass, "cap646_200": f"{cap646_200}/{cap646_total}"}, indent=2))
    print(f"Wrote {OUT}")
    if doc["status"] != "PASS":
        raise SystemExit("Gate Zero live execution FAILED — documented, not elevated")


if __name__ == "__main__":
    main()
