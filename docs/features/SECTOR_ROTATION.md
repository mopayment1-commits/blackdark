# Sector Rotation & Flow Module — #286 (Sprint 2 Intelligence Ledger)

Detects strength rotation between sectors. Rotation matrix + leaderboard (backend).

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Sector taxonomy | Messari/TheBlock base, versioned, custom flagged |
| Survivorship | Delisted = -100%, no look-ahead bias |
| Breadth | % above 50D MA, % positive returns — formula documented |
| Universe | Versioned at time t |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/sector-rotation/status` | Module status |
| `GET /api/platform/intelligence-ledger/sector-rotation` | Matrix + leaderboard |
