"""Public site search index — titles and paths only (visitor nav + footer)."""

from __future__ import annotations

from typing import Any


def site_search_entries() -> list[dict[str, str]]:
    from site_services import footer_manifest

    entries: list[dict[str, str]] = [
        {"title": "Home", "path": "/", "tags": "blackdark trust pulse oracle"},
        {"title": "Pricing", "path": "/pricing", "tags": "plans free plus pro enterprise"},
        {"title": "Public Accuracy Ledger", "path": "/oracle-accuracy", "tags": "verify ledger misses"},
        {"title": "Open the lenses", "path": "/lenses", "tags": "prove operate desk room"},
        {"title": "Developer docs", "path": "/docs", "tags": "api public evidence"},
        {"title": "Contact", "path": "/contact", "tags": "support email complaints"},
        {"title": "Complaints", "path": "/complaints", "tags": "complaint dispute"},
        {"title": "Login", "path": "/login", "tags": "sign in account"},
        {"title": "FAQ", "path": "/faq", "tags": "help questions"},
        {"title": "Capabilities", "path": "/capabilities", "tags": "product features"},
        {"title": "B2B Institutional Feed", "path": "/b2b", "tags": "institutional api websocket"},
        {"title": "Data Room", "path": "/data-room", "tags": "institutional room"},
        {"title": "Cookies", "path": "/cookies", "tags": "privacy analytics optional"},
    ]
    fm = footer_manifest()
    seen = {e["path"] for e in entries}
    for group in ("product", "trust", "company", "legal"):
        for item in fm.get(group) or []:
            href = str(item.get("href") or "").strip()
            if not href.startswith("/") or href in seen:
                continue
            seen.add(href)
            entries.append(
                {
                    "title": str(item.get("label") or href),
                    "path": href,
                    "tags": group,
                }
            )
    return entries


def search_site(query: str, limit: int = 12) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        return []
    out: list[dict[str, Any]] = []
    for row in site_search_entries():
        blob = f"{row['title']} {row['path']} {row.get('tags', '')}".lower()
        if q in blob or all(part in blob for part in q.split() if len(part) > 1):
            out.append(row)
    return out[:limit]
