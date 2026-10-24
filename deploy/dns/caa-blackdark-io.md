# DNS CAA for blackdark.io (SSL Labs / Observatory)

Railway terminates TLS with **Let's Encrypt** on the edge (`railway-hikari`). Add **CAA** records at the DNS host (Namecheap **Advanced DNS** for `blackdark.io`) so certificate issuance is explicitly allowed and scanners stop reporting “DNS CAA: No”.

## Records to add (Let's Encrypt / Railway)

| Type | Host | Flag | Tag | Value |
|------|------|------|-----|--------|
| CAA | `@` | 0 | issue | `letsencrypt.org` |
| CAA | `@` | 0 | issuewild | `letsencrypt.org` |
| CAA | `@` | 0 | iodef | `mailto:security@blackdark.io` |

Namecheap UI: **Advanced DNS → Add New Record → CAA Record**.

Optional (only if you later proxy through **Cloudflare** and use their edge certs instead of or in addition to origin LE):

| Type | Host | Flag | Tag | Value |
|------|------|------|-----|--------|
| CAA | `@` | 0 | issue | `digicert.com` |

Do **not** remove the Railway CNAME/ALIAS to `*.up.railway.app` when adding CAA.

## Verify

```bash
dig blackdark.io CAA +short
# or
dig @1.1.1.1 blackdark.io type257 +short
```

Expect `0 issue "letsencrypt.org"` (and `issuewild` if configured).

## HSTS preload list (browsers)

The app sends `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`.  
**Inclusion in Chrome/Firefox preload lists** requires a separate submission at [https://hstspreload.org](https://hstspreload.org) after CAA is live and HTTPS is stable. That submission is an operator action outside this repository.
