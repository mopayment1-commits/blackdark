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


# Public Swap API host (legacy quote-api.jup.ag/v6 no longer resolves in many environments).
DEFAULT_JUPITER_API_URL = "https://api.jup.ag/swap/v1"


def jupiter_api_base() -> str:
    return os.getenv("JUPITER_API_URL", DEFAULT_JUPITER_API_URL).strip().rstrip("/")


def jupiter_configured() -> dict[str, bool]:
    return {
        "api": bool(jupiter_api_base()),
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
    base = jupiter_api_base()
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
            "executable_product_path": bool(dry_run),
            "quote": q,
            "configured": cfg,
            "message": (
                f"Jupiter product path ready — would {side} ${amount_usd:.0f} {asset}. "
                "Set SOLANA_PRIVATE_KEY + JUPITER_LIVE_EXECUTION=true for live fill."
            ),
            "blocked_reason": None if dry_run else "live_requires_wallet_and_flag",
        }
    # Live path: never return synthetic success. Submit requires operator runtime;
    # production remains fail-closed and unreachable as executed=True.
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
        "blocked_reason": "live_submit_fail_closed_no_synthetic",
        "message": (
            "Live Jupiter submit is fail-closed in-repo: quote was live API, "
            "but no production-reachable synthetic fill is permitted."
        ),
        "stub_unreachable": True,
    }


async def prove_jupiter_live_quote(
    *,
    amount_atomic: int = 1_000_000,
) -> dict[str, Any]:
    """Prove live Jupiter quote path (not submit). Fail-closed; never synthetic ok."""
    usdc = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    sol = "So11111111111111111111111111111111111111112"
    q = await quote_swap(input_mint=usdc, output_mint=sol, amount_atomic=amount_atomic)
    out_amount = None
    if q.get("ok") and isinstance(q.get("quote"), dict):
        out_amount = q["quote"].get("outAmount")
    return {
        "ok": bool(q.get("ok") and q.get("executable_quote") and out_amount),
        "surface": "jupiter_live_quote_proof",
        "api_base": jupiter_api_base(),
        "executable_quote": bool(q.get("executable_quote")),
        "out_amount": out_amount,
        "quote": q,
        "live_submit_implemented": False,
        "implementation_class": "PARTIAL" if q.get("ok") else "UNVERIFIED",
        "product_complete": False,
        "verified_complete": False,
        "note": "Live quote only — submit remains NOT_IMPLEMENTED / fail-closed.",
        "at": _utcnow(),
    }


def adapter_status() -> dict[str, Any]:
    cfg = jupiter_configured()
    return {
        "surface": "jupiter_dex_adapter",
        "configured": cfg,
        "api_base": jupiter_api_base(),
        "synthetic_ok_forbidden": True,
        "live_submit_fail_closed": True,
        "live_submit_implemented": False,
        "production_stub_reachable": False,
        "product_complete": False,
        "verified_complete": False,
        "implementation_class": "NOT_IMPLEMENTED",  # submit class
        "quote_implementation_class": "PARTIAL",
        "quote_path_ready": bool(cfg["api"]),
        "note": (
            f"Quotes via {jupiter_api_base()}. Live submit is intentionally "
            "NOT_IMPLEMENTED in-repo and fail-closed (never executed=True)."
        ),
    }
