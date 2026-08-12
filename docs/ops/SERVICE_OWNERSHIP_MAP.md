# Service Ownership Map

| Service / module | Runtime entry | Owner role | Critical data |
|------------------|---------------|------------|---------------|
| Web / Dashboard | `dashboard:app` / `SERVICE_MODE=web` | Platform | Sessions, UI, API mount |
| Oracle (canonical) | `oracle_unified.py` | Product/Quant | Decision scores |
| Arb evaluation | `ai_oracle.py` + `arbitrage_engine.py` | Quant | Opportunity labels |
| Fee authority | `fee_matrix.py` | Quant/Risk | Venue fees |
| Money math | `money_decimal.py` | Quant/Risk | Decimal net |
| Gas oracle | `gas_oracle.py` | Data | Chain gas USD |
| Ingestion | `run_service.py ingestion` | Data | Order books |
| Postgres | `database.py` / `postgres_backend.py` | Platform | System of record |
| Redis | viral / bus | Platform | Coord/cache |
| Alerts | `alert_service.py` | Growth/Ops | Telegram/email |
| Payments | Stripe/Lemon routers | Growth | Subscriptions |
| Observability | `observability.py` | SRE | `/metrics` |

## External vendors

| Vendor | Used for | Fail mode |
|--------|----------|-----------|
| Exchange APIs (ccxt / venues) | Market data | Degrade scans; no invented books |
| Dexscreener / public RPCs | DeFi / gas | Fail closed when stale/unknown |
| Stripe / Lemon | Billing | Soft Launch may defer |
| Telegram | Alerts | Optional |
| SonarCloud / GitHub | SDLC gates | Admin EXTERNAL |
