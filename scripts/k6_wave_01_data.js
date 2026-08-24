/**
 * BLACKDARK Wave 01 — Data Engine institutional k6 suite
 *
 * Modes:
 *   smoke (default) — warmup + low concurrency, institutional proof bar
 *   load            — 50 VU soak (REL-001 exploratory; not a PASS gate alone)
 *
 * Usage:
 *   k6 run -e MODE=smoke -e BASE=https://blackdark-production.up.railway.app scripts/k6_wave_01_data.js
 *   k6 run -e MODE=load  -e BASE=https://blackdark-production.up.railway.app scripts/k6_wave_01_data.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const BASE = __ENV.BASE || 'https://blackdark-production.up.railway.app';
const MODE = (__ENV.MODE || 'smoke').toLowerCase();

const wave01Duration = new Trend('wave_01_http_duration', true);

const PATHS = [
  '/api/v1/data/wave-01',
  '/api/v1/data/status',
  '/api/v1/data/ohlcv?symbol=BTCUSDT&interval=1h&limit=10',
  '/api/v1/data/funding?symbol=BTCUSDT&limit=5',
  '/api/v1/data/open-interest?symbol=BTCUSDT&limit=5',
  '/api/v1/data/events?limit=5',
];

export const options =
  MODE === 'load'
    ? {
        stages: [
          { duration: '30s', target: 20 },
          { duration: '1m', target: 20 },
          { duration: '30s', target: 0 },
        ],
        setupTimeout: '120s',
        thresholds: {
          http_req_failed: ['rate<0.05'],
          http_req_duration: ['p(95)<2000'],
          checks: ['rate>0.90'],
        },
      }
    : {
        vus: 3,
        duration: '45s',
        setupTimeout: '120s',
        thresholds: {
          http_req_failed: ['rate<0.01'],
          http_req_duration: ['p(95)<1500'],
          checks: ['rate>0.99'],
        },
      };

export function setup() {
  for (const path of PATHS) {
    http.get(`${BASE}${path}`, { tags: { phase: 'warmup' } });
  }
  sleep(1);
}

export default function () {
  for (const path of PATHS) {
    const res = http.get(`${BASE}${path}`, { tags: { path } });
    wave01Duration.add(res.timings.duration);

    if (path.includes('ohlcv')) {
      check(res, {
        'ohlcv status 200': (r) => r.status === 200,
        'ohlcv has data_state LIVE': (r) => {
          try {
            const b = JSON.parse(r.body);
            return b.data_state === 'LIVE' && Array.isArray(b.data) && b.count > 0;
          } catch (e) {
            return false;
          }
        },
        'ohlcv has provenance_id': (r) => {
          try {
            const b = JSON.parse(r.body);
            return b.data && b.data.length > 0 && !!b.data[0].provenance_id;
          } catch (e) {
            return false;
          }
        },
        'ohlcv X-Wave-01 header': (r) => !!(r.headers['X-Wave-01'] || r.headers['x-wave-01']),
      });
    } else if (path.includes('funding') || path.includes('open-interest')) {
      check(res, {
        'empty dataset status 200': (r) => r.status === 200,
        'explicit MISSING state (D-01)': (r) => {
          try {
            const b = JSON.parse(r.body);
            return b.data_state === 'MISSING' && b.count === 0;
          } catch (e) {
            return false;
          }
        },
      });
    } else if (path.includes('wave-01')) {
      check(res, {
        'wave-01 status 200': (r) => r.status === 200,
        'institutional verdict NOT READY': (r) => {
          try {
            const b = JSON.parse(r.body);
            return b.institutional_verdict === 'NOT READY';
          } catch (e) {
            return false;
          }
        },
      });
    } else {
      check(res, {
        'status is 200': (r) => r.status === 200,
      });
    }
    sleep(0.3);
  }
  sleep(0.5);
}
