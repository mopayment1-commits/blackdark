"""COM-SLA commercial SLA publication closure tests."""

from __future__ import annotations

import pytest


def test_commercial_sla_publication_ready():
    from commercial_sla import commercial_sla_status

    status = commercial_sla_status()
    assert status["publication_ready"] is True
    cfg = status["config"]
    assert cfg["legal_status"] == "APPROVED FOR PUBLICATION"
    assert cfg["effective_date"] == "1 January 2025"
    assert cfg["legal_entity_en"] == "MO Software Design LLC"
    assert "Arab Republic of Egypt" in cfg["governing_law"]
    assert "Cairo" in cfg["dispute_resolution"]


def test_legal_hub_lists_sla_page():
    from site_services import legal_hub_manifest

    hub = legal_hub_manifest()
    assert any(p.get("href") == "/sla" for p in hub["pages"])


def test_sla_legal_page_registered():
    from legal_content import LEGAL_PAGES

    assert "sla" in LEGAL_PAGES
    assert "APPROVED FOR PUBLICATION" in LEGAL_PAGES["sla"]["html"]
    assert "MO Software Design LLC" in LEGAL_PAGES["sla"]["html"]


@pytest.mark.asyncio
async def test_com_sla_rvm_gate_pass():
    from rvm.verify import verify_commercial_gate

    gate = await verify_commercial_gate("COM-SLA")
    assert gate["status"] == "PASS"
    assert "legal_status=APPROVED FOR PUBLICATION" in gate["evidence"]
    assert "effective_date=1 January 2025" in gate["evidence"]
    assert "governing_law_published" in gate["evidence"]
