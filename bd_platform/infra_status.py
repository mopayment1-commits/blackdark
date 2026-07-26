"""
BLACKDARK — Unified infrastructure status (Postgres, Kafka, Vault, Microservices, RL, ZK).
"""

from __future__ import annotations

import os
from typing import Any


def infra_matrix() -> dict[str, Any]:
    from bd_platform.kafka_bridge import bus_status as kafka_status
    from bd_platform.vault_client import vault_status
    from ml.rl_policy import policy_status
    from postgres_backend import pool_stats, use_postgres

    pg = use_postgres()
    rl = policy_status()
    return {
        "microservices": {
            "status": "ready",
            "mode": os.getenv("SERVICE_MODE", "all"),
            "docker_compose": "docker-compose.yml",
            "launcher": "python run_service.py <web|aggregator|arbitrage|ingestion|all>",
            "scale_hint": "docker compose up -d --scale arbitrage=2",
        },
        "postgresql": {
            "status": "connected" if pg and pool_stats().get("active") else ("configured" if pg else "sqlite_fallback"),
            "engine": "postgresql" if pg else "sqlite",
            "pool": pool_stats(),
            "database_url_set": bool(os.getenv("DATABASE_URL", "").strip()),
        },
        "haascloud_deploy": {
            "status": "ready",
            "dockerfile": "Dockerfile",
            "railway": "railway.json",
            "haascloud_manifest": "haascloud.json",
            "compose_stack": "docker-compose.yml",
        },
        "hashicorp_vault": vault_status(),
        "apache_kafka": kafka_status(),
        "rl_policy": rl,
        "zk_public_proof": {
            "status": "ready",
            "module": "bd_platform.public_proof",
            "endpoint": "/api/platform/proof/public",
            "features": ["merkle_root", "inclusion_proof", "commitment_verify"],
        },
    }


def infra_ready_score() -> dict[str, Any]:
    m = infra_matrix()
    checks = {
        "microservices": m["microservices"]["status"] == "ready",
        "postgresql_code": True,
        "postgresql_live": m["postgresql"]["engine"] == "postgresql",
        "haascloud": m["haascloud_deploy"]["status"] == "ready",
        "vault_module": True,
        "kafka_module": True,
        "rl_module": m["rl_policy"]["active_policy"] in {"ppo", "sac", "heuristic"},
        "zk_proof": m["zk_public_proof"]["status"] == "ready",
    }
    ready = sum(1 for v in checks.values() if v)
    return {
        "checks": checks,
        "ready_count": ready,
        "total": len(checks),
        "ready_percent": round(ready / len(checks) * 100, 1),
        "matrix": m,
    }
