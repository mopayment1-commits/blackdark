# Portfolio Risk Management — Feature #109

Actionable Portfolio AI risk surface (NOT generic fear/greed indices).

| Capability | Function | API |
|------------|----------|-----|
| Stop-loss suggestions | `suggest_stop_loss()` | via `/api/platform/portfolio/risk` |
| Protocol risk score | `score_protocol_risk()` | via `/api/platform/portfolio/risk` |
| Concentration risk | `analyze_concentration()` | via `/api/platform/portfolio/risk` |

Portfolio analyze enrichment: `POST /portfolio/analyze` → `risk_management` block.

## Actionable outputs

1. **Stop-loss**: "If SOL drops 5%, sell 20% of position" (volatility-scaled)
2. **Protocol risk**: "Exit New Farm — TVL under $10M + audit older than 2 years"
3. **Concentration**: "60% of portfolio in Solana ecosystem — concentration risk"

## Security integration

- #190 Security Controls — `security.controls_verified` in response
- #192 Security-First Architecture — `security.security_first_architecture`
- `risk_manager` execution freeze state surfaced

## Acceptance criteria

| Criterion | Target |
|-----------|--------|
| API latency | ≤2s (`sla_met`) |
| Accuracy | ≥95% (protocol registry + vol model) |
| Mode | `suggestion_only` — not auto-execution |
