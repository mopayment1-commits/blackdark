#!/usr/bin/env python3
"""Close REL-002 using live production multi-replica HA + signed load evidence."""

from __future__ import annotations

import json
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
LOAD_LOG = ROOT / "docs" / "LOAD_TEST_RUN_LOG.md"


def _fetch_json(url: str, *, retries: int = 6) -> dict:
    import time

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BLACKDARK-REL002-CLOSURE/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:  # nosec B310
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code in {429, 503} and attempt + 1 < retries:
                time.sleep(min(60, 5 * (2**attempt)))
                continue
            raise
        except Exception as exc:
            last_exc = exc
            if attempt + 1 < retries:
                time.sleep(min(30, 3 * (2**attempt)))
                continue
            raise
    raise last_exc or RuntimeError(f"fetch_failed: {url}")


def verify_production() -> dict:
    scale = _fetch_json(f"{PROD}/api/scale/readiness")
    viral = _fetch_json(f"{PROD}/api/viral/readiness")
    build = _fetch_json(f"{PROD}/api/build-info")

    parallel = scale.get("parallelism") or viral.get("parallelism") or {}
    workers = int(parallel.get("workers") or 0)
    replicas = int(parallel.get("replicas") or 0)
    parallelism = int(parallel.get("parallelism") or workers * replicas)

    if not scale.get("signed_load_evidence", {}).get("present"):
        raise SystemExit(f"signed_load_evidence_missing: {scale.get('signed_load_evidence')}")

    if not scale.get("ha_ready_codepath"):
        raise SystemExit(f"ha_ready_codepath_false: {scale}")

    if replicas < 2:
        raise SystemExit(f"multi_replica_not_met: replicas={replicas} (need Railway numReplicas≥2 + railway.json baked)")

    if parallelism < 4:
        raise SystemExit(f"multi_replica_parallelism_not_met: parallelism={parallelism} (need workers×replicas≥4)")

    multi = next((c for c in scale.get("checks", []) if c.get("id") == "multi_worker"), {})
    if not multi.get("ok"):
        raise SystemExit(f"multi_worker_check_failed: {multi}")

    if not viral.get("viral_production_approved"):
        raise SystemExit(f"viral_production_not_approved: {viral}")

    return {
        "verified_at": datetime.now(UTC).isoformat(),
        "production_url": PROD,
        "build_commit": build.get("git_commit"),
        "parallelism": parallel,
        "workers": workers,
        "replicas": replicas,
        "parallelism_total": parallelism,
        "scale": scale,
        "viral": viral,
        "evidence": [
            "production_railway_replicas_ge_2",
            "production_multi_worker_parallelism_ge_4",
            "signed_load_evidence_present",
            "ha_ready_codepath",
            "viral_production_approved",
            f"commit={str(build.get('git_commit', ''))[:12]}",
        ],
    }


def _append_load_log(evidence: dict) -> None:
    ts = evidence["verified_at"].replace("+00:00", "Z")
    block = f"""
### {ts} — SIGNED: REL-002 production multi-replica HA @ Railway

| Field | Value |
|-------|--------|
| Date (UTC) | {ts} |
| Control | **REL-002** — Signed multi-worker HA load evidence |
| Environment | **production** — `{PROD}` |
| Railway replicas | **{evidence['replicas']}** (`numReplicas` + `railway.json`) |
| Workers / parallelism | **{evidence['workers']} × {evidence['replicas']} = {evidence['parallelism_total']}** |
| Signed load (CAP-644) | `present=true` |
| HA codepath | `ha_ready_codepath=true` |
| Notes | **SIGNED: REL-002 closure.** Multi-replica production topology with signed CAP-644 load evidence. |
| Operator | cloud-agent REL-002 closure |

"""
    text = LOAD_LOG.read_text(encoding="utf-8")
    if "REL-002 production multi-replica HA @ Railway" in text:
        return
    marker = "## Status"
    if marker in text:
        text = text.replace(marker, block + marker, 1)
    else:
        text = text.rstrip() + "\n" + block
    LOAD_LOG.write_text(text, encoding="utf-8")


def _patch_row(row: dict, evidence: dict) -> None:
    note = (
        f"REL-002 PASS: Railway production {evidence['replicas']} replicas, "
        f"parallelism={evidence['parallelism_total']}, signed load evidence present."
    )
    detail = {
        "id": "REL-002",
        "status": "VERIFIED_COMPLETE",
        "evidence": evidence["evidence"],
        "note": note,
        "parallelism": evidence["parallelism"],
        "production_url": PROD,
        "signed_load_evidence": evidence["scale"].get("signed_load_evidence"),
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
        and r["id"] in {"CAP-644", "CAP-645", "SEC-006", "SEC-008", "REL-002", "COM-P0-EXT", "COM-KYC"}
    ]
    return {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "external_count": external_count,
        "p0_external_remaining": p0_external,
    }


def main() -> int:
    evidence = verify_production()
    _append_load_log(evidence)
    print(json.dumps(evidence, indent=2))

    rvm = json.loads(RVM_PATH.read_text(encoding="utf-8"))
    rows = rvm.get("requirements") or []
    for row in rows:
        if row.get("id") == "REL-002":
            _patch_row(row, evidence)
            break
    else:
        raise SystemExit("REL-002 row missing in RVM.json")

    counts = _recompute_summary(rows)
    rvm["p0_external_remaining"] = counts["p0_external_remaining"]
    rvm["generated_at"] = evidence["verified_at"]
    RVM_PATH.write_text(json.dumps(rvm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if SUMMARY_PATH.exists():
        summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        summary.update(counts)
        summary["generated_at"] = evidence["verified_at"]
        ctrl = summary.get("by_kind", {}).get("control", {})
        if ctrl.get("EXTERNAL_EVIDENCE_REQUIRED", 0) > 0:
            ctrl["EXTERNAL_EVIDENCE_REQUIRED"] = max(0, ctrl["EXTERNAL_EVIDENCE_REQUIRED"] - 1)
        ctrl["PASS"] = ctrl.get("PASS", 0) + 1
        summary.setdefault("by_kind", {})["control"] = ctrl
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if BASELINE_PATH.exists():
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        for row in baseline.get("requirements") or []:
            if row.get("id") == "REL-002":
                row["final_status"] = "PASS"
                row["verification_status"] = "PASS"
                row["validation_status"] = "PASS"
        BASELINE_PATH.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("REL-002 closed PASS in RVM artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
