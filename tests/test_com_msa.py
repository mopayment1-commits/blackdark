"""COM-MSA commercial MSA publication closure tests."""

from __future__ import annotations

import pytest


def test_commercial_msa_publication_ready():
    from commercial_msa import commercial_msa_status

    status = commercial_msa_status()
    assert status["publication_ready"] is True
    cfg = status["config"]
    assert cfg["legal_status"] == "APPROVED FOR PUBLICATION / COMMERCIAL USE"
    assert cfg["version"] == "1.0-FINAL"
    assert cfg["legal_entity_en"] == "AMO Software Design LLC"
    assert "Arab Republic of Egypt" in cfg["governing_law"]
    assert "CRCICA" in cfg["dispute_resolution"]


def test_legal_hub_lists_msa_page():
    from site_services import legal_hub_manifest

    hub = legal_hub_manifest()
    assert any(p.get("href") == "/msa" for p in hub["pages"])


def test_msa_legal_page_registered():
    from legal_content import LEGAL_PAGES

    assert "msa" in LEGAL_PAGES
    assert "APPROVED FOR PUBLICATION / COMMERCIAL USE" in LEGAL_PAGES["msa"]["html"]
    assert "AMO Software Design LLC" in LEGAL_PAGES["msa"]["html"]
    assert "CRCICA" in LEGAL_PAGES["msa"]["html"]


def test_msa_doc_contains_schedules():
    from pathlib import Path

    text = Path("docs/legal/MSA.md").read_text(encoding="utf-8")
    assert "SCHEDULE A" in text
    assert "DATA PROCESSING AGREEMENT" in text
    assert "SCHEDULE B" in text
    assert "FINAL LEGAL REVIEW JUDGMENT" in text


@pytest.mark.asyncio
async def test_com_msa_rvm_gate_pass():
    from rvm.verify import verify_commercial_gate

    gate = await verify_commercial_gate("COM-MSA")
    assert gate["status"] == "PASS"
    assert "legal_status=APPROVED FOR PUBLICATION / COMMERCIAL USE" in gate["evidence"]
    assert "version=1.0-FINAL" in gate["evidence"]
    assert "crcica_dispute_resolution_published" in gate["evidence"]
