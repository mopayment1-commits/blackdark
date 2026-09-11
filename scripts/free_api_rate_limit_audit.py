#!/usr/bin/env python3
"""Audit free-tier API rate limits vs projected user load (pre-launch)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Documented vendor limits (conservative; verify against current ToS before launch).
SOURCES = [
    {
        "source": "CoinGecko",
        "tier": "free/demo",
        "documented_limit": "10-30 calls/min (varies by endpoint)",
        "blackdark_usage": "price fallback, market context",
        "env_key": "COINMARKETCAP_API_KEY",
        "upgrade_trigger_users": 50,
        "upgrade_path": "CoinGecko Pro / CMC paid",
        "risk": "HIGH at >100 concurrent users without cache",
    },
    {
        "source": "Binance Public API",
        "tier": "free",
        "documented_limit": "1200 weight/min per IP",
        "blackdark_usage": "tickers, WS streams, order book",
        "env_key": "BINANCE_WS_ENABLED",
        "upgrade_trigger_users": 200,
        "upgrade_path": "Dedicated IP / VIP / colo feed",
        "risk": "MEDIUM — WS reduces REST pressure",
    },
    {
        "source": "Alternative.me Fear&Greed",
        "tier": "free",
        "documented_limit": "~1 req/min recommended",
        "blackdark_usage": "sentiment macro",
        "env_key": None,
        "upgrade_trigger_users": 10,
        "upgrade_path": "cache 15min+",
        "risk": "LOW with cache",
    },
    {
        "source": "DefiLlama",
        "tier": "free",
        "documented_limit": "reasonable use",
        "blackdark_usage": "TVL, raises",
        "env_key": None,
        "upgrade_trigger_users": 100,
        "upgrade_path": "Pro API if commercial",
        "risk": "MEDIUM for B2B redistribution",
    },
    {
        "source": "Groq / Gemini / OpenRouter",
        "tier": "free tier",
        "documented_limit": "RPM/TPM per provider",
        "blackdark_usage": "oracle LLM chain",
        "env_key": "GROQ_API_KEY",
        "upgrade_trigger_users": 20,
        "upgrade_path": "Paid API keys before launch",
        "risk": "HIGH for oracle-heavy UX",
    },
]


def main() -> int:
    projected_users = int(__import__("os").environ.get("LAUNCH_PROJECTED_USERS", "100"))
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "projected_concurrent_users": projected_users,
        "sources": SOURCES,
        "recommendations": [],
        "PASS_RATE_LIMIT_REVIEW": True,
    }
    for src in SOURCES:
        if projected_users >= src["upgrade_trigger_users"] and src["risk"] in {"HIGH", "MEDIUM"}:
            report["recommendations"].append(
                f"{src['source']}: consider {src['upgrade_path']} before {src['upgrade_trigger_users']}+ users"
            )
            if src["risk"] == "HIGH" and projected_users >= src["upgrade_trigger_users"]:
                report["PASS_RATE_LIMIT_REVIEW"] = False

    out = ROOT / "FREE_API_RATE_LIMIT_AUDIT.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["PASS_RATE_LIMIT_REVIEW"] else 1


if __name__ == "__main__":
    sys.exit(main())
