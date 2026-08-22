"""
BLACKDARK — Honest public product surfaces used by Production E2E.

These endpoints exist so advertised readiness / inventory / L2 remainder /
changed-mind journeys fail closed with real payloads instead of HTTP 404.
They never invent live money, Full Mesh L2 100%, or multi-AZ HA.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def build_l2_remainder() -> dict[str, Any]:
    """Honest CORE L2 remainder — live venues vs planned remainder."""
    live: dict[str, Any] = {}
    planned: dict[str, Any] = {}
    next_wave: dict[str, Any] = {}
    try:
        from coverage_honesty import build_coverage_honesty_board

        board = await build_coverage_honesty_board()
        live = board.get("live") or {}
        planned = board.get("planned") or {}
        next_wave = board.get("next_wave") or {}
    except Exception:
        try:
            from platform_universe import exchanges_by_status

            live_rows = exchanges_by_status("ingestion_ready")
            mapped = exchanges_by_status("ccxt_mapped")
            live = {"count": len(live_rows), "ids": [r.get("id") for r in live_rows]}
            next_wave = {"count": len(mapped)}
            planned = {"count": 0}
        except Exception:
            live = {"count": 0, "ids": []}
            next_wave = {"count": 0}
            planned = {"count": 0}
    live_count = int(live.get("count") or 0)
    planned_count = int(planned.get("count") or 0)
    next_count = int(next_wave.get("count") or 0)
    remainder = max(0, planned_count + next_count)
    return {
        "surface": "l2_remainder",
        "generated_at": _utcnow(),
        "headline": "Venue L2 remainder — live depth, not vanity breadth",
        "live_venues": live_count,
        "live_ids": live.get("ids") or [],
        "next_wave_count": next_count,
        "planned_count": planned_count,
        "remainder_not_live": remainder,
        "full_mesh_claimed": False,
        "full_mesh_percent": None,
        "note": (
            "Remainder is roadmap / mapped venues not yet decision-grade. "
            "Full Mesh L2 100% is NOT claimed."
        ),
        "coverage_honesty": "/api/public/coverage-honesty",
        "page": "/coverage-honesty",
        "disclaimer": "Not financial advice. Planned venues are never sold as live.",
    }


async def build_capability_inventory() -> dict[str, Any]:
    """Capability inventory from platform registry + CAP646 closure sample."""
    from bd_platform.registry import FEATURE_MATRIX

    cap646_status = None
    try:
        from cap646.closure import final_institutional_verification

        cap646_status = await final_institutional_verification(sample_only=True)
    except Exception:
        cap646_status = {"verdict": "NOT READY", "error": "cap646_runtime_unavailable"}

    try:
        from production_guard import evaluate_production_guard

        guard = evaluate_production_guard()
    except Exception:
        guard = {"required_pass": False, "required_failures": ["unavailable"]}

    items = []
    for row in FEATURE_MATRIX:
        items.append(
            {
                "id": row.get("id"),
                "key": row.get("key"),
                "title": row.get("title"),
                "endpoint": row.get("endpoint"),
                "module": row.get("module"),
                "status": "shipped_codepath",
            }
        )
    return {
        "surface": "capability_inventory",
        "generated_at": _utcnow(),
        "count": len(items),
        "items": items,
        "production_guard": {
            "required_pass": guard.get("required_pass"),
            "required_failures": guard.get("required_failures") or [],
            "viral_mode": guard.get("viral_mode"),
            "billing_provider": guard.get("billing_provider"),
        },
        "honesty": (
            "Codepath inventory ≠ every journey LIVE-MONEY-READY. "
            "See production_guard.required_failures for ops blockers."
        ),
        "cap646_closure_sample": cap646_status,
        "api": "/api/product/capability-inventory",
    }


async def build_public_readiness() -> dict[str, Any]:
    """Public readiness probe — demo vs live-money tracks, no inflation."""
    try:
        from production_guard import evaluate_production_guard

        guard = evaluate_production_guard()
    except Exception:
        guard = {
            "required_pass": False,
            "required_failures": ["unavailable"],
            "viral_mode": False,
            "billing_provider": "none",
            "parallelism": {"workers": 1, "replicas": 1, "parallelism": 1},
        }

    try:
        from viral_capacity import viral_health_payload

        viral = viral_health_payload()
    except Exception:
        viral = {"ok": False, "redis_live": False}

    required_failures = list(guard.get("required_failures") or [])
    billing_ok = "billing_checkout" not in required_failures
    mfa_ok = "admin_mfa_configured" not in required_failures
    multi_ok = "viral_multi_instance" not in required_failures
    redis_ok = bool(viral.get("redis_live"))

    public_demo_ready = True  # process + oracle/radar surfaces exist
    live_production_ready = bool(guard.get("required_pass")) and redis_ok and multi_ok
    live_money_ready = bool(live_production_ready and billing_ok)

    return {
        "surface": "public_readiness",
        "generated_at": _utcnow(),
        "tracks": {
            "PUBLIC_DEMO_READY": public_demo_ready,
            "LIVE_PRODUCTION_READY": live_production_ready,
            "LIVE_MONEY_READY": live_money_ready,
        },
        "gates": {
            "production_guard_required_pass": bool(guard.get("required_pass")),
            "redis_live": redis_ok,
            "viral_multi_instance": multi_ok,
            "billing_checkout": billing_ok,
            "admin_mfa_configured": mfa_ok,
        },
        "required_failures": required_failures,
        "parallelism": guard.get("parallelism"),
        "billing_provider": guard.get("billing_provider"),
        "viral": {
            "ok": viral.get("ok"),
            "redis_live": viral.get("redis_live"),
            "parallelism": viral.get("parallelism"),
        },
        "unconditional_go": False if not live_money_ready else bool(guard.get("required_pass")),
        "note": (
            "PUBLIC-DEMO-READY can be true while LIVE-PRODUCTION-READY / "
            "LIVE-MONEY-READY remain false. Agent-env proofs are not Production PASS."
        ),
        "api": "/api/product/public-readiness",
        "guard_api": "/api/production/guard",
    }


async def build_changed_mind(*, limit: int = 25) -> dict[str, Any]:
    """Public changed-mind / miss revisions — honesty atom, not buried errors."""
    from public_miss_feed import build_public_miss_feed

    feed = await build_public_miss_feed(limit=limit)
    items = []
    for row in feed.get("items") or []:
        items.append(
            {
                "prediction_id": row.get("prediction_id"),
                "asset": row.get("asset"),
                "prior_verdict": row.get("verdict"),
                "label": row.get("label"),
                "lesson": row.get("lesson"),
                "timestamp": row.get("timestamp"),
                "changed_mind": True,
                "verify_href": row.get("verify_href") or "/miss-feed",
            }
        )
    return {
        "surface": "changed_mind",
        "generated_at": _utcnow(),
        "headline": "We changed our mind in public",
        "thesis": (
            "When a sealed decision is later labeled incorrect/partial, "
            "we publish the revision instead of burying it."
        ),
        "count": len(items),
        "items": items,
        "related": {
            "miss_feed": "/api/public/miss-feed",
            "contradiction_replay": "/api/contradiction-replay",
            "kill_rate": "/api/public/kill-rate",
        },
        "page": "/miss-feed",
        "api": "/api/public/changed-mind",
        "disclaimer": "Educational transparency — not financial advice.",
    }


async def build_decision_graph(*, asset: str = "BTC", limit: int = 12) -> dict[str, Any]:
    """Lightweight decision graph from recent public accuracy / miss context."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    try:
        from database import fetch_labeled_oracle_predictions

        rows = await fetch_labeled_oracle_predictions(limit=max(limit * 3, 40), include_synthetic=False)
    except Exception:
        rows = []

    asset_u = (asset or "BTC").upper()
    filtered = [
        r
        for r in (rows or [])
        if str(r.get("asset") or r.get("symbol") or "").upper() in {asset_u, f"{asset_u}USDT", ""}
        or True
    ]
    for idx, r in enumerate(filtered[:limit]):
        nid = str(r.get("id") or r.get("prediction_id") or f"n{idx}")
        nodes.append(
            {
                "id": nid,
                "asset": str(r.get("asset") or r.get("symbol") or asset_u).upper(),
                "verdict": r.get("verdict") or r.get("action"),
                "label": r.get("label"),
                "score": r.get("opportunity_score") or r.get("score"),
                "timestamp": r.get("timestamp") or r.get("created_at"),
            }
        )
        if idx > 0:
            prev = nodes[idx - 1]["id"]
            edges.append({"from": prev, "to": nid, "rel": "next_decision"})

    return {
        "surface": "decision_graph",
        "generated_at": _utcnow(),
        "asset": asset_u,
        "nodes": nodes,
        "edges": edges,
        "count_nodes": len(nodes),
        "count_edges": len(edges),
        "api": "/api/public/decision-graph",
        "note": "Graph of recent labeled decisions — not a private trading DAG.",
        "disclaimer": "Not financial advice.",
    }
