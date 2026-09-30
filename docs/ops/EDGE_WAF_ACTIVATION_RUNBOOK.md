# Edge WAF/CDN Activation Runbook (Launch-57)

**FINDING-19**

## Prerequisites

- `deploy/cloudflare/waf-rules.json` imported to zone
- DNS proxied through Cloudflare (or equivalent)

## Activation

```bash
export CDN_WAF_ACTIVE=1
export CLOUDFLARE_ZONE_ID=<zone-id>
```

## Verification

```bash
python scripts/verify_edge_waf_cdn.py
```

Exit `0` when `edge_active` is true.
