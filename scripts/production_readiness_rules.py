"""Production Readiness — thin orchestrator over 161 governing requirements."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from production_readiness_checks import (  # noqa: E402
    CheckContext,
    RequirementResult,
    aggregate_counters,
    build_traceability_matrix,
    engineering_closure_verdict,
    evaluate_all,
    integrity_closure_verdict,
    load_json,
)
from production_readiness_governing_catalog import governing_requirements  # noqa: E402

SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"

ENVIRONMENTS_DISCOVERED = [
    {"id": "local", "purpose": "Developer workstation / uvicorn", "runtime": "Python 3.12 + uvicorn"},
    {"id": "test", "purpose": "pytest isolated SQLite / CI Postgres service", "runtime": "pytest + TestClient"},
    {"id": "ci", "purpose": "GitHub Actions critical gate", "runtime": "ubuntu-latest + postgres:16 service"},
    {"id": "staging", "purpose": "Pre-prod rehearsal", "runtime": "Docker / Railway preview"},
    {"id": "production", "purpose": "Strict institutional topology", "runtime": "Railway / Docker / k8s"},
    {"id": "worker", "purpose": "Background ingestion / scheduled jobs", "runtime": "SERVICE_MODE=worker"},
    {"id": "scheduled", "purpose": "Cron / GitHub schedule security scans", "deployment": ".github/workflows/security.yml schedule"},
    {"id": "b2b_api", "purpose": "Institutional API + websocket feed", "runtime": "FastAPI routers"},
]


def git_sha(cwd: Path | None = None) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd or ROOT, text=True).strip()
    except Exception:
        return "unknown"


def git_dirty_files(cwd: Path | None = None) -> list[str]:
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], cwd=cwd or ROOT, text=True)
        return [ln[3:].strip() for ln in out.splitlines() if ln.strip()]
    except Exception:
        return []


def load_ssot() -> dict[str, Any]:
    return load_json(SSOT_PATH)


def evaluate_requirements(ctx: CheckContext | None = None) -> list[RequirementResult]:
    return evaluate_all(ctx)


def closure_verdict(counters: dict[str, Any]) -> str:
    integrity = integrity_closure_verdict(counters)
    if integrity == "PRODUCTION_READINESS_FINAL_INTEGRITY_VERIFIED":
        eng = engineering_closure_verdict(counters)
        if eng.endswith("WITH_GENUINE_EXTERNAL_GATES"):
            return "CAPABILITY_PRODUCTION_READINESS_ENGINEERING_CLOSED_WITH_GENUINE_EXTERNAL_GATES"
        return eng
    return integrity


# Backward compatibility for tests importing REQUIREMENTS length via governing catalog
REQUIREMENTS = governing_requirements()
