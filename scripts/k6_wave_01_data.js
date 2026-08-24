import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '1m', target: 50 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1000'],
  },
};

const BASE = __ENV.BASE || 'https://blackdark-production.up.railway.app';

export default function () {
  const res = http.get(`${BASE}/api/v1/data/ohlcv?symbol=BTCUSDT&interval=1h&limit=10`);
  check(res, {
    'status is 200': (r) => r.status === 200,
    'has data array': (r) => {
      try {
        const b = JSON.parse(r.body);
        return Array.isArray(b.data);
      } catch (e) {
        return false;
      }
    },
    'response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  sleep(1);
}
