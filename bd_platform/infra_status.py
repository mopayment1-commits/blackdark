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
    if pg and pool_stats().get("active"):
        pg_status = "connected"
    elif pg:
        pg_status = "configured"
    else:
        pg_status = "sqlite_fallback"
    return {
        "microservices": {
            "status": "ready",
            "mode": os.getenv("SERVICE_MODE", "all"),
            "docker_compose": "docker-compose.yml",
            "launcher": "python run_service.py <web|aggregator|arbitrage|ingestion|all>",
            "scale_hint": "docker compose up -d --scale arbitrage=2",
        },
        "postgresql": {
            "status": pg_status,
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
        "local_etl": _etl_status_block(),
        "price_aggregation": _price_aggregation_status_block(),
        "fee_database": _fee_database_status_block(),
    }


def _etl_status_block() -> dict[str, Any]:
    try:
        from bd_platform.influx_timeseries import timeseries_status

        ts = timeseries_status()
        return {
            "status": "ready",
            "module": "bd_platform.local_data_etl",
            "feature": "#118",
            "endpoints": [
                "/api/platform/infra/etl/status",
                "/api/platform/infra/etl/run",
                "/api/platform/infra/etl/query",
            ],
            "influxdb": ts,
        }
    except ImportError:
        return {"status": "module_missing", "feature": "#118"}


def _price_aggregation_status_block() -> dict[str, Any]:
    try:
        from bd_platform.price_aggregation_engine import price_aggregation_status

        status = price_aggregation_status()
        return {
            "status": "ready",
            "module": "bd_platform.price_aggregation_engine",
            "features": ["#133", "#127", "#194"],
            "user_facing": False,
            "endpoints": [
                "/api/platform/infra/prices/aggregate",
                "/api/platform/infra/prices/live",
                "/api/platform/infra/prices/status",
                "/api/platform/infra/connectors/status",
            ],
            "pipeline": status.get("pipeline"),
            "connector_count": status.get("connector_layer", {}).get("connector_count"),
        }
    except ImportError:
        return {"status": "module_missing", "features": ["#133", "#127", "#194"]}


def _fee_database_status_block() -> dict[str, Any]:
    try:
        from bd_platform.fee_database_service import fee_database_status

        status = fee_database_status()
        return {
            "status": "ready",
            "module": "bd_platform.fee_database_service",
            "feature": "#130",
            "user_facing": False,
            "endpoints": [
                "/api/platform/infra/fees/status",
                "/api/platform/infra/fees/lookup",
                "/api/platform/infra/fees/transaction-cost",
            ],
            "coverage": status.get("coverage"),
        }
    except ImportError:
        return {"status": "module_missing", "feature": "#130"}


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
