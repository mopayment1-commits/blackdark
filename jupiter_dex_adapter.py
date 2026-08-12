"""
BLACKDARK — Jupiter / Solana DEX live leg adapter (Report-1 C4 cure).

Fail-closed: network failure / non-200 NEVER returns ok=True synthetic economics
as a live quote. Synthetic may only appear as ok=False research residue.
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
    """Fetch Jupiter quote. Fail closed on network/API failure (no synthetic ok=True)."""
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
                    "executable_quote": True,
                    "at": _utcnow(),
                }
            return {
                "ok": False,
                "source": "jupiter_api_error",
                "status_code": r.status_code,
                "quote": None,
                "configured": cfg,
                "executable_quote": False,
                "reason": f"http_{r.status_code}",
                "at": _utcnow(),
            }
    except Exception as exc:
        return {
            "ok": False,
            "source": "network_unavailable",
            "quote": None,
            "configured": cfg,
            "executable_quote": False,
            "reason": f"network_unavailable:{type(exc).__name__}",
            "synthetic_forbidden": True,
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
            "mode": "blocked",
            "executed": False,
            "executable_product_path": False,
            "quote": q,
            "configured": cfg,
            "blocked_reason": q.get("reason") or "jupiter_quote_unavailable",
            "message": "Jupiter quote unavailable — fail closed (no synthetic economics).",
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
            "executable_product_path": True,
            "quote": q,
            "configured": cfg,
            "message": (
                f"Jupiter product path ready — would {side} ${amount_usd:.0f} {asset}. "
                "Set SOLANA_PRIVATE_KEY + JUPITER_LIVE_EXECUTION=true for live fill."
            ),
            "blocked_reason": None if dry_run else "live_requires_wallet_and_flag",
        }
    return {
        "leg": "dex",
        "venue": venue,
        "asset": asset,
        "side": side,
        "amount_usd": amount_usd,
        "mode": "live_submit_not_implemented_in_repo",
        "executed": False,
        "executable_product_path": True,
        "quote": q,
        "configured": cfg,
        "blocked_reason": "live_submit_requires_operator_wallet_runtime",
        "message": "Live Jupiter submit is operator-gated; quote was live API.",
    }


def adapter_status() -> dict[str, Any]:
    cfg = jupiter_configured()
    return {
        "surface": "jupiter_dex_adapter",
        "configured": cfg,
        "synthetic_ok_forbidden": True,
        "product_complete": bool(cfg["api"]),
        "note": "Quotes fail closed on network errors; no synthetic ok=True.",
    }
