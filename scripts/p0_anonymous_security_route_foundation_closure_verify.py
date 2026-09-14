#!/usr/bin/env python3
"""P0_ANONYMOUS_SECURITY_AND_ROUTE_FOUNDATION closure verification."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

os_env = __import__("os")
os_env.environ.setdefault("ENV", "development")
os_env.environ.setdefault("SESSION_TOKEN_PEPPER", "test-pepper-p0-closure")

ARTIFACT = Path("/opt/cursor/artifacts/ANONYMOUS_P0_SECURITY_ROUTE_FOUNDATION_CLOSURE_EVIDENCE.json")
REPO_ARTIFACT = REPO / "ANONYMOUS_P0_SECURITY_ROUTE_FOUNDATION_CLOSURE_EVIDENCE.json"

from anonymous_route_foundation import (  # noqa: E402
    GOVERNING_SPEC,
    PRIVATE_BY_DEFAULT,
    ProductAuthState,
    build_route_inventory,
    is_anonymous_route_allowed,
    response_contains_private_data,
    summarize_inventory,
)
from dashboard import app  # noqa: E402

TEST_FILE = "tests/test_p0_anonymous_route_foundation.py"


def _run_pytest() -> dict[str, Any]:
    cmd = [sys.executable, "-m", "pytest", TEST_FILE, "-q", "--tb=no"]
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    tail = proc.stdout.splitlines()[-3:] if proc.stdout else []
    passed_line = next((line for line in proc.stdout.splitlines() if "passed" in line), "")
    return {
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "summary": passed_line,
        "tail": tail,
    }


def _probe_no_cookie(client: Any, method: str, path: str) -> int:
    if "{" in path:
        return -1
    if method == "GET":
        return client.get(path).status_code
    if method == "HEAD":
        return client.head(path).status_code
    if method == "POST":
        return client.post(path, json={}).status_code
    return -1


def main() -> int:
    from starlette.testclient import TestClient

    inventory = build_route_inventory(app)
    summary = summarize_inventory(inventory)

    accidental_public: list[str] = []
    private_exposure: list[str] = []
    client_only_boundaries: list[str] = []

    probe_private_paths = (
        "/api/platform/keys/status",
        "/api/user/profile",
        "/api/privacy/export",
        "/api/billing/subscription",
        "/api/cap646/47",
        "/api/v1/data/status",
        "/api/journal",
        "/dashboard",
        "/profile",
        "/admin/launch",
        "/openapi.json",
        "/graphql",
    )
    probe_public_paths = (
        "/",
        "/health/live",
        "/api/status",
        "/api/security/status",
        "/login",
        "/oracle-accuracy",
    )

    with TestClient(app) as client:
        for row in inventory:
            path = row["PATH"]
            method = row["METHOD"]
            if path in probe_public_paths and method == "GET":
                response = client.get(path)
                row["ACTUAL_NO_COOKIE_RESPONSE"] = response.status_code
                if response.status_code == 200 and response_contains_private_data(response.text):
                    private_exposure.append(path)
            elif path in probe_private_paths and method == "GET":
                response = client.get(path)
                row["ACTUAL_NO_COOKIE_RESPONSE"] = response.status_code
                if response.status_code in {200, 201, 204}:
                    accidental_public.append(f"{method} {path}")
                if response.status_code == 200 and response_contains_private_data(response.text):
                    private_exposure.append(path)

        for path in ("/api/auth/me", "/api/user/profile", "/api/billing/subscription"):
            response = client.get(path)
            if response.status_code == 200:
                client_only_boundaries.append(path)

    pytest_result = _run_pytest()
    regression_failures = 0 if pytest_result["passed"] else 1

    locally_buildable_remaining = 0
    if not PRIVATE_BY_DEFAULT:
        locally_buildable_remaining += 1
    if accidental_public:
        locally_buildable_remaining += len(accidental_public)
    if private_exposure:
        locally_buildable_remaining += len(private_exposure)
    if client_only_boundaries:
        locally_buildable_remaining += len(client_only_boundaries)
    if regression_failures:
        locally_buildable_remaining += regression_failures

    p0_closed = (
        len(accidental_public) == 0
        and len(private_exposure) == 0
        and len(client_only_boundaries) == 0
        and locally_buildable_remaining == 0
        and regression_failures == 0
    )
    verdict = "P0_CLOSED" if p0_closed else "P0_NOT_CLOSED"

    implementation_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()

    report = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "phase": "P0_ANONYMOUS_SECURITY_AND_ROUTE_FOUNDATION",
        "governing_spec": GOVERNING_SPEC,
        "implementation_sha": implementation_sha,
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip(),
        "canonical_owners": {
            "allowlist": "anonymous_route_foundation.py",
            "enforcement_middleware": "dashboard.anonymous_route_enforcement_middleware",
            "auth_guards": "security_auth.py",
            "public_docs_filter": "public_api_docs.py",
        },
        "product_auth_state": ProductAuthState.ANONYMOUS.value,
        "private_by_default": PRIVATE_BY_DEFAULT,
        "summary": {
            "ROUTES_INVENTORIED": summary["ROUTES_INVENTORIED"],
            "PUBLIC_EXPLICIT": summary["PUBLIC_EXPLICIT"],
            "PRIVATE_PROTECTED": summary["PRIVATE_PROTECTED"],
            "ACCIDENTAL_PUBLIC_ROUTES": len(accidental_public),
            "PRIVATE_DATA_EXPOSURE_PATHS": len(private_exposure),
            "CLIENT_ONLY_AUTH_BOUNDARIES": len(client_only_boundaries),
            "LOCALLY_BUILDABLE_REMAINING": locally_buildable_remaining,
            "REGRESSION_FAILURES": regression_failures,
            "final_verdict": verdict,
        },
        "accidental_public_routes": accidental_public,
        "private_data_exposure_paths": private_exposure,
        "client_only_auth_boundaries": client_only_boundaries,
        "route_inventory": inventory,
        "runtime_proofs": {
            "p0_pytest": pytest_result,
        },
        "verification_command": "python3 scripts/p0_anonymous_security_route_foundation_closure_verify.py",
        "final_verdict": verdict,
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPO_ARTIFACT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "PHASE": "P0_ANONYMOUS_SECURITY_AND_ROUTE_FOUNDATION",
                **report["summary"],
            },
            indent=2,
        )
    )
    return 0 if verdict == "P0_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
