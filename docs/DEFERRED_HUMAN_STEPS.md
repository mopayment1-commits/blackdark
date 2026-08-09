# Runtime operator steps (not product deferrals)

> Product code for Sat/Sun + wow surfaces is **complete**.  
> Rows below are **account/secret/runtime** actions on your machine — not missing features.

| ID | Action | Why runtime |
|----|--------|-------------|
| Ops-Pay | Set Lemon/Stripe + webhook secrets; one test purchase | Your PSP account |
| Ops-WA | Set `WHATSAPP_CLOUD_TOKEN` + `WHATSAPP_CLOUD_PHONE_NUMBER_ID` for server push (click-to-send already works) | Meta Cloud credentials |
| Ops-DB | Postgres + Redis + `WEB_CONCURRENCY≥2` for viral claim | Your hosting |
| Ops-HA | Sign a real row in [`LOAD_TEST_RUN_LOG.md`](./LOAD_TEST_RUN_LOG.md) after staging load | Needs live staging |
| Ops-OAuth | Google/GitHub OAuth client secrets | Developer console |
| Ops-Ext | Chrome → Load unpacked `browser_extension/` | Local browser install (package shipped) |
| Ops-Glass | When `/api/glass-box/announce-schedule` is due, post drafts | Your social accounts |
| Ops-60s | Founder cold open of live URL (machine probe: `GET /api/acceptance/60s`) | Human perception check |
| Ops-Legal | Counsel / pentest / CDN-WAF as you choose | External vendors |

## Product surfaces now shipped (do not re-open as deferred)

- Kill-Rate Board · Contradiction Replay · Committee One-Pager · Half-Life Heat Clock · Proof Arena  
- WhatsApp channel path (click-to-send + Cloud API adapter)  
- Browser extension package in-repo  
- Glass Box announce schedule API  
- See [`WOW_UNIQUE_FULL_SHIP_AR.md`](./WOW_UNIQUE_FULL_SHIP_AR.md)

```bash
curl -s "$BASE/api/wow/surfaces" | jq .
curl -s "$BASE/api/glass-box/announce-drafts" | jq .
curl -s "$BASE/api/acceptance/60s?base_url=$BASE" | jq .
```
