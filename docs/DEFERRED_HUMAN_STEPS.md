# Deferred — requires human decision (do not block product)

> Owner: product/founder  
> Agent rule: **do not ask again until explicitly unblocked**  
> Related: [`REPORT_INVENTORY_STATUS.md`](./REPORT_INVENTORY_STATUS.md)

| ID | Item | Why deferred | Unblock condition |
|----|------|--------------|-------------------|
| H1 | Browser Extension (OQS overlay) | **UNBLOCKED — building** (`browser_extension/`) | User said «ابنيه» 2026-08-06 |
| H2 | Glass Box Challenge launch timing + channel | LAUNCH_ONLY narrative | Choose event clock + announce channel |
| H3 | 60-second value test (human) | Needs real user/founder walkthrough | Founder opens live site cold and confirms |
| Ops | Railway deploy · live Stripe · Telegram/SMTP secrets · DNS | External accounts / credentials | Paste secrets + deploy |

Live try URL: `https://blackdark-production.up.railway.app/`  
Extension install: see [`browser_extension/README.md`](../browser_extension/README.md).

Everything else is treated as **product-complete in code**. See [`PRODUCT_COMPLETE_STATUS.md`](./PRODUCT_COMPLETE_STATUS.md).
