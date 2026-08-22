#!/usr/bin/env python3
"""Close CAP-658 using live production BigQuery export evidence; refresh RVM artifacts."""

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

    hdrs = {"User-Agent": "BLACKDARK-CAP658-CLOSURE/1.0", **(headers or {})}
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, method=method, headers=hdrs)
            with urllib.request.urlopen(req, timeout=120) as resp:  # nosec B310
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
    closure_token = os.getenv("CAP658_CLOSURE_TOKEN", "").strip()
    headers: dict[str, str] = {}
    if admin_key:
        headers["X-Admin-Key"] = admin_key
    if closure_token:
        headers["X-CAP658-Closure-Token"] = closure_token

    status = _fetch_json(f"{PROD}/api/warehouse/bigquery/status")
    bq = status.get("bigquery") or {}
    if not bq.get("configured"):
        raise SystemExit(f"bigquery_not_configured_on_production: {bq}")

    if not status.get("export_ready"):
        if admin_key or closure_token:
            try:
                _fetch_json(
                    f"{PROD}/api/warehouse/bigquery/export?limit=500",
                    method="POST",
                    headers=headers,
                )
                status = _fetch_json(f"{PROD}/api/warehouse/bigquery/status")
            except RuntimeError as exc:
                if not str(exc).startswith("http_403"):
                    raise

        if not status.get("export_ready"):
            import time

            deadline = time.time() + int(os.getenv("CAP658_EXPORT_WAIT_SEC", "720"))
            while time.time() < deadline and not status.get("export_ready"):
                time.sleep(15)
                status = _fetch_json(f"{PROD}/api/warehouse/bigquery/status")

    if not status.get("export_ready"):
        raise SystemExit(f"production_bigquery_export_not_verified: {status}")

    if status.get("gate") != "CAP-658":
        raise SystemExit(f"cap658_gate_mismatch: {status.get('gate')}")

    last_export = status.get("last_export") or {}
    if int(last_export.get("rows_verified") or 0) <= 0:
        raise SystemExit(f"cap658_rows_not_verified: {last_export}")

    build = _fetch_json(f"{PROD}/api/build-info")
    return {
        "verified_at": datetime.now(UTC).isoformat(),
        "production_url": PROD,
        "build_commit": build.get("git_commit"),
        "bigquery": bq,
        "last_export": last_export,
        "cap658": {
            "success": True,
            "surface": status.get("surface"),
            "export_ready": status.get("export_ready"),
            "gate": status.get("gate"),
        },
        "evidence": [
            "production_bigquery_configured",
            "production_bigquery_export_verified",
            "cap658_warehouse_status_ready",
            f"export_id={last_export.get('export_id')}",
            f"rows_verified={last_export.get('rows_verified')}",
            f"table={last_export.get('table_fqn')}",
            f"manifest_sha256={last_export.get('manifest_sha256')}",
            f"commit={str(build.get('git_commit', ''))[:12]}",
        ],
    }


def _patch_row(row: dict, evidence: dict) -> None:
    note = (
        f"BigQuery export live on {PROD}; table={evidence['last_export'].get('table_fqn')}; "
        f"rows_verified={evidence['last_export'].get('rows_verified')}."
    )
    detail = {
        "id": 658,
        "capability": "White-Label Embedded Analytics",
        "status": "VERIFIED_COMPLETE",
        "verdict": "VERIFIED_COMPLETE",
        "classification": "VERIFIED_COMPLETE",
        "bigquery": evidence["bigquery"],
        "last_export": evidence["last_export"],
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
        if row.get("id") == "CAP-658":
            _patch_row(row, evidence)
            break
    else:
        raise SystemExit("CAP-658 row missing in RVM.json")

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
            if row.get("id") == "CAP-658":
                row["final_status"] = "PASS"
                row["verification_status"] = "PASS"
                row["validation_status"] = "PASS"
        BASELINE_PATH.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CAP-658 closed PASS in RVM artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
