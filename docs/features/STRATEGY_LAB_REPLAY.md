# Feature #92 — Strategy Lab Replay Mode

AI-powered historical replay — **not** basic TradingView bar replay.

## Differentiator

At each bar close, users see:
1. What AI would have signaled (point-in-time, no future data)
2. What actually happened over the next N bars
3. Whether the prediction was correct

## No future data leakage

- `PurgedBarSeries.view_as_of(index)` returns only `bars[0:index+1]`
- Signals computed from past closes only (`point_in_time_decision_signal`)
- Outcomes revealed separately after the signal bar (for comparison only)

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/strategy-lab/replay?asset=BTC` | Run replay batch |
| `GET /api/platform/strategy-lab/replay/status` | Module health |

## Example flow

```
Bar 100 close → AI: BUY (78% confidence) → 24 bars later: +3.2% ✓
Bar 101 close → AI: HOLD (52%) → skipped
```
