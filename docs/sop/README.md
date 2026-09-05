# BLACKDARK Release Engineering SOPs

Standard Operating Procedures — **not sprint tickets**. Run with every release.

| SOP | Feature | Scope | Script |
|-----|---------|-------|--------|
| [RELEASE_CAPACITY_EVIDENCE_SOP.md](./RELEASE_CAPACITY_EVIDENCE_SOP.md) | #30 | Load/soak/burst evidence, SLO pass/fail, regression trend | `scripts/release_capacity_evidence.py` |
| [RELEASE_CHAOS_RESILIENCE_SOP.md](./RELEASE_CHAOS_RESILIENCE_SOP.md) | #31 | Controlled fault injection, fail-closed, recovery proof | `scripts/release_chaos_gate.py` |
| [../infrastructure/RESILIENCE_PATTERNS.md](../infrastructure/RESILIENCE_PATTERNS.md) | #32 | Circuit breakers on every external API call | `blackdark/ingestion/connector_cache.py` |

## Release gate (run before deploy)

```bash
python scripts/release_engineering_gate.py
```

This orchestrates capacity evidence + chaos resilience checks and writes a combined report to `data/release_engineering/`.
