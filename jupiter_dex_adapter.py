"""
BLACKDARK — Jupiter / Solana DEX live leg adapter (Report-1 C4 cure).

Fail-closed: network failure / non-200 NEVER returns ok=True synthetic economics
as a live quote. Synthetic may only appear as ok=False research residue.

Submit path is implemented in-repo (quote → /swap → sign → RPC). Live execution
requires SOLANA_PRIVATE_KEY + JUPITER_LIVE_EXECUTION=true; otherwise fail-closed.
"""

from __future__ import annotations

import base64
import os
from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


# Public Swap API host (legacy quote-api.jup.ag/v6 no longer resolves in many environments).
DEFAULT_JUPITER_API_URL = "https://api.jup.ag/swap/v1"
DEFAULT_SOLANA_RPC = "https://api.mainnet-beta.solana.com"


def jupiter_api_base() -> str:
    return os.getenv("JUPITER_API_URL", DEFAULT_JUPITER_API_URL).strip().rstrip("/")


def solana_rpc_url() -> str:
    return os.getenv("SOLANA_RPC_URL", DEFAULT_SOLANA_RPC).strip().rstrip("/")


def jupiter_configured() -> dict[str, bool]:
    return {
        "api": bool(jupiter_api_base()),
        "wallet": bool(os.getenv("SOLANA_PRIVATE_KEY", "").strip()),
        "live_enabled": os.getenv("JUPITER_LIVE_EXECUTION", "").lower() in {"1", "true", "yes"},
        "signing_libs": _signing_libs_available(),
    }


def _signing_libs_available() -> bool:
    try:
        import solders.keypair  # noqa: F401
        import solders.transaction  # noqa: F401

        return True
    except Exception:
        return False


def _load_keypair():
    raw = os.getenv("SOLANA_PRIVATE_KEY", "").strip()
    if not raw:
        raise ValueError("SOLANA_PRIVATE_KEY missing")
    from solders.keypair import Keypair

    # Accept base58 secret or JSON byte array.
    if raw.startswith("["):
        import json

        return Keypair.from_bytes(bytes(json.loads(raw)))
    try:
        return Keypair.from_base58_string(raw)
    except Exception:
        import base58

        return Keypair.from_bytes(base58.b58decode(raw))


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


async def build_swap_transaction(*, quote: dict[str, Any], user_public_key: str) -> dict[str, Any]:
    """Build unsigned/ partially signed swap tx via Jupiter /swap (live API)."""
    base = jupiter_api_base()
    try:
        import httpx

        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                f"{base}/swap",
                json={
                    "quoteResponse": quote,
                    "userPublicKey": user_public_key,
                    "wrapAndUnwrapSol": True,
                    "dynamicComputeUnitLimit": True,
                },
            )
            if r.status_code != 200:
                return {
                    "ok": False,
                    "reason": f"swap_http_{r.status_code}",
                    "body": (r.text or "")[:240],
                }
            data = r.json()
            tx_b64 = data.get("swapTransaction")
            if not tx_b64:
                return {"ok": False, "reason": "swap_transaction_missing", "body": data}
            return {"ok": True, "swap_transaction": tx_b64, "raw": data}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"swap_network:{type(exc).__name__}"}


async def _rpc_send_transaction(tx_b64: str) -> dict[str, Any]:
    import httpx

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            solana_rpc_url(),
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sendTransaction",
                "params": [
                    tx_b64,
                    {
                        "encoding": "base64",
                        "skipPreflight": False,
                        "preflightCommitment": "confirmed",
                    },
                ],
            },
        )
        body = r.json()
        if body.get("error"):
            return {
                "ok": False,
                "reason": "rpc_error",
                "error": body.get("error"),
            }
        sig = body.get("result")
        if not sig:
            return {"ok": False, "reason": "rpc_no_signature", "body": body}
        return {"ok": True, "signature": sig, "rpc": solana_rpc_url()}


