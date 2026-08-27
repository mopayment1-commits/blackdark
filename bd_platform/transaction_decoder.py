"""
Transaction Decoder (#100) — AI Layer: human-readable tx explanations without hallucinated intent.

Uses verified on-chain data only (Etherscan-compatible APIs + logs).
Unknown actions are explicitly marked; intent is never inferred without evidence.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.TransactionDecoder")

_KNOWN_SELECTORS: dict[str, dict[str, Any]] = {
    "0xa9059cbb": {
        "name": "transfer",
        "protocol": "ERC20",
        "description": "Token transfer",
        "intent_inferred": False,
    },
    "0x095ea7b3": {
        "name": "approve",
        "protocol": "ERC20",
        "description": "Token spending approval",
        "intent_inferred": False,
    },
    "0x38ed1739": {
        "name": "swapExactTokensForTokens",
        "protocol": "Uniswap V2",
        "description": "DEX token swap",
        "intent_inferred": False,
    },
    "0x7ff36ab5": {
        "name": "swapExactETHForTokens",
        "protocol": "Uniswap V2",
        "description": "ETH to token swap",
        "intent_inferred": False,
    },
    "0x414bf389": {
        "name": "exactInputSingle",
        "protocol": "Uniswap V3",
        "description": "Single-hop concentrated liquidity swap",
        "intent_inferred": False,
    },
    "0x88316456": {
        "name": "mint",
        "protocol": "Uniswap V3",
        "description": "Liquidity provision (mint position)",
        "intent_inferred": False,
        "confidence": "high",
        "risk_notes": ["impermanent_loss"],
    },
}

_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _scan_base(chain: str) -> tuple[str, str]:
    mapping = {
        "ethereum": ("ETHERSCAN_API_KEY", "https://api.etherscan.io/api"),
        "bsc": ("BSCSCAN_API_KEY", "https://api.bscscan.com/api"),
        "arbitrum": ("ARBISCAN_API_KEY", "https://api.arbiscan.io/api"),
        "polygon": ("POLYGONSCAN_API_KEY", "https://api.polygonscan.com/api"),
    }
    return mapping.get(chain.lower(), ("ETHERSCAN_API_KEY", "https://api.etherscan.io/api"))


async def _fetch_tx_and_receipt(tx_hash: str, *, chain: str) -> dict[str, Any]:
    env_key, base = _scan_base(chain)
    api_key = (os.getenv(env_key) or "").strip()
    if not api_key:
        return {"ok": False, "error": f"{env_key} not configured"}

    from blackdark.ingestion.unified_connector import UnifiedConnector

    slug = f"{chain}_scan"
    conn = UnifiedConnector(source_slug=slug)
    tx_resp = await conn.get_json(
        base,
        params={
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": tx_hash,
            "apikey": api_key,
        },
        cache_parts=("tx", chain, tx_hash),
        ttl=300,
    )
    rcpt_resp = await conn.get_json(
        base,
        params={
            "module": "proxy",
            "action": "eth_getTransactionReceipt",
            "txhash": tx_hash,
            "apikey": api_key,
        },
        cache_parts=("receipt", chain, tx_hash),
        ttl=300,
    )
    if not tx_resp.get("ok"):
        return {"ok": False, "error": tx_resp.get("error")}
    tx = (tx_resp.get("data") or {}).get("result")
    receipt = (rcpt_resp.get("data") or {}).get("result") if rcpt_resp.get("ok") else None
    if not isinstance(tx, dict):
        return {"ok": False, "error": "transaction_not_found", "tx_hash": tx_hash}
    return {"ok": True, "transaction": tx, "receipt": receipt}


def _decode_input(input_hex: str) -> dict[str, Any]:
    data = (input_hex or "0x").lower()
    if data in {"0x", ""}:
        return {
            "action": "native_transfer",
            "description": "Native token transfer",
            "known": True,
            "intent_inferred": False,
            "selector": None,
        }
    selector = data[:10] if len(data) >= 10 else data
    known = _KNOWN_SELECTORS.get(selector)
    if known:
        return {
            "action": known["name"],
            "protocol": known.get("protocol"),
            "description": known.get("description"),
            "known": True,
            "intent_inferred": False,
            "selector": selector,
            "risk_notes": known.get("risk_notes") or [],
            "confidence": known.get("confidence", "verified_selector"),
        }
    return {
        "action": "unknown",
        "description": "Unknown contract call — intent not inferred",
        "known": False,
        "intent_inferred": False,
        "selector": selector,
        "unknown_marked": True,
    }


def _decode_logs(logs: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    decoded: list[dict[str, Any]] = []
    for log in logs or []:
        if not isinstance(log, dict):
            continue
        topics = [str(t).lower() for t in (log.get("topics") or [])]
        if topics and topics[0] == _TRANSFER_TOPIC:
            decoded.append(
                {
                    "event": "Transfer",
                    "known": True,
                    "intent_inferred": False,
                    "contract": log.get("address"),
                    "topics_count": len(topics),
                }
            )
        else:
            decoded.append(
                {
                    "event": "unknown_log",
                    "known": False,
                    "intent_inferred": False,
                    "unknown_marked": True,
                    "contract": log.get("address"),
                }
            )
    return decoded


def _build_explanation(
    *,
    tx: dict[str, Any],
    input_decoded: dict[str, Any],
    logs_decoded: list[dict[str, Any]],
    chain: str,
) -> str:
    action = input_decoded.get("action")
    protocol = input_decoded.get("protocol") or "on-chain"
    if action == "mint" and protocol == "Uniswap V3":
        return (
            "AI Decoded: This transaction is a liquidity provision to Uniswap V3 pool. "
            "You may earn trading fees. Risk: impermanent loss."
        )
    if action == "swapExactTokensForTokens" or action == "exactInputSingle":
        return f"AI Decoded: This transaction is a DEX swap via {protocol}. Intent verified from function selector."
    if action == "transfer":
        return "AI Decoded: This transaction is an ERC-20 token transfer. Intent verified from function selector."
    if action == "native_transfer":
        return "AI Decoded: This transaction is a native token transfer."
    if not input_decoded.get("known"):
        return (
            "AI Decoded: This transaction contains unclassified contract interactions. "
            "Unknown actions are marked — intent was NOT inferred."
        )
    return f"AI Decoded: {input_decoded.get('description', 'On-chain action')} on {chain} ({protocol})."


async def decode_transaction(*, tx_hash: str, chain: str = "ethereum") -> dict[str, Any]:
    """Decode transaction to human-readable explanation — no hallucinated intent (#100)."""
    t0 = time.perf_counter()
    h = (tx_hash or "").strip()
    if not h.startswith("0x") or len(h) < 10:
        return {"ok": False, "error": "invalid_tx_hash", "tx_hash": h}

    fetched = await _fetch_tx_and_receipt(h, chain=chain)
    if not fetched.get("ok"):
        return {
            "ok": False,
            "feature": "#100",
            "tx_hash": h,
            "chain": chain.lower(),
            "error": fetched.get("error"),
            "data_state": "MISSING",
            "unknown_actions_marked": True,
            "intent_inferred": False,
        }

    tx = fetched["transaction"]
    receipt = fetched.get("receipt") or {}
    input_decoded = _decode_input(str(tx.get("input") or "0x"))
    logs_decoded = _decode_logs(receipt.get("logs") if isinstance(receipt, dict) else None)

    unknown_count = sum(1 for x in [input_decoded, *logs_decoded] if not x.get("known"))
    explanation = _build_explanation(
        tx=tx,
        input_decoded=input_decoded,
        logs_decoded=logs_decoded,
        chain=chain.lower(),
    )

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature": "#100",
        "capability": "transaction_decoder",
        "tx_hash": h,
        "chain": chain.lower(),
        "from": tx.get("from"),
        "to": tx.get("to"),
        "value_wei": tx.get("value"),
        "actions": [input_decoded, *logs_decoded],
        "input_decoded": input_decoded,
        "logs_decoded": logs_decoded,
        "explanation": explanation,
        "ai_decoded_line": explanation,
        "unknown_actions_marked": unknown_count > 0,
        "unknown_action_count": unknown_count,
        "intent_inferred": False,
        "hallucinated_intent": False,
        "data_state": "LIVE",
        "sources": ["etherscan_compatible_api"],
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }
