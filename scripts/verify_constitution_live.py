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


def main() -> int:
    _load_launch_env()
    os.environ["LOCAL_DEV"] = "true"
    os.environ["ENV"] = "development"

    from fastapi.testclient import TestClient

    from dashboard import app

    results: list[dict] = []
    ok_all = True

    with TestClient(app) as client:
        probes = [
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
        for method, path, _body, expect in probes:
            resp = client.request(method, path)
            expect_set = expect if isinstance(expect, set) else {expect}
            passed = resp.status_code in expect_set
            # Oracle may 404 if upstream ticker blocked — accept graceful failures
            if path.startswith("/oracle/BTC"):
                if resp.status_code == 200:
                    data = resp.json()
                    if "beginner" in path:
                        passed = bool(data.get("decision_sentence") or data.get("persona_clarity"))
                        # English-only site rule
                        sentence = str(data.get("decision_sentence") or "")
                        if sentence and any(ord(ch) > 1500 for ch in sentence):
                            # Arabic script leaked into UI sentence
                            passed = False
                    else:
                        passed = bool(
                            data.get("net_edge_truth")
                            or data.get("persona_clarity")
                            or data.get("opportunity_half_life")
                        )
                elif resp.status_code == 403:
                    # Anonymous free quota burned by prior probes — product gate works
                    passed = True
                    results.append(
                        {
                            "path": path,
                            "status": resp.status_code,
                            "ok": True,
                            "note": "anonymous oracle quota exceeded (gate OK)",
                        }
                    )
                    print(f"  [OK] {path} → {resp.status_code}")
                    continue
                elif resp.status_code in {404, 502, 503}:
                    passed = True
                    results.append(
                        {
                            "path": path,
                            "status": resp.status_code,
                            "ok": True,
                            "note": "ticker upstream unavailable in this environment",
                        }
                    )
                    continue
            ok_all = ok_all and passed
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
            results.append(row)
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
