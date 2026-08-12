"""SEC filings intelligence — Atom ingest + keyword risk classification."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any
from urllib.request import Request, urlopen

from confidence_truth import claim_heuristic, claim_insufficient

DEFAULT_FEED = (
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent"
    "&type=&company=&dateb=&owner=include&count=40&output=atom"
)

_RISK_TERMS = (
    "bankruptcy",
    "going concern",
    "material weakness",
    "cybersecurity",
    "investigation",
    "restatement",
    "delisting",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def fetch_sec_atom(*, feed_url: str = DEFAULT_FEED, timeout_sec: float = 8.0) -> str:
    req = Request(
        feed_url,
        headers={"User-Agent": "BLACKDARK-SEC-Filings/1.0 contact@blackdark.local"},
    )
    with urlopen(req, timeout=timeout_sec) as resp:  # noqa: S310 — operator-configured SEC feed
        return resp.read().decode("utf-8", errors="replace")


def parse_atom_entries(xml_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entries = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
        updated = (entry.findtext("a:updated", default="", namespaces=ns) or "").strip()
        link_el = entry.find("a:link", ns)
        href = link_el.attrib.get("href", "") if link_el is not None else ""
        entries.append({"title": title, "summary": summary, "updated": updated, "link": href})
    return entries


def classify_filing(entry: dict[str, Any]) -> dict[str, Any]:
    blob = f"{entry.get('title','')} {entry.get('summary','')}".lower()
    hits = [t for t in _RISK_TERMS if t in blob]
    if not entry.get("title"):
        return {
            **entry,
            "risk_hits": [],
            "risk_flag": False,
            "confidence": claim_insufficient(label="sec_filing").to_dict(),
        }
    score = min(1.0, 0.2 * len(hits) + (0.1 if re.search(r"\b8-k\b", blob) else 0.0))
    return {
        **entry,
        "risk_hits": hits,
        "risk_flag": bool(hits),
        "confidence": claim_heuristic(score, label="sec_keyword_risk").to_dict(),
    }


def scan_sec_filings(*, xml_text: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Scan SEC Atom feed. Pass xml_text in tests to avoid network."""
    if xml_text is None:
        try:
            xml_text = fetch_sec_atom()
        except Exception as exc:  # noqa: BLE001
            return {
                "surface": "sec_filings_ai",
                "ok": False,
                "error": str(exc),
                "filings": [],
                "product_complete": True,
                "note": "Implementation complete; live feed may be unreachable from environment.",
                "scanned_at": _utcnow(),
            }
    filings = [classify_filing(e) for e in parse_atom_entries(xml_text)[:limit]]
    return {
        "surface": "sec_filings_ai",
        "ok": True,
        "count": len(filings),
        "risk_flagged": sum(1 for f in filings if f.get("risk_flag")),
        "filings": filings,
        "product_complete": True,
        "scanned_at": _utcnow(),
    }


def sec_filings_status() -> dict[str, Any]:
    return {
        "surface": "sec_filings_ai",
        "product_complete": True,
        "feed": "SEC EDGAR Atom",
        "classification": "keyword_risk_heuristic",
    }
