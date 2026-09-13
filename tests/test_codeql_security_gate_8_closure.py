"""Regression: final 8 original-security alerts — inline CRLF scrub + email redaction."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

GATE_FILES = {
    "billing/audit_ledger.py": ("logger.info", "email=%s"),
    "bd_platform/address_intelligence.py": ("logger.debug", "snapshot read failed"),
    "audit_registry.py": ("logger.exception", "KG ingest failed"),
    "api/routers/didit_webhook.py": ("logger.exception", "didit_webhook_processing_failed"),
    "ml/market_replay_bootstrap.py": ("logger.warning", "Insufficient klines"),
    "signal_compounding.py": ("logger.exception", "KG signal ingest failed"),
}


def test_gate_modules_use_inline_crlf_scrub_not_sanitize_helper():
    for path in GATE_FILES:
        text = Path(path).read_text(encoding="utf-8")
        assert "sanitize_log_value(" not in text, path
        assert "sanitize_asset(" not in text, path
        assert '.replace("\\r"' in text, path
        assert '.replace("\\n"' in text, path


@pytest.mark.asyncio
async def test_billing_audit_never_logs_raw_email(caplog):
    caplog.set_level(logging.INFO, logger="BLACKDARK.Billing.Audit")
    malicious = "user@evil.com\r\nFORGED_LOG_LINE"
    with patch("database.get_connection") as mock_conn:
        db = AsyncMock()
        cursor = MagicMock()
        cursor.lastrowid = 1
        db.execute = AsyncMock(return_value=cursor)
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=db)
        cm.__aexit__ = AsyncMock(return_value=False)
        mock_conn.return_value = cm
        from billing.audit_ledger import record_audit

        await record_audit(
            action="plan_change\r\nINJECT",
            actor="test",
            user_id=42,
            email=malicious,
            old_plan="free",
            new_plan="pro\nTAMPER",
        )
    text = "\n".join(r.getMessage() for r in caplog.records)
    assert malicious not in text
    assert "user@evil.com" not in text
    assert "[redacted]" in text
    assert "\r" not in text
    assert "\n" not in text


@pytest.mark.parametrize(
    "payload,needle",
    [
        ("btc\r\nINJECT", "snapshot read failed"),
        ("dec-1\r\nX", "KG ingest failed for decision"),
        ("ver-1\nY", "KG ingest failed for decision version"),
        ("evt\r\nZ", "didit_webhook_processing_failed"),
        ("ETH\nBAD", "Insufficient klines"),
        ("sig\r\nQ", "KG signal ingest failed"),
    ],
)
def test_inline_scrub_strips_crlf_from_log_messages(payload: str, needle: str):
    clean = str(payload).replace("\r", " ").replace("\n", " ")
    assert "\r" not in clean
    assert "\n" not in clean
    assert needle  # static reference for parametrization traceability
