# Trust OS Lenses UX (Binding)

**Story users memorize:** Prove → Operate → Desk → Room  
**Four doors:** Decide · Verify · My book · Alerts  
**Viral atom:** Shareable Decision Certificate (Proof Card)  
**Canon:** 1 product · 4 lenses · 6 heroes — not multi-platform SKUs

## Lenses

| Lens | Audience | Tier | Promise |
|------|----------|------|---------|
| **Prove** | Retail / Free | Proof Pass | Decide… and prove it |
| **Operate** | Daily pro | Decision Pro | Make proof a daily habit |
| **Desk** | Whales / small offices | Whale Desk | Convince someone else |
| **Room** | Funds | Institutional | Official decision room — Talk to us |

## Primary entries

1. **Decide** — Oracle + Why + Proof Card (`/dashboard#decide`)  
2. **Verify** — Public Accuracy Ledger (`/oracle-accuracy`)  
3. **My book** — Portfolio AI (Operate+)  
4. **Alerts** — Truth-gated inbox (Operate+)  

## Progressive disclosure

- Prove: Decide + Verify + certificate; soft-lock My book / Alerts  
- Operate: unlock habit tools; hide Stealth/MEV deep desk  
- Desk: full desk packaging (S/N, Stealth, Evidence, Arb)  
- Room: leave self-serve chrome → Data Room / Fund Terminal  

## APIs

- `GET /api/lenses`  
- `GET /api/lenses/{lens}`  
- `GET /api/lenses/{lens}/entries`  
- Audience entry includes `lens` + `primary_entries`  

## Design rules

- One composition per first viewport; brand-first  
- No feature dump; no sixth “platform”  
- Motion: Proof Card reveal + Why factors + share pulse  
- Honesty: no guaranteed accuracy — Ledger is the trust surface  

## Success (launch)

1. Proof Card shares  
2. Free → Operate trial  
3. Trial → $29  
4. Only then Desk $199  
