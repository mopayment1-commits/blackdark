"""
Security Rate Limiting Layer — API gateway cross-cutting protection (#1046).

NOT standalone. Security gate (IP/bot/brute-force) runs BEFORE billing quota (#908)
and authZ (#1022). Complements viral_capacity middleware.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import HTTPException, Request
from starlette.responses import JSONResponse

logger = logging.getLogger("BLACKDARK.SecurityRateLimit")

_FEATURE = "security_rate_limiting"
_SEED_PATH = Path("data/security_rate_limiting_seed.json")
_AUDIT_PATH = Path("data/security_rate_limit_audit.jsonl")

_INCIDENT_REF = 1017
_ACTIVITY_REF = 1038
_BILLING_REF = 908
_SESSION_REF = 1019

Tier = Literal["anonymous", "free", "pro", "institution"]

_buckets: dict[str, list[float]] = defaultdict(list)
_blocked_ips: dict[str, float] = {}
_backend = "memory"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("security_rate_limiting") or {}


def _client_ip(request: Request) -> str:
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


def _path_class(path: str) -> str | None:
    if path.startswith("/api/auth"):
        return "auth"
    if path.startswith("/api/"):
        return "api"
    return None


def _detect_tier(request: Request) -> Tier:
    tier_hdr = (request.headers.get("x-bd-tier") or "").strip().lower()
    if tier_hdr in {"pro", "institution", "free"}:
        return tier_hdr  # type: ignore[return-value]
    if request.headers.get("authorization") or request.cookies.get("bd_token"):
        return "free"
    return "anonymous"


def _limit_for_tier(tier: Tier, *, seed: dict[str, Any] | None = None) -> int:
    api = (_cfg(seed).get("api_endpoints") or {})
    mapping = {
        "anonymous": int(api.get("anonymous_per_min", 100)),
        "free": int(api.get("free_tier_per_min", 100)),
        "pro": int(api.get("pro_tier_per_min", 10000)),
        "institution": int(api.get("pro_tier_per_min", 10000)),
    }
    return mapping.get(tier, 100)


def _is_bot_like(request: Request) -> bool:
    ua = (request.headers.get("user-agent") or "").strip()
    if not ua:
        return True
    bot_tokens = ("python-requests", "scrapy", "curl/", "wget/", "httpclient")
    lower = ua.lower()
    return any(tok in lower for tok in bot_tokens)


def _record_audit(
    *,
    ip: str,
    path: str,
    action: str,
    count: int,
    tier: str = "anonymous",
    user: str = "",
) -> None:
    entry = {
        "ts": time.time(),
        "iso": _utcnow(),
        "feature": _FEATURE,
        "ip": ip,
        "path": path,
        "tier": tier,
        "user": user,
        "count": count,
        "action": action,
    }
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("rate limit audit write failed", exc_info=True)


def _check_bucket(key: str, *, limit: int, window_sec: int) -> tuple[bool, int]:
    global _backend
    now = time.time()
    window = _buckets[key]
    _buckets[key] = [t for t in window if now - t < window_sec]
    count = len(_buckets[key])
    if count >= limit:
        return False, count
    _buckets[key].append(now)
    _backend = "memory"
    return True, count + 1


def check_auth_rate_limit(*, ip: str, account: str = "") -> None:
    """Auth endpoints: 5/IP/5min + 10/account/hour."""
    seed = _load_seed()
    auth = _cfg(seed).get("auth_endpoints") or {}
    ip_limit = int(auth.get("attempts_per_ip_per_5min", 5))
    acct_limit = int(auth.get("attempts_per_account_per_hour", 10))

    ok, count = _check_bucket(f"auth:ip:{ip}", limit=ip_limit, window_sec=300)
    if not ok:
        _record_audit(ip=ip, path="/api/auth/*", action="blocked_ip", count=count)
        raise HTTPException(
            status_code=429,
            detail="Too many authentication attempts from this IP.",
            headers={"Retry-After": "300"},
        )
    if account:
        ok2, acct_count = _check_bucket(
            f"auth:acct:{account.lower()}", limit=acct_limit, window_sec=3600
        )
        if not ok2:
            _record_audit(ip=ip, path="/api/auth/*", action="blocked_account", count=acct_count, user=account)
            raise HTTPException(
                status_code=429,
                detail="Too many authentication attempts for this account.",
                headers={"Retry-After": "3600"},
            )


def check_api_rate_limit(request: Request) -> None:
    """General API rate limit by tier."""
    ip = _client_ip(request)
    if ip in _blocked_ips and time.time() < _blocked_ips[ip]:
        raise HTTPException(status_code=429, detail="Temporarily blocked.", headers={"Retry-After": "60"})

    tier = _detect_tier(request)
    limit = _limit_for_tier(tier)
    key = f"api:{tier}:{ip}"
    ok, count = _check_bucket(key, limit=limit, window_sec=60)
    if not ok:
        _record_audit(ip=ip, path=request.url.path, action="throttled", count=count, tier=tier)
        _maybe_trigger_attack_incident(ip, count)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded.",
            headers={"Retry-After": "60"},
        )

    scraping = (_cfg().get("scraping_protection") or {})
    if scraping.get("enabled") and _is_bot_like(request):
        _record_audit(ip=ip, path=request.url.path, action="bot_signature", count=count, tier=tier)
        if scraping.get("bot_signature_challenge"):
            raise HTTPException(
                status_code=429,
                detail="Automated traffic detected — use official API client.",
                headers={"Retry-After": "120"},
            )


def _maybe_trigger_attack_incident(ip: str, count: int) -> None:
    threshold = int((_cfg().get("ddos_layer7") or {}).get("auto_block_threshold_per_min", 1000))
    if count < threshold:
        return
    _blocked_ips[ip] = time.time() + 3600
    try:
        from security_events import record_security_event

        record_security_event(
            "sustained_rate_limit_attack",
            severity="high",
            actor="security_rate_limiting",
            ip=ip,
            detail={
                "count_per_min": count,
                "action": "ip_blocked_1h",
                "integration_ref": _INCIDENT_REF,
            },
        )
    except ImportError:
        pass


def security_rate_limiting_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _cfg(seed)
    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "merged_into": seed.get("merged_into"),
        "policy_version": policy.get("policy_version", "1.0.0"),
        "backend_enforced": policy.get("backend_enforced", True),
        "auth_endpoints": policy.get("auth_endpoints") or {},
        "api_endpoints": policy.get("api_endpoints") or {},
        "scraping_protection": policy.get("scraping_protection") or {},
        "response": policy.get("response") or {},
        "gate_sequence": ["security_rate_limit", "billing_quota", "authz", "service"],
        "integrations": policy.get("integrations") or {},
        "backend": _backend,
        "audit_path": str(_AUDIT_PATH),
        "timestamp": _utcnow(),
    }


def check_security_rate_limiting_production_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _cfg(seed)
    auth = policy.get("auth_endpoints") or {}
    api = policy.get("api_endpoints") or {}
    checks = {
        "backend_enforced": policy.get("backend_enforced") is True,
        "auth_ip_limit": auth.get("attempts_per_ip_per_5min", 0) == 5,
        "auth_account_limit": auth.get("attempts_per_account_per_hour", 0) == 10,
        "anonymous_api_limit": api.get("anonymous_per_min", 0) == 100,
        "pro_api_limit": api.get("pro_tier_per_min", 0) == 10000,
        "scraping_protection": (policy.get("scraping_protection") or {}).get("enabled") is True,
        "retry_after_header": (policy.get("response") or {}).get("retry_after_header") is True,
        "audit_retention": policy.get("audit_retention_days", 0) >= 90,
        "billing_integration": (policy.get("integrations") or {}).get("pay_per_request_ref") == _BILLING_REF,
        "session_integration": (policy.get("integrations") or {}).get("session_security_ref") == _SESSION_REF,
    }
    return {
        "ok": all(checks.values()),
        "feature": _FEATURE,
        "blocks_production": policy.get("blocks_production", True),
        "checks": checks,
        "timestamp": _utcnow(),
    }


def run_security_rate_limiting_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    status = security_rate_limiting_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "backend_enforced", "passed": status["backend_enforced"] is True})
    checks.append({"id": "auth_5_per_5min", "passed": status["auth_endpoints"].get("attempts_per_ip_per_5min") == 5})
    checks.append({"id": "incident_integration", "passed": status["integrations"].get("incident_response_ref") == _INCIDENT_REF})
    gate = check_security_rate_limiting_production_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})
    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature": _FEATURE, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}


def security_rate_limiting_enabled() -> bool:
    return os.getenv("SECURITY_RATE_LIMITING", "true").lower() in {"1", "true", "yes"}


async def security_rate_limit_middleware(request: Request, call_next):
    """Security RL middleware — runs before billing/authZ."""
    if not security_rate_limiting_enabled():
        return await call_next(request)

    path = request.url.path or "/"
    kind = _path_class(path)
    if kind is None:
        return await call_next(request)

    try:
        if kind == "auth":
            ip = _client_ip(request)
            check_auth_rate_limit(ip=ip)
        else:
            check_api_rate_limit(request)
        response = await call_next(request)
        response.headers.setdefault("X-Security-RateLimit", "1")
        return response
    except HTTPException as exc:
        headers = dict(exc.headers or {})
        return JSONResponse(
            exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail},
            status_code=exc.status_code,
            headers=headers,
        )
