# Data Categories (Technical Inventory)

| Category | Examples | Store | Notes |
|----------|----------|-------|-------|
| Market data | Order books, funding | Postgres / parquet | Public market origin |
| Decision artifacts | Oracle scores, truth gates | Postgres | Not financial advice |
| Account | Email, password hash, MFA secret | Postgres | Auth identity |
| Billing | Customer ids, subscription status | Postgres + PSP | PSP is system of charge |
| Secrets | Exchange keys (Fernet), bot tokens | Fernet / 0600 files | Never log |
| Ops logs | Request metrics, errors | App logs | Redact secrets |

Not a legal classification — counsel EXTERNAL.