async def submit_swap_live(*, quote_payload: dict[str, Any]) -> dict[str, Any]:
    """Sign + submit Jupiter swap. Never returns executed=True without RPC signature."""
    if not _signing_libs_available():
        return {
            "ok": False,
            "executed": False,
            "reason": "signing_libs_missing_install_solders_base58",
            "live_submit_implemented": True,
        }
    try:
        kp = _load_keypair()
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "executed": False,
            "reason": f"wallet_load_failed:{type(exc).__name__}",
            "live_submit_implemented": True,
        }

    quote = quote_payload.get("quote") if isinstance(quote_payload, dict) else None
    if not isinstance(quote, dict):
        return {"ok": False, "executed": False, "reason": "quote_missing", "live_submit_implemented": True}

    built = await build_swap_transaction(quote=quote, user_public_key=str(kp.pubkey()))
    if not built.get("ok"):
        return {
            "ok": False,
            "executed": False,
            "reason": built.get("reason"),
            "build": built,
            "live_submit_implemented": True,
        }

    try:
        from solders.transaction import VersionedTransaction

        raw = base64.b64decode(built["swap_transaction"])
        tx = VersionedTransaction.from_bytes(raw)
        signed = VersionedTransaction(tx.message, [kp])
        signed_b64 = base64.b64encode(bytes(signed)).decode("ascii")
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "executed": False,
            "reason": f"sign_failed:{type(exc).__name__}:{exc}"[:200],
            "live_submit_implemented": True,
        }

    sent = await _rpc_send_transaction(signed_b64)
    if not sent.get("ok"):
        return {
            "ok": False,
            "executed": False,
            "reason": sent.get("reason"),
            "rpc_error": sent.get("error"),
            "live_submit_implemented": True,
            "signed": True,
        }
    return {
        "ok": True,
        "executed": True,
        "signature": sent["signature"],
        "rpc": sent.get("rpc"),
        "user_public_key": str(kp.pubkey()),
        "live_submit_implemented": True,
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
            "live_submit_implemented": True,
            "message": "Jupiter quote unavailable — fail closed (no synthetic economics).",
        }
    if dry_run:
        return {
            "leg": "dex",
            "venue": venue,
            "asset": asset,
            "side": side,
            "amount_usd": amount_usd,
            "mode": "dry_run",
            "executed": False,
            "executable_product_path": True,
            "quote": q,
            "configured": cfg,
            "live_submit_implemented": True,
            "message": (
                f"Jupiter product path ready — would {side} ${amount_usd:.0f} {asset}. "
                "Set SOLANA_PRIVATE_KEY + JUPITER_LIVE_EXECUTION=true for live fill."
            ),
            "blocked_reason": None,
        }
    if not cfg["wallet"] or not cfg["live_enabled"]:
        return {
            "leg": "dex",
            "venue": venue,
            "asset": asset,
            "side": side,
            "amount_usd": amount_usd,
            "mode": "ready_needs_live_flag_or_wallet",
            "executed": False,
            "executable_product_path": False,
            "quote": q,
            "configured": cfg,
            "live_submit_implemented": True,
            "blocked_reason": "live_requires_wallet_and_flag",
            "message": "Live submit implemented — arm SOLANA_PRIVATE_KEY + JUPITER_LIVE_EXECUTION.",
        }
    if not cfg.get("signing_libs"):
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
            "live_submit_implemented": True,
            "blocked_reason": "signing_libs_missing",
            "message": "Install solders+base58 for live Jupiter submit.",
        }

    submitted = await submit_swap_live(quote_payload=q)
    return {
        "leg": "dex",
        "venue": venue,
        "asset": asset,
        "side": side,
        "amount_usd": amount_usd,
        "mode": "live_submit" if submitted.get("executed") else "live_submit_failed",
        "executed": bool(submitted.get("executed")),
        "executable_product_path": True,
        "quote": q,
        "configured": cfg,
        "submit": submitted,
        "signature": submitted.get("signature"),
        "live_submit_implemented": True,
        "blocked_reason": None if submitted.get("executed") else submitted.get("reason"),
        "message": (
            "Jupiter live submit succeeded."
            if submitted.get("executed")
            else f"Jupiter live submit failed: {submitted.get('reason')}"
        ),
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
        "live_submit_implemented": True,
        "implementation_class": "PARTIAL" if q.get("ok") else "UNVERIFIED",
        "product_complete": False,
        "verified_complete": False,
        "note": "Live quote proven — submit path implemented; live execution needs wallet+flag.",
        "at": _utcnow(),
    }


