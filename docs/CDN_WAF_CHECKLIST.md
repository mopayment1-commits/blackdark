# CDN / WAF Operator Checklist

Edge protection is **outside** the app process. Templates live in `deploy/cloudflare/` and `nginx/blackdark.conf`.

## Cloudflare (recommended)

1. Point DNS to Cloudflare (orange cloud)
2. SSL/TLS → **Full (strict)** + Always Use HTTPS + HSTS
3. Enable Managed WAF + Bot Fight Mode
4. Rate-limit `/api/auth/*`, `/oracle/*` (see `deploy/cloudflare/waf-rules.json`)
5. Hide origin IP; firewall origin to Cloudflare ranges only
6. Cache `/static/*`; bypass cache for `/api/*` and `/oracle/*`

## Nginx origin (optional)

```bash
docker compose -f docker-compose.yml -f docker-compose.ha.yml --profile edge up -d
```

## Verify

```bash
curl -sI https://YOUR_DOMAIN/ | rg -i 'cf-ray|strict-transport|x-frame'
curl -s https://YOUR_DOMAIN/api/security/status | jq '.honesty'
```

Mark done in `docs/SECURITY_MAX_CHECKLIST.md` when live.
