"""
Verifiable AI Engine — Feature #230 (Sprint 1, Core AI Layer).

Evidence-Linked Intelligence: every AI insight anchored to canonical market data.
Middleware between AI engine and platform APIs — NOT a standalone product.

Prerequisites: #208 Source Registry, #219 Freshness Assurance, #162 Oracle API.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.VerifiableAI")

_FEATURE_ID = 230
_ALTERNATE_TITLE = "Evidence-Linked Intelligence"
_STANDALONE = False
_SPRINT = 1
_SEED_PATH = Path("data/verifiable_ai_engine_seed.json")
_AUDIT_LOG = Path("data/verifiable_ai/audit_trail.jsonl")
_ORACLE_API_VERSION = "v2.1"
_ORACLE_SOURCE_LABEL = f"Oracle API {_ORACLE_API_VERSION}"

_DISCLAIMER = (
    "This analysis is based on BLACKDARK canonical data. "
    "It does not constitute financial advice."
)
_FAIL_CLOSED_ANSWER = (
    "I'm unable to retrieve current market data. "
    "Please check the Market Radar directly."
)
_NO_DATA_ANSWER = "I don't have verified data for that."
_MARKET_FACT_PATTERN = re.compile(
    r"\$[\d,]+(?:\.\d+)?|\b\d+(?:\.\d+)?%\b|"
    r"\b(price|verdict|score|confidence|volume|market cap)\b",
    re.IGNORECASE,
)

ConfidenceBadge = Literal["Verified", "Partial", "Simulated"]

SYSTEM_PROMPT = (
    "You are BLACKDARK Verifiable AI. You must call the BLACKDARK data tool before "
    "stating any market fact. If the tool returns no data, say "
    "'I don't have current data for that.' Never use training data as a fallback "
    "for market numbers. Every answer must cite canonical sources with timestamps."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {
            "audit_retention_days": 90,
            "source_links": {},
            "fail_closed": True,
            "no_model_only_facts": True,
        }
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("verifiable ai seed load failed: %s", exc)
        return {"audit_retention_days": 90, "source_links": {}}


def _append_audit(entry: dict[str, Any]) -> None:
    _AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with _AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def _source_link(metric: str, asset: str) -> str:
    seed = _load_seed()
    template = (seed.get("source_links") or {}).get(metric) or f"/api/v1/platform/{metric}?asset={{asset}}"
    return template.format(asset=asset.upper())


def _freshness_for_asset(asset: str, feed_id: str = "oracle") -> dict[str, Any]:
    try:
        from bd_platform.freshness_assurance import get_feed_freshness

        return get_feed_freshness(feed_id, asset)
    except Exception:
        logger.debug("freshness lookup failed", exc_info=True)
        return {"latency_ms": None, "stale": False, "status": "unknown"}


def _confidence_badge(evidence: list[dict[str, Any]], *, tools_ok: bool) -> ConfidenceBadge:
    if not evidence or not tools_ok:
        return "Simulated"
    verified = sum(1 for e in evidence if e.get("confidence") == "verified")
    if verified == len(evidence):
        return "Verified"
    if verified > 0:
        return "Partial"
    return "Simulated"


def _build_evidence_item(
    *,
    fact: str,
    source_api: str,
    timestamp: str,
    value: Any,
    confidence: str = "verified",
    freshness_ms: float | None = None,
    source_link: str | None = None,
) -> dict[str, Any]:
    return {
        "fact": fact,
        "source": source_api,
        "source_api": source_api,
        "timestamp": timestamp,
        "value": value,
        "confidence": confidence,
        "freshness_ms": freshness_ms,
        "source_link": source_link,
        "citation_display": (
            f"Source: {source_link or source_api} | Data verified at {timestamp}"
            + (f" | Latency: {freshness_ms}ms" if freshness_ms is not None else "")
        ),
    }


async def blackdark_data_tool(
    asset: str,
    *,
    metrics: tuple[str, ...] = ("oracle", "price"),
) -> dict[str, Any]:
    """
    Tool-grounded retrieval — same endpoints as user-facing Oracle API (#162).
    Fail-closed: returns ok=False when canonical data unavailable.
    """
    sym = asset.upper().replace("/USDT", "")
    tools_called: list[str] = []
    data_returned: dict[str, Any] = {}
    evidence: list[dict[str, Any]] = []
    t0 = time.perf_counter()

    from bd_platform.unified_api_platform import fetch_oracle, fetch_price

    fetchers = {
        "oracle": fetch_oracle,
        "price": fetch_price,
    }

    for metric in metrics:
        fetcher = fetchers.get(metric)
        if not fetcher:
            continue
        tools_called.append(f"blackdark_data_tool:{metric}")
        try:
            envelope = await fetcher(sym)
        except Exception as exc:
            logger.warning("blackdark_data_tool %s failed: %s", metric, exc)
            continue

        if not envelope.get("ok", True):
            continue

        meta = envelope.get("metadata") or {}
        fetched_at = meta.get("fetched_at") or envelope.get("timestamp") or _utcnow()
        freshness = _freshness_for_asset(sym, feed_id=metric)
        latency_ms = freshness.get("latency_ms")
        if latency_ms is None:
            try:
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            except Exception:
                latency_ms = None

        if freshness.get("stale"):
            continue

        payload = envelope.get("data") or {}
        data_returned[metric] = payload
        link = _source_link(metric, sym)

        if metric == "oracle":
            fact = (
                f"{sym} verdict {payload.get('verdict')} "
                f"(confidence {payload.get('confidence_score', '—')}%)"
            )
            value = {
                "verdict": payload.get("verdict"),
                "confidence_score": payload.get("confidence_score"),
                "headline": payload.get("headline"),
            }
        elif metric == "price":
            fact = f"{sym} price ${payload.get('price_usd')} ({payload.get('change_24h_pct')}% 24h)"
            value = {
                "price_usd": payload.get("price_usd"),
                "change_24h_pct": payload.get("change_24h_pct"),
            }
        else:
            fact = f"{sym} {metric}: {payload}"
            value = payload

        evidence.append(
            _build_evidence_item(
                fact=fact,
                source_api=_ORACLE_SOURCE_LABEL if metric == "oracle" else f"Unified API {metric}",
                timestamp=fetched_at,
                value=value,
                confidence="verified",
                freshness_ms=latency_ms,
                source_link=link,
            )
        )

    ok = bool(evidence)
    return {
        "ok": ok,
        "feature_id": _FEATURE_ID,
        "asset": sym,
        "tools_called": tools_called,
        "data_returned": data_returned,
        "evidence": evidence,
        "fail_closed": not ok,
        "timestamp": _utcnow(),
    }


def attach_verifiable_ai(
    payload: dict[str, Any],
    *,
    evidence: list[dict[str, Any]],
    answer: str | None = None,
    tools_called: list[str] | None = None,
    query: str | None = None,
) -> dict[str, Any]:
    """Wrap any AI response with evidence, disclaimer, and confidence badge."""
    tools_ok = bool(evidence)
    badge = _confidence_badge(evidence, tools_ok=tools_ok)
    out = dict(payload)
    out["answer"] = answer or out.get("answer") or out.get("reply") or ""
    out["evidence"] = evidence
    out["confidence_badge"] = badge
    out["disclaimer"] = _DISCLAIMER
    out["disclaimer_hideable"] = False
    out["no_model_only_facts"] = True
    out["fail_closed"] = not tools_ok
    out["view_source_data"] = {
        "enabled": bool(evidence),
        "links": [e.get("source_link") for e in evidence if e.get("source_link")],
    }
    out["verifiable_ai"] = {
        "feature_id": _FEATURE_ID,
        "title": "Verifiable AI Engine",
        "system_prompt_rule": "tool_grounded_retrieval_required",
        "oracle_api_parity": True,
    }

    _append_audit({
        "query": (query or "")[:500],
        "tools_called": tools_called or [],
        "evidence_count": len(evidence),
        "confidence_badge": badge,
        "response_preview": (out["answer"] or "")[:300],
        "timestamp": _utcnow(),
    })
    return out


def _query_needs_market_facts(query: str) -> bool:
    return bool(_MARKET_FACT_PATTERN.search(query))


async def ground_ai_response(
    query: str,
    *,
    asset: str | None = None,
    answer: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Main middleware: tool-grounded retrieval + evidence attachment.
    No source = no market facts in answer (fail-closed).
    """
    text = (query or "").strip()
    sym = (asset or "").upper().replace("/USDT", "") if asset else None

    if not sym and text:
        sym = _extract_asset_from_query(text)

    tools_called: list[str] = []
    evidence: list[dict[str, Any]] = []
    tool_result: dict[str, Any] | None = None

    if sym:
        tool_result = await blackdark_data_tool(sym)
        tools_called = tool_result.get("tools_called") or []
        evidence = tool_result.get("evidence") or []

    needs_facts = _query_needs_market_facts(text)
    final_answer = answer

    if needs_facts and not evidence:
        final_answer = _NO_DATA_ANSWER if sym else _FAIL_CLOSED_ANSWER
    elif not final_answer and evidence:
        final_answer = _format_evidence_answer(sym or "Market", evidence)
    elif not final_answer:
        final_answer = _FAIL_CLOSED_ANSWER if needs_facts else (
            "Ask about any asset — e.g. What should I do with BTC?"
        )

    if needs_facts and evidence and final_answer and answer:
        if not _answer_references_evidence(final_answer, evidence):
            final_answer = _format_evidence_answer(sym or "Market", evidence)

    payload = attach_verifiable_ai(
        {"ok": bool(evidence) or not needs_facts, "asset": sym, "context": context or {}},
        evidence=evidence,
        answer=final_answer,
        tools_called=tools_called,
        query=text,
    )
    payload["tools_called"] = tools_called
    payload["data_returned"] = (tool_result or {}).get("data_returned")
    return payload


def _extract_asset_from_query(text: str) -> str | None:
    upper = text.upper()
    for sym in ("BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "LINK"):
        if sym in upper:
            return sym
    aliases = {
        "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL",
        "بيتكوين": "BTC", "ايث": "ETH",
    }
    lower = text.lower()
    for alias, sym in aliases.items():
        if alias in lower:
            return sym
    return None


def _format_evidence_answer(asset: str, evidence: list[dict[str, Any]]) -> str:
    lines = [f"📊 **{asset}** — verified market data\n"]
    for item in evidence:
        lines.append(f"• {item['fact']}")
        lines.append(f"  _{item.get('citation_display', '')}_")
    return "\n".join(lines)


def _answer_references_evidence(answer: str, evidence: list[dict[str, Any]]) -> bool:
    lower = answer.lower()
    for item in evidence:
        val = item.get("value")
        if isinstance(val, dict):
            for v in val.values():
                if v is not None and str(v).lower() in lower:
                    return True
        elif item.get("fact") and str(item["fact"]).split()[0].lower() in lower:
            return True
    return False


def get_audit_trail(*, limit: int = 50, since_days: int | None = None) -> dict[str, Any]:
    seed = _load_seed()
    retention = int(seed.get("audit_retention_days") or 90)
    entries: list[dict[str, Any]] = []

    if _AUDIT_LOG.is_file():
        try:
            lines = _AUDIT_LOG.read_text(encoding="utf-8").strip().splitlines()
            for line in lines[-limit * 2:]:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        except OSError:
            pass

    if since_days is not None:
        cutoff = datetime.now(UTC) - timedelta(days=since_days)
        entries = [
            e for e in entries
            if _parse_ts(e.get("timestamp", _utcnow())) >= cutoff
        ]

    entries = entries[-limit:]
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "audit_retention_days": retention,
        "count": len(entries),
        "entries": entries,
        "timestamp": _utcnow(),
    }


def verifiable_ai_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Verifiable AI Engine",
        "alternate_title": _ALTERNATE_TITLE,
        "description": (
            "Every AI-generated insight is anchored to canonical market data "
            "with traceable source links. No answer without evidence."
        ),
        "standalone": _STANDALONE,
        "sprint": _SPRINT,
        "all_tiers": seed.get("all_tiers", True),
        "fail_closed": seed.get("fail_closed", True),
        "no_model_only_facts": seed.get("no_model_only_facts", True),
        "prerequisites": seed.get("prerequisites", {"canonical_sources": 208, "freshness_metadata": 219}),
        "integrated_surfaces": seed.get("integrated_surfaces", []),
        "acceptance_criteria": {
            "no_response_without_source": True,
            "oracle_api_cross_reference": True,
            "hallucination_target_pct": seed.get("hallucination_target_pct", 0.1),
            "source_link_clickable": True,
            "timestamp_visible": True,
            "fail_closed_fallback": True,
        },
        "system_prompt": SYSTEM_PROMPT,
        "audit_retention_days": seed.get("audit_retention_days", 90),
        "confidence_badges": ["Verified", "Partial", "Simulated"],
        "timestamp": _utcnow(),
    }


async def enrich_oracle_envelope(envelope: dict[str, Any], asset: str) -> dict[str, Any]:
    """Add verifiable AI citation block to Oracle API responses."""
    sym = asset.upper().replace("/USDT", "")
    data = envelope.get("data") or {}
    meta = envelope.get("metadata") or {}
    fetched_at = meta.get("fetched_at") or envelope.get("timestamp") or _utcnow()
    freshness = _freshness_for_asset(sym, "oracle")

    evidence = []
    if data.get("verdict") is not None:
        evidence.append(
            _build_evidence_item(
                fact=f"{sym} verdict {data.get('verdict')}",
                source_api=_ORACLE_SOURCE_LABEL,
                timestamp=fetched_at,
                value={"verdict": data.get("verdict"), "confidence_score": data.get("confidence_score")},
                freshness_ms=freshness.get("latency_ms"),
                source_link=_source_link("oracle", sym),
            )
        )

    envelope["verifiable_ai"] = {
        "feature_id": _FEATURE_ID,
        "evidence": evidence,
        "confidence_badge": _confidence_badge(evidence, tools_ok=bool(evidence)),
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "view_source_data": {"enabled": True, "links": [_source_link("oracle", sym)]},
    }
    return envelope
