"""
Read-only wallet balance lookup (no keys stored, no transactions).
"""

from __future__ import annotations

import re
from typing import Any

_EVM_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


def _valid_evm(address: str) -> bool:
    return bool(_EVM_RE.match((address or "").strip()))


def _norm_chain(chain: str) -> str:
    c = (chain or "ethereum").lower().strip()
    if c in {"eth", "mainnet"}:
        return "ethereum"
    return c


async def fetch_readonly_wallet_balance(
    address: str,
    *,
    chain: str = "ethereum",
) -> dict[str, Any]:
    addr = (address or "").strip()
    if not _valid_evm(addr):
        return {
            "ok": False,
            "error": "invalid_address",
            "read_only": True,
            "non_custodial": True,
        }
    ch = _norm_chain(chain)

    if ch == "ethereum":
        try:
            from etherscan_public_api import fetch_eth_balance_wei, usage_stats

            eth = await fetch_eth_balance_wei(addr)
            if eth:
                out: dict[str, Any] = {
                    "ok": True,
                    "read_only": True,
                    "non_custodial": True,
                    "no_private_key": True,
                    "address": addr,
                    "chain": ch,
                    "source": "etherscan_free",
                    "attribution": "Data: Etherscan",
                    "balance_native": eth.get("balance_eth"),
                    "balance_wei": eth.get("balance_wei"),
                    "native_symbol": "ETH",
                    "usage": usage_stats(),
                }
                return out
        except Exception:
            pass

    try:
        from blockscout_public_api import fetch_address_summary, usage_stats as bs_usage

        summary = await fetch_address_summary(addr, chain=ch)
        if summary:
            return {
                "ok": True,
                "read_only": True,
                "non_custodial": True,
                "no_private_key": True,
                "address": addr,
                "chain": ch,
                "source": "blockscout",
                "attribution": f"Data: Blockscout ({ch})",
                "balance_native": summary.get("balance_native"),
                "balance_wei": summary.get("balance_wei"),
                "native_symbol": summary.get("native_symbol") or "ETH",
                "native_usd_estimate": summary.get("native_usd_estimate"),
                "ens_domain": summary.get("ens_domain_name"),
                "usage": bs_usage(),
            }
    except Exception:
        pass

    try:
        from bd_platform.free_integrations import wallet_balance

        row = await wallet_balance(addr)
        if row.get("available"):
            return {
                "ok": True,
                "read_only": True,
                "non_custodial": True,
                "no_private_key": True,
                "address": addr,
                "chain": ch,
                "source": row.get("source"),
                "total_usd": row.get("total_usd"),
                "balance_native": row.get("balance_eth") or row.get("balance_native"),
                "balance_wei": row.get("balance_wei"),
                "tier": row.get("tier"),
                "note": row.get("note"),
            }
    except Exception:
        pass

    return {
        "ok": False,
        "error": "balance_unavailable",
        "read_only": True,
        "non_custodial": True,
        "address": addr,
        "chain": ch,
    }