async def prove_jupiter_swap_build() -> dict[str, Any]:
    """Prove Jupiter /swap builds a real transaction without broadcasting.

    Uses an ephemeral pubkey (no operator wallet required). Never claims executed.
    """
    usdc = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    sol = "So11111111111111111111111111111111111111112"
    q = await quote_swap(input_mint=usdc, output_mint=sol, amount_atomic=1_000_000)
    if not q.get("ok") or not isinstance(q.get("quote"), dict):
        return {
            "ok": False,
            "surface": "jupiter_swap_build_proof",
            "reason": q.get("reason") or "quote_unavailable",
            "executed": False,
            "broadcast": False,
            "live_submit_implemented": True,
            "verified_complete": False,
            "implementation_class": "UNVERIFIED",
            "product_complete": False,
            "at": _utcnow(),
        }
    try:
        from solders.keypair import Keypair

        ephemeral = Keypair()
        pubkey = str(ephemeral.pubkey())
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "surface": "jupiter_swap_build_proof",
            "reason": f"keypair_unavailable:{type(exc).__name__}",
            "executed": False,
            "broadcast": False,
            "live_submit_implemented": True,
            "verified_complete": False,
            "implementation_class": "PARTIAL",
            "product_complete": False,
            "at": _utcnow(),
        }
    built = await build_swap_transaction(quote=q["quote"], user_public_key=pubkey)
    tx_b64 = built.get("swap_transaction") if built.get("ok") else None
    ok = bool(built.get("ok") and tx_b64 and len(str(tx_b64)) > 100)
    return {
        "ok": ok,
        "surface": "jupiter_swap_build_proof",
        "api_base": jupiter_api_base(),
        "ephemeral_pubkey": pubkey,
        "swap_transaction_built": ok,
        "swap_transaction_chars": len(str(tx_b64 or "")),
        "executed": False,
        "broadcast": False,
        "live_submit_implemented": True,
        "reason": None if ok else built.get("reason"),
        "verified_complete": False,
        "implementation_class": "PARTIAL" if ok else "UNVERIFIED",
        "product_complete": False,
        "note": "Live /swap tx build proven with ephemeral pubkey — no broadcast, no fill claim.",
        "at": _utcnow(),
    }


async def prove_jupiter_submit_path() -> dict[str, Any]:
    """Prove submit path is implemented (build readiness); execute only if armed."""
    cfg = jupiter_configured()
    quote_proof = await prove_jupiter_live_quote()
    build_proof = await prove_jupiter_swap_build()
    # Dry-run execute always exercises quote→path without broadcasting.
    dry = await execute_swap(asset="SOL", side="buy", amount_usd=1, dry_run=True)
    live = None
    if cfg["wallet"] and cfg["live_enabled"] and cfg.get("signing_libs"):
        live = await execute_swap(asset="SOL", side="buy", amount_usd=1, dry_run=False)
    return {
        "ok": bool(
            quote_proof.get("ok")
            and dry.get("live_submit_implemented")
            and build_proof.get("ok")
        ),
        "surface": "jupiter_submit_path_proof",
        "live_submit_implemented": True,
        "configured": cfg,
        "quote_ok": quote_proof.get("ok"),
        "swap_build": {
            "ok": build_proof.get("ok"),
            "swap_transaction_built": build_proof.get("swap_transaction_built"),
            "swap_transaction_chars": build_proof.get("swap_transaction_chars"),
            "broadcast": False,
            "executed": False,
        },
        "dry_run": {
            "mode": dry.get("mode"),
            "executed": dry.get("executed"),
            "executable_product_path": dry.get("executable_product_path"),
        },
        "live_attempt": (
            {
                "mode": (live or {}).get("mode"),
                "executed": (live or {}).get("executed"),
                "signature": (live or {}).get("signature"),
                "blocked_reason": (live or {}).get("blocked_reason"),
            }
            if live is not None
            else {"armed": False, "reason": "wallet_or_live_flag_absent"}
        ),
        "implementation_class": "PARTIAL",
        "product_complete": False,
        "verified_complete": bool(live and live.get("executed")),
        "note": (
            "Submit path is in-repo (quote→/swap build→sign→RPC). "
            "Swap build proven without wallet; verified_complete only with live signature."
        ),
        "at": _utcnow(),
    }


def adapter_status() -> dict[str, Any]:
    cfg = jupiter_configured()
    return {
        "surface": "jupiter_dex_adapter",
        "configured": cfg,
        "api_base": jupiter_api_base(),
        "rpc": solana_rpc_url(),
        "synthetic_ok_forbidden": True,
        "live_submit_fail_closed": True,
        "live_submit_implemented": True,
        "production_stub_reachable": False,
        "product_complete": False,
        "verified_complete": False,
        "implementation_class": "PARTIAL",  # submit implemented; live needs wallet
        "quote_implementation_class": "PARTIAL",
        "quote_path_ready": bool(cfg["api"]),
        "note": (
            f"Quotes via {jupiter_api_base()}. Live submit implemented "
            "(solders sign + RPC); requires SOLANA_PRIVATE_KEY + JUPITER_LIVE_EXECUTION."
        ),
    }
