#!/usr/bin/env python3
"""Close CAP-644 using live production multi-worker load evidence; refresh RVM artifacts."""

from __future__ import annotations

import json
import re
import subprocess
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
SIGNED_JSON = ROOT / "docs" / "evidence" / "signed_load_production_cap644.json"
CAPACITY_PATH = ROOT / "data" / "institutional_assurance" / "signed_capacity.json"


def _fetch_json(url: str, *, retries: int = 6) -> dict:
    import time

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BLACKDARK-CAP644-CLOSURE/1.0"})
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


def _run_load_test() -> tuple[int, str]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "load_test_concurrent.py"),
        "--base",
        PROD,
        "--workers",
        "15",
        "--requests",
        "80",
        "--require-viral-approved",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def _parse_live_metrics(output: str) -> dict[str, float]:
    match = re.search(
        r"live:\s+p50=([\d.]+)ms\s+p95=([\d.]+)ms\s+max=([\d.]+)ms\s+ok=\d+\s+controlled=\d+\s+errors=(\d+)/(\d+)",
        output,
    )
    if not match:
        raise SystemExit(f"load_test_parse_failed: could not parse live row from:\n{output[-2000:]}")
    p50, p95, p99, errors, total = match.groups()
    return {
        "p50_ms": float(p50),
        "p95_ms": float(p95),
        "p99_ms": float(p99),
        "error_rate": float(errors) / max(float(total), 1.0),
        "requests": int(total),
    }


def verify_production() -> dict:
    scale = _fetch_json(f"{PROD}/api/scale/readiness")
    viral = _fetch_json(f"{PROD}/api/viral/readiness")
    build = _fetch_json(f"{PROD}/api/build-info")

    parallel = scale.get("parallelism") or viral.get("parallelism") or {}
    workers = int(parallel.get("workers") or 0)
    replicas = int(parallel.get("replicas") or 0)
    parallelism = int(parallel.get("parallelism") or workers * replicas)

    if parallelism < 2:
        raise SystemExit(f"multi_worker_not_met: parallelism={parallelism}")

    multi = next((c for c in scale.get("checks", []) if c.get("id") == "multi_worker"), {})
    if not multi.get("ok"):
        raise SystemExit(f"multi_worker_check_failed: {multi}")

    if not viral.get("viral_production_approved"):
        raise SystemExit(f"viral_production_not_approved: {viral}")

    if scale.get("database") != "postgresql":
        raise SystemExit(f"postgres_required: database={scale.get('database')}")

    redis_check = next((c for c in scale.get("checks", []) if c.get("id") == "redis_shared"), {})
    if not redis_check.get("ok"):
        raise SystemExit(f"redis_required: {redis_check}")

    code, load_out = _run_load_test()
    if code != 0:
        raise SystemExit(f"load_test_failed exit={code}\n{load_out}")

    metrics = _parse_live_metrics(load_out)
    if metrics["error_rate"] > 0.01:
        raise SystemExit(f"load_test_error_rate_too_high: {metrics}")

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
        "load_test": {
            "script": "scripts/load_test_concurrent.py",
            "workers": 15,
            "requests_per_endpoint": 80,
            "exit_code": code,
            "metrics": metrics,
            "output_excerpt": load_out.strip()[-2500:],
        },
        "evidence": [
            "production_multi_worker_parallelism_ge_2",
            "production_postgres_redis_ha_codepath",
            "signed_multi_worker_load_test_production",
            "viral_production_approved",
            f"commit={str(build.get('git_commit', ''))[:12]}",
        ],
    }


def _publish_signed_capacity(evidence: dict) -> dict:
    from institutional_assurance import publish_signed_capacity, verify_signed_capacity

    metrics = evidence["load_test"]["metrics"]
    row = publish_signed_capacity(
        environment="production",
        workers=int(evidence["parallelism_total"]),
        postgres=True,
        redis=True,
        requests=int(metrics["requests"]),
        p50_ms=float(metrics["p50_ms"]),
        p95_ms=float(metrics["p95_ms"]),
        p99_ms=float(metrics["p99_ms"]),
        error_rate=float(metrics["error_rate"]),
        operator="cloud-agent-cap644-closure",
        notes=(
            f"SIGNED: CAP-644 production load on {PROD}; "
            f"parallelism={evidence['parallelism_total']} "
            f"({evidence['workers']}x{evidence['replicas']}); "
            f"viral_production_approved=true"
        ),
    )
    if not verify_signed_capacity(row):
        raise SystemExit("signed_capacity_signature_invalid")
    return row


def _write_signed_json(row: dict, evidence: dict) -> None:
    SIGNED_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **row,
        "gate": "CAP-644",
        "production_url": PROD,
        "parallelism": evidence["parallelism"],
        "load_test": evidence["load_test"],
        "verified_at": evidence["verified_at"],
    }
    SIGNED_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    CAPACITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    CAPACITY_PATH.write_text(json.dumps(row, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_load_log(evidence: dict, signed_row: dict) -> None:
    metrics = evidence["load_test"]["metrics"]
    ts = evidence["verified_at"].replace("+00:00", "Z")
    block = f"""
### {ts} — SIGNED: production multi-worker HA load @ Railway (CAP-644 closure)

| Field | Value |
|-------|--------|
| Date (UTC) | {ts} |
| Commit / tip | `{str(evidence.get('build_commit', ''))[:12]}` |
| Environment | **production** — `{PROD}` (Railway `blackdark`) |
| Workers / replicas | **{evidence['workers']} × {evidence['replicas']}** (`parallelism={evidence['parallelism_total']}`) |
| Postgres | yes (`{evidence['scale'].get('database')}`) |
| Redis | yes (`login_rate_limit_backend={evidence['scale'].get('login_rate_limit_backend')}`) |
| HA / viral gates | `ha_ready_codepath={evidence['scale'].get('ha_ready_codepath')}`, `viral_production_approved={evidence['viral'].get('viral_production_approved')}` |
| Script | `scripts/load_test_concurrent.py --workers 15 --requests 80 --require-viral-approved` |
| Concurrency | 15 client threads; 80 requests/endpoint |
| Latency (live) | p50/p95/p99={metrics['p50_ms']}/{metrics['p95_ms']}/{metrics['p99_ms']}ms |
| Error rate | **{metrics['error_rate']:.4f}** (hard errors on scored endpoints) |
| Signed capacity id | `{signed_row.get('capacity_id')}` |
| Signature | `{signed_row.get('signature', '')[:16]}…` |
| Notes | **SIGNED: CAP-644 production topology.** Multi-worker (`parallelism≥2`) with Postgres+Redis. Does not claim 1k–10k global capacity without `WEB_REPLICAS≥2` staging. |
| Operator | cloud-agent CAP-644 closure |

"""
    text = LOAD_LOG.read_text(encoding="utf-8")
    if "SIGNED: production multi-worker HA load @ Railway (CAP-644 closure)" in text:
        return
    marker = "## Status"
    if marker in text:
        text = text.replace(marker, block + marker, 1)
    else:
        text = text.rstrip() + "\n" + block
    LOAD_LOG.write_text(text, encoding="utf-8")


def _patch_row(row: dict, evidence: dict, signed_row: dict) -> None:
    note = (
        f"SIGNED multi-worker load on {PROD}; parallelism={evidence['parallelism_total']} "
        f"({evidence['workers']} workers × {evidence['replicas']} replicas); "
        f"Postgres+Redis; viral_production_approved=true."
    )
    detail = {
        "id": 644,
        "capability": "Capacity / Load Evidence",
        "status": "VERIFIED_COMPLETE",
        "verdict": "VERIFIED_COMPLETE",
        "checks": {
            "backend": True,
            "signed_load_evidence": True,
            "multi_worker": True,
            "note": note,
        },
        "signed_load_evidence": {
            "present": True,
            "artifact": str(SIGNED_JSON.relative_to(ROOT)),
            "capacity_id": signed_row.get("capacity_id"),
            "signature": signed_row.get("signature"),
        },
        "parallelism": evidence["parallelism"],
        "production_url": PROD,
    }
    row["verification_status"] = "PASS"
    row["validation_status"] = "PASS"
    row["final_status"] = "PASS"
    row["implementation_evidence"] = evidence["evidence"]
    row["runtime_evidence"] = evidence["evidence"]
    row["verification_detail"] = detail
    row["validation_detail"] = {
        **detail,
        "capability_id": 644,
        "surface": "capacity_load_evidence",
        "report": evidence["scale"],
        "success": True,
    }
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
    signed_row = _publish_signed_capacity(evidence)
    _write_signed_json(signed_row, evidence)
    _append_load_log(evidence, signed_row)
    print(json.dumps({**evidence, "signed_capacity": signed_row}, indent=2))

    rvm = json.loads(RVM_PATH.read_text(encoding="utf-8"))
    rows = rvm.get("requirements") or []
    for row in rows:
        if row.get("id") == "CAP-644":
            _patch_row(row, evidence, signed_row)
            break
    else:
        raise SystemExit("CAP-644 row missing in RVM.json")

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
            if row.get("id") == "CAP-644":
                row["final_status"] = "PASS"
                row["verification_status"] = "PASS"
                row["validation_status"] = "PASS"
        BASELINE_PATH.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CAP-644 closed PASS in RVM artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
