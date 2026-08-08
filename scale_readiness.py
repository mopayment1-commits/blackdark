"""
BLACKDARK — Concurrent scale readiness (honest capacity posture).

Code can enable high concurrency; proven HA still requires signed
Postgres+Redis multi-worker load evidence (see docs/LOAD_TEST_RUN_LOG.md).
"""

from __future__ import annotations

import os
from typing import Any

import config


def scale_readiness_report() -> dict[str, Any]:
    from postgres_backend import pool_stats, use_postgres
    from security_auth import login_rate_limit_backend
    from viral_capacity import effective_parallelism

    soft_launch = os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}
    redis_url = (getattr(config, "REDIS_URL", "") or "").strip()
    redis_ok = bool(redis_url) and not getattr(config, "SERVICE_BUS_LOCAL", True)
    pg = use_postgres()
    pool = pool_stats() if pg else {"active": False}
    parallel = effective_parallelism()
    rl_backend = login_rate_limit_backend()

    checks = [
        {
            "id": "postgres",
            "ok": pg,
            "required_for_ha": True,
            "detail": "postgresql" if pg else "sqlite",
        },
        {
            "id": "postgres_pool",
            "ok": bool(pool.get("active")),
            "required_for_ha": True,
            "detail": pool,
        },
        {
            "id": "redis_shared",
            "ok": redis_ok,
            "required_for_ha": True,
            "detail": "REDIS_URL set and SERVICE_BUS_LOCAL=false" if redis_ok else "missing",
        },
        {
            "id": "login_rate_limit_shared",
            "ok": rl_backend == "redis",
            "required_for_ha": True,
            "detail": rl_backend,
        },
        {
            "id": "multi_worker",
            "ok": parallel["parallelism"] >= 2 and pg and redis_ok,
            "required_for_ha": True,
            "detail": parallel,
        },
        {
            "id": "soft_launch_honesty",
            "ok": not soft_launch or not pg,
            "required_for_ha": False,
            "detail": "SOFT_LAUNCH demo is not HA" if soft_launch else "strict/non-soft",
        },
    ]
    ha_ready = all(c["ok"] for c in checks if c["required_for_ha"])
    return {
        "product": "BLACKDARK",
        "ha_ready_codepath": ha_ready,
        "soft_launch": soft_launch,
        "database": "postgresql" if pg else "sqlite",
        "login_rate_limit_backend": rl_backend,
        "postgres_pool": pool,
        "parallelism": parallel,
        "recommended_env": {
            "DATABASE_URL": "postgresql://...",
            "REDIS_URL": "redis://...",
            "SERVICE_BUS_LOCAL": "false",
            "WEB_CONCURRENCY": "4+",
            "WEB_REPLICAS": "2+",
            "PG_POOL_MAX": str(getattr(config, "PG_POOL_MAX", 20)),
            "SOFT_LAUNCH": "unset for institutional pitch",
            "VIRAL_MODE": "true",
        },
        "checks": checks,
        "capacity_claim": {
            "code_enables_high_concurrency": True,
            "proven_high_concurrency_signed": False,
            "proof_path": "docs/LOAD_TEST_RUN_LOG.md",
            "note": (
                "Do not claim production HA concurrent capacity until a signed "
                "Postgres+Redis multi-worker row is recorded in LOAD_TEST_RUN_LOG.md."
            ),
        },
        "viral": {
            "readiness_api": "/api/viral/readiness",
            "playbook": "docs/VIRAL_LAUNCH_CAPACITY.md",
            "protections": [
                "load_shedding",
                "oracle_semaphore",
                "shared_rate_limits",
                "quick_cache",
            ],
        },
        "k8s": {
            "web_deployment": "deploy/k8s/web-deployment.yaml",
            "worker_deployments": "deploy/k8s/workers-deployment.yaml",
            "hpa": "deploy/k8s/workers-hpa.yaml",
        },
    }
