"""
ChangeNOW partner API — non-custodial swaps with revenue-share (no subscription).

Funds are sent by the user directly to ChangeNOW deposit addresses; BLACKDARK never
custodies assets. Server-side API key is required only to create attributed exchanges.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any

import aiohttp

from config import (
    CHANGENOW_API_KEY,
    CHANGENOW_PARTNER_FEE_PERCENT,
    CHANGENOW_REFERRAL_LINK,
)

logger = logging.getLogger("BLACKDARK.ChangeNOW")

_BASE = "https://api.changenow.io"
_TIMEOUT = aiohttp.ClientTimeout(total=20)
_HEADERS = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

_TICKER_RE = re.compile(r"^[a-z0-9]{2,16}$")
_ADDRESS_MIN = 8
_ADDRESS_MAX = 256

_USER_MESSAGES: dict[str, str] = {
    "invalid_amount": (
        "Enter a positive number for the amount to send (for example 0.001). "
        "Use digits and a decimal point only — no spaces, commas, or currency symbols."
    ),
    "amount_below_minimum": (
        "Amount is below the ChangeNOW minimum for this pair. Increase the amount or choose another pair."
    ),
    "invalid_payout_address": (
        "Enter the full wallet address where you want to receive funds (at least 8 characters, no spaces)."
    ),
    "invalid_pair": "Choose a valid currency pair from the lists.",
    "changenow_error": "ChangeNOW could not create this swap right now. Try again in a few minutes.",
}


def _err(code: str, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"error": code, "message": _USER_MESSAGES.get(code, "Request failed.")}
    row.update(extra)
    return row


def parse_swap_amount(raw: Any) -> float | None:
    """Normalize user/API amount input to a positive float."""
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        val = float(raw)
        if not math.isfinite(val) or val <= 0:
            return None
        return val
    s = str(raw).strip()
    if not s:
        return None
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[^\d.,\-+eE]", "", s)
    if not s or s in {".", ",", "-", "+", "-.", "+."}:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        val = float(s)
    except ValueError:
        return None
    if not math.isfinite(val) or val <= 0:
        return None
    return val


def swap_meta() -> dict[str, Any]:
    return {
        "provider": "changenow",
        "non_custodial": True,
        "custody_model": "user_to_changenow_deposit",
        "api_configured": bool(CHANGENOW_API_KEY),
        "partner_fee_percent": CHANGENOW_PARTNER_FEE_PERCENT,
        "commission_model": "revenue_share",
        "attribution": "Powered by ChangeNOW",
        "referral_fallback_url": CHANGENOW_REFERRAL_LINK or None,
    }


def _norm_ticker(raw: str) -> str:
    return (raw or "").lower().strip()


def _norm_network(raw: str | None, fallback_ticker: str) -> str:
    n = _norm_ticker(raw or "")
    return n or fallback_ticker


async def _get_json(
    path: str,
    *,
    params: dict[str, str] | None = None,
    api_key: bool = False,
) -> Any | None:
    headers = dict(_HEADERS)
    if api_key and CHANGENOW_API_KEY:
        headers["x-changenow-api-key"] = CHANGENOW_API_KEY
    url = f"{_BASE}{path}"
    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT, headers=headers) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.debug("ChangeNOW GET %s -> %s", path, resp.status)
                    return None
                return await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


async def _post_json(path: str, body: dict[str, Any]) -> tuple[int, Any | None]:
    headers = dict(_HEADERS)
    if not CHANGENOW_API_KEY:
        return 503, None
    headers["x-changenow-api-key"] = CHANGENOW_API_KEY
    url = f"{_BASE}{path}"
    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT, headers=headers) as session:
            async with session.post(url, json=body) as resp:
                try:
                    data = await resp.json()
                except (TypeError, ValueError):
                    data = None
                return resp.status, data
    except aiohttp.ClientError:
        return 502, None


async def fetch_currencies(limit: int = 400) -> list[dict[str, Any]]:
    data = await _get_json(
        "/v2/exchange/currencies",
        params={"active": "true", "flow": "standard"},
    )
    if not isinstance(data, list):
        return []
    rows: list[dict[str, Any]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        ticker = _norm_ticker(str(row.get("ticker") or ""))
        network = _norm_network(row.get("network"), ticker)
        if not _TICKER_RE.match(ticker):
            continue
        rows.append(
            {
                "ticker": ticker,
                "name": row.get("name"),
                "network": network,
                "image": row.get("image"),
                "isFiat": bool(row.get("isFiat")),
            }
        )
    return rows[:limit]


async def fetch_min_amount(
    from_currency: str,
    to_currency: str,
    *,
    from_network: str | None = None,
    to_network: str | None = None,
) -> dict[str, Any] | None:
    fc = _norm_ticker(from_currency)
    tc = _norm_ticker(to_currency)
    if not _TICKER_RE.match(fc) or not _TICKER_RE.match(tc):
        return None
    fn = _norm_network(from_network, fc)
    tn = _norm_network(to_network, tc)
    data = await _get_json(
        "/v2/exchange/min-amount",
        params={
            "fromCurrency": fc,
            "toCurrency": tc,
            "fromNetwork": fn,
            "toNetwork": tn,
            "flow": "standard",
        },
    )
    if isinstance(data, dict) and data.get("minAmount") is not None:
        return {
            "from_currency": fc,
            "to_currency": tc,
            "from_network": fn,
            "to_network": tn,
            "min_amount": float(data["minAmount"]),
        }
    legacy = await _get_json(f"/v1/min-amount/{fc}_{tc}")
    if isinstance(legacy, dict) and legacy.get("minAmount") is not None:
        return {
            "from_currency": fc,
            "to_currency": tc,
            "from_network": fn,
            "to_network": tn,
            "min_amount": float(legacy["minAmount"]),
        }
    return None


async def fetch_estimate(
    from_currency: str,
    to_currency: str,
    from_amount: float,
    *,
    from_network: str | None = None,
    to_network: str | None = None,
) -> dict[str, Any] | None:
    fc = _norm_ticker(from_currency)
    tc = _norm_ticker(to_currency)
    if not _TICKER_RE.match(fc) or not _TICKER_RE.match(tc):
        return None
    if from_amount <= 0:
        return None
    fn = _norm_network(from_network, fc)
    tn = _norm_network(to_network, tc)
    amt = f"{from_amount:.12f}".rstrip("0").rstrip(".")
    if CHANGENOW_API_KEY:
        data = await _get_json(
            "/v2/exchange/estimated-amount",
            params={
                "fromCurrency": fc,
                "toCurrency": tc,
                "fromNetwork": fn,
                "toNetwork": tn,
                "fromAmount": amt,
                "flow": "standard",
                "type": "direct",
            },
            api_key=True,
        )
        if isinstance(data, dict) and data.get("toAmount") is not None:
            return {
                "from_currency": fc,
                "to_currency": tc,
                "from_amount": from_amount,
                "to_amount": float(data["toAmount"]),
                "flow": "standard",
                "source": "changenow_v2",
            }
    key_q = CHANGENOW_API_KEY or ""
    legacy = await _get_json(
        f"/v1/exchange-amount/{amt}_{fc}_{tc}",
        params={"api_key": key_q} if key_q else None,
    )
    if isinstance(legacy, dict) and legacy.get("estimatedAmount") is not None:
        return {
            "from_currency": fc,
            "to_currency": tc,
            "from_amount": from_amount,
            "to_amount": float(legacy["estimatedAmount"]),
            "flow": "standard",
            "source": "changenow_v1",
            "transaction_speed_forecast": legacy.get("transactionSpeedForecast"),
        }
    return None


def _valid_payout_address(address: str) -> bool:
    cleaned = (address or "").strip()
    if len(cleaned) < _ADDRESS_MIN or len(cleaned) > _ADDRESS_MAX:
        return False
    if any(ch.isspace() for ch in cleaned):
        return False
    return True


async def create_exchange(
    *,
    from_currency: str,
    to_currency: str,
    from_amount: float,
    payout_address: str,
    from_network: str | None = None,
    to_network: str | None = None,
    refund_address: str | None = None,
    payout_extra_id: str | None = None,
    refund_extra_id: str | None = None,
) -> tuple[int, dict[str, Any] | None]:
    if not CHANGENOW_API_KEY:
        return 503, {
            "error": "swap_not_configured",
            "message": "ChangeNOW API key is not configured on this deployment.",
            "non_custodial": True,
            "referral_fallback_url": CHANGENOW_REFERRAL_LINK or None,
        }
    fc = _norm_ticker(from_currency)
    tc = _norm_ticker(to_currency)
    if not _TICKER_RE.match(fc) or not _TICKER_RE.match(tc):
        return 400, _err("invalid_pair", non_custodial=True)
    if from_amount <= 0:
        return 400, _err("invalid_amount", non_custodial=True)
    if not _valid_payout_address(payout_address):
        return 400, _err("invalid_payout_address", non_custodial=True)
    fn = _norm_network(from_network, fc)
    tn = _norm_network(to_network, tc)
    min_row = await fetch_min_amount(fc, tc, from_network=fn, to_network=tn)
    if min_row and from_amount < float(min_row["min_amount"]):
        return 400, _err(
            "amount_below_minimum",
            non_custodial=True,
            min_amount=min_row["min_amount"],
            from_currency=fc,
            to_currency=tc,
        )
    amt = f"{from_amount:.12f}".rstrip("0").rstrip(".")
    body: dict[str, Any] = {
        "fromCurrency": fc,
        "toCurrency": tc,
        "fromNetwork": fn,
        "toNetwork": tn,
        "fromAmount": amt,
        "address": payout_address.strip(),
        "flow": "standard",
        "type": "direct",
        "source": "blackdark",
    }
    if refund_address and _valid_payout_address(refund_address):
        body["refundAddress"] = refund_address.strip()
    if payout_extra_id:
        body["extraId"] = str(payout_extra_id).strip()[:128]
    if refund_extra_id:
        body["refundExtraId"] = str(refund_extra_id).strip()[:128]
    status, data = await _post_json("/v2/exchange", body)
    if status != 200 or not isinstance(data, dict):
        if isinstance(data, dict):
            msg = str(data.get("message") or data.get("error") or "").lower()
            if "min" in msg and "amount" in msg:
                return 400, _err(
                    "amount_below_minimum",
                    non_custodial=True,
                    min_amount=min_row.get("min_amount") if min_row else None,
                    provider_detail=data,
                )
        detail = _err("changenow_error", non_custodial=True, status=status)
        if isinstance(data, dict) and data.get("message"):
            detail["provider_message"] = data.get("message")
        return status if status >= 400 else 502, detail
    return 200, {
        "id": data.get("id"),
        "status": data.get("status"),
        "payin_address": data.get("payinAddress"),
        "payin_extra_id": data.get("payinExtraId"),
        "payout_address": data.get("payoutAddress"),
        "from_currency": fc,
        "to_currency": tc,
        "from_amount": data.get("fromAmount") or from_amount,
        "to_amount": data.get("toAmount"),
        "provider": "changenow",
        "non_custodial": True,
        "message": (
            "Send the exact amount to the pay-in address below. "
            "BLACKDARK does not hold your funds — ChangeNOW executes the swap."
        ),
        "partner_fee_percent": CHANGENOW_PARTNER_FEE_PERCENT,
    }


async def fetch_transaction_status(exchange_id: str) -> dict[str, Any] | None:
    eid = (exchange_id or "").strip()
    if len(eid) != 14 or not eid.isalnum():
        return None
    if not CHANGENOW_API_KEY:
        return None
    data = await _get_json(f"/v2/exchange/by-id/{eid}", api_key=True)
    if not isinstance(data, dict):
        return None
    return {
        "id": data.get("id"),
        "status": data.get("status"),
        "payin_address": data.get("payinAddress"),
        "payout_address": data.get("payoutAddress"),
        "provider": "changenow",
        "non_custodial": True,
    }
