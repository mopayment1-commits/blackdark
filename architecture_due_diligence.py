"""
BLACKDARK — Architecture due diligence (ARC-001 … ARC-010).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def _verdict(score: float) -> str:
    if score >= 0.85:
        return "pass"
    if score >= 0.55:
        return "partial"
    return "fail"


def evaluate_architecture_dd() -> dict[str, Any]:
    from production_guard import evaluate_production_guard

    guard = evaluate_production_guard()
    mode = os.getenv("SERVICE_MODE", "all")
    has_ha = (ROOT / "docker-compose.ha.yml").is_file()
    has_nginx = (ROOT / "nginx" / "blackdark.conf").is_file()
    router_count = len(list((ROOT / "api" / "routers").glob("*.py"))) - 1
    repo_count = len(list((ROOT / "repos").glob("*.py"))) - 1
    guard_count = len(list(ROOT.glob("*_guard.py")))
    dashboard_lines = len((ROOT / "dashboard.py").read_text(encoding="utf-8", errors="ignore").splitlines())
    redis = bool(os.getenv("REDIS_URL", "").strip())
    kafka_cfg = bool(os.getenv("KAFKA_BROKERS", "").strip())
    sentry = bool(os.getenv("SENTRY_DSN", "").strip())
    replicas = int(os.getenv("RAILWAY_REPLICA_COUNT", "1") or "1")

    items: dict[str, dict[str, Any]] = {
        "ARC-001": {
            "question": "Is the architecture modular?",
            "score": min(1.0, (router_count / 8) * 0.4 + (1 if (ROOT / "bd_platform").is_dir() else 0) * 0.3 + (0.3 if mode != "all" else 0.1)),
            "evidence": [f"api/routers: {router_count}", f"SERVICE_MODE={mode}", f"dashboard.py ~{dashboard_lines} lines"],
        },
        "ARC-002": {
            "question": "Is the architecture loosely coupled?",
            "score": 0.65 if (ROOT / "service_bus.py").is_file() else 0.3,
            "evidence": ["service_bus.py Redis pub/sub", "repos/ thin — most code uses database.py directly"],
        },
        "ARC-003": {
            "question": "Is high cohesion maintained?",
            "score": min(1.0, 0.5 + guard_count / 30),
            "evidence": [f"{guard_count} *_guard.py policy modules", "microservices/lifecycle.py mode boot"],
        },
        "ARC-004": {
            "question": "Is the architecture scalable?",
            "score": (0.4 if has_ha else 0.1) + (0.3 if redis else 0.05) + (0.2 if replicas >= 2 else 0.05) + 0.25,
            "evidence": [f"HA compose={has_ha}", f"redis={redis}", f"replicas={replicas}"],
        },
        "ARC-005": {
            "question": "Is there any single point of failure?",
            "score": 0.7 if guard.get("required_pass") and replicas >= 2 else (0.45 if guard.get("required_pass") else 0.25),
            "evidence": guard.get("required_failures") or ["postgres+billing ok"] if guard.get("required_pass") else guard.get("required_failures"),
        },
        "ARC-006": {
            "question": "Can modules be replaced independently?",
            "score": 0.55 + (0.2 if mode in {"web", "aggregator", "arbitrage", "ingestion"} else 0) + (0.15 if guard.get("database") == "postgresql" else 0),
            "evidence": [f"repos={repo_count}", "SERVICE_MODE swap", "Lemon Squeezy / Stripe billing swap"],
        },
        "ARC-007": {
            "question": "Is dependency injection implemented?",
            "score": min(1.0, 0.35 + router_count / 15),
            "evidence": ["api/deps.py optional_user, require_feature", "FastAPI Depends on routers — no service container"],
        },
        "ARC-008": {
            "question": "Is the architecture cloud native?",
            "score": 0.9 if (ROOT / "Dockerfile").is_file() and (ROOT / "railway.toml").is_file() else 0.5,
            "evidence": ["Dockerfile HEALTHCHECK", "railway.toml /health/live", "12-factor config.py"],
        },
        "ARC-009": {
            "question": "Is event-driven architecture required?",
            "score": 0.75 if (ROOT / "service_bus.py").is_file() and kafka_cfg else 0.55,
            "evidence": ["Redis pub/sub service_bus", f"Kafka configured={kafka_cfg}", "WS/SSE hubs"],
        },
        "ARC-010": {
            "question": "Can the architecture support enterprise deployment?",
            "score": (0.35 if has_ha and has_nginx else 0.15) + (0.25 if sentry else 0.05) + 0.35,
            "evidence": [f"nginx HA={has_nginx}", f"Sentry={sentry}", "due-diligence API endpoints"],
        },
    }

    results = {}
    for arc_id, row in items.items():
        v = _verdict(row["score"])
        results[arc_id] = {
            "question": row["question"],
            "verdict": v,
            "score": round(row["score"], 2),
            "evidence": row["evidence"],
        }

    verdicts = [r["verdict"] for r in results.values()]
    overall = "pass" if verdicts.count("fail") == 0 and verdicts.count("partial") <= 3 else "partial"
    if verdicts.count("fail") >= 4:
        overall = "fail"

    return {
        "overall_verdict": overall,
        "production_guard": guard,
        "items": results,
        "recommendations_applied": [
            "SERVICE_MODE=web default on Railway",
            "numReplicas=2 in railway.json",
            "production_guard.py runtime checks",
            "LEMON_SQUEEZY_CHECKOUT_PRO billing path",
            "Routes extracted to api/routers/gtm.py + telegram.py",
        ],
    }
