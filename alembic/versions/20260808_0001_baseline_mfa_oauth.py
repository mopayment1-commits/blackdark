"""baseline MFA / OAuth user columns

Revision ID: 20260808_0001
Revises:
Create Date: 2026-08-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260808_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "users" not in inspector.get_table_names():
        return
    cols = {c["name"] for c in inspector.get_columns("users")}
    alter = []
    if "mfa_enabled" not in cols:
        alter.append(sa.Column("mfa_enabled", sa.Integer(), server_default="0"))
    if "mfa_secret_enc" not in cols:
        alter.append(sa.Column("mfa_secret_enc", sa.Text()))
    if "mfa_pending_secret_enc" not in cols:
        alter.append(sa.Column("mfa_pending_secret_enc", sa.Text()))
    if "mfa_recovery_hashes" not in cols:
        alter.append(sa.Column("mfa_recovery_hashes", sa.Text()))
    if "oauth_provider" not in cols:
        alter.append(sa.Column("oauth_provider", sa.Text()))
    if "oauth_subject" not in cols:
        alter.append(sa.Column("oauth_subject", sa.Text()))
    if "password_hash" in cols:
        # Allow empty password for OAuth-only accounts (nullable already or keep as-is).
        pass
    for col in alter:
        op.add_column("users", col)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "users" not in inspector.get_table_names():
        return
    cols = {c["name"] for c in inspector.get_columns("users")}
    for name in (
        "oauth_subject",
        "oauth_provider",
        "mfa_recovery_hashes",
        "mfa_pending_secret_enc",
        "mfa_secret_enc",
        "mfa_enabled",
    ):
        if name in cols:
            op.drop_column("users", name)
