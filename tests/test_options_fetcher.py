"""Tests for options fetcher (mocked HTTP)."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_fetch_options_success():
    from options_fetcher import fetch_deribit_options_summary

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={
        "result": [{"instrument_name": "BTC-TEST", "mark_price": 0.05, "bid_price": 0.04, "ask_price": 0.06}]
    })

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_ctx)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("options_fetcher.aiohttp.ClientSession", return_value=mock_session):
        result = await fetch_deribit_options_summary("BTC")

    assert result["success"] is True
    assert result["count"] == 1
