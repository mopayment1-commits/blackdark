#!/usr/bin/env python3
"""Live HTTP probes for Batch05 claimed free-tier external sources (lesson #165)."""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/BATCH05_FREE_TIER_LIVE_PROBE.json"

PROBE_TARGETS: list[dict[str, Any]] = [
    {
        "capability_id": 204,
        "source": "BscScan API (claimed attribution)",
        "url": "https://api.bscscan.com/api?module=stats&action=bnbsupply",
        "note": "Hero ingest_bscscan_204 uses static seed — probe documents live endpoint gate",
    },
    {
        "capability_id": 205,
        "source": "Glassnode (free tier claimed)",
        "url": "https://api.glassnode.com/v1/metrics/market/price_usd_close?a=BTC&i=24h",
        "note": "Hero ingest_glassnode_metrics_205 uses static seed metrics",
    },
    {
        "capability_id": 206,
        "source": "Uniswap subgraph GraphQL",
        "url": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        "method": "POST",
        "body": json.dumps({"query": "{ _meta { block { number } } }"}).encode(),
        "headers": {"Content-Type": "application/json"},
    },
    {
        "capability_id": 243,
        "source": "Bybit public ticker",
        "url": "https://api.bybit.com/v5/market/tickers?category=spot&symbol=BTCUSDT",
    },
    {
        "capability_id": 244,
        "source": "CoinTelegraph RSS",
        "url": "https://cointelegraph.com/rss",
    },
    {
        "capability_id": 246,
        "source": "Etherscan API",
        "url": "https://api.etherscan.io/api?module=stats&action=ethsupply",
        "note": "Hero list_etherscan_watchlist_246 is local watchlist — probe etherscan gate",
    },
]


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def http_probe(target: dict[str, Any]) -> dict[str, Any]:
    url = target["url"]
    method = target.get("method", "GET")
    headers = target.get("headers") or {}
    data = target.get("body")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    result: dict[str, Any] = {
        "capability_id": target["capability_id"],
        "source": target["source"],
        "url": url,
    }
    if target.get("note"):
        result["note"] = target["note"]
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read(512)
            result["http_status"] = resp.status
            result["body_preview"] = body.decode("utf-8", errors="replace")[:240]
            if result["http_status"] == 402:
                result["action"] = "NOT_COMPLETE + PAID_VENDOR_DESIGNED"
            elif result["http_status"] >= 400:
                result["action"] = "NOT_COMPLETE — live endpoint degraded"
            else:
                result["action"] = "reachable_free_or_anon — spine remains NOT_COMPLETE until PA gate"
    except urllib.error.HTTPError as exc:
        result["http_status"] = exc.code
        result["body_preview"] = exc.read(240).decode("utf-8", errors="replace")
        result["action"] = (
            "NOT_COMPLETE + PAID_VENDOR_DESIGNED" if exc.code == 402 else "NOT_COMPLETE — HTTP error"
        )
    except Exception as exc:
        result["http_status"] = None
        result["error"] = str(exc)
        result["action"] = "NOT_COMPLETE — probe failed"
    return result


def main() -> None:
    probes = [http_probe(t) for t in PROBE_TARGETS]
    paid = [p["capability_id"] for p in probes if p.get("http_status") == 402]
    doc = {
        "probed_at": datetime.now(UTC).isoformat(),
        "probe_commit": git_commit(),
        "summary": {
            "probed_count": len(probes),
            "paid_gate_402": paid,
            "all_remain_not_complete": True,
            "note": "Batch05 spine built NOT_COMPLETE; no PA until owner probe sign-off per #165 lesson",
        },
        "probes": probes,
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} — {len(probes)} probes, 402 gates: {paid}")


if __name__ == "__main__":
    main()
