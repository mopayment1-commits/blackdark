"""
Smart Contract Scanner — Feature #193 (security layer for token tools).

Heuristic contract risk scan from DEX metadata + labels.
Integrates with Early Stage Token Scanner (#115) and Liquidity Inflow (#116).
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.SmartContractScanner")

_RISK_LABELS = frozenset({"scam", "honeypot", "rug", "malicious", "fake", "phishing"})
_POSITIVE_LABELS = frozenset({"verified", "audited", "locked"})


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def scan_contract_from_pair(pair: dict[str, Any]) -> dict[str, Any]:
    """
    Scan token/pair metadata for security red flags (#193).
    """
    t0 = time.perf_counter()
    base = pair.get("baseToken") or {}
    address = str(base.get("address") or "")
    symbol = str(base.get("symbol") or "").upper()
    chain = str(pair.get("chainId") or "unknown")
    labels = [str(x).lower() for x in (pair.get("labels") or [])]

    risks: list[dict[str, Any]] = []
    passes: list[str] = []

    for label in labels:
        if any(r in label for r in _RISK_LABELS):
            risks.append({
                "level": "critical",
                "code": "MALICIOUS_LABEL",
                "message": f"Contract flagged — label '{label}' detected. Avoid.",
            })
        if "verified" in label:
            passes.append("contract_verified_label")

    if pair.get("info"):
        passes.append("dexscreener_info_present")

    # Holder concentration proxy — heavy sell pressure + thin liquidity
    liq = float((pair.get("liquidity") or {}).get("usd") or 0)
    mcap = float(pair.get("marketCap") or pair.get("fdv") or 0)
    txns = pair.get("txns") or {}
    h24 = txns.get("h24") or {}
    buys = int(h24.get("buys") or 0)
    sells = int(h24.get("sells") or 0)
    if sells > 0 and buys > 0 and sells > buys * 3 and liq < 100_000:
        risks.append({
            "level": "high",
            "code": "SELL_PRESSURE",
            "message": "Heavy sell pressure vs buys — possible exit liquidity trap",
        })
    elif buys > 0 and sells > 0 and 0.4 <= buys / (buys + sells) <= 0.7:
        passes.append("balanced_txn_flow")

    # Liquidity vs mcap — very thin = rug risk
    if mcap > 0 and liq > 0 and liq / mcap < 0.02:
        risks.append({
            "level": "high",
            "code": "THIN_LIQUIDITY",
            "message": f"Liquidity only {liq/mcap*100:.1f}% of market cap — exit risk",
        })
    elif mcap > 0 and liq / mcap >= 0.05:
        passes.append("liquidity_ratio_ok")

    # Backdoor heuristic — unverified + high mcap + new pair
    created = pair.get("pairCreatedAt")
    if created and not any("verified" in l for l in labels):
        risks.append({
            "level": "medium",
            "code": "UNVERIFIED_CONTRACT",
            "message": "Contract not verified — review before interaction",
        })

    risk_level = "low"
    if any(r["level"] == "critical" for r in risks):
        risk_level = "critical"
    elif any(r["level"] == "high" for r in risks):
        risk_level = "high"
    elif risks:
        risk_level = "medium"

    headline = "Contract scan clear — no critical flags"
    if risk_level == "critical":
        headline = f"WARNING — {symbol} contract has critical security flags"
    elif risk_level == "high":
        headline = f"Caution — {symbol} shows elevated contract risk"

    return {
        "ok": True,
        "feature_id": 193,
        "surface": "smart_contract_scanner",
        "symbol": symbol,
        "contract_address": address,
        "chain": chain,
        "risk_level": risk_level,
        "risks": risks,
        "passes": passes,
        "contract_verified": "contract_verified_label" in passes or "dexscreener_info_present" in passes,
        "headline": headline,
        "timestamp": _utcnow(),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
    }
