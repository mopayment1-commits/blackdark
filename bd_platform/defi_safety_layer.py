"""
DeFi Safety Layer — Feature #160 (Sprint 2).

Passive smart contract risk scanner — time-bomb / malicious logic flags.
NOT 100% protection — risk flags only. Integrates with #193 LP safety.

Displayed before any protocol interaction: owner mint, selfdestruct, pause, etc.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.DeFiSafety")

_FEATURE_ID = 160
_SCANNER_VERSION = "1.0.0"

# Opcode / pattern risk signatures (heuristic — not exhaustive audit)
_RISK_PATTERNS: list[dict[str, Any]] = [
    {
        "id": "owner_selfdestruct",
        "severity": "critical",
        "keywords": ("selfdestruct", "suicide", "destroy"),
        "headline": "Contract may contain selfDestruct callable by owner",
    },
    {
        "id": "unlimited_mint",
        "severity": "critical",
        "keywords": ("mint(", "mint unlimited", "_mint", "totalSupply"),
        "headline": "Unlimited or owner-controlled mint function detected",
    },
    {
        "id": "pause_mechanism",
        "severity": "high",
        "keywords": ("pause", "paused", "whennotpaused", "emergencystop"),
        "headline": "Pausable contract — owner can halt trading",
    },
    {
        "id": "proxy_upgrade",
        "severity": "high",
        "keywords": ("upgradeTo", "implementation", "transparentupgradeableproxy", "delegatecall"),
        "headline": "Upgradeable proxy — logic can change without notice",
    },
    {
        "id": "time_lock_missing",
        "severity": "medium",
        "keywords": ("timelock", "delay"),
        "headline": "No timelock detected — instant owner actions possible",
        "inverse": True,
    },
    {
        "id": "hidden_fee",
        "severity": "high",
        "keywords": ("setfee", "settax", "feepercent", "maxfee"),
        "headline": "Owner-adjustable fee/tax function detected",
    },
    {
        "id": "blacklist",
        "severity": "medium",
        "keywords": ("blacklist", "isblacklisted", "blocklist"),
        "headline": "Address blacklist function — selective trading restriction",
    },
]

_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
_NO_PROTECTION_DISCLAIMER = (
    "Risk flags only — not a security audit or 100% protection guarantee. "
    "Always verify contracts independently before interacting."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _scan_text_for_flags(text: str) -> list[dict[str, Any]]:
    lower = text.lower()
    flags: list[dict[str, Any]] = []
    for pattern in _RISK_PATTERNS:
        if pattern.get("inverse"):
            if not any(kw in lower for kw in pattern["keywords"]):
                flags.append({
                    "flag_id": pattern["id"],
                    "severity": pattern["severity"],
                    "headline": pattern["headline"],
                    "evidence": "timelock_keywords_absent",
                })
            continue
        hits = [kw for kw in pattern["keywords"] if kw in lower]
        if hits:
            flags.append({
                "flag_id": pattern["id"],
                "severity": pattern["severity"],
                "headline": pattern["headline"],
                "evidence": f"matched:{','.join(hits[:3])}",
            })
    return flags


async def _fetch_contract_context(contract_address: str, chain: str) -> dict[str, Any]:
    """Gather passive context from DEX pair metadata and optional explorer."""
    context: dict[str, Any] = {"sources": [], "text_blob": ""}

    try:
        from bd_platform.onchain_hub import dexscreener_pairs

        # Try to find pair with this contract
        dex = await dexscreener_pairs("ETH")
        for pair in dex.get("pairs") or []:
            base = str((pair.get("baseToken") or {}).get("address") or "").lower()
            quote = str((pair.get("quoteToken") or {}).get("address") or "").lower()
            target = contract_address.lower()
            if target in {base, quote}:
                labels = json_dumps_safe(pair)
                context["text_blob"] += labels
                context["sources"].append("dexscreener_pair_metadata")
                context["pair"] = {
                    "dex": pair.get("dexId"),
                    "liquidity_usd": (pair.get("liquidity") or {}).get("usd"),
                    "pair_address": pair.get("pairAddress"),
                }
                break
    except Exception:
        logger.debug("dexscreener context failed", exc_info=True)

    # Etherscan-free public API (no key required for contract ABI fragment)
    if chain.lower() in {"ethereum", "eth"} and _ADDRESS_RE.match(contract_address):
        try:
            import aiohttp

            url = "https://api.etherscan.io/api"
            params = {
                "module": "contract",
                "action": "getabi",
                "address": contract_address,
            }
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        abi = str(data.get("result") or "")
                        if abi and abi != "Contract source code not verified":
                            context["text_blob"] += abi
                            context["sources"].append("etherscan_abi_public")
        except Exception:
            logger.debug("etherscan ABI fetch failed", exc_info=True)

    return context


def json_dumps_safe(obj: Any) -> str:
    import json

    try:
        return json.dumps(obj, default=str).lower()
    except Exception:
        return str(obj).lower()


async def scan_contract_risk(
    contract_address: str,
    *,
    chain: str = "ethereum",
    protocol_name: str = "",
) -> dict[str, Any]:
    """Passive DeFi safety scan — risk flags only."""
    t0 = time.perf_counter()

    if not _ADDRESS_RE.match(contract_address):
        elapsed = (time.perf_counter() - t0) * 1000
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "invalid_contract_address",
            "disclaimer": _NO_PROTECTION_DISCLAIMER,
            "sla_met": elapsed <= 2000,
            "timestamp": _utcnow(),
        }

    context = await _fetch_contract_context(contract_address, chain)
    flags = _scan_text_for_flags(context.get("text_blob") or "")

    # If no ABI, apply conservative baseline flags for unverified contracts
    if not context.get("sources"):
        flags.append({
            "flag_id": "unverified_contract",
            "severity": "high",
            "headline": "Contract unverified or no public ABI — elevated risk",
            "evidence": "no_public_abi",
        })

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    flags.sort(key=lambda f: severity_order.get(f.get("severity", "low"), 9))

    critical = sum(1 for f in flags if f.get("severity") == "critical")
    high = sum(1 for f in flags if f.get("severity") == "high")
    risk_level = "low"
    if critical:
        risk_level = "critical"
    elif high:
        risk_level = "high"
    elif flags:
        risk_level = "medium"

    elapsed = (time.perf_counter() - t0) * 1000
    headline = "✅ No critical flags" if risk_level == "low" else f"⚠️ {len(flags)} risk flag(s) detected"

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "scanner_version": _SCANNER_VERSION,
        "mode": "passive_check",
        "contract_address": contract_address,
        "chain": chain,
        "protocol_name": protocol_name or None,
        "risk_level": risk_level,
        "risk_flags": flags,
        "flag_count": len(flags),
        "critical_count": critical,
        "headline": headline,
        "sources": context.get("sources") or [],
        "evidence_mandatory": True,
        "protection_guarantee": False,
        "disclaimer": _NO_PROTECTION_DISCLAIMER,
        "integrated_features": ["#193"],
        "sla_met": elapsed <= 2000,
        "latency_ms": round(elapsed, 1),
        "timestamp": _utcnow(),
    }


def defi_safety_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "DeFi Safety Layer",
        "scanner_version": _SCANNER_VERSION,
        "mode": "passive_risk_flags",
        "patterns_monitored": len(_RISK_PATTERNS),
        "protection_guarantee": False,
        "integrated_features": ["#193"],
        "disclaimer": _NO_PROTECTION_DISCLAIMER,
        "timestamp": _utcnow(),
    }
