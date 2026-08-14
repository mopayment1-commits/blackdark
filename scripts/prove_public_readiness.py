"""Prove public direct-use HTTP readiness. Never claims institutional COMPLETE."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "dd" / "BLACKDARK_PUBLIC_READINESS_EVIDENCE.json"


def main() -> int:
    from fastapi.testclient import TestClient

    from dashboard import app
    from public_readiness import PUBLIC_FLOOR_PCT, probe_with_client

    client = TestClient(app, follow_redirects=False)
    out = probe_with_client(client)
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    score = out.get("score") or {}
    pct = float(score.get("public_direct_use_percent") or 0)
    fails = score.get("failures") or []
    print(
        json.dumps(
            {
                "public_direct_use_percent": pct,
                "floor_percent": PUBLIC_FLOOR_PCT,
                "meets_public_floor": score.get("meets_public_floor"),
                "counted_pass": score.get("counted_pass"),
                "counted_total": score.get("counted_total"),
                "failures": fails,
                "institutional_verdict": "NOT_COMPLETE",
                "product_complete": False,
                "evidence": str(EVIDENCE),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    if pct < PUBLIC_FLOOR_PCT:
        print(f"PUBLIC FLOOR MISS: {pct} < {PUBLIC_FLOOR_PCT}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
