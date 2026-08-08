# BLACKDARK — Trust OS Value Layers (Acquisition Framing)

**Thesis:** Don't trust us. Verify us.

## Do not value as 16/21 independent platforms

BLACKDARK is **one product** with **four value layers**. Presenting sixteen separately priced “platforms” overstates independence and invites diligence rejection.

## The four layers

| # | Layer | What ships | Honest limits |
|---|--------|------------|---------------|
| 1 | **Decision Intelligence** | Single-Sentence Oracle, Conflict Guard, Discipline Mirror | Analytical tool — not advice |
| 2 | **Transparency & Evidence** | Public Accuracy Ledger, Glass Box pack, Decision Certificates, DD pack | Glass Box *media event* is operator-run |
| 3 | **Market / Execution Edge** | Arb scanner, Whale S/N, Stealth Advisor, slippage/net-edge gates | **Not** SOR / TWAP / VWAP / TCA |
| 4 | **Institutional Packaging** | Emerging Fund Terminal, Anti-Hype `/compliance`, B2B feed, vault/MFA | Posture ≠ SEC/MiCA/SOC2 certificate |

Machine-readable: `GET /api/trust-os` · module `trust_os.py`.

## Overclaim denylist (must not market as shipped)

- SOR / Smart Order Routing  
- TWAP / VWAP algo execution  
- Institutional TCA  
- IFRS 13 certification (Decimal helpers ≠ certification)  
- SOC 2 / ISO 27001 certificate  
- Full VaR/ES risk desk  
- Knowledge Graph platform  
- “16 independently valued platforms”

## Primary entry points

| Audience | URL |
|----------|-----|
| Proof-first (homepage CTA) | `/oracle-accuracy` |
| Decision | `/dashboard` |
| Emerging funds | `/b2b#fund-terminal` |
| Anti-Hype | `/compliance` |

## Load / HA proof

Harness: `scripts/load_test.py`, `scripts/load_test_1m_simulation.py`.  
Record results in `docs/LOAD_TEST_RUN_LOG.md` after a live Postgres+Redis run (operator step).

## Honest acquisition fit

**Fit:** Decision-trust layer / acqui-hire / bolt-on to a larger data or OMS stack.  
**Not a fit claim:** Sixteen institutional OS products with separate P&Ls.
