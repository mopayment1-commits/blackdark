# UI Visibility Roadmap — Institutional Execution Plan

**Date:** 2026-08-27 | **Principle:** We build financial decisions, not APIs.

## Strategic Verdict

| Layer | Completion | Status |
|-------|------------|--------|
| L2–L4 Backend | ~85% | Engineering-ready |
| L5 UI Visibility | ~5% → **P0 in progress** | Product-blocking |

**Yield Delta (#yield_delta_listener):** **Deferred to Sprint-3.** No `bd_platform` module exists — only CAP646/RVM docs. Cancelling Sprint-2 scope avoids phantom capability debt.

---

## Three Sovereignty Levels (Production-Ready Gate)

Every capability must pass all three before "Production-Ready":

### 1. Route Sovereignty
- Dedicated path `/capability` OR first-class dashboard section (≤2 clicks from `/`)
- **Not acceptable:** 3+ clicks through IL search

### 2. Component Sovereignty
- Custom renderer answering: **What? Why? Risks?**
- **Not acceptable:** generic JSON dump, raw table

### 3. Decision Surface
- Sticky Decision Card or hero CTA: **"What should I do now?"**
- Wired to `ux_mode.build_beginner_decision_card()` on every surface

---

## Phase Plan

### Sprint-2 P0 (This PR) — Route + Component Foundation
| Item | Status |
|------|--------|
| `/exchanges` Grade Cards | ✅ |
| `/stablecoins` De-Peg + Grade | ✅ |
| `/arbitrage` Net-Edge Truth | ✅ |
| `/brief` 3-Point Narrative | ✅ |
| `/whales` Accumulation Chart | ✅ |
| Intelligence Hub typed renderers | ✅ (12 module patterns) |
| Provenance ⓘ badge (foundation) | ✅ |
| Yield Delta | ❌ → Sprint-3 |

### Sprint-2 P1 — Decision + Alerts
| Item | Target |
|------|--------|
| `/wallet/{addr}` Profiler UI | DeBank + ScopeScan + clusters graph |
| Decision Card sticky on all pages | `capability_core.js` + dashboard |
| Unified Alert Center | `/api/alerts/unified-feed` aggregating 6 sources |
| Remaining 12 capability routes | `/correlation`, `/stress-test`, `/thesis/{asset}`, etc. |

### Sprint-2 P2 — Trust + Signal Quality
| Item | Target |
|------|--------|
| Provenance badge on every metric | Extend `BDCapability.provBadge` |
| Strategy Vetting Grade A–F | New `strategy_vetting.py` — backtest + OOS + overfit |
| NAV page | Portfolio valuation surface |

---

## Architecture Pattern (Institutional Standard)

```
Route (dashboard.py)
  → Jinja template (capability_page.html)
    → capability_pages.js (decision question + custom render)
      → Existing IL API (/api/platform/intelligence-ledger/...)
        → bd_platform module (source of truth)
```

**Intelligence Hub** uses `intelligence_hub_renderers.js` — module_id → renderer map. Raw JSON tab remains for engineering audit only.

---

## Quality Gates (CI)

1. `tests/test_capability_routes_batch.py` — all 5 routes return 200 + capability_id
2. Hub renderer smoke — mapped modules never fall back to JSON in formatted view
3. Every capability page includes Decision Card mount point
4. No new capability without Route + Renderer registration

---

## Recommendation Summary

1. **Stop adding IL modules without UI renderers** — backend-first created the "blind giant."
2. **Enforce Capability Registry** — `CAPABILITY_UI_REGISTRY.json` mapping route → API → renderer → decision question.
3. **Yield Delta:** reschedule Sprint-3 with full spec before any code.
4. **P1 Alert Center** is highest ROI after P0 routes — users need one feed, not 6 silos.
5. **Strategy Vetting Grade** should reuse #417 truth + #472 thesis + backtest fixtures — not a new opaque score.
