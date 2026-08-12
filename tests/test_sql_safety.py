"""Bandit sql_safety allowlist helpers."""

from __future__ import annotations

import pytest

import sql_safety


def test_require_sql_ident_accepts_safe():
    assert sql_safety.require_sql_ident("pricing_logs") == "pricing_logs"


def test_require_sql_ident_rejects_injection():
    with pytest.raises(ValueError):
        sql_safety.require_sql_ident("evil;drop")
    with pytest.raises(ValueError):
        sql_safety.require_sql_ident("1bad")


def test_require_sqlite_table_allowlist():
    assert sql_safety.require_sqlite_table("pricing_logs") == "pricing_logs"
    with pytest.raises(ValueError):
        sql_safety.require_sqlite_table("not_allowlisted_table")


def test_table_count_and_delete_catalogs():
    assert "COUNT(*)" in sql_safety.table_count_sql("pricing_logs")
    assert "DELETE FROM pricing_logs" in sql_safety.delete_all_sql("pricing_logs")
    assert "timestamp < ?" in sql_safety.delete_before_sql("order_books")
    with pytest.raises(ValueError):
        sql_safety.delete_all_sql("oracle_predictions")  # not in delete-all catalog


def test_platform_metric_increment_sql():
    sql = sql_safety.platform_metric_increment_sql("page_views")
    assert "page_views" in sql
    with pytest.raises(ValueError):
        sql_safety.platform_metric_increment_sql("not_a_metric")


def test_user_profile_update_and_oracle_constants():
    assert "UPDATE users SET name" in sql_safety.USER_PROFILE_UPDATE_SQL["name"]
    assert "historical_seed" in sql_safety.LIVE_ORACLE_SOURCE_SQL
    assert len(sql_safety.RISK_ORACLE_VERDICTS) == 4
    assert sql_safety.require_schema_ident("public") == "public"
