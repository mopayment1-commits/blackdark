# Gap Detection & Recovery Engine (#1028)

Merged into **Data Engine / #1024** — not a standalone module. Detects temporal gaps, attempts recovery from alternate sources, and labels unrecoverable gaps explicitly.

## Pipeline sequence

```
detect gap → failover (#1025) → backfill → validate → normalize (#1027) → outlier (#1026) → serve
```

## Detection thresholds (rule-based)

| Type | Expected interval | Gap trigger |
|------|-------------------|-------------|
| **Price** | 5 minutes | >5 min between points |
| **Volume** | 1 hour | >1 hour between points |
| **On-chain** | 1 block (~12s) | >1 block between points |

## Recovery behavior

| Outcome | Action |
|---------|--------|
| **Recovered** | Insert from alternate #1024 source + badge `Recovered from [source]` |
| **Unrecovered** | Explicit `N/A` / `Data Gap` badge — no silent null/zero |
| **Silent gap** | Pipeline failure + #1017 ops alert |

## Provenance (#945)

```
Gap: 2024-01-15 14:00–14:05 UTC | Source A: missing | Source B: recovered | Confidence: Medium
```

Fields: `gap_start`, `gap_end`, `sources_attempted`, `recovery_status` — append-only.

## API

```
GET  /api/v1/data/gap-recovery/status
GET  /api/v1/data/gap-recovery/events
GET  /api/v1/data/gap-recovery/production-gate
GET  /api/v1/data/gap-recovery/e2e
```

## Integrations

- **#1024** Multi-Source Ingest — same source pool for backfill
- **#1025** Automatic Failover — gap from source failure triggers failover
- **#1026** Outlier Detection — recovered data passes same gate
- **#945** Provenance — gap = lineage node
- **#950** Data Stabilization — provisional vs stabilized gap handling
- **#967** Historical archive — backfill for historical gaps
- **#980** Point-in-Time Metrics — backfill creates new revision, no PIT mutation

## Production gate

Blocks production if incomplete. Silent gaps = trust violation.

## Fee DB

Gap detection + backfill attempt + source query + storage — per gap.
