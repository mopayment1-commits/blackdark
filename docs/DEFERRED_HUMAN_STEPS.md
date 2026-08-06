# Deferred — requires human decision (do not block product)

> Owner: product/founder  
> Agent rule: **do not ask again until explicitly unblocked**  
> Related: [`REPORT_INVENTORY_STATUS.md`](./REPORT_INVENTORY_STATUS.md)

| ID | Item | Why deferred | Unblock condition |
|----|------|--------------|-------------------|
| H1 | Browser Extension (OQS overlay) | Built in PR #4 (`browser_extension/`) | Merge PR #4 + Load unpacked |
| H2 | Glass Box Challenge launch timing + channel | LAUNCH_ONLY narrative | Choose event clock + announce channel |
| H3 | 60-second value test (human) | Needs real user/founder walkthrough | Founder opens live URL cold and confirms Act/Wait |
| Ops | Railway trial ended · Stripe/Telegram optional | Railway cannot redeploy free | **Free path:** merge PR #5 + Render Blueprint — [`RENDER_FREE_AR.md`](./RENDER_FREE_AR.md) |

Old Railway URL may be stale: `https://blackdark-production.up.railway.app/`  
Free Render steps: [`RENDER_FREE_AR.md`](./RENDER_FREE_AR.md)

Everything else is treated as **product-complete in code**. See [`PRODUCT_COMPLETE_STATUS.md`](./PRODUCT_COMPLETE_STATUS.md).
