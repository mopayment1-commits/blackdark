# Financial & Decision Integrity Audit

**SHA:** `99e4db09eff8ec642d047aa72c231b6c6cf36bc6`  
**Pipeline:** Raw source → ingestion → canonical → signal/rules → risk → decision → displayed output → audit record  
**Verdict:** **PASS** (11/11)

| Case | Intent | Verdict |
|---|---|---|
| correct | fresh executable net-edge may pass | PASS |
| stale | stale quote must reject | PASS |
| missing | missing net/fees/slippage must reject | PASS |
| contradictory | severe dimension conflict must veto and abstain | PASS |
| duplicated | duplicate evaluation must be deterministic (same reject/score) | PASS |
| delayed | delayed quote must not be treated as live-executable | PASS |
| outlier | poison/outlier price must freeze trading | PASS |
| exchange_disconnected | missing venue quote must not be fresh for execution | PASS |
| wrong_timestamp | absurd quote age must reject | PASS |
| source_disagreement | mild disagreement must abstain (not convert uncertainty to BUY) | PASS |
| partial_market_coverage | uncovered books must stay synthetic_mid, never venue_l2 | PASS |

Rule: correct data may pass; stale / missing / contradictory / duplicated / delayed / outlier / disconnected / wrong timestamp / source disagreement / partial coverage must reject or abstain — never convert uncertainty into a live BUY.

Independent venue FILL vs P&amp;L reference: **FAIL** (live_fill=false, geo 451) — evaluated, not untested.
