"""Tests for postgres backend helper."""

from postgres_backend import use_postgres, _sqlite_schema_to_pg


def test_use_postgres_false_when_empty(monkeypatch):
    import config
    monkeypatch.setattr(config, "DATABASE_URL", "")
    assert use_postgres() is False


def test_use_postgres_true(monkeypatch):
    import config
    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://u:p@localhost/db")
    assert use_postgres() is True


def test_schema_conversion():
    sql = "CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT, price REAL)"
    pg = _sqlite_schema_to_pg(sql)
    assert "SERIAL PRIMARY KEY" in pg
    assert "DOUBLE PRECISION" in pg
