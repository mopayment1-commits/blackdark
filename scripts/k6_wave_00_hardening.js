/**
 * BLACKDARK Wave 0 — Security & Performance Hardening k6 suite
 *
 * Fast bar: institutional verify + health + trust surfaces p(95) < 200ms after warmup.
 *
 * Usage:
 *   k6 run -e MODE=fast -e BASE=https://blackdark-production.up.railway.app scripts/k6_wave_00_hardening.js
 *   k6 run -e BASE=http://127.0.0.1:8765 scripts/k6_wave_00_hardening.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const BASE = __ENV.BASE || 'http://127.0.0.1:8765';
const MODE = (__ENV.MODE || 'smoke').toLowerCase();

const waveDuration = new Trend('wave_00_http_duration', true);

const FAST_PATHS = [
  '/health/live',
  '/health/ready',
  '/api/compounding/_verify',
  '/api/security/wave-00',
  '/api/trust-os',
  '/api/pricing',
  '/',
];

export const options = {
  vus: 1,
  iterations: MODE === 'fast' ? 8 : 3,
  setupTimeout: '90s',
  thresholds:
    MODE === 'fast'
      ? {
          http_req_failed: ['rate<0.01'],
          checks: ['rate>0.99'],
          wave_00_http_duration: ['p(95)<200', 'avg<150'],
        }
      : {
          http_req_failed: ['rate<0.05'],
          wave_00_http_duration: ['p(95)<500'],
        },
};

export function setup() {
  for (const path of FAST_PATHS) {
    http.get(`${BASE}${path}`, { redirects: 5, tags: { phase: 'warmup' } });
  }
  sleep(0.2);
}

export default function () {
  for (const path of FAST_PATHS) {
    const res = http.get(`${BASE}${path}`, { redirects: 5, tags: { path } });
    waveDuration.add(res.timings.duration);
    check(res, {
      'status is 2xx': (r) => r.status >= 200 && r.status < 300,
      'has X-Response-Time': (r) => !!(r.headers['X-Response-Time'] || r.headers['x-response-time']),
      'has X-Wave-00': (r) => !!(r.headers['X-Wave-00'] || r.headers['x-wave-00']),
    });
    if (path === '/api/compounding/_verify') {
      check(res, {
        'verify ok true': (r) => {
          try {
            return JSON.parse(r.body).ok === true;
          } catch (e) {
            return false;
          }
        },
      });
    }
  }
  sleep(0.1);
}
