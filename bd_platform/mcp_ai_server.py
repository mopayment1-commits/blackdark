"""
MCP for AI — Feature #262 (Sprint 2, AI Infrastructure).

MCP Server exposing canonical market data to AI agents via tool-grounded retrieval.
Integrated with Verifiable AI Engine (#230) — same data path for agents, users, and internal AI.

NOT a separate data path. Tool traceability + rate limiting + authentication required.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.MCPAI")

_FEATURE_ID = 262
_MCP_VERSION = "1.0"
_MCP_SPEC = "2025-03"
_STANDALONE = False
_SPRINT = 2
_INTEGRATED_WITH = (230,)
_SEED_PATH = Path("data/mcp_ai_server_seed.json")
_TRACE_LOG = Path("data/mcp_ai/trace_log.jsonl")

_DISCLAIMER_TEMPLATE = (
    "Data provided by BLACKDARK MCP Server | Timestamp: {timestamp} | Not investment advice."
)

# In-memory rate limit counters (per agent per day)
_rate_counters: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
_rate_day: str = ""

_TOOL_SCHEMAS: tuple[dict[str, Any], ...] = (
    {
        "name": "blackdark_get_price",
        "description": "Get canonical FX-adjusted spot price for an asset from BLACKDARK Oracle path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset": {
                    "type": "string",
                    "description": "Asset symbol, e.g. BTC, ETH",
                },
            },
            "required": ["asset"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "asset": {"type": "string"},
                "price_usd": {"type": "number"},
                "change_24h_pct": {"type": "number"},
                "evidence": {"type": "array"},
                "disclaimer": {"type": "string"},
            },
        },
        "examples": [
            {
                "input": {"asset": "BTC"},
                "output_summary": "BTC price $98,500 with source + timestamp + freshness_ms",
            },
        ],
    },
    {
        "name": "blackdark_get_onchain_metric",
        "description": "Get canonical on-chain metric (mvrv_proxy, sopr_proxy, nvt) via Oracle path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset": {"type": "string", "description": "Asset symbol"},
                "metric": {
                    "type": "string",
                    "enum": ["mvrv_proxy", "sopr_proxy", "nvt", "all"],
                    "description": "On-chain metric to retrieve",
                },
            },
            "required": ["asset"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "asset": {"type": "string"},
                "metric": {"type": "string"},
                "value": {},
                "evidence": {"type": "array"},
                "disclaimer": {"type": "string"},
            },
        },
        "examples": [
            {
                "input": {"asset": "BTC", "metric": "mvrv_proxy"},
                "output_summary": "MVRV proxy with source + timestamp",
            },
        ],
    },
    {
        "name": "blackdark_get_exchange_quality",
        "description": "Get exchange connectivity and quality score from connector coverage probes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "exchange": {
                    "type": "string",
                    "description": "Exchange id, e.g. binance, coinbase, okx",
                },
            },
            "required": ["exchange"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "exchange": {"type": "string"},
                "live": {"type": "boolean"},
                "quality_score": {"type": "number"},
                "evidence": {"type": "array"},
                "disclaimer": {"type": "string"},
            },
        },
        "examples": [
            {
                "input": {"exchange": "binance"},
                "output_summary": "Binance live=true, latency_ms, probe timestamp",
            },
        ],
    },
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {
            "mcp_server_version": _MCP_VERSION,
            "mcp_spec_compatible": _MCP_SPEC,
            "trace_retention_days": 90,
            "daily_quotas": {"free": 50, "pro": 5000, "enterprise": -1},
            "demo_api_keys": {},
        }
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("mcp ai seed load failed: %s", exc)
        return {"daily_quotas": {"free": 50, "pro": 5000}, "demo_api_keys": {}}


def _hash_response(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _append_trace(entry: dict[str, Any]) -> None:
    _TRACE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with _TRACE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def _disclaimer() -> str:
    return _DISCLAIMER_TEMPLATE.format(timestamp=_utcnow())


def _resolve_agent(api_key: str, agent_fingerprint: str | None) -> dict[str, Any]:
    """Authenticate agent — API key + fingerprint. No anonymous access."""
    if not api_key or len(api_key) < 8:
        return {"ok": False, "error": "authentication_required", "message": "API key required"}

    if not agent_fingerprint or len(agent_fingerprint) < 8:
        return {
            "ok": False,
            "error": "agent_fingerprint_required",
            "message": "Agent fingerprint required — no anonymous MCP access",
        }

    seed = _load_seed()
    demo_keys = seed.get("demo_api_keys") or {}
    entry = demo_keys.get(api_key)

    if entry:
        agent_id = entry.get("agent_id") or f"agent_{hashlib.sha256(api_key.encode()).hexdigest()[:12]}"
        tier = entry.get("tier", "free")
        return {
            "ok": True,
            "agent_id": agent_id,
            "tier": tier,
            "fingerprint": agent_fingerprint,
            "authenticated": True,
        }

    # Production path: hash lookup (demo keys in seed for tests)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    for _name, cfg in (seed.get("demo_agents") or {}).items():
        if cfg.get("api_key_hash") == key_hash:
            return {
                "ok": True,
                "agent_id": cfg.get("agent_id", _name),
                "tier": cfg.get("tier", "free"),
                "fingerprint": agent_fingerprint,
                "authenticated": True,
            }

    return {"ok": False, "error": "invalid_api_key", "message": "Invalid API key"}


def _reset_rate_counters_if_needed() -> None:
    global _rate_day
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    if _rate_day != today:
        _rate_counters.clear()
        _rate_day = today


def check_mcp_rate_limit(agent_id: str, tier: str) -> dict[str, Any]:
    """Per-agent daily rate limit — Free 50, Pro 5K, Enterprise unlimited."""
    _reset_rate_counters_if_needed()
    seed = _load_seed()
    quotas = seed.get("daily_quotas") or {}
    limit = int(quotas.get(tier) or quotas.get("free") or 50)

    if limit < 0:
        return {
            "ok": True,
            "allowed": True,
            "tier": tier,
            "daily_limit": "unlimited",
            "priority_queue": tier in ("enterprise", "institutional"),
            "calls_today": _rate_counters[agent_id].get("calls", 0),
        }

    used = _rate_counters[agent_id].get("calls", 0)
    if used >= limit:
        return {
            "ok": False,
            "allowed": False,
            "rate_limited": True,
            "tier": tier,
            "daily_limit": limit,
            "calls_today": used,
            "message": f"MCP daily quota exceeded ({limit}/day for {tier})",
        }

    return {
        "ok": True,
        "allowed": True,
        "tier": tier,
        "daily_limit": limit,
        "calls_today": used,
        "remaining": limit - used,
    }


def _increment_rate(agent_id: str) -> None:
    _reset_rate_counters_if_needed()
    if "calls" not in _rate_counters[agent_id]:
        _rate_counters[agent_id]["calls"] = 0
    _rate_counters[agent_id]["calls"] += 1


def get_tool_schemas() -> dict[str, Any]:
    """Machine-readable MCP tool documentation."""
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "mcp_server_version": seed.get("mcp_server_version", _MCP_VERSION),
        "mcp_spec_compatible": seed.get("mcp_spec_compatible", _MCP_SPEC),
        "tools": list(_TOOL_SCHEMAS),
        "tool_count": len(_TOOL_SCHEMAS),
        "authentication": {
            "required": True,
            "headers": ["X-API-Key", "X-Agent-Fingerprint"],
            "no_anonymous": True,
        },
        "rate_limits": seed.get("daily_quotas") or {},
        "grounding_layer": "#230 Verifiable AI Engine",
        "timestamp": _utcnow(),
    }


async def _tool_get_price(asset: str) -> dict[str, Any]:
    from bd_platform.unified_api_platform import fetch_price
    from bd_platform.verifiable_ai_engine import _build_evidence_item, _freshness_for_asset, attach_verifiable_ai

    sym = asset.upper().replace("/USDT", "")
    try:
        envelope = await fetch_price(sym)
    except Exception as exc:
        logger.warning("mcp get_price failed: %s", exc)
        return {
            "ok": False,
            "error": "Data unavailable",
            "message": "Data unavailable",
            "fail_closed": True,
            "asset": sym,
            "disclaimer": _disclaimer(),
            "disclaimer_hideable": False,
        }

    if not envelope.get("ok", True):
        return {
            "ok": False,
            "error": "Data unavailable",
            "message": "Data unavailable",
            "fail_closed": True,
            "asset": sym,
            "disclaimer": _disclaimer(),
            "disclaimer_hideable": False,
        }

    data = envelope.get("data") or {}
    meta = envelope.get("metadata") or {}
    fetched_at = meta.get("fetched_at") or envelope.get("timestamp") or _utcnow()
    freshness = _freshness_for_asset(sym, "price")
    latency_ms = freshness.get("latency_ms")

    if freshness.get("stale"):
        return {
            "ok": False,
            "error": "Data unavailable",
            "message": "Data unavailable — stale feed",
            "fail_closed": True,
            "asset": sym,
            "disclaimer": _disclaimer(),
            "disclaimer_hideable": False,
        }

    evidence = [
        _build_evidence_item(
            fact=f"{sym} price ${data.get('price_usd')}",
            source_api="Unified API price",
            timestamp=fetched_at,
            value={"price_usd": data.get("price_usd"), "change_24h_pct": data.get("change_24h_pct")},
            freshness_ms=latency_ms,
            source_link=f"/api/v1/platform/price?asset={sym}",
        ),
    ]

    payload = attach_verifiable_ai(
        {
            "ok": True,
            "asset": sym,
            "price_usd": data.get("price_usd"),
            "change_24h_pct": data.get("change_24h_pct"),
            "exchange": data.get("exchange"),
        },
        evidence=evidence,
        tools_called=["blackdark_get_price"],
        query=f"mcp:price:{sym}",
    )
    payload["disclaimer"] = _disclaimer()
    payload["disclaimer_hideable"] = False
    return payload


async def _tool_get_onchain_metric(asset: str, metric: str = "all") -> dict[str, Any]:
    from bd_platform.unified_api_platform import fetch_onchain
    from bd_platform.verifiable_ai_engine import _build_evidence_item, _freshness_for_asset, attach_verifiable_ai

    sym = asset.upper().replace("/USDT", "")
    try:
        envelope = await fetch_onchain(sym)
    except Exception as exc:
        logger.warning("mcp get_onchain failed: %s", exc)
        return {
            "ok": False,
            "error": "Data unavailable",
            "message": "Data unavailable",
            "fail_closed": True,
            "asset": sym,
            "disclaimer": _disclaimer(),
            "disclaimer_hideable": False,
        }

    if not envelope.get("ok", True):
        return {
            "ok": False,
            "error": "Data unavailable",
            "message": "Data unavailable",
            "fail_closed": True,
            "asset": sym,
            "disclaimer": _disclaimer(),
            "disclaimer_hideable": False,
        }

    data = envelope.get("data") or {}
    meta = envelope.get("metadata") or {}
    fetched_at = meta.get("fetched_at") or envelope.get("timestamp") or _utcnow()
    freshness = _freshness_for_asset(sym, "onchain")
    latency_ms = freshness.get("latency_ms")

    metrics_map = {
        "mvrv_proxy": data.get("mvrv_proxy"),
        "sopr_proxy": data.get("sopr_proxy"),
        "nvt": data.get("nvt"),
    }

    if metric != "all" and metric in metrics_map:
        value = metrics_map[metric]
        if value is None:
            return {
                "ok": False,
                "error": "Data unavailable",
                "message": f"Data unavailable for metric {metric}",
                "fail_closed": True,
                "asset": sym,
                "metric": metric,
                "disclaimer": _disclaimer(),
                "disclaimer_hideable": False,
            }
        evidence = [
            _build_evidence_item(
                fact=f"{sym} {metric}={value}",
                source_api="Unified API onchain",
                timestamp=fetched_at,
                value={metric: value},
                freshness_ms=latency_ms,
                source_link=f"/api/v1/platform/onchain?asset={sym}",
            ),
        ]
        payload = attach_verifiable_ai(
            {"ok": True, "asset": sym, "metric": metric, "value": value},
            evidence=evidence,
            tools_called=["blackdark_get_onchain_metric"],
            query=f"mcp:onchain:{sym}:{metric}",
        )
    else:
        evidence = [
            _build_evidence_item(
                fact=f"{sym} {k}={v}",
                source_api="Unified API onchain",
                timestamp=fetched_at,
                value={k: v},
                freshness_ms=latency_ms,
                source_link=f"/api/v1/platform/onchain?asset={sym}",
            )
            for k, v in metrics_map.items()
            if v is not None
        ]
        if not evidence:
            return {
                "ok": False,
                "error": "Data unavailable",
                "message": "Data unavailable",
                "fail_closed": True,
                "asset": sym,
                "disclaimer": _disclaimer(),
                "disclaimer_hideable": False,
            }
        payload = attach_verifiable_ai(
            {"ok": True, "asset": sym, "metric": "all", "value": metrics_map},
            evidence=evidence,
            tools_called=["blackdark_get_onchain_metric"],
            query=f"mcp:onchain:{sym}:all",
        )

    payload["disclaimer"] = _disclaimer()
    payload["disclaimer_hideable"] = False
    return payload


async def _tool_get_exchange_quality(exchange: str) -> dict[str, Any]:
    from bd_platform.connector_coverage_map import build_coverage_map
    from bd_platform.verifiable_ai_engine import _build_evidence_item, attach_verifiable_ai

    ex = exchange.lower().strip()
    try:
        coverage = await build_coverage_map()
    except Exception as exc:
        logger.warning("mcp exchange quality failed: %s", exc)
        return {
            "ok": False,
            "error": "Data unavailable",
            "message": "Data unavailable",
            "fail_closed": True,
            "exchange": ex,
            "disclaimer": _disclaimer(),
            "disclaimer_hideable": False,
        }

    venues = coverage.get("venues") or []
    venue = next((v for v in venues if v.get("venue_id") == ex), None)

    if not venue:
        return {
            "ok": False,
            "error": "Data unavailable",
            "message": f"Exchange {ex} not in coverage map",
            "fail_closed": True,
            "exchange": ex,
            "disclaimer": _disclaimer(),
            "disclaimer_hideable": False,
        }

    live = bool(venue.get("live"))
    latency = venue.get("latency_ms")
    quality_score = round(max(0, 100 - (latency or 0) / 10), 1) if live else 0.0
    probed_at = venue.get("probed_at") or _utcnow()

    evidence = [
        _build_evidence_item(
            fact=f"{ex} live={live} latency={latency}ms quality={quality_score}",
            source_api="Connector Coverage Map",
            timestamp=probed_at,
            value={"live": live, "latency_ms": latency, "quality_score": quality_score},
            source_link=f"/api/platform/connector-coverage/map",
        ),
    ]

    payload = attach_verifiable_ai(
        {
            "ok": True,
            "exchange": ex,
            "live": live,
            "latency_ms": latency,
            "quality_score": quality_score,
            "pairs": venue.get("pairs"),
            "status_display": venue.get("status_display"),
        },
        evidence=evidence,
        tools_called=["blackdark_get_exchange_quality"],
        query=f"mcp:exchange:{ex}",
    )
    payload["disclaimer"] = _disclaimer()
    payload["disclaimer_hideable"] = False
    return payload


_TOOL_HANDLERS = {
    "blackdark_get_price": lambda p: _tool_get_price(p.get("asset", "BTC")),
    "blackdark_get_onchain_metric": lambda p: _tool_get_onchain_metric(
        p.get("asset", "BTC"), p.get("metric", "all"),
    ),
    "blackdark_get_exchange_quality": lambda p: _tool_get_exchange_quality(p.get("exchange", "binance")),
}


async def call_mcp_tool(
    tool_name: str,
    parameters: dict[str, Any],
    *,
    api_key: str,
    agent_fingerprint: str,
) -> dict[str, Any]:
    """
    Execute MCP tool with auth, rate limiting, traceability, and #230 grounding.
    """
    t0 = time.perf_counter()
    auth = _resolve_agent(api_key, agent_fingerprint)
    if not auth.get("ok"):
        return {**auth, "disclaimer": _disclaimer(), "disclaimer_hideable": False}

    agent_id = auth["agent_id"]
    tier = auth["tier"]

    rate = check_mcp_rate_limit(agent_id, tier)
    if not rate.get("allowed"):
        return {**rate, "disclaimer": _disclaimer(), "disclaimer_hideable": False}

    handler = _TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {
            "ok": False,
            "error": "unknown_tool",
            "message": f"Unknown tool: {tool_name}",
            "available_tools": [t["name"] for t in _TOOL_SCHEMAS],
            "disclaimer": _disclaimer(),
            "disclaimer_hideable": False,
        }

    result = await handler(parameters or {})
    _increment_rate(agent_id)

    response_hash = _hash_response(result)
    _append_trace({
        "agent_id": agent_id,
        "agent_fingerprint": agent_fingerprint[:16] + "...",
        "tool_called": tool_name,
        "parameters": parameters,
        "timestamp": _utcnow(),
        "response_hash": response_hash,
        "ok": result.get("ok", False),
        "tier": tier,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
    })

    result["mcp"] = {
        "feature_id": _FEATURE_ID,
        "server_version": _MCP_VERSION,
        "mcp_spec": _MCP_SPEC,
        "tool": tool_name,
        "agent_id": agent_id,
        "trace_recorded": True,
        "grounding_layer": "#230",
    }
    if "disclaimer" not in result:
        result["disclaimer"] = _disclaimer()
    result["disclaimer_hideable"] = False
    return result


def get_tool_trace(*, limit: int = 50, agent_id: str | None = None) -> dict[str, Any]:
    seed = _load_seed()
    retention = int(seed.get("trace_retention_days") or 90)
    entries: list[dict[str, Any]] = []

    if _TRACE_LOG.is_file():
        try:
            lines = _TRACE_LOG.read_text(encoding="utf-8").strip().splitlines()
            for line in lines:
                try:
                    entry = json.loads(line)
                    if agent_id and entry.get("agent_id") != agent_id:
                        continue
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
        except OSError:
            pass

    entries = entries[-limit:]
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "trace_retention_days": retention,
        "count": len(entries),
        "entries": entries,
        "timestamp": _utcnow(),
    }


def mcp_ai_server_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "MCP for AI",
        "standalone": _STANDALONE,
        "sprint": _SPRINT,
        "mcp_server_version": seed.get("mcp_server_version", _MCP_VERSION),
        "mcp_spec_compatible": seed.get("mcp_spec_compatible", _MCP_SPEC),
        "integrated_with": list(_INTEGRATED_WITH),
        "grounding_layer": "Verifiable AI Engine (#230)",
        "tools": [t["name"] for t in _TOOL_SCHEMAS],
        "authentication": {
            "api_key_required": True,
            "agent_fingerprint_required": True,
            "no_anonymous_access": True,
        },
        "rate_limits": seed.get("daily_quotas") or {},
        "trace_retention_days": seed.get("trace_retention_days", 90),
        "acceptance_criteria": {
            "tool_traceability": True,
            "no_model_only_facts": True,
            "schema_documented": True,
            "rate_limiting_per_agent": True,
            "authentication_required": True,
            "disclaimer_mandatory": True,
            "fail_closed": True,
            "verifiable_ai_integration": True,
            "versioned_protocol": True,
        },
        "disclaimer": _disclaimer(),
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
