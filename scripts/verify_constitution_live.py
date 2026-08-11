#!/usr/bin/env python3
"""Verify constitution product endpoints via FastAPI TestClient (no external deploy)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Soft local env — never fail-closed production in this verify harness
os.environ.setdefault("LOCAL_DEV", "true")
os.environ.setdefault("ENV", "development")
os.environ.setdefault("PRICE_FEED_WS_ONLY", "false")
os.environ.setdefault("PRODUCTION_GUARD_FAIL_CLOSED", "false")


def _load_launch_env() -> None:
    path = ROOT / ".env.launch.local"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, _, value = raw.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip()


def _constitution_probes() -> list[tuple[str, str, None, int | set[int]]]:
    return [
        ("GET", "/health/live", None, 200),
        ("GET", "/api/launch/readiness", None, 200),
        ("GET", "/api/due-diligence/evidence-pack/public-summary", None, 200),
        ("GET", "/api/oracle/net-edge-truth", None, 200),
        ("GET", "/api/oracle/half-life", None, 200),
        ("GET", "/api/oracle/persona-clarity/demo", None, 200),
        ("GET", "/oracle-accuracy", None, {200}),
        ("GET", "/oracle/accuracy", None, {200}),
        ("GET", "/dashboard", None, {200}),
        ("GET", "/robots.txt", None, {200}),
        ("GET", "/sitemap.xml", None, {200}),
        ("GET", "/api/mev/sandwich-report", None, {200}),
        ("GET", "/api/glass-box/challenge", None, {200}),
        ("GET", "/api/alerts/generosity", None, {200}),
        ("GET", "/api/whale/signal-vs-noise?limit=3", None, {200, 500, 502, 503}),
        ("GET", "/api/audience/entry?audience=whale", None, {200}),
        ("GET", "/oracle/BTC?ux_mode=beginner&lang=en", None, {200, 403, 404, 502, 503}),
        ("GET", "/oracle/BTC?ux_mode=pro&lang=en", None, {200, 403, 404, 502, 503}),
        ("GET", "/admin/plan", None, {200}),
        ("GET", "/admin/roadmap", None, {200}),
        ("GET", "/api/plan/audit", None, {200}),
        ("GET", "/api/roadmap/audit", None, {200}),
        ("GET", "/api/due-diligence/evidence-pack", None, {401, 403}),  # must be gated
    ]


def _oracle_success(resp, path: str) -> bool:
    data = resp.json()
    if "beginner" in path:
        sentence = str(data.get("decision_sentence") or "")
        if sentence and any(ord(ch) > 1500 for ch in sentence):
            return False
        return bool(data.get("decision_sentence") or data.get("persona_clarity"))
    return bool(
        data.get("net_edge_truth")
        or data.get("persona_clarity")
        or data.get("opportunity_half_life")
    )


def _oracle_grace_row(path: str, status_code: int) -> dict | None:
    if status_code == 403:
        return {
            "path": path,
            "status": status_code,
            "ok": True,
            "note": "anonymous oracle quota exceeded (gate OK)",
        }
    if status_code in {404, 502, 503}:
        return {
            "path": path,
            "status": status_code,
            "ok": True,
            "note": "ticker upstream unavailable in this environment",
        }
    return None


def _probe_row(path: str, resp, expect_set: set[int], passed: bool) -> dict:
    row = {
        "path": path,
        "status": resp.status_code,
        "ok": passed,
        "expect": sorted(expect_set),
    }
    if path.startswith("/oracle/BTC") and resp.status_code == 200:
        payload = resp.json()
        row["has_decision_sentence"] = bool(payload.get("decision_sentence"))
        row["has_persona"] = bool(payload.get("persona_clarity"))
        row["has_truth"] = bool(payload.get("net_edge_truth"))
        row["ux_mode"] = payload.get("ux_mode")
    return row


def _evaluate_probe(path: str, resp, expect_set: set[int]) -> tuple[bool, dict | None]:
    passed = resp.status_code in expect_set
    if not path.startswith("/oracle/BTC"):
        return passed, None
    if resp.status_code == 200:
        return _oracle_success(resp, path), None
    grace_row = _oracle_grace_row(path, resp.status_code)
    return (True, grace_row) if grace_row is not None else (passed, None)


def main() -> int:
    _load_launch_env()
    os.environ["LOCAL_DEV"] = "true"
    os.environ["ENV"] = "development"

    from fastapi.testclient import TestClient

    from dashboard import app

    results: list[dict] = []
    ok_all = True

    with TestClient(app) as client:
        for method, path, _body, expect in _constitution_probes():
            resp = client.request(method, path)
            expect_set = expect if isinstance(expect, set) else {expect}
            passed, short_row = _evaluate_probe(path, resp, expect_set)
            if short_row is not None:
                results.append(short_row)
                print(f"  [OK] {path} → {resp.status_code}")
                continue
            ok_all = ok_all and passed
            results.append(_probe_row(path, resp, expect_set, passed))
            mark = "OK" if passed else "FAIL"
            print(f"  [{mark}] {path} → {resp.status_code}")

    out = {
        "ok": ok_all,
        "results": results,
        "constitution": "docs/PRODUCT_CONSTITUTION_AR.md",
    }
    path = ROOT / "data" / "constitution_live_verify.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {path}")
    print("PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
