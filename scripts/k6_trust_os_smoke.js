/**
 * BLACKDARK Trust OS — k6 smoke / light load
 *
 * Fast bar (product): HTML + health p95 well under 200ms on localhost
 * AFTER a warm-up pass (cold first-hit after process start is excluded).
 *
 * Smoke:
 *   k6 run scripts/k6_trust_os_smoke.js
 *
 * Fast-only (strict <200ms thresholds):
 *   k6 run -e MODE=fast scripts/k6_trust_os_smoke.js
 *
 * Light concurrent (local Soft Launch):
 *   k6 run -e BASE=http://127.0.0.1:8080 -e VUS=10 -e DURATION=30s scripts/k6_trust_os_smoke.js
 *
 * Honest HA claim still requires Postgres+Redis+multi-worker staging
 * and a filled row in docs/LOAD_TEST_RUN_LOG.md — not this smoke alone.
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const BASE = __ENV.BASE || 'http://127.0.0.1:8080';
const VUS = Number(__ENV.VUS || 1);
const DURATION = __ENV.DURATION || '';
const MODE = (__ENV.MODE || 'smoke').toLowerCase();

const fastDuration = new Trend('fast_http_duration', true);

const FAST_PATHS = [
  '/health/live',
  '/',
  '/?lang=ar',
  '/login',
  '/api/pricing',
  '/api/billing/payments',
  '/static/img/blackdark-sealed-hero-1280.webp',
];

const HEAVY_PATHS = [
  '/#pricing',
  '/oracle-accuracy',
  '/api/trust-os',
  '/oracle/BTC/quick?ux_mode=beginner&lang=en',
];

const PATHS = MODE === 'fast' ? FAST_PATHS : FAST_PATHS.concat(HEAVY_PATHS);

const fastThresholds = {
  http_req_failed: ['rate<0.01'],
  checks: ['rate>0.99'],
  // Measured only after setup() warm-up — cold process start is not the product bar.
  fast_http_duration: ['p(95)<200', 'avg<150', 'med<100'],
};

export const options = DURATION
  ? {
      vus: VUS,
      duration: DURATION,
      setupTimeout: '60s',
      thresholds: {
        http_req_failed: ['rate<0.05'],
        http_req_duration: ['p(95)<3000'],
        fast_http_duration: ['p(95)<200'],
      },
    }
  : {
      vus: 1,
      iterations: MODE === 'fast' ? 5 : 1,
      setupTimeout: '60s',
      thresholds: fastThresholds,
    };

/** Warm Jinja/static/API once so Windows cold-start (often 400–600ms) is not scored. */
export function setup() {
  http.get(`${BASE}/health/live`);
  for (const path of FAST_PATHS) {
    http.get(`${BASE}${path}`, { redirects: 5 });
  }
  sleep(0.15);
  return { warmed: true };
}

export default function () {
  for (const path of PATHS) {
    const url = path.startsWith('http') ? path : `${BASE}${path}`;
    const res = http.get(url, { redirects: 5, tags: { name: path } });
    const isFast = FAST_PATHS.includes(path);
    if (isFast) {
      fastDuration.add(res.timings.duration);
    }
    check(res, {
      'status is 2xx or 3xx': (r) => r.status >= 200 && r.status < 400,
      // Per-request soft bar; p95 threshold is the binding gate.
      'fast path under 200ms': (r) => !isFast || r.timings.duration < 200,
    });
    sleep(MODE === 'fast' ? 0.05 : 0.2);
  }
}
