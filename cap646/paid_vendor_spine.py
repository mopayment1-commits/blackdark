"""Reusable paid-vendor spine — full design, env-gated activation.

Capabilities that require a paid third-party API must:
  1. Ship complete handler + response parsing + tests.
  2. Return an explicit PENDING_PAYMENT state when the API key is absent.
  3. Activate live calls only when a real key is present in the environment.
  4. Never emit placeholder metrics or auto-start free trials.

Future paid vendors: register in ``PAID_VENDOR_REGISTRY`` and reuse ``build_pending_payment_payload``.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import aiohttp

from path_safety import assert_url_path_safe

_HEADERS_JSON = {"Accept": "application/json", "User-Agent": "BLACKDARK-PaidVendor/1.0"}

_PLACEHOLDER_KEYS = frozenset(
    {
        "",
        "yourapikeytoken",
        "changeme",
        "pending",
        "none",
        "null",
        "placeholder",
        "test",
    }
)

PENDING_PAYMENT_STATUS = "PENDING_PAYMENT"


@dataclass(frozen=True, slots=True)
class PaidVendorSpec:
    vendor_id: str
    vendor_label: str
    env_var: str
    subscription_note: str


@dataclass(frozen=True, slots=True)
class PaidCapabilitySpec:
    capability_id: int
    catalog_goal: str
    vendor: PaidVendorSpec


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def paid_vendor_api_key(env_var: str) -> str | None:
    """Return a configured API key, or None when activation is not allowed."""
    raw = os.getenv(env_var, "").strip()
    if not raw or raw.lower() in _PLACEHOLDER_KEYS:
        return None
    return raw


def is_paid_vendor_active(env_var: str) -> bool:
    return paid_vendor_api_key(env_var) is not None


def pending_payment_message(vendor_label: str) -> str:
    return f"{PENDING_PAYMENT_STATUS} — requires {vendor_label} subscription"


def build_pending_payment_payload(
    spec: PaidCapabilitySpec,
    *,
    symbol: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Honest deferred response — no fake vendor metrics."""
    payload: dict[str, Any] = {
        "ok": True,
        "feature_ref": spec.capability_id,
        "symbol": symbol.upper(),
        "catalog_goal": spec.catalog_goal,
        "vendor_status": PENDING_PAYMENT_STATUS,
        "status": pending_payment_message(spec.vendor.vendor_label),
        "vendor": spec.vendor.vendor_id,
        "vendor_label": spec.vendor.vendor_label,
        "env_var": spec.vendor.env_var,
        "subscription_note": spec.vendor.subscription_note,
        "data_available": False,
        "live_vendor_call": False,
        "activation_note": f"Set {spec.vendor.env_var} to enable live data — no code change required",
        "data_freshness": _utcnow(),
    }
    if extra:
        payload.update(extra)
    return payload


async def paid_vendor_get_json(
    url: str,
    *,
    api_key: str,
    params: dict[str, Any] | None = None,
    auth_header: str = "Authorization",
    auth_scheme: str = "Bearer",
) -> dict[str, Any] | None:
    """Authenticated GET for a paid vendor endpoint."""
    t0 = time.perf_counter()
    timeout = aiohttp.ClientTimeout(total=20)
    headers = dict(_HEADERS_JSON)
    headers[auth_header] = f"{auth_scheme} {api_key}"
    try:
        safe_url = assert_url_path_safe(url)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(safe_url, headers=headers, params=params) as resp:
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)
                if resp.status != 200:
                    return {
                        "ok": False,
                        "http_status": resp.status,
                        "latency_ms": latency_ms,
                        "error": "vendor_http_error",
                    }
                body = await resp.json()
                if not isinstance(body, dict):
                    return {"ok": False, "latency_ms": latency_ms, "error": "invalid_vendor_json"}
                body["_latency_ms"] = latency_ms
                return body
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


CRYPTOQUANT_VENDOR = PaidVendorSpec(
    vendor_id="cryptoquant",
    vendor_label="CryptoQuant",
    env_var="CRYPTOQUANT_API_KEY",
    subscription_note="Professional/Premium plan (~$29/mo documented minimum) — owner decision required",
)

PAID_VENDOR_REGISTRY: dict[str, PaidVendorSpec] = {
    "cryptoquant": CRYPTOQUANT_VENDOR,
}
