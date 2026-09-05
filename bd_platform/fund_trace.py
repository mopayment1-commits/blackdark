"""
Automated fund trace — single-chain path finding (#18).

Graph traversal over verified on-chain transactions only.
No fabricated paths. Bridge contracts are labeled explicitly; cross-chain
continuation is NOT inferred in MVP (single-chain only).
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.FundTrace")

# Known Ethereum bridge / portal contracts — explicit hop labeling, no cross-chain fabrication
_BRIDGE_CONTRACTS: dict[str, str] = {
    "0x8315177ab297ba92a06054bd893aff76f9bee014": "arbitrum_inbox",
    "0x99c9fc46f92e8a1c0dec1b1747d010903884c6ae": "optimism_gateway",
    "0x401f6c983ea342656ec41f22a706a8e1710955aa": "polygon_pos_bridge",
    "0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f": "arbitrum_outbox",
    "0x66a71dcef29a0ffbdbe3c7736a5b5b2c7e9d7b6": "hop_bridge",
    "0x3666cf60dcc1ffcf39b132f6876b74fc7b0f4786": "across_bridge",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _bridge_label(address: str) -> str | None:
    return _BRIDGE_CONTRACTS.get((address or "").lower())


def _build_adjacency(txs: list[dict[str, Any]], origin: str) -> dict[str, list[dict[str, Any]]]:
    """Build outbound adjacency list from verified transactions only."""
    graph: dict[str, list[dict[str, Any]]] = {}
    origin_l = origin.lower()
    for tx in txs:
        if tx.get("is_error"):
            continue
        if float(tx.get("value_eth") or 0) <= 0:
            continue
        frm = str(tx.get("from") or "").lower()
        to = str(tx.get("to") or "").lower()
        if not frm or not to:
            continue
        edge = {
            "from": frm,
            "to": to,
            "tx_hash": tx.get("hash"),
            "value_eth": tx.get("value_eth"),
            "block_number": tx.get("block_number"),
            "timestamp": tx.get("timestamp"),
            "hop_type": "bridge_exit" if _bridge_label(to) else "transfer",
            "bridge": _bridge_label(to),
        }
        graph.setdefault(frm, []).append(edge)
        if frm == origin_l:
            graph.setdefault(origin_l, graph.get(origin_l, []))
    return graph


def _trace_paths(
    graph: dict[str, list[dict[str, Any]]],
    origin: str,
    *,
    max_hops: int,
    min_value_eth: float,
) -> list[dict[str, Any]]:
    """BFS path search — returns only paths built from actual tx edges."""
    origin_l = origin.lower()
    paths: list[dict[str, Any]] = []
    queue: list[tuple[str, list[dict[str, Any]]]] = [(origin_l, [])]
    seen_depth: set[tuple[str, int]] = set()

    while queue:
        node, hops = queue.pop(0)
        depth = len(hops)
        if depth >= max_hops:
            continue
        if (node, depth) in seen_depth:
            continue
        seen_depth.add((node, depth))

        for edge in graph.get(node, []):
            if float(edge.get("value_eth") or 0) < min_value_eth:
                continue
            new_hops = hops + [edge]
            path_id = "→".join(h["tx_hash"][:10] for h in new_hops if h.get("tx_hash"))
            bridge_hops = [h for h in new_hops if h.get("hop_type") == "bridge_exit"]
            paths.append(
                {
                    "path_id": path_id or f"path_{len(paths)}",
                    "hops": new_hops,
                    "hop_count": len(new_hops),
                    "terminal": edge["to"],
                    "terminal_bridge": edge.get("bridge"),
                    "complete": False,
                    "fabricated": False,
                    "cross_chain_continuation": False,
                    "bridge_handling": "explicit" if bridge_hops else "none",
                    "ends_at_bridge": edge.get("hop_type") == "bridge_exit",
                }
            )
            # Do NOT traverse past bridge exits — no fabricated cross-chain path
            if edge.get("hop_type") != "bridge_exit":
                queue.append((edge["to"], new_hops))

    paths.sort(key=lambda p: (-p["hop_count"], -sum(float(h.get("value_eth") or 0) for h in p["hops"])))
    return paths[:20]


async def trace_funds(
    address: str,
    *,
    chain: str = "ethereum",
    max_hops: int = 5,
    min_value_eth: float = 0.01,
    direction: str = "outbound",
) -> dict[str, Any]:
    """
    Single-chain fund trace (#18).

  Acceptance:
    - No fabricated path (only verified tx edges)
    - Bridge hops labeled explicitly; no cross-chain inference
    """
    t0 = time.perf_counter()
    addr = (address or "").strip().lower()
    if chain.lower() != "ethereum" or not addr.startswith("0x"):
        return {
            "ok": False,
            "error": "single_chain_ethereum_only",
            "feature": "#18",
            "supported_chains": ["ethereum"],
        }
    if direction != "outbound":
        return {"ok": False, "error": "outbound_only_in_mvp", "feature": "#18"}

    from bd_platform.onchain_client import get_normal_transactions

    tx_resp = await get_normal_transactions(addr, limit=100)
    if not tx_resp.get("ok"):
        return {
            "ok": False,
            "error": tx_resp.get("error") or "tx_fetch_failed",
            "feature": "#18",
            "fabricated": False,
        }

    txs = tx_resp.get("transactions") or []
    graph = _build_adjacency(txs, addr)
    paths = _trace_paths(graph, addr, max_hops=max(1, min(8, max_hops)), min_value_eth=min_value_eth)

    elapsed = time.perf_counter() - t0
    headline = None
    if paths:
        top = paths[0]
        val = sum(float(h.get("value_eth") or 0) for h in top["hops"])
        if top.get("ends_at_bridge"):
            headline = (
                f"{val:.4f} ETH traced in {top['hop_count']} hop(s) → "
                f"bridge exit ({top.get('terminal_bridge')}) — cross-chain not inferred"
            )
        else:
            headline = f"{val:.4f} ETH traced in {top['hop_count']} on-chain hop(s)"

    return {
        "ok": True,
        "surface": "on_chain_address_intelligence",
        "capability": "fund_trace",
        "feature": "#18",
        "address": addr,
        "chain": chain.lower(),
        "direction": direction,
        "paths": paths,
        "path_count": len(paths),
        "max_hops": max_hops,
        "fabricated": False,
        "bridge_handling": "explicit",
        "cross_chain_supported": False,
        "headline": headline,
        "data_state": "LIVE" if paths else "PARTIAL",
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }
