/**
 * k6 Performance Validation Gate (#832 / REL-001)
 *
 * Usage:
 *   k6 run --env BASE_URL=https://staging.example.com scripts/k6_performance_validation_gate.js
 *
 * NOT for localhost — production-like or production off-peak only.
 */
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE_URL || 'https://staging.example.com';

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m', target: 100 },
    { duration: '2m', target: 500 },
    { duration: '2m', target: 1000 },
    { duration: '3m', target: 5000 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    'http_req_duration{endpoint:oracle}': ['p(95)<500'],
    'http_req_duration{endpoint:market_radar}': ['p(95)<2000'],
    'http_req_duration{endpoint:intelligence}': ['p(95)<500'],
  },
};

const CRITICAL_PATHS = [
  { tag: 'oracle', path: '/api/oracle/price?symbol=BTC' },
  { tag: 'market_radar', path: '/api/market-radar/snapshot' },
  { tag: 'portfolio', path: '/api/portfolio/summary' },
  { tag: 'intelligence', path: '/api/intelligence/score' },
  { tag: 'data_engine', path: '/api/data-engine/health' },
  { tag: 'admin', path: '/api/admin/health' },
];

export default function () {
  const pick = CRITICAL_PATHS[__ITER % CRITICAL_PATHS.length];
  const res = http.get(`${BASE}${pick.path}`, { tags: { endpoint: pick.tag } });
  check(res, {
    'status 2xx': (r) => r.status >= 200 && r.status < 300,
  });
  sleep(0.1);
}

export function handleSummary(data) {
  return {
    stdout: JSON.stringify({
      module: 'performance_validation_gate_832',
      tool: 'k6',
      metrics: {
        p50: data.metrics.http_req_duration?.values?.['p(50)'],
        p95: data.metrics.http_req_duration?.values?.['p(95)'],
        p99: data.metrics.http_req_duration?.values?.['p(99)'],
        error_rate: data.metrics.http_req_failed?.values?.rate,
        rps: data.metrics.http_reqs?.values?.rate,
      },
    }, null, 2),
  };
}
