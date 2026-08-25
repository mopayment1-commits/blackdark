# OHLCV Core Feed + News Context Panel — #217 + #216

## #217 — OHLCV Core Feed (Sprint 0)

| Rule | Implementation |
|------|----------------|
| Interval exactness | `1H candle closes at :00` — boundary validation |
| Multi-source | Min 3 sources per asset (binance, okx, bybit) |
| Gap handling | `Missing data: Exchange X down \| Interpolated: No` |
| Volume validation | Cross-check exchange vs on-chain proxy |
| Batch not real-time | OHLCV = batch; real-time ticks = #212 |

### APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/ohlcv/status` | Module status |
| `GET /api/platform/ohlcv/candles` | List aggregated candles |
| `GET /api/platform/ohlcv/candles/{id}` | Candle detail |

---

## #216 — News Context Panel (Sprint 1)

| Rule | Implementation |
|------|----------------|
| Source links required | No summary without `source_url` |
| Dedupe | Same story from N sources = 1 card with "N sources" |
| Asset relevance | `Relevance: High/Medium/Low` via entity extraction |
| Timestamp | `Published: X minutes ago` |
| Not a signal | `News: SEC Filing` not `Buy Signal: SEC News` |
| Disclaimer | Non-hideable: "News aggregation does not imply endorsement or recommendation." |

### APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/news-context/status` | Panel status |
| `GET /api/platform/news-context` | Deduped news cards |
| `GET /api/platform/news-context/{card_id}` | Card detail |
| `POST /api/platform/news-context/refresh` | Import from CoinDesk RSS |

## Related

- `blackdark/data/` — Wave 01 OHLCV ingestion engine
- `bd_platform/news_classifier.py` — headline classification
- `bd_platform/block_level_ingestion.py` — #212 real-time ticks
