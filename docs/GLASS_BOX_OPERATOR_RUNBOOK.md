# Glass Box Operator Runbook

> Launch packaging for Locked Predictions + Public Accuracy Ledger + Decision Certificates.  
> **Not a seventh product.** Timing, channel, and press remain human.

## Machine-ready (already shipped)

| Surface | Path |
|---------|------|
| Public Accuracy Ledger | `/oracle-accuracy` |
| Locked Predictions | `/oracle-accuracy#locked` |
| Glass Box Challenge | `/oracle-accuracy#glass-box-challenge` |
| Challenge API | `/api/glass-box/challenge` |
| Operator pack API | `/api/glass-box/operator` |
| Ledger share kit | `/api/ledger/share-kit` |
| Decision Certificate | `/api/oracle/decision-certificate` |

## Human-only (do not automate)

- Exact event datetime + timezone  
- Announcement channel (X / Telegram / press)  
- Press / counsel outreach if needed  

## T-minus checklist

1. **T-48h** — Pick one macro/crypto event window; draft Hook + challenge post.  
2. **T-24h** — Seal ≥3 Decision Certificates on `/oracle-accuracy#locked`; confirm share kit.  
3. **T-1h** — Publish challenge text + ledger link; pin Glass Box section.  
4. **T+0** — Do not edit sealed rows.  
5. **T+resolve** — Unlock wins **and** losses live; invite competitors to publish full ledgers.

## Acceptance

- New visitor can verify the ledger without login.  
- Challenge text is copyable/shareable.  
- Operator gates visible under Glass Box on the accuracy page.  
- No SOR / TWAP / TCA / IFRS / SOC2 overclaims in the post.

## API

```bash
curl -s "$BASE/api/glass-box/operator" | jq .
curl -s "$BASE/api/glass-box/announce-drafts" | jq .
curl -s "$BASE/api/ledger/share-kit" | jq .
```

## Announce drafts

Product copy is ready via `GET /api/glass-box/announce-drafts`.  
**Human only:** pick `exact_datetime` + `timezone` + channel, then post. Do not auto-schedule from code.
