# SSL Labs findings — blackdark.io (Railway edge TLS)

Test context: **Railway** custom domain (`*.up.railway.app` → `railway-hikari`), **Let's Encrypt** leaf certificate (~90-day lifetime).

| SSL Labs item | Repo / app change | Platform / DNS action |
|---------------|-------------------|------------------------|
| **Certificate expires ~90 days** | None (cert is platform-managed) | Railway **auto-renews** LE certs before expiry. LE cannot issue >90-day leaves; longer *browser-visible* validity requires **Cloudflare proxy** (edge cert) or uploading a **custom** multi-month cert if Railway adds support. Monitor: `scripts/check_ssl_labs_posture.py`. |
| **PQC key exchange** | None | **Not exposed** on Railway edge today. If the zone moves to **Cloudflare**, enable **Post-Quantum** / PQC settings in SSL/TLS when available. |
| **OCSP stapling: No** | None | **Not configurable** on Railway-managed TLS. **Cloudflare proxied** orange-cloud typically staples at the edge. |
| **HSTS preload not in browsers** | `security_middleware.py` sends `max-age=31536000; includeSubDomains; preload` | Browser lists need **[hstspreload.org](https://hstspreload.org)** submission after **CAA** is published (see `deploy/dns/caa-blackdark-io.md`). |
| **DNS CAA: No** | `deploy/dns/caa-blackdark-io.md` | Add CAA at **Namecheap** (or current DNS host). |
| **SNI only** | None | Expected for modern HTTPS; **no change** (non-SNI would break current clients). |

## Optional: Cloudflare in front of Railway

If you need **OCSP stapling**, **PQC**, and a **longer-lived edge certificate** without weakening origin TLS:

1. Proxy `blackdark.io` / `www` through Cloudflare (orange cloud) to `blackdark-production.up.railway.app`.
2. SSL mode **Full (strict)**; origin cert remains Railway LE.
3. Add CAA for both `letsencrypt.org` (origin) and `digicert.com` (Cloudflare edge) if both can issue.
4. See `deploy/cloudflare/wrangler.blackdark.toml` for worker-based proxy alternative.

## Verify after DNS / platform changes

```bash
python3 scripts/check_ssl_labs_posture.py --host blackdark.io
```

Then re-run SSL Labs: [https://www.ssllabs.com/ssltest/analyze.html?d=blackdark.io](https://www.ssllabs.com/ssltest/analyze.html?d=blackdark.io)
