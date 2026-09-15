"""Secure transport policy and trusted proxy handling (FDS-09)."""

from __future__ import annotations

import ipaddress
import os
from typing import Any

from starlette.requests import Request

TLS_MIN_VERSION = "1.2"
TLS_PREFERRED_VERSION = "1.3"
HSTS_MAX_AGE = 31_536_000


def _is_production() -> bool:
    tokens = [
        (os.getenv("ENV") or "").strip().lower(),
        (os.getenv("APP_ENV") or "").strip().lower(),
        (os.getenv("ENVIRONMENT") or "").strip().lower(),
        (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
    ]
    return any(t in {"production", "prod"} for t in tokens)


def trusted_proxy_networks() -> list[ipaddress._BaseNetwork]:
    raw = (os.getenv("TRUSTED_PROXY_CIDRS") or os.getenv("TRUSTED_PROXY_IPS") or "").strip()
    if not raw:
        return []
    nets: list[ipaddress._BaseNetwork] = []
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        try:
            if "/" in token:
                nets.append(ipaddress.ip_network(token, strict=False))
            else:
                nets.append(ipaddress.ip_network(f"{token}/32", strict=False))
        except ValueError:
            continue
    return nets


def _peer_ip(request: Request) -> str | None:
    client = request.client
    if not client:
        return None
    return str(client.host or "")


def _trusted_forwarded_proto(request: Request) -> str | None:
    peer = _peer_ip(request)
    nets = trusted_proxy_networks()
    if not nets or not peer:
        return None
    try:
        addr = ipaddress.ip_address(peer)
    except ValueError:
        return None
    if not any(addr in net for net in nets):
        return None
    proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    return proto or None


def request_effective_scheme(request: Request) -> str:
    trusted = _trusted_forwarded_proto(request)
    if trusted in {"https", "http"}:
        return trusted
    return str(request.url.scheme or "http").lower()


def request_is_secure(request: Request) -> bool:
    if request_effective_scheme(request) == "https":
        return True
    if os.getenv("SECURE_TRANSPORT_OVERRIDE", "").strip().lower() in {"1", "true", "yes"}:
        return True
    return False


def enforce_secure_transport(request: Request, *, sensitive: bool = True) -> None:
    if not _is_production():
        return
    if not sensitive:
        return
    if request_is_secure(request):
        return
    raise PermissionError("insecure_transport_forbidden_in_production")


def transport_policy_status() -> dict[str, Any]:
    return {
        "tls_minimum_version": TLS_MIN_VERSION,
        "tls_preferred_version": TLS_PREFERRED_VERSION,
        "hsts_max_age": HSTS_MAX_AGE,
        "production": _is_production(),
        "trusted_proxy_configured": bool(trusted_proxy_networks()),
        "secure_cookie_required_in_production": _is_production(),
        "downgrade_allowed": not _is_production(),
        "ingress_contract": "https_only_in_production",
    }


def deployment_transport_contract() -> dict[str, Any]:
    violations: list[str] = []
    if _is_production():
        if not (os.getenv("APP_BASE_URL") or "").strip().lower().startswith("https://"):
            violations.append("app_base_url_not_https")
        if os.getenv("ALLOW_INSECURE_HTTP", "").strip().lower() in {"1", "true", "yes"}:
            violations.append("allow_insecure_http_forbidden")
    return {
        "contract": transport_policy_status(),
        "violations": violations,
        "fail_closed": len(violations) == 0 or not _is_production(),
    }
