/**
 * Cloudflare Worker — proxy blackdark.io / www to Railway origin (all HTTP methods).
 * Use when the zone is on Cloudflare but apex DNS is not yet CNAME'd to Railway.
 */
const DEFAULT_ORIGIN = "blackdark-production.up.railway.app";

export default {
  async fetch(request, env) {
    const originHost = (env && env.ORIGIN) || DEFAULT_ORIGIN;
    const incoming = new URL(request.url);
    const target = new URL(incoming.pathname + incoming.search, `https://${originHost}`);
    const headers = new Headers(request.headers);
    headers.set("Host", originHost);
    headers.set("X-Forwarded-Host", incoming.host);
    headers.set("X-Forwarded-Proto", "https");
    const method = request.method.toUpperCase();
    const init = {
      method,
      headers,
      redirect: "manual",
    };
    if (method !== "GET" && method !== "HEAD") {
      init.body = request.body;
    }
    return fetch(target.toString(), init);
  },
};
