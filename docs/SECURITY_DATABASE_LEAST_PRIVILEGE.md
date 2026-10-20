# Database least privilege (operations)

Application code uses a single `DATABASE_URL` / `POSTGRES_URL` role today. For production hardening:

1. Create a dedicated app role with `CONNECT` on the app database only.
2. Grant `SELECT`, `INSERT`, `UPDATE`, `DELETE` on application tables — not `SUPERUSER`, not `CREATEDB`.
3. Revoke `DROP` on production schemas; run migrations from a separate CI role.
4. Enable `log_connections`, `log_disconnections`, and `log_statement = 'ddl'` on Postgres for anomaly review.
5. Sensitive columns (`mfa_secret_enc`, sealed session cookies) rely on `secrets_vault` Fernet — rotate `SECRETS_MASTER_KEY` via envelope migration runbooks.

This repository enforces parameterized SQL in `database.py`; never concatenate user input into queries.
