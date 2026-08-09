# Third-pass audit — Visible critical surfaces (Sat 8/8 + Sun 9/8)

**Trigger:** Founder asked where the 15-language control, login/registration, and payment system are — treating invisibility as catastrophic omission.

**Root cause (confirmed):**
1. Those surfaces were implemented on **PR #33**, not on `origin/main`. Pulling `main` alone cannot show the language control or the corrected Desk price.
2. Even on PR #33, landing CSS hid `.nav-links` on mobile — and Language + Login lived *inside* `.nav-links`, so mobile users saw **neither**.
3. Sign up was a tab on `/login` but not a primary top-right CTA.
4. Payment rails existed in APIs/profile, but readiness was not explained on the pricing section.

## Strict confirmation — critical surfaces

| Surface | Agreed | Was invisible / broken why | Status after this pass (PR #33) |
|---------|--------|----------------------------|----------------------------------|
| 15-language selector top-right | Yes (msg ~7034) | Missing on `main`; on #33 buried in collapsible nav | **VISIBLE** via `partials/top_utility.html` on landing, dashboard, login, profile, accuracy — outside collapsible links |
| Login | Yes | Link existed but hidden on mobile with nav-links | **VISIBLE** in always-on utility chrome |
| Sign up / registration | Yes | Tab only; weak entry | **VISIBLE** `Sign up` → `/login?tab=register` + Start free CTA |
| USD payments / checkout | Yes (msg ~8131) | Architecture yes; UX weak | Pricing CTAs + Profile Plan & billing + readiness line from `/api/billing/payments` |
| Pricing ladder $0/$29/$49/$3k→open | Yes | `main` still $199 Whale Desk | Correct on PR #33; must **merge #33** |
| Legal 4-layer + terms ack | Yes | Partial | Done prior commit on #33 |
| Trust Pulse / sealed landing | Yes | Was unmerged until #32 | On `main` via #32 |
| HUMAN_OPS (PSP keys, Glass Box clock, HA signed load, ext merge) | Deferred | Not code omission | Still human — see `DEFERRED_HUMAN_STEPS.md` |

## Exact places the user should see (after merge #33 + pull)

1. **Home `/` top-right:** Language (15) · Pricing · Login · Sign up  
2. **`/login`:** Login + Sign up tabs · Google when configured · Forgot password · top chrome Language  
3. **`/#pricing`:** Proof Pass $0 · Decision Pro $29 · Decision Desk $49 · Institutional From $3,000 → open · payment readiness line  
4. **`/profile`:** Plan & billing USD · checkout buttons · Manage billing · Language chrome  

## Honesty rule (binding)

Do **not** claim “100% of the conversation is done on the user’s localhost” until:
1. PR #33 is **merged** into `main`, and  
2. Windows tree runs `git pull origin main` and restarts `:8080`.

Code-complete on the PR ≠ visible on an unmerged `main` checkout. That distinction is the failure mode that threatened the project.

## Windows after merge

```bat
cd C:\Users\o\Desktop\BLACKDARK
git checkout main
git pull origin main
```

Restart the server, hard-refresh (Ctrl+F5). Confirm top-right Language + Login + Sign up, then `/#pricing`.
