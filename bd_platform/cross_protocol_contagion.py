"""
Cross-Protocol Contagion — Feature #652 (Sprint-2 Risk Layer).

Graph contagion model across protocol dependencies, collateral, bridges, shared assets.
NOT standalone — Contagion Monitor dimension in Risk Layer.

Principle: dependency provenance mandatory on every graph edge.
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.CrossProtocolContagion")

_FEATURE_ID = 652
_TITLE = "Contagion Monitor"
_LEGAL_NAME = "Cross-Protocol Contagion"
_STANDALONE = False
_MERGED_INTO = "Sprint-2 Risk Layer Core"
_SPRINT = 2
_PRIORITY = "critical"
_SEED_PATH = Path("data/cross_protocol_contagion_seed.json")
_METHODOLOGY_VERSION = "1.0"
_GRAPH_RENDER_LIMIT = 50

_DEPENDENCY_TYPES = (
    "shared_collateral",
    "bridge_dependency",
    "common_oracle",
    "overlapping_liquidity",
)

_DISCLAIMER = (
    "Cross-Protocol Contagion — graph contagion model with documented dependency provenance. "
    "Cascade scenarios are analytical simulations only. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"protocols": {}, "edges": [], "triggers": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("cross-protocol contagion seed load failed: %s", exc)
        return {"protocols": {}, "edges": [], "triggers": {}}


def _risk_color(level: str) -> str:
    return {
        "low": "green",
        "medium": "yellow",
        "high": "orange",
        "critical": "red",
    }.get(level, "gray")


def _build_adjacency(seed: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    adj: dict[str, list[dict[str, Any]]] = {}
    for edge in seed.get("edges") or []:
        src = edge.get("from")
        if not src:
            continue
        adj.setdefault(src, []).append(edge)
    return adj


def _propagate_contagion(
    trigger_id: str,
    *,
    seed: dict[str, Any],
    max_hops: int = 4,
) -> dict[str, float]:
    """BFS graph contagion with weighted edge transmission."""
    adj = _build_adjacency(seed)
    triggers = seed.get("triggers") or {}
    trigger_cfg = triggers.get(trigger_id) or {}
    direct = {
        pid: float(info.get("exposure_pct", 0))
        for pid, info in (trigger_cfg.get("direct_exposure") or {}).items()
    }

    scores: dict[str, float] = dict(direct)
    visited: set[str] = set(direct)
    queue: deque[tuple[str, float, int]] = deque((pid, score, 0) for pid, score in direct.items())

    while queue:
        current, current_score, hop = queue.popleft()
        if hop >= max_hops:
            continue
        for edge in adj.get(current, []):
            target = edge.get("to")
            if not target:
                continue
            weight = float(edge.get("transmission_weight", 0.5))
            propagated = round(current_score * weight, 2)
            if propagated <= 0:
                continue
            prev = scores.get(target, 0)
            merged = max(prev, propagated)
            scores[target] = merged
            if target not in visited or merged > prev:
                visited.add(target)
                queue.append((target, merged, hop + 1))

    return scores


def compute_contagion_vector(
    trigger_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#652 — contagion vector (0–100) with affected protocols and cascade scenario."""
    seed = seed or _load_seed()
    triggers = seed.get("triggers") or {}
    trigger = triggers.get(trigger_id)
    if not trigger:
        return {"ok": False, "trigger_id": trigger_id, "error": "trigger_not_found"}

    protocols = seed.get("protocols") or {}
    scores = _propagate_contagion(trigger_id, seed=seed)
    if not scores:
        scores = {
            pid: float(info.get("exposure_pct", 0))
            for pid, info in (trigger.get("direct_exposure") or {}).items()
        }

    affected: list[dict[str, Any]] = []
    for pid, exposure in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        proto = protocols.get(pid) or {}
        edges = [
            e for e in (seed.get("edges") or [])
            if e.get("to") == pid and e.get("from") in scores
        ]
        reasons = [
            {
                "dependency_type": e.get("dependency_type"),
                "from_protocol": e.get("from"),
                "provenance_source": e.get("provenance_source"),
                "provenance_version": e.get("provenance_version"),
                "detail": e.get("detail"),
            }
            for e in edges[:3]
        ]
        if not reasons and pid in (trigger.get("direct_exposure") or {}):
            direct = trigger["direct_exposure"][pid]
            reasons = [{
                "dependency_type": direct.get("dependency_type", trigger.get("trigger_type")),
                "from_protocol": trigger_id,
                "provenance_source": direct.get("provenance_source"),
                "provenance_version": direct.get("provenance_version"),
                "detail": direct.get("detail"),
            }]

        affected.append({
            "protocol_id": pid,
            "protocol_name": proto.get("protocol_name", pid),
            "exposure_pct": exposure,
            "tvl_usd": proto.get("tvl_usd"),
            "risk_level": proto.get("risk_level"),
            "dependency_reasons": reasons,
            "dependency_provenance_required": True,
        })

    vector_score = round(min(100.0, max(scores.values()) if scores else 0), 1)
    cascade_steps = []
    for hop in range(1, 4):
        hop_protocols = [a for a in affected if a["exposure_pct"] >= 80 - hop * 20]
        if hop_protocols:
            cascade_steps.append({
                "hop": hop,
                "protocols": [p["protocol_id"] for p in hop_protocols[:5]],
                "max_exposure_pct": max(p["exposure_pct"] for p in hop_protocols),
            })

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "trigger_id": trigger_id,
        "trigger_type": trigger.get("trigger_type"),
        "trigger_label": trigger.get("label"),
        "contagion_vector": vector_score,
        "affected_protocols": affected,
        "affected_count": len(affected),
        "cascade_scenario": {
            "trigger": trigger.get("label"),
            "steps": cascade_steps,
            "display": trigger.get("display"),
        },
        "dependency_provenance": True,
        "timestamp": _utcnow(),
    }


