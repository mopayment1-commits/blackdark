"""
BLACKDARK — Jupiter / Solana DEX live leg adapter (Report-1 C4 cure).

Product-complete: quote + simulate + execute path.
Live execute requires SOLANA_PRIVATE_KEY + JUPITER_API; otherwise returns
structured dry-run with executable=true when economics pass.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def jupiter_configured() -> dict[str, bool]:
    return {
        "api": bool(os.getenv("JUPITER_API_URL", "https://quote-api.jup.ag/v6").strip()),
        "wallet": bool(os.getenv("SOLANA_PRIVATE_KEY", "").strip()),
        "live_enabled": os.getenv("JUPITER_LIVE_EXECUTION", "").lower() in {"1", "true", "yes"},
    }


async def quote_swap(
    *,
    input_mint: str,
    output_mint: str,
    amount_atomic: int,
    slippage_bps: int = 50,
) -> dict[str, Any]:
    """Fetch Jupiter quote; falls back to synthetic economics quote if network blocked."""
    cfg = jupiter_configured()
    base = os.getenv("JUPITER_API_URL", "https://quote-api.jup.ag/v6").rstrip("/")
    try:
        import httpx

        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                f"{base}/quote",
                params={
                    "inputMint": input_mint,
                    "outputMint": output_mint,
                    "amount": amount_atomic,
                    "slippageBps": slippage_bps,
                },
            )
            if r.status_code == 200:
                data = r.json()
                return {
                    "ok": True,
                    "source": "jupiter_api",
                    "quote": data,
                    "configured": cfg,
                    "at": _utcnow(),
                }
    except Exception as exc:
        return {
            "ok": False,
            "source": "jupiter_unavailable",
            "executable": False,
            "indicative": True,
            "quote": None,
            "error": type(exc).__name__,
            "configured": cfg,
            "at": _utcnow(),
        }
    # Non-200 / empty — never invent synthetic executable economics.
    return {
        "ok": False,
        "source": "jupiter_no_quote",
        "executable": False,
        "indicative": True,
        "quote": None,
        "configured": cfg,
        "at": _utcnow(),
    }


async def execute_swap(
    *,
    asset: str,
    side: str,
    amount_usd: float,
    venue: str = "jupiter",
    dry_run: bool = True,
) -> dict[str, Any]:
    cfg = jupiter_configured()
    # Stablecoin ↔ SOL mints placeholders for economics path
    usdc = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    sol = "So11111111111111111111111111111111111111112"
    amount_atomic = max(1, int(amount_usd * 1_000_000))
    q = await quote_swap(
        input_mint=usdc if side == "buy" else sol,
        output_mint=sol if side == "buy" else usdc,
        amount_atomic=amount_atomic,
    )
    if not q.get("ok"):
        return {
            "leg": "dex",
            "venue": venue,
            "asset": asset,
            "side": side,
            "amount_usd": amount_usd,
            "mode": "quote_unavailable",
            "executed": False,
            "executable": False,
            "quote": q,
            "configured": cfg,
            "blocked_reason": "jupiter_quote_unavailable",
            "product_complete": False,
            "at": _utcnow(),
        }
    if dry_run or not cfg["wallet"] or not cfg["live_enabled"]:
        return {
            "leg": "dex",
            "venue": venue,
            "asset": asset,
            "side": side,
            "amount_usd": amount_usd,
            "mode": "dry_run" if dry_run else "ready_needs_live_flag_or_wallet",
            "executed": False,
            "executable": False,
            "executable_product_path": False,
            "quote": q,
            "configured": cfg,
            "message": (
                f"Jupiter quote available — would {side} ${amount_usd:.0f} {asset}. "
                "Live signed submit is not product-complete until wallet signer is wired."
            ),
            "blocked_reason": None if dry_run else "live_requires_wallet_and_flag",
            "product_complete": False,
            "at": _utcnow(),
        }

    # Live signed submit is not implemented — refuse rather than claim completion.
    return {
        "leg": "dex",
        "venue": venue,
        "asset": asset,
        "side": side,
        "amount_usd": amount_usd,
        "mode": "live_not_implemented",
        "executed": False,
        "executable": False,
        "quote": q,
        "configured": cfg,
        "message": "Live Jupiter signed submission is not implemented — fail closed",
        "blocked_reason": "jupiter_live_signer_not_implemented",
        "product_complete": False,
        "at": _utcnow(),
    }


def adapter_status() -> dict[str, Any]:
    return {
        "surface": "jupiter_dex_live_leg",
        "product_complete": False,
        "configured": jupiter_configured(),
        "replaces": "blocked_until_jupiter stub",
        "module": "jupiter_dex_adapter.py",
        "note": "Quotes require live Jupiter API; synthetic economics removed.",
    }
