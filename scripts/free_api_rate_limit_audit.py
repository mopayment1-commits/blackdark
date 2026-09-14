#!/usr/bin/env python3
"""Audit free-tier API rate limits vs projected user load (pre-launch)."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Documented vendor limits (conservative; verify against current ToS before launch).
SOURCES = [
    {
        "source": "CoinGecko",
        "tier": "free/demo",
        "documented_limit": "10-30 calls/min (demo); 500/min (Pro)",
        "blackdark_usage": "price fallback, market context, ingestion",
        "env_key": "COINGECKO_API_KEY",
        "cache_ttl_sec": int(os.getenv("COINGECKO_CACHE_TTL_SEC", "3600")),
        "calls_per_user_per_hour_est": 2,
        "upgrade_trigger_users": 50,
        "upgrade_path": "CoinGecko Pro API key or CoinMarketCap paid",
        "risk": "HIGH at >100 concurrent users without Pro key + cache",
    },
    {
        "source": "Binance Public API",
        "tier": "free",
        "documented_limit": "1200 weight/min per IP",
        "blackdark_usage": "tickers, WS streams, order book",
        "env_key": "BINANCE_WS_ENABLED",
        "ws_reduces_rest": True,
        "calls_per_user_per_hour_est": 12,
        "upgrade_trigger_users": 200,
        "upgrade_path": "Dedicated IP / VIP / colo feed",
        "risk": "MEDIUM — BINANCE_WS_ENABLED=true reduces REST pressure",
    },
    {
        "source": "Alternative.me Fear&Greed",
        "tier": "free",
        "documented_limit": "~1 req/min recommended",
        "blackdark_usage": "sentiment macro",
        "env_key": None,
        "cache_ttl_sec": 900,
        "calls_per_user_per_hour_est": 0.1,
        "upgrade_trigger_users": 500,
        "upgrade_path": "cache 15min+ (already default)",
        "risk": "LOW with cache",
    },
    {
        "source": "DefiLlama",
        "tier": "free",
        "documented_limit": "reasonable use",
        "blackdark_usage": "TVL, raises",
        "env_key": None,
        "calls_per_user_per_hour_est": 0.5,
        "upgrade_trigger_users": 100,
        "upgrade_path": "Pro API if commercial redistribution",
        "risk": "MEDIUM for B2B redistribution",
    },
    {
        "source": "Groq / Gemini / OpenRouter",
        "tier": "free tier",
        "documented_limit": "RPM/TPM per provider (varies)",
        "blackdark_usage": "oracle LLM chain",
        "env_key": "GROQ_API_KEY",
        "calls_per_user_per_hour_est": 3,
        "upgrade_trigger_users": 20,
        "upgrade_path": "Paid API keys before oracle-heavy launch",
        "risk": "HIGH for oracle-heavy UX",
    },
]


def _capacity_estimate(src: dict, projected_users: int) -> dict:
    calls_per_hour = projected_users * float(src.get("calls_per_user_per_hour_est") or 1)
    cache_ttl = src.get("cache_ttl_sec") or 300
    effective_calls_per_hour = calls_per_hour / max(1, 3600 / cache_ttl)
    return {
        "projected_users": projected_users,
        "raw_calls_per_hour_est": round(calls_per_hour, 1),
        "cache_adjusted_calls_per_hour_est": round(effective_calls_per_hour, 1),
        "within_free_tier": effective_calls_per_hour < 600,
    }


def main() -> int:
    projected_users = int(os.environ.get("LAUNCH_PROJECTED_USERS", "100"))
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "projected_concurrent_users": projected_users,
        "sources": [],
        "recommendations": [],
        "PASS_RATE_LIMIT_REVIEW": True,
        "upgrade_before_launch": [],
    }
    for src in SOURCES:
        row = {**src, "capacity": _capacity_estimate(src, projected_users)}
        report["sources"].append(row)
        if projected_users >= src["upgrade_trigger_users"] and src["risk"] in {"HIGH", "MEDIUM"}:
            rec = f"{src['source']}: consider {src['upgrade_path']} before {src['upgrade_trigger_users']}+ users"
            report["recommendations"].append(rec)
            if src["risk"] == "HIGH" and projected_users >= src["upgrade_trigger_users"]:
                report["PASS_RATE_LIMIT_REVIEW"] = False
                report["upgrade_before_launch"].append(src["source"])

    # CoinGecko Pro key downgrades risk
    if os.getenv("COINGECKO_API_KEY") or os.getenv("COINMARKETCAP_API_KEY"):
        report["PASS_RATE_LIMIT_REVIEW"] = True
        report["recommendations"].append("Paid price API key configured — CoinGecko/CMC risk mitigated")

    if os.getenv("BINANCE_WS_ENABLED", "true").lower() in {"1", "true", "yes"}:
        report["recommendations"].append("Binance WS enabled — REST rate pressure reduced")

    out = ROOT / "FREE_API_RATE_LIMIT_AUDIT.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["PASS_RATE_LIMIT_REVIEW"] else 1


if __name__ == "__main__":
    sys.exit(main())
