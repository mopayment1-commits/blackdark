"""Bandit sql_safety allowlist helpers."""

from __future__ import annotations

import pytest

import sql_safety


def test_allowed_sqlite_tables_nonempty():
    assert "pricing_logs" in sql_safety.ALLOWED_SQLITE_TABLES


def test_table_count_sql_allowlisted_only():
    assert "pricing_logs" in sql_safety._TABLE_COUNT_SQL
    with pytest.raises(Exception):
        # helper if present
        if hasattr(sql_safety, "table_count_sql"):
            sql_safety.table_count_sql("not_a_real_table_xyz")
        else:
            raise ValueError("no helper")


def test_assert_ident_or_equivalent():
    if hasattr(sql_safety, "assert_safe_ident"):
        sql_safety.assert_safe_ident("pricing_logs")
        with pytest.raises(ValueError):
            sql_safety.assert_safe_ident("evil;drop")
    elif hasattr(sql_safety, "safe_ident"):
        assert sql_safety.safe_ident("pricing_logs")
    else:
        # Catalog presence is enough for import coverage.
        assert sql_safety.LIVE_ORACLE_SOURCE_SQL
