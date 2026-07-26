"""Tests for auto key import from keys/platform_keys.env."""

from __future__ import annotations

from pathlib import Path

from bd_platform import auto_keys


def test_parse_keys_file_skips_comments_and_blanks(tmp_path: Path):
    f = tmp_path / "platform_keys.env"
    f.write_text(
        "# comment\nLUNARCRUSH_API_KEY=abc123\nCOINMARKETCAL_API_KEY=\nDEBANK_API_KEY=xyz\n",
        encoding="utf-8",
    )
    parsed = auto_keys.parse_keys_file(f)
    assert parsed == {
        "LUNARCRUSH_API_KEY": "abc123",
        "DEBANK_API_KEY": "xyz",
    }


def test_payload_from_env_file(tmp_path: Path):
    f = tmp_path / "platform_keys.env"
    f.write_text("COINMARKETCAL_API_KEY=cal-key\n", encoding="utf-8")
    assert auto_keys.payload_from_env_file(f) == {"coinmarketcal": "cal-key"}
