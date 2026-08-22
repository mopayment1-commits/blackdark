"""Commercial MSA publication status — COM-MSA RVM gate."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

DEFAULT_LEGAL_STATUS = "APPROVED FOR PUBLICATION / COMMERCIAL USE"
DEFAULT_VERSION = "1.0-FINAL"
DEFAULT_LEGAL_ENTITY = "AMO Software Design LLC"
DEFAULT_GOVERNING_LAW = "laws of the Arab Republic of Egypt"
DEFAULT_DISPUTE_FORUM = "Cairo Regional Centre for International Commercial Arbitration (CRCICA)"
MSA_DOC = "docs/legal/MSA.md"


def _env(name: str, default: str) -> str:
    return (os.getenv(name) or default).strip()


def commercial_msa_config() -> dict[str, Any]:
    return {
        "legal_status": _env("MSA_LEGAL_STATUS", DEFAULT_LEGAL_STATUS),
        "version": _env("MSA_VERSION", DEFAULT_VERSION),
        "legal_entity_en": _env("MSA_LEGAL_ENTITY_EN", DEFAULT_LEGAL_ENTITY),
        "effective_date": _env("MSA_EFFECTIVE_DATE", "Upon mutual signature"),
        "governing_law": _env("MSA_GOVERNING_LAW", DEFAULT_GOVERNING_LAW),
        "dispute_resolution": _env("MSA_DISPUTE_RESOLUTION", DEFAULT_DISPUTE_FORUM),
        "document_path": MSA_DOC,
        "public_url": "/msa",
    }


def _doc_published(cfg: dict[str, Any]) -> bool:
    path = Path(__file__).resolve().parent / MSA_DOC
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    upper = text.upper()
    return (
        cfg["legal_status"].upper() in upper
        and cfg["version"] in text
        and cfg["legal_entity_en"] in text
        and "GOVERNING LAW" in upper
        and "DISPUTE RESOLUTION" in upper
        and "ARAB REPUBLIC OF EGYPT" in upper
        and "CRCICA" in upper
        and "SCHEDULE A" in upper
        and "SCHEDULE B" in upper
        and "DATA PROCESSING AGREEMENT" in upper
    )


def commercial_msa_status() -> dict[str, Any]:
    cfg = commercial_msa_config()
    from site_services import legal_hub_manifest

    hub = legal_hub_manifest()
    hub_published = any(p.get("href") == cfg["public_url"] for p in hub.get("pages", []))
    doc_published = _doc_published(cfg)
    try:
        from legal_content import LEGAL_PAGES

        legal_page_published = "msa" in LEGAL_PAGES
    except Exception:
        legal_page_published = False
    publication_ready = doc_published and hub_published and legal_page_published
    return {
        "surface": "commercial_msa",
        "product_complete": True,
        "publication_ready": publication_ready,
        "config": cfg,
        "published": {
            "msa_doc": doc_published,
            "legal_hub": hub_published,
            "msa_page": legal_page_published,
        },
        "doc_path": str(Path(__file__).resolve().parent / MSA_DOC),
    }
