# External Vendor / Dependency Map

| Dependency | Type | Criticality | Repo evidence | Live evidence |
|------------|------|-------------|---------------|---------------|
| PostgreSQL | Infra | High | compose, `postgres_backend.py` | Buyer deploy |
| Redis | Infra | High for viral | compose, viral tests | Buyer deploy |
| Exchange APIs | Market data | High | ccxt / adapters | API keys EXTERNAL |
| Public EVM/Solana RPC | Gas | Medium | `gas_oracle.py` | Network |
| Dexscreener | DeFi scans | Low/Med | `defi_arbitrage_engine.py` | Network |
| Stripe / Lemon | Payments | High for paid | scripts + routers | `F-EXT-01` |
| Telegram | Alerts | Low | setup + alert_service | Bot token |
| SonarCloud | Quality gate | Med | workflow | Admin `F-EXT-08` |
| GitHub Actions / CodeQL | SDLC | Med | workflows | UI `F-EXT-02` |
| HashiCorp Vault `-dev` | Local optional | None (prod) | compose profile `vault-dev` | N/A |
