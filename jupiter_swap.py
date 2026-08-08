"""
BLACKDARK — Jupiter v6 quote + swap execution (Solana DEX leg).

Requires:
  SOLANA_PRIVATE_KEY (base58) — wallet that signs swaps
  SOLANA_RPC_URL (optional, default public mainnet RPC)
  solders + base58 packages for signing

Live execution remains gated by caller dry_run / LIVE_EXECUTION_ALLOW_API.
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.JupiterSwap")

# Canonical mints (Solana mainnet)
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
SOL_MINT = "So11111111111111111111111111111111111111112"

ASSET_MINTS: dict[str, str] = {
    "SOL": SOL_MINT,
    "USDT": USDT_MINT,
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "BTC": "3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh",  # wbBTC
    "ETH": "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",  # wETH
}

# Token decimals for amount conversion
ASSET_DECIMALS: dict[str, int] = {
    "SOL": 9,
    "USDT": 6,
    "USDC": 6,
    "BTC": 8,
    "ETH": 8,
}

QUOTE_API = os.getenv("JUPITER_QUOTE_API", "https://quote-api.jup.ag/v6/quote").strip()
SWAP_API = os.getenv("JUPITER_SWAP_API", "https://quote-api.jup.ag/v6/swap").strip()


def jupiter_ready() -> dict[str, Any]:
    has_key = bool(os.getenv("SOLANA_PRIVATE_KEY", "").strip())
    try:
        import solders  # noqa: F401
        import base58  # noqa: F401

        deps = True
    except Exception:
        deps = False
    return {
        "wallet_configured": has_key,
        "signing_deps": deps,
        "ready": has_key and deps,
        "quote_api": QUOTE_API,
        "swap_api": SWAP_API,
        "rpc": os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com").strip(),
    }


def _keypair_from_env():
    raw = os.getenv("SOLANA_PRIVATE_KEY", "").strip()
    if not raw:
        raise ValueError("SOLANA_PRIVATE_KEY not configured")
    from solders.keypair import Keypair

    try:
        if raw.startswith("["):
            import json

            secret = bytes(json.loads(raw))
            return Keypair.from_bytes(secret)
        if hasattr(Keypair, "from_base58_string"):
            return Keypair.from_base58_string(raw)
        import base58

        return Keypair.from_bytes(base58.b58decode(raw))
    except Exception as exc:
        raise ValueError(f"Invalid SOLANA_PRIVATE_KEY: {exc}") from exc


def _amount_raw(asset: str, amount_usd: float, *, price_usd: float | None = None) -> int:
    """Convert USD notional to raw token amount for the input mint."""
    asset_u = asset.upper()
    decimals = ASSET_DECIMALS.get(asset_u, 6)
    if asset_u in {"USDT", "USDC"}:
        return max(1, int(round(float(amount_usd) * (10**decimals))))
    px = float(price_usd or 0)
    if px <= 0:
        raise ValueError(f"Need price_usd to size {asset_u} swap")
    tokens = float(amount_usd) / px
    return max(1, int(round(tokens * (10**decimals))))


async def fetch_jupiter_quote(
    session: aiohttp.ClientSession,
    *,
    input_mint: str,
    output_mint: str,
    amount_raw: int,
    slippage_bps: int = 50,
) -> dict[str, Any]:
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": str(amount_raw),
        "slippageBps": str(int(slippage_bps)),
        "onlyDirectRoutes": "false",
    }
    async with session.get(QUOTE_API, params=params) as resp:
        body = await resp.json(content_type=None)
        if resp.status >= 400:
            raise RuntimeError(f"Jupiter quote HTTP {resp.status}: {body}")
        if not isinstance(body, dict) or not body.get("outAmount"):
            raise RuntimeError(f"Jupiter quote empty: {body}")
        return body


async def build_jupiter_swap_tx(
    session: aiohttp.ClientSession,
    *,
    quote: dict[str, Any],
    user_public_key: str,
) -> str:
    payload = {
        "quoteResponse": quote,
        "userPublicKey": user_public_key,
        "wrapAndUnwrapSol": True,
        "dynamicComputeUnitLimit": True,
        "prioritizationFeeLamports": "auto",
    }
    async with session.post(SWAP_API, json=payload) as resp:
        body = await resp.json(content_type=None)
        if resp.status >= 400:
            raise RuntimeError(f"Jupiter swap HTTP {resp.status}: {body}")
        tx_b64 = body.get("swapTransaction")
        if not tx_b64:
            raise RuntimeError(f"Jupiter swap missing swapTransaction: {body}")
        return str(tx_b64)


async def send_signed_tx(session: aiohttp.ClientSession, signed_b64: str) -> str:
    rpc = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com").strip()
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendTransaction",
        "params": [
            signed_b64,
            {
                "encoding": "base64",
                "skipPreflight": False,
                "preflightCommitment": "confirmed",
                "maxRetries": 3,
            },
        ],
    }
    async with session.post(rpc, json=payload) as resp:
        body = await resp.json(content_type=None)
        if body.get("error"):
            raise RuntimeError(f"RPC sendTransaction error: {body['error']}")
        sig = body.get("result")
        if not sig:
            raise RuntimeError(f"RPC sendTransaction empty: {body}")
        return str(sig)


def sign_swap_transaction(swap_tx_b64: str) -> str:
    from solders.message import to_bytes_versioned
    from solders.transaction import VersionedTransaction

    keypair = _keypair_from_env()
    raw = base64.b64decode(swap_tx_b64)
    tx = VersionedTransaction.from_bytes(raw)
    signature = keypair.sign_message(to_bytes_versioned(tx.message))
    signed = VersionedTransaction.populate(tx.message, [signature])
    return base64.b64encode(bytes(signed)).decode("ascii")


async def execute_jupiter_swap(
    *,
    asset: str,
    side: str,
    amount_usd: float,
    price_usd: float | None = None,
    slippage_bps: int | None = None,
) -> dict[str, Any]:
    """
    Live Jupiter swap: buy asset with USDT (side=buy) or sell asset to USDT (side=sell).
    """
    status = jupiter_ready()
    if not status["ready"]:
        return {
            "executed": False,
            "mode": "blocked_until_jupiter",
            "blocked_reason": (
                "missing_solana_private_key"
                if not status["wallet_configured"]
                else "missing_solders_base58_deps"
            ),
            "status": status,
        }

    asset_u = asset.upper().strip()
    mint = ASSET_MINTS.get(asset_u)
    if not mint:
        return {
            "executed": False,
            "mode": "blocked",
            "blocked_reason": f"unsupported_asset_mint:{asset_u}",
        }

    side_l = side.lower().strip()
    if side_l == "buy":
        input_mint, output_mint = USDT_MINT, mint
        amount_raw = _amount_raw("USDT", amount_usd)
    elif side_l == "sell":
        input_mint, output_mint = mint, USDT_MINT
        amount_raw = _amount_raw(asset_u, amount_usd, price_usd=price_usd)
    else:
        return {"executed": False, "mode": "blocked", "blocked_reason": "invalid_side"}

    slip = int(slippage_bps or os.getenv("JUPITER_SLIPPAGE_BPS", "50") or 50)
    timeout = aiohttp.ClientTimeout(total=30)
    try:
        keypair = _keypair_from_env()
        pubkey = str(keypair.pubkey())
        async with aiohttp.ClientSession(timeout=timeout) as session:
            quote = await fetch_jupiter_quote(
                session,
                input_mint=input_mint,
                output_mint=output_mint,
                amount_raw=amount_raw,
                slippage_bps=slip,
            )
            swap_tx = await build_jupiter_swap_tx(session, quote=quote, user_public_key=pubkey)
            signed = sign_swap_transaction(swap_tx)
            sig = await send_signed_tx(session, signed)
        return {
            "executed": True,
            "mode": "live",
            "venue": "jupiter",
            "asset": asset_u,
            "side": side_l,
            "amount_usd": float(amount_usd),
            "amount_raw": amount_raw,
            "in_amount": quote.get("inAmount"),
            "out_amount": quote.get("outAmount"),
            "signature": sig,
            "explorer": f"https://solscan.io/tx/{sig}",
            "wallet": pubkey,
        }
    except Exception as exc:
        logger.exception("Jupiter live swap failed")
        return {
            "executed": False,
            "mode": "error",
            "blocked_reason": "jupiter_swap_failed",
            "error": str(exc)[:300],
            "asset": asset_u,
            "side": side_l,
        }
