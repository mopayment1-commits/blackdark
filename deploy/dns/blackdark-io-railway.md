# blackdark.io → Railway (POST /api/auth/logout must reach the web service)

## Symptom

- `POST https://blackdark-production.up.railway.app/api/auth/logout` → **200** (fast)
- `POST https://blackdark.io/api/auth/logout` → **000** / timeout (no HTTP body)

The app logout handler is fine; **DNS does not route the marketing domain to Railway**.

## Current misconfiguration (verify)

```bash
dig +short blackdark.io CNAME
dig +short blackdark.io A
```

If you see `parkingpage.namecheap.com` or a Namecheap parking **A** record, remove it.

## Fix (Namecheap + Railway)

1. **Railway** → your `web` service → **Settings → Networking → Custom Domain**
   - Add `blackdark.io` and `www.blackdark.io`
   - Copy the **CNAME target** Railway shows (e.g. `xxxx.up.railway.app`)

2. **Namecheap** → Advanced DNS for `blackdark.io`
   - Remove **URL Redirect** / parking **A** / `parkingpage.namecheap.com` **CNAME**
   - **ALIAS/ANAME** or **CNAME** `@` → Railway CNAME target (per Railway docs)
   - **CNAME** `www` → same Railway target

3. **Railway variables** (same service as production):

```env
APP_BASE_URL=https://blackdark.io
ALLOWED_HOSTS=blackdark.io,www.blackdark.io,blackdark-production.up.railway.app
CORS_ALLOWED_ORIGINS=https://blackdark.io,https://www.blackdark.io,https://blackdark-production.up.railway.app
PUBLIC_CANONICAL_HOSTS=blackdark.io,www.blackdark.io
```

4. Redeploy web service after env change.

## Verify (must pass before “done”)

```bash
python3 scripts/verify_custom_domain_logout.py --canonical https://blackdark.io --origin https://blackdark-production.up.railway.app
```

Expect: canonical `POST /api/auth/logout` → **200** in **< 8s**.

## Cloudflare (optional)

If the zone is on Cloudflare, use `deploy/cloudflare/worker-origin-proxy.js` + `wrangler.toml` to proxy all paths (including `POST /api/*`) to `blackdark-production.up.railway.app`, or set origin to Railway custom domain with **Full (strict)** TLS.
