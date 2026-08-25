"""
BLACKDARK Research Portal — Feature #187.

Searchable research library: sector/protocol reports with tagging,
full-text + semantic search, version archive, and saved items.
"""

from __future__ import annotations

import json
import logging
import re
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.ResearchPortal")

_FEATURE_ID = 187
_STORE_PATH = Path("data/research_portal.json")
_SEED_PATH = Path("data/research_portal_seed.json")

_SEMANTIC_EXPANSIONS: dict[str, list[str]] = {
    "سيولة": ["liquidity", "liquid", "depth", "order book", "orderbook"],
    "البيتكوين": ["bitcoin", "btc"],
    "بيتكوين": ["bitcoin", "btc"],
    "تمويل": ["defi", "finance", "lending"],
    "مشاعر": ["sentiment", "social", "mood"],
    "أمان": ["security", "exploit", "risk"],
    "liquidity": ["سيولة", "depth", "order book"],
    "bitcoin": ["btc", "بيتكوين"],
    "defi": ["decentralized", "tvl", "تمويل"],
    "sentiment": ["social", "مشاعر", "volume"],
    "whale": ["accumulation", "on-chain", "حوت"],
    "macro": ["fed", "dxy", "interest", "اقتصاد"],
    "security": ["exploit", "hack", "أمان"],
    "etf": ["institutional", "flows", "spot"],
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _tokenize(text: str) -> list[str]:
    cleaned = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text.lower())
    return [t for t in cleaned.split() if len(t) > 1]


def _expand_query_tokens(tokens: list[str]) -> set[str]:
    expanded = set(tokens)
    for tok in tokens:
        expanded.add(tok)
        for key, synonyms in _SEMANTIC_EXPANSIONS.items():
            if tok == key or tok in synonyms:
                expanded.add(key)
                expanded.update(synonyms)
    return expanded


def _load_store() -> dict[str, Any]:
    if not _STORE_PATH.is_file():
        return _bootstrap_store()
    try:
        return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _bootstrap_store()


def _bootstrap_store() -> dict[str, Any]:
    reports: dict[str, Any] = {}
    if _SEED_PATH.is_file():
        try:
            seed_rows = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
            for row in seed_rows:
                rid = row["id"]
                reports[rid] = {
                    **row,
                    "version": 1,
                    "version_history": [],
                    "updated_at": row.get("publication_date", _utcnow()),
                }
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("research seed load failed: %s", exc)
    store = {"reports": reports, "saved_items": {}, "updated_at": _utcnow()}
    _save_store(store)
    return store


