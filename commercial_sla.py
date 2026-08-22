"""Commercial SLA publication status — COM-SLA RVM gate."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

DEFAULT_LEGAL_STATUS = "APPROVED FOR PUBLICATION"
DEFAULT_EFFECTIVE_DATE = "1 January 2025"
DEFAULT_LEGAL_ENTITY_EN = "MO Software Design LLC"
DEFAULT_LEGAL_ENTITY_AR = "شركة أم أو لتصميم البرامج"
SLA_DOC = "docs/legal/SLA.md"


def _env(name: str, default: str) -> str:
    return (os.getenv(name) or default).strip()


def commercial_sla_config() -> dict[str, Any]:
    return {
        "legal_status": _env("SLA_LEGAL_STATUS", DEFAULT_LEGAL_STATUS),
        "effective_date": _env("SLA_EFFECTIVE_DATE", DEFAULT_EFFECTIVE_DATE),
        "legal_entity_en": _env("SLA_LEGAL_ENTITY_EN", DEFAULT_LEGAL_ENTITY_EN),
        "legal_entity_ar": _env("SLA_LEGAL_ENTITY_AR", DEFAULT_LEGAL_ENTITY_AR),
        "governing_law": _env(
            "SLA_GOVERNING_LAW",
            "Laws of the Arab Republic of Egypt",
        ),
        "dispute_resolution": _env(
            "SLA_DISPUTE_RESOLUTION",
            "Good-faith negotiation via published support channels, then exclusive jurisdiction of the competent courts in Cairo, Egypt",
        ),
        "document_path": SLA_DOC,
        "public_url": "/sla",
    }


def _doc_published(cfg: dict[str, Any]) -> bool:
    path = Path(__file__).resolve().parent / SLA_DOC
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return (
        cfg["legal_status"].upper() in text.upper()
        and cfg["effective_date"] in text
        and cfg["legal_entity_en"] in text
        and cfg["legal_entity_ar"] in text
        and "governing law" in text.lower()
        and "dispute resolution" in text.lower()
        and cfg["governing_law"].lower() in text.lower()
    )


def commercial_sla_status() -> dict[str, Any]:
    cfg = commercial_sla_config()
    from site_services import legal_hub_manifest

    hub = legal_hub_manifest()
    hub_published = any(p.get("href") == cfg["public_url"] for p in hub.get("pages", []))
    doc_published = _doc_published(cfg)
    try:
        from legal_content import LEGAL_PAGES

        legal_page_published = "sla" in LEGAL_PAGES
    except Exception:
        legal_page_published = False
    publication_ready = doc_published and hub_published and legal_page_published
    return {
        "surface": "commercial_sla",
        "product_complete": True,
        "publication_ready": publication_ready,
        "config": cfg,
        "published": {
            "sla_doc": doc_published,
            "legal_hub": hub_published,
            "sla_page": legal_page_published,
        },
        "doc_path": str(Path(__file__).resolve().parent / SLA_DOC),
    }
