#!/usr/bin/env python3
"""Close CAP-649 using live production dbt run evidence; refresh RVM artifacts."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

PROD = "https://blackdark-production.up.railway.app"
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RVM_PATH = ROOT / "docs" / "rvm" / "RVM.json"
SUMMARY_PATH = ROOT / "docs" / "rvm" / "RVM_SUMMARY.json"
BASELINE_PATH = ROOT / "docs" / "rvm" / "REQUIREMENTS_BASELINE.json"


def _fetch_json(url: str, *, method: str = "GET", headers: dict | None = None, retries: int = 4) -> dict:
    import time

    hdrs = {"User-Agent": "BLACKDARK-CAP649-CLOSURE/1.0", **(headers or {})}
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, method=method, headers=hdrs)
            with urllib.request.urlopen(req, timeout=180) as resp:  # nosec B310
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            last_exc = exc
            body = exc.read().decode() if exc.fp else ""
            if exc.code in {429, 503} and attempt + 1 < retries:
                time.sleep(min(30, 3 * (2**attempt)))
                continue
            raise RuntimeError(f"http_{exc.code}: {body[:500]}") from exc
        except Exception as exc:
            last_exc = exc
            if attempt + 1 < retries:
                time.sleep(min(20, 2 * (2**attempt)))
                continue
            raise
    raise last_exc or RuntimeError(f"fetch_failed: {url}")


def verify_production() -> dict:
    admin_key = os.getenv("ADMIN_API_KEY", "").strip()
    closure_token = os.getenv("CAP649_CLOSURE_TOKEN", "").strip()
    headers: dict[str, str] = {}
    if admin_key:
        headers["X-Admin-Key"] = admin_key
    if closure_token:
        headers["X-CAP649-Closure-Token"] = closure_token

    status = _fetch_json(f"{PROD}/api/warehouse/dbt/status")
    dbt = status.get("dbt") or {}
    if not dbt.get("configured"):
        raise SystemExit(f"dbt_not_configured_on_production: {dbt}")
    if not dbt.get("bigquery_export_ready"):
        raise SystemExit(f"bigquery_export_prerequisite_not_ready: {dbt}")

    if not status.get("run_ready"):
        if admin_key or closure_token:
            try:
                _fetch_json(f"{PROD}/api/warehouse/dbt/run", method="POST", headers=headers)
                status = _fetch_json(f"{PROD}/api/warehouse/dbt/status")
            except RuntimeError as exc:
                if not str(exc).startswith("http_403"):
                    raise

        if not status.get("run_ready"):
            import time

            deadline = time.time() + int(os.getenv("CAP649_DBT_WAIT_SEC", "900"))
            while time.time() < deadline and not status.get("run_ready"):
                time.sleep(20)
                status = _fetch_json(f"{PROD}/api/warehouse/dbt/status")

    if not status.get("run_ready"):
        raise SystemExit(f"production_dbt_run_not_verified: {status}")

    if status.get("gate") != "CAP-649":
        raise SystemExit(f"cap649_gate_mismatch: {status.get('gate')}")

    last_run = status.get("last_run") or {}
    if int(last_run.get("mart_rows_verified") or 0) <= 0:
        raise SystemExit(f"cap649_mart_rows_not_verified: {last_run}")

    build = _fetch_json(f"{PROD}/api/build-info")
    return {
        "verified_at": datetime.now(UTC).isoformat(),
        "production_url": PROD,
        "build_commit": build.get("git_commit"),
        "dbt": dbt,
        "last_run": last_run,
        "cap649": {
            "success": True,
            "surface": status.get("surface"),
            "run_ready": status.get("run_ready"),
            "gate": status.get("gate"),
        },
        "evidence": [
            "production_dbt_configured",
            "production_bigquery_export_ready",
            "production_dbt_run_verified",
            "cap649_warehouse_status_ready",
            f"run_id={last_run.get('run_id')}",
            f"mart_rows_verified={last_run.get('mart_rows_verified')}",
            f"mart_table={last_run.get('mart_table_fqn')}",
            f"models_run={last_run.get('models_run')}",
            f"commit={str(build.get('git_commit', ''))[:12]}",
        ],
    }


def _patch_row(row: dict, evidence: dict) -> None:
    note = (
        f"dbt run live on {PROD}; mart={evidence['last_run'].get('mart_table_fqn')}; "
        f"mart_rows_verified={evidence['last_run'].get('mart_rows_verified')}."
    )
    detail = {
        "id": 649,
        "capability": "dbt Connector",
        "status": "VERIFIED_COMPLETE",
        "verdict": "VERIFIED_COMPLETE",
        "classification": "VERIFIED_COMPLETE",
        "dbt": evidence["dbt"],
        "last_run": evidence["last_run"],
        "note": note,
    }
    row["verification_status"] = "PASS"
    row["validation_status"] = "PASS"
    row["final_status"] = "PASS"
    row["implementation_evidence"] = evidence["evidence"]
    row["runtime_evidence"] = evidence["evidence"]
    row["verification_detail"] = detail
    row["validation_detail"] = detail
    row["external_step"] = ""
    row["notes"] = evidence["verified_at"]


def _recompute_summary(rows: list[dict]) -> dict:
    pass_count = sum(1 for r in rows if r.get("final_status") == "PASS")
    fail_count = sum(1 for r in rows if r.get("final_status") == "FAIL")
    external_count = sum(1 for r in rows if r.get("final_status") == "EXTERNAL_EVIDENCE_REQUIRED")
    p0_external = [
        r["id"]
        for r in rows
        if r.get("final_status") == "EXTERNAL_EVIDENCE_REQUIRED"
        and r["id"] in {"CAP-644", "CAP-645", "SEC-006", "SEC-008", "REL-002", "COM-P0-EXT", "COM-KYC", "CAP-658"}
    ]
    return {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "external_count": external_count,
        "p0_external_remaining": p0_external,
    }


def main() -> int:
    evidence = verify_production()
    print(json.dumps(evidence, indent=2))

    rvm = json.loads(RVM_PATH.read_text(encoding="utf-8"))
    rows = rvm.get("requirements") or []
    for row in rows:
        if row.get("id") == "CAP-649":
            _patch_row(row, evidence)
            break
    else:
        raise SystemExit("CAP-649 row missing in RVM.json")

    counts = _recompute_summary(rows)
    rvm["p0_external_remaining"] = counts["p0_external_remaining"]
    rvm["generated_at"] = evidence["verified_at"]
    RVM_PATH.write_text(json.dumps(rvm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if SUMMARY_PATH.exists():
        summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        summary.update(counts)
        summary["generated_at"] = evidence["verified_at"]
        cap = summary.get("by_kind", {}).get("capability", {})
        if cap.get("EXTERNAL_EVIDENCE_REQUIRED", 0) > 0:
            cap["EXTERNAL_EVIDENCE_REQUIRED"] = max(0, cap["EXTERNAL_EVIDENCE_REQUIRED"] - 1)
        cap["PASS"] = cap.get("PASS", 0) + 1
        summary.setdefault("by_kind", {})["capability"] = cap
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if BASELINE_PATH.exists():
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        for row in baseline.get("requirements") or []:
            if row.get("id") == "CAP-649":
                row["final_status"] = "PASS"
                row["verification_status"] = "PASS"
                row["validation_status"] = "PASS"
        BASELINE_PATH.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CAP-649 closed PASS in RVM artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
