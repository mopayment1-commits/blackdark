/**
 * Tier-aware live refresh — poll intervals and optional Trust Pulse SSE from
 * GET /api/entitlements/refresh-policy (server entitlements SSOT).
 */
(function (global) {
    const DEFAULT_POLL_MS = 45000;
    let policy = null;
    let policyPromise = null;
    const timers = new Map();
    const streams = new Map();

    function normalizePolicy(raw) {
        const pollSec = Number(raw && raw.poll_interval_sec) || 45;
        const pollMs = Number(raw && raw.poll_interval_ms) || pollSec * 1000;
        return {
            poll_interval_sec: pollSec,
            poll_interval_ms: pollMs,
            live_stream_enabled: !!(raw && raw.live_stream_enabled),
            trust_pulse_stream: (raw && raw.trust_pulse_stream) || null,
            ledger_poll_enabled: raw ? raw.ledger_poll_enabled !== false : true,
            effective_plan: (raw && raw.effective_plan) || 'free',
            server_enforced: !!(raw && raw.server_enforced),
            entitlement_allowed: raw ? raw.entitlement_allowed !== false : true,
        };
    }

    async function ensurePolicy() {
        if (policy) return policy;
        if (policyPromise) return policyPromise;
        policyPromise = fetch('/api/entitlements/refresh-policy', { credentials: 'same-origin' })
            .then((res) => (res.ok ? res.json() : {}))
            .catch(() => ({}))
            .then((raw) => {
                policy = normalizePolicy(raw);
                policyPromise = null;
                return policy;
            });
        return policyPromise;
    }

    function pollMs() {
        return (policy && policy.poll_interval_ms) || DEFAULT_POLL_MS;
    }

    function clearTimer(key) {
        const id = timers.get(key);
        if (id != null) {
            clearInterval(id);
            timers.delete(key);
        }
    }

    function startInterval(key, fn, ms) {
        clearTimer(key);
        const interval = Math.max(5000, Number(ms) || pollMs());
        const id = setInterval(() => {
            try {
                fn();
            } catch (err) {
                console.debug(err);
            }
        }, interval);
        timers.set(key, id);
        return id;
    }

    function stopStream(key) {
        const es = streams.get(key);
        if (!es) return;
        try {
            es.close();
        } catch (err) {
            console.debug(err);
        }
        streams.delete(key);
    }

    function startTrustPulseStream(symbol, onMessage, opts) {
        const key = (opts && opts.key) || 'trust-pulse';
        stopStream(key);
        const p = policy || normalizePolicy(null);
        if (!p.live_stream_enabled) return null;
        const base = p.trust_pulse_stream || '/api/trust-pulse/stream';
        const sym = String(symbol || 'BTC').trim().toUpperCase() || 'BTC';
        const extra = (opts && opts.query) || '';
        try {
            const es = new EventSource(
                base + '?symbol=' + encodeURIComponent(sym) + (extra ? '&' + extra : '')
            );
            es.onmessage = (ev) => {
                try {
                    const d = JSON.parse(ev.data);
                    if (typeof onMessage === 'function') onMessage(d);
                } catch (err) {
                    console.debug(err);
                }
            };
            streams.set(key, es);
            return es;
        } catch (err) {
            console.debug(err);
            return null;
        }
    }

    function stopAll() {
        for (const k of [...timers.keys()]) clearTimer(k);
        for (const k of [...streams.keys()]) stopStream(k);
    }

    global.BDLiveRefresh = {
        ensurePolicy,
        getPolicy: () => policy,
        pollMs,
        startInterval,
        clearTimer,
        startTrustPulseStream,
        stopStream,
        stopAll,
    };
})(typeof window !== 'undefined' ? window : globalThis);
