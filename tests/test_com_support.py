"""COM-SUPPORT commercial support closure tests."""

from __future__ import annotations

import pytest


def test_commercial_support_operational_ready():
    from commercial_support import commercial_support_status

    status = commercial_support_status()
    assert status["operational_ready"] is True
    cfg = status["config"]
    assert cfg["support_email"] == "mopayment1@gmail.com"
    assert cfg["support_owner"] == "Project owner/operator"
    assert "Cairo" in cfg["support_hours"]
    assert cfg["urgent_escalation"]["subject_prefix"] == "URGENT"


def test_contact_channels_publish_support_details():
    from site_services import contact_channels

    contact = contact_channels()
    assert contact["support_email"] == "mopayment1@gmail.com"
    assert contact["support_owner"]
    assert contact["support_hours"]
    assert contact["urgent_escalation"]["subject_prefix"] == "URGENT"


@pytest.mark.asyncio
async def test_com_support_rvm_gate_pass():
    from rvm.verify import verify_commercial_gate

    gate = await verify_commercial_gate("COM-SUPPORT")
    assert gate["status"] == "PASS"
    assert "support_email=mopayment1@gmail.com" in gate["evidence"]
    assert "urgent_escalation_published" in gate["evidence"]
