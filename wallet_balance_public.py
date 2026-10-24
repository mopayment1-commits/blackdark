"""
Read-only wallet balance lookup (no keys stored, no transactions).
"""

from __future__ import annotations

import re
from typing import Any

_EVM_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

_USER_MESSAGES: dict[str, str] = {
    "invalid_address": (
        "Enter a valid EVM wallet address: 0x followed by 40 hexadecimal characters."
    ),
    "balance_unavailable": (
        "Balance service is temporarily unavailable. Please try again in a few minutes."
    ),
    "service_unavailable": (
        "Balance service is temporarily unavailable. Please try again in a few minutes."
    ),
}


def _user_message(error_code: str) -> str:
    return _USER_MESSAGES.get(error_code, "Could not load balance for this address.")


def _normalize_evm_input(address: str) -> str:
    raw = (address or "").strip()
    if not raw:
        return ""
    if raw.lower().startswith("0x"):
        return "0x" + raw[2:].lower()
    if re.fullmatch(r"[a-fA-F0-9]{40}", raw):
        return "0x" + raw.lower()
    return raw


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
    addr = _normalize_evm_input(address)
    if not _valid_evm(addr):
        return {
            "ok": False,
            "error": "invalid_address",
            "message": _user_message("invalid_address"),
            "read_only": True,
            "non_custodial": True,
        }
    ch = _norm_chain(chain)

    if ch == "ethereum":
        try:
            from etherscan_public_api import fetch_eth_balance_wei, usage_stats

            eth = await fetch_eth_balance_wei(addr)
            if eth:
                return {
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
            bal = row.get("balance") or {}
            native = None
            wei = None
            if isinstance(bal, dict):
                try:
                    wei = int(bal.get("result") or 0)
                    native = round(wei / 1e18, 8)
                except (TypeError, ValueError):
                    native = row.get("total_usd")
            return {
                "ok": True,
                "read_only": True,
                "non_custodial": True,
                "no_private_key": True,
                "address": addr,
                "chain": ch,
                "source": row.get("source"),
                "total_usd": row.get("total_usd"),
                "balance_native": row.get("balance_eth") or row.get("balance_native") or native,
                "balance_wei": row.get("balance_wei") or wei,
                "native_symbol": "ETH" if ch == "ethereum" else str(row.get("native_symbol") or "ETH"),
                "tier": row.get("tier"),
                "note": row.get("note"),
            }
    except Exception:
        pass

    return {
        "ok": False,
        "error": "balance_unavailable",
        "message": _user_message("balance_unavailable"),
        "read_only": True,
        "non_custodial": True,
        "address": addr,
        "chain": ch,
    }
