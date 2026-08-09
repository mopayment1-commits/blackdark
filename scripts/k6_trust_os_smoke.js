/**
 * BLACKDARK Trust OS — k6 smoke / light load
 *
 * Smoke (what you already proved):
 *   k6 run scripts/k6_trust_os_smoke.js
 *
 * Light concurrent (local Soft Launch):
 *   k6 run -e BASE=http://127.0.0.1:8080 -e VUS=10 -e DURATION=30s scripts/k6_trust_os_smoke.js
 *
 * Honest HA claim still requires Postgres+Redis+multi-worker staging
 * and a filled row in docs/LOAD_TEST_RUN_LOG.md — not this smoke alone.
 */
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE || 'http://127.0.0.1:8080';
const VUS = Number(__ENV.VUS || 1);
const DURATION = __ENV.DURATION || '';

export const options = DURATION
  ? {
      vus: VUS,
      duration: DURATION,
      thresholds: {
        http_req_failed: ['rate<0.05'],
        http_req_duration: ['p(95)<3000'],
      },
    }
  : {
      vus: 1,
      iterations: 1,
      thresholds: {
        http_req_failed: ['rate<0.01'],
        checks: ['rate>0.99'],
      },
    };

const PATHS = [
  '/',
  '/?lang=ar',
  '/login',
  '/#pricing',
  '/oracle-accuracy',
  '/api/pricing',
  '/api/billing/payments',
  '/api/trust-os',
  '/health/live',
  '/oracle/BTC/quick?ux_mode=beginner&lang=en',
];

export default function () {
  for (const path of PATHS) {
    const url = path.startsWith('http') ? path : `${BASE}${path}`;
    const res = http.get(url, { redirects: 5, tags: { name: path } });
    check(res, {
      'status is 2xx or 3xx': (r) => r.status >= 200 && r.status < 400,
    });
    sleep(0.2);
  }
}
