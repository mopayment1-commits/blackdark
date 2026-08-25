# Options Intelligence Module — #274 + #275 + #276 (Wave 3)

**NOT standalone** — merged cluster: **Options Intelligence Module (Wave 3)**.

| Ticket | Role |
|--------|------|
| #274 | Product/analytics layer |
| #275 | Data normalization layer (chains, IV, OI) |
| #276 | Volume sub-task |

Dashboard UI deferred — backend module only. Pro/Institution tier (Wave 3).

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Dependency gate | Spot + Perp data (Sprint 1 stable) before options |
| Scope Phase 1 | Deribit only |
| Scope Phase 2 | DEX options (Lyra, Premia) |
| Scope Phase 3 | CME |
| No TradFi | Equity options excluded |
| Mapping accuracy | Expiry/strike mapping > 99% |
| IV surface | Black-Scholes-Merton model documented |
| OI | Verified against exchange |
| Greeks | Exchange-sourced or BSM-calculated with documented formula |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/options/status` | Module status + acceptance criteria |
| `GET /api/platform/intelligence-ledger/options` | Full panel (mapping, IV, OI, Greeks, data + volume layers) |

## Data Sources

- Phase 1: Deribit public API via `options_fetcher.py`
- Normalized fields: expiry, strike, option_type, mark_iv, open_interest, volume_24h

## Disclaimer

"Options analytics for institutional due diligence — not auto-execution." Non-hideable.