def _save_store(blob: dict[str, Any]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    blob["updated_at"] = _utcnow()
    _STORE_PATH.write_text(json.dumps(blob, indent=2, ensure_ascii=False), encoding="utf-8")


def _score_report(report: dict[str, Any], query_tokens: set[str], mode: str) -> float:
    if not query_tokens:
        return 0.0
    fields = {
        "title": 4.0,
        "summary": 2.5,
        "body": 1.0,
        "sector": 3.0,
        "author": 1.5,
    }
    score = 0.0
    tags = [str(t).lower() for t in report.get("tags") or []]
    assets = [str(a).lower() for a in report.get("assets") or []]

    for field, weight in fields.items():
        text = str(report.get(field) or "").lower()
        field_tokens = set(_tokenize(text))
        overlap = len(query_tokens & field_tokens)
        score += overlap * weight

    tag_overlap = len(query_tokens & set(tags))
    score += tag_overlap * 5.0
    asset_overlap = len(query_tokens & set(assets))
    score += asset_overlap * 4.0

    if mode == "semantic":
        for qt in query_tokens:
            for tag in tags:
                if qt in tag or tag in qt:
                    score += 2.0
    return score


def search_reports(
    query: str,
    *,
    mode: Literal["fulltext", "semantic"] = "fulltext",
    sector: str | None = None,
    asset: str | None = None,
    author: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Full-text or semantic search across research library."""
    store = _load_store()
    tokens = _tokenize(query)
    expanded = _expand_query_tokens(tokens) if mode == "semantic" else set(tokens)

    results: list[dict[str, Any]] = []
    for report in store.get("reports", {}).values():
        if sector and str(report.get("sector", "")).lower() != sector.lower():
            continue
        if asset:
            assets_upper = [str(a).upper() for a in report.get("assets") or []]
            if asset.upper() not in assets_upper:
                continue
        if author and author.lower() not in str(report.get("author", "")).lower():
            continue

        relevance = _score_report(report, expanded, mode)
        if query.strip() and relevance <= 0:
            continue
        results.append({
            "id": report["id"],
            "title": report.get("title"),
            "author": report.get("author"),
            "sector": report.get("sector"),
            "assets": report.get("assets"),
            "tags": report.get("tags"),
            "summary": report.get("summary"),
            "source": report.get("source"),
            "publication_date": report.get("publication_date"),
            "version": report.get("version", 1),
            "relevance_score": round(relevance, 2),
        })

    results.sort(key=lambda r: (-r["relevance_score"], r.get("publication_date") or ""), reverse=False)
    if not query.strip():
        results.sort(key=lambda r: r.get("publication_date") or "", reverse=True)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "query": query,
        "mode": mode,
        "count": len(results[:limit]),
        "results": results[:limit],
        "filters_applied": {
            "sector": sector,
            "asset": asset,
            "author": author,
        },
        "timestamp": _utcnow(),
    }


def get_report(report_id: str, *, version: int | None = None) -> dict[str, Any]:
    """Get report by ID; optional historical version from archive."""
    store = _load_store()
    report = store.get("reports", {}).get(report_id)
    if not report:
        return {"ok": False, "error": "report_not_found"}

    if version is not None and version != report.get("version"):
        for archived in report.get("version_history") or []:
            if archived.get("version") == version:
                return {
                    "ok": True,
                    "feature_id": _FEATURE_ID,
                    "report": archived,
                    "archived": True,
                    "current_version": report.get("version"),
                }
        return {"ok": False, "error": "version_not_found"}

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "report": report,
        "version_count": 1 + len(report.get("version_history") or []),
        "has_previous_versions": bool(report.get("version_history")),
        "timestamp": _utcnow(),
    }


def update_report(
    report_id: str,
    *,
    editor_id: str,
    title: str | None = None,
    summary: str | None = None,
    body: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Update report — archives previous version automatically."""
    store = _load_store()
    report = store.get("reports", {}).get(report_id)
    if not report:
        return {"ok": False, "error": "report_not_found"}

    archive = {
        "version": report.get("version", 1),
        "title": report.get("title"),
        "summary": report.get("summary"),
        "body": report.get("body"),
        "tags": list(report.get("tags") or []),
        "archived_at": _utcnow(),
        "archived_by": editor_id,
    }
    history = list(report.get("version_history") or [])
    history.append(archive)

    if title is not None:
        report["title"] = title
    if summary is not None:
        report["summary"] = summary
    if body is not None:
        report["body"] = body
    if tags is not None:
        report["tags"] = tags

    report["version"] = int(report.get("version") or 1) + 1
    report["version_history"] = history
    report["updated_at"] = _utcnow()
    report["last_editor"] = editor_id
    store["reports"][report_id] = report
    _save_store(store)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "report_id": report_id,
        "version": report["version"],
        "previous_versions": len(history),
        "message": f"Report updated — {len(history)} previous version(s) archived",
        "timestamp": _utcnow(),
    }


def save_report_for_user(user_id: str, report_id: str) -> dict[str, Any]:
    store = _load_store()
    if report_id not in store.get("reports", {}):
        return {"ok": False, "error": "report_not_found"}

    uid = str(user_id)
    saved = store.setdefault("saved_items", {}).setdefault(uid, [])
    if report_id not in saved:
        saved.append(report_id)
    _save_store(store)
    return {"ok": True, "feature_id": _FEATURE_ID, "saved": True, "report_id": report_id}


def unsave_report_for_user(user_id: str, report_id: str) -> dict[str, Any]:
    store = _load_store()
    uid = str(user_id)
    saved = store.get("saved_items", {}).get(uid, [])
    if report_id in saved:
        saved.remove(report_id)
    _save_store(store)
    return {"ok": True, "feature_id": _FEATURE_ID, "saved": False, "report_id": report_id}


def list_saved_reports(user_id: str) -> dict[str, Any]:
    store = _load_store()
    saved_ids = store.get("saved_items", {}).get(str(user_id), [])
    reports = [store["reports"][rid] for rid in saved_ids if rid in store.get("reports", {})]
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "count": len(reports),
        "saved": [
            {
                "id": r["id"],
                "title": r.get("title"),
                "sector": r.get("sector"),
                "assets": r.get("assets"),
                "version": r.get("version"),
                "publication_date": r.get("publication_date"),
            }
            for r in reports
        ],
        "timestamp": _utcnow(),
    }


def list_filters() -> dict[str, Any]:
    store = _load_store()
    reports = list(store.get("reports", {}).values())
    sectors = sorted({str(r.get("sector")) for r in reports if r.get("sector")})
    assets = sorted({a for r in reports for a in (r.get("assets") or [])})
    authors = sorted({str(r.get("author")) for r in reports if r.get("author")})
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "sectors": sectors,
        "assets": assets,
        "authors": authors,
        "report_count": len(reports),
        "timestamp": _utcnow(),
    }


def research_portal_status() -> dict[str, Any]:
    store = _load_store()
    reports = list(store.get("reports", {}).values())
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "BLACKDARK Research Portal",
        "report_count": len(reports),
        "internal_reports_target": "20-30",
        "tagging": ["Sector", "Asset", "Date", "Author"],
        "search_modes": ["fulltext", "semantic"],
        "version_archive": True,
        "saved_items": True,
        "community_open": False,
        "source_metadata": True,
        "timestamp": _utcnow(),
    }
