# Miner Intelligence Layer — #566 #567 #568

## Epic Decision

Three miner intelligence tickets merged into **Miner Intelligence Layer** (Sprint 1 On-Chain Layer).

| Task | Sub-Module | Role |
|------|------------|------|
| #566 | Miner Flow Intelligence | Dashboard + flow tracking |
| #567 | Miner Flow Monitor | Aggregation, anomaly, market context |
| #568 | Miners' Position Index (MPI) | Outflow vs historical baseline percentile |

Depends on: **#541 Entity Resolution Engine** (miner entity clusters)

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Miner labels confidence | Confidence/source on every miner label |
| Pool reclassification handling | Reclassification events tracked with continuity |
| No direct sell claim without evidence | "Miner-to-Exchange Flow Observed" — not selling pressure |
| Miner labels provenance | Source documented on monitor panel |
| Internal transfer filtering | Same-miner internal transfers excluded |
| Historical validation | Baseline deviation vs historical mean |
| Baseline/window documented | MPI 365d window, IQR outlier trim |
| Robust to outliers | IQR trimming before percentile rank |
| Historical replay | Point-in-time MPI replay on historical data |
| No anomaly = sell | MPI descriptive only — not a sell signal |

## Naming Rules

- **Banned:** "selling pressure", "sell signal", "confirmed sell", "anomaly = sell"
- **Renamed:** "Miner-to-Exchange Flow Observed" (replaces selling pressure)
- **MPI display:** "Current outflow vs historical baseline: Xth percentile"

## API

```
GET /api/platform/intelligence-ledger/onchain-layer/miner-intelligence/status
GET /api/platform/intelligence-ledger/onchain-layer/miner-intelligence?miner_id=miner_foundry_usa
GET /api/platform/intelligence-ledger/onchain-layer/miner-intelligence/mpi?miner_id=miner_foundry_usa
GET /api/platform/intelligence-ledger/onchain-layer/miner-intelligence/reconciliation-tests
```

## Layer Architecture

```
Foundation Layer (Sprint 0)
└── #541 Entity Resolution Engine

On-Chain Layer (Sprint 1)
└── Miner Intelligence Layer (Epic #566)
    ├── #566 Miner Flow Intelligence (dashboard)
    ├── #567 Miner Flow Monitor (monitor + baseline)
    └── #568 Miners' Position Index (MPI metric)
```
