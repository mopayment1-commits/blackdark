# Database migration authority

## Canonical authority

**Runtime schema authority is `database.py`:**

1. `SCHEMA` — baseline tables
2. `_apply_migrations()` — additive / upgrade DDL

`init_db()` applies both for SQLite and PostgreSQL.

## PostgreSQL dialect

`postgres_backend._sqlite_schema_to_pg()` translates:

- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- `REAL` → `DOUBLE PRECISION`
- `INSERT OR IGNORE` → `INSERT … ON CONFLICT DO NOTHING` (execute path)

`PgConnectionAdapter.execute()` always runs DDL through this translator so
migration statements are valid on Postgres.

## Alembic status

`alembic/` is **not** the runtime authority. The baseline revision only covers
MFA/OAuth columns and is incomplete relative to `_apply_migrations`.

Do not run Alembic as a second competing migration path in production until
revisions are generated from the full live schema and `init_db` is switched
explicitly. Until then, treat Alembic as historical / optional tooling only.

## Transactions

`pg_connection()` opens an asyncpg transaction. Adapter `commit()` / `rollback()`
commit or roll back that transaction and open a fresh one so mid-context
semantics match SQLite caller expectations.