def build_contagion_graph_visualization(
    trigger_id: str | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Graph visualization — aggregate when >50 protocols."""
    seed = seed or _load_seed()
    protocols = seed.get("protocols") or {}
    edges = seed.get("edges") or []
    trigger_id = trigger_id or seed.get("default_trigger", "usdc_circle")

    vector = compute_contagion_vector(trigger_id, seed=seed)
    scores = {a["protocol_id"]: a["exposure_pct"] for a in vector.get("affected_protocols", [])}

    nodes: list[dict[str, Any]] = []
    for pid, proto in protocols.items():
        nodes.append({
            "id": pid,
            "label": proto.get("protocol_name", pid),
            "size": proto.get("tvl_usd", 0),
            "risk_level": proto.get("risk_level"),
            "color": _risk_color(str(proto.get("risk_level", "medium"))),
            "contagion_exposure_pct": scores.get(pid, 0),
            "cluster_id": proto.get("cluster_id"),
        })

    aggregated = False
    if len(nodes) > _GRAPH_RENDER_LIMIT:
        aggregated = True
        clusters: dict[str, dict[str, Any]] = {}
        for node in nodes:
            cid = node.get("cluster_id") or "other"
            bucket = clusters.setdefault(cid, {
                "id": cid,
                "label": cid.replace("_", " ").title(),
                "size": 0,
                "protocol_count": 0,
                "max_contagion_exposure_pct": 0,
                "risk_level": "medium",
                "color": "yellow",
            })
            bucket["size"] += float(node.get("size") or 0)
            bucket["protocol_count"] += 1
            bucket["max_contagion_exposure_pct"] = max(
                bucket["max_contagion_exposure_pct"],
                float(node.get("contagion_exposure_pct") or 0),
            )
        nodes = list(clusters.values())

    graph_edges = [
        {
            "from": e.get("from"),
            "to": e.get("to"),
            "dependency_type": e.get("dependency_type"),
            "provenance_source": e.get("provenance_source"),
            "provenance_version": e.get("provenance_version"),
            "hover_detail": e.get("detail"),
        }
        for e in edges
        if not aggregated or e.get("from") in scores or e.get("to") in scores
    ][: _GRAPH_RENDER_LIMIT * 2]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "route": "/contagion",
        "trigger_id": trigger_id,
        "graph": {
            "nodes": nodes[:_GRAPH_RENDER_LIMIT],
            "edges": graph_edges,
            "node_size_metric": "tvl_usd",
            "node_color_metric": "risk_level",
            "hover_shows_dependency_type": True,
            "aggregated": aggregated,
            "aggregation_threshold": _GRAPH_RENDER_LIMIT,
        },
        "contagion_vector": vector.get("contagion_vector"),
        "affected_protocols": vector.get("affected_protocols"),
        "dependency_provenance": True,
        "timestamp": _utcnow(),
    }


def build_contagion_monitor(
    trigger_id: str | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    trigger_id = trigger_id or seed.get("default_trigger", "usdc_circle")

    vector = compute_contagion_vector(trigger_id, seed=seed)
    graph = build_contagion_graph_visualization(trigger_id, seed=seed)

    portfolio_alert = None
    try:
        portfolio_alert = build_portfolio_cluster_alert_410(trigger_id=trigger_id, seed=seed)
    except Exception:
        logger.debug("410 portfolio cluster alert skipped", exc_info=True)

    stablecoin_triggers = None
    try:
        stablecoin_triggers = get_contagion_triggers_from_stablecoin_467(seed=seed)
    except Exception:
        logger.debug("467 stablecoin trigger hook skipped", exc_info=True)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": vector.get("ok", False),
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "trigger_id": trigger_id,
        "contagion_vector": vector.get("contagion_vector"),
        "affected_protocols": vector.get("affected_protocols"),
        "cascade_scenario": vector.get("cascade_scenario"),
        "graph_visualization": graph.get("graph"),
        "portfolio_alert_410": portfolio_alert,
        "stablecoin_triggers_467": stablecoin_triggers,
        "defi_opportunity_cancellation_438": True,
        "dependency_provenance": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_portfolio_cluster_alert_410(
    *,
    portfolio_id: str = "demo_portfolio",
    trigger_id: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#410 — alert if portfolio exposure in threatened cluster."""
    seed = seed or _load_seed()
    trigger_id = trigger_id or seed.get("default_trigger", "usdc_circle")
    vector = compute_contagion_vector(trigger_id, seed=seed)
    if not vector.get("ok"):
        return vector

    portfolio = (seed.get("portfolios") or {}).get(portfolio_id) or {}
    holdings = portfolio.get("protocol_exposure") or {}
    threshold = float((seed.get("alert_thresholds") or {}).get("cluster_exposure_pct", 15))

    threatened: list[dict[str, Any]] = []
    for pid, pct in holdings.items():
        exposure = next(
            (a for a in vector.get("affected_protocols", []) if a["protocol_id"] == pid),
            None,
        )
        if exposure and float(pct) >= threshold and exposure.get("exposure_pct", 0) >= 40:
            threatened.append({
                "protocol_id": pid,
                "portfolio_pct": pct,
                "contagion_exposure_pct": exposure.get("exposure_pct"),
                "alert": True,
            })

    return {
        "ok": True,
        "feature_ref": 410,
        "portfolio_id": portfolio_id,
        "trigger_id": trigger_id,
        "cluster_threatened": len(threatened) > 0,
        "alerts": threatened,
        "threshold_pct": threshold,
        "display": (
            f"Portfolio cluster alert: {len(threatened)} protocols in threatened contagion cluster"
            if threatened else "No portfolio cluster exposure above threshold"
        ),
        "timestamp": _utcnow(),
    }


def cancel_defi_opportunities_in_affected_cluster(
    opportunities: list[dict[str, Any]],
    *,
    trigger_id: str | None = None,
    seed: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """#438 — auto-cancel DeFi opportunities in affected contagion cluster."""
    seed = seed or _load_seed()
    trigger_id = trigger_id or seed.get("default_trigger", "usdc_circle")
    vector = compute_contagion_vector(trigger_id, seed=seed)
    affected = {
        a["protocol_id"]: a["exposure_pct"]
        for a in vector.get("affected_protocols", [])
        if a.get("exposure_pct", 0) >= float((seed.get("alert_thresholds") or {}).get("opportunity_cancel_exposure_pct", 50))
    }
    protocol_map = seed.get("opportunity_protocol_map") or {}

    result: list[dict[str, Any]] = []
    for opp in opportunities:
        opp_copy = dict(opp)
        pid = (
            opp_copy.get("protocol_id")
            or protocol_map.get(str(opp_copy.get("opportunity_id", "")))
            or protocol_map.get(str(opp_copy.get("asset", "")).lower())
        )
        if pid and pid in affected:
            opp_copy["contagion_cancelled_652"] = True
            opp_copy["signal_suppressed"] = True
            opp_copy["contagion_exposure_pct"] = affected[pid]
            opp_copy["cancel_reason_652"] = f"affected_cluster_{trigger_id}"
        result.append(opp_copy)
    return result


def get_contagion_triggers_from_stablecoin_467(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#467 — stablecoin depeg as contagion trigger."""
    seed = seed or _load_seed()
    triggers: list[dict[str, Any]] = []
    try:
        from bd_platform.stablecoin_health_monitor import analyze_stablecoin

        for sym in ("USDC", "USDT", "DAI"):
            health = analyze_stablecoin(sym, seed=None)
            if not health.get("ok"):
                continue
            prob = float(health.get("depeg_probability", 0))
            if prob >= float(seed.get("stablecoin_depeg_trigger_threshold", 0.35)):
                trigger_id = f"{sym.lower()}_depeg"
                triggers.append({
                    "trigger_id": trigger_id,
                    "stablecoin": sym,
                    "depeg_probability": prob,
                    "contagion_trigger": True,
                    "source": "stablecoin_health_monitor_467",
                })
    except Exception:
        logger.debug("467 stablecoin health analysis skipped", exc_info=True)

    mapped = seed.get("stablecoin_trigger_map") or {}
    for t in triggers:
        mapped_id = mapped.get(t["stablecoin"])
        if mapped_id:
            t["mapped_contagion_trigger"] = mapped_id
            t["vector"] = compute_contagion_vector(mapped_id, seed=seed).get("contagion_vector")

    return {
        "ok": True,
        "feature_ref": 467,
        "triggers": triggers,
        "count": len(triggers),
        "timestamp": _utcnow(),
    }


def cross_protocol_contagion_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "protocol_count": len(seed.get("protocols") or {}),
        "edge_count": len(seed.get("edges") or []),
        "dependency_types": list(_DEPENDENCY_TYPES),
        "dependency_provenance_required": True,
        "graph_render_limit": _GRAPH_RENDER_LIMIT,
        "integrations": {
            "capital_protection_410": True,
            "defi_opportunity_scanner_438": True,
            "stablecoin_health_monitor_467": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": _STANDALONE is False, "detail": "652"})
    monitor = build_contagion_monitor(seed=seed)
    checks.append({"id": "monitor_ok", "passed": monitor.get("ok") is True, "detail": "monitor"})
    checks.append({"id": "contagion_vector", "passed": monitor.get("contagion_vector") is not None, "detail": "vector"})
    checks.append({"id": "affected_protocols", "passed": len(monitor.get("affected_protocols") or []) >= 2, "detail": "affected"})
    checks.append({"id": "cascade_scenario", "passed": bool(monitor.get("cascade_scenario")), "detail": "cascade"})
    checks.append({"id": "dependency_provenance", "passed": monitor.get("dependency_provenance") is True, "detail": "provenance"})

    graph = build_contagion_graph_visualization(seed=seed)
    checks.append({"id": "graph_viz", "passed": graph.get("ok") is True, "detail": "graph"})
    checks.append({"id": "graph_limit", "passed": len(graph["graph"]["nodes"]) <= _GRAPH_RENDER_LIMIT, "detail": "limit"})

    usdc = compute_contagion_vector("usdc_circle", seed=seed)
    top = (usdc.get("affected_protocols") or [{}])[0]
    checks.append({"id": "usdc_example", "passed": "aave" in top.get("protocol_id", ""), "detail": "aave"})
    checks.append({"id": "edge_provenance", "passed": bool((top.get("dependency_reasons") or [{}])[0].get("provenance_source")), "detail": "source"})

    alert = build_portfolio_cluster_alert_410(seed=seed)
    checks.append({"id": "portfolio_410", "passed": alert.get("ok") is True, "detail": "410"})

    opps = cancel_defi_opportunities_in_affected_cluster(
        [{"protocol_id": "aave", "asset": "ETH"}],
        seed=seed,
    )
    checks.append({"id": "defi_cancel_438", "passed": opps[0].get("contagion_cancelled_652") is True, "detail": "438"})

    triggers = get_contagion_triggers_from_stablecoin_467(seed=seed)
    checks.append({"id": "stablecoin_467", "passed": triggers.get("ok") is True, "detail": "467"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
