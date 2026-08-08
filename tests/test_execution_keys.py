"""Tests for execution keys module."""

from __future__ import annotations

from pathlib import Path

from execution_keys import execution_keys_status, parse_exchange_keys_file


def test_parse_exchange_keys_file(tmp_path: Path):
    f = tmp_path / "exchange_keys.env"
    f.write_text(
        "BINANCE_API_KEY=abc\nBINANCE_API_SECRET=sec\nAUTO_EXECUTION_DRY_RUN=true\n",
        encoding="utf-8",
    )
    parsed = parse_exchange_keys_file(f)
    assert parsed["BINANCE_API_KEY"] == "abc"
    assert parsed["AUTO_EXECUTION_DRY_RUN"] == "true"


def test_execution_keys_status_defaults():
    data = execution_keys_status()
    assert "mode" in data
    assert data["keys_file"].endswith("exchange_keys.env")
