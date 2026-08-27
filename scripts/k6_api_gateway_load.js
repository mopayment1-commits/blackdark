/**
 * k6 load test — API Gateway #876
 * Target: 1000 req/sec, P99 < 500ms
 * Run: k6 run scripts/k6_api_gateway_load.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    gateway_load: {
      executor: 'constant-arrival-rate',
      rate: 1000,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 50,
      maxVUs: 200,
    },
  },
  thresholds: {
    http_req_duration: ['p(99)<500'],
    http_req_failed: ['rate<0.05'],
  },
};

const BASE = __ENV.API_BASE || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || 'bd_free_demo_key_0001';

export default function () {
  const res = http.get(`${BASE}/api/v1/market/overview`, {
    headers: { 'X-API-Key': API_KEY },
  });
  check(res, {
    'status is 200': (r) => r.status === 200,
    'has ok field': (r) => {
      try {
        return JSON.parse(r.body).ok !== false;
      } catch {
        return false;
      }
    },
  });
  sleep(0.01);
}
