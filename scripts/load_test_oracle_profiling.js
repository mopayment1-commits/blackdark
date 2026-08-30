/**
 * Oracle API profiling load — targets /oracle/{asset}/quick under concurrent VUs.
 *
 *   k6 run --vus 50 --duration 3m scripts/load_test_oracle_profiling.js
 *   k6 run -e BASE=http://127.0.0.1:8765 --vus 50 --duration 3m scripts/load_test_oracle_profiling.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const BASE = (__ENV.BASE || 'http://127.0.0.1:8765').replace(/\/$/, '');
const ASSETS = ['BTC', 'ETH', 'SOL', 'ADA', 'AAVE', 'ARB', 'LINK', 'XRP', 'DOGE', 'AVAX'];
const LANGS = ['en', 'ar'];

const oracleDuration = new Trend('oracle_quick_duration', true);
const cacheHits = new Counter('oracle_cache_hits');
const cacheMisses = new Counter('oracle_cache_misses');

export const options = {
  vus: Number(__ENV.VUS || 50),
  duration: __ENV.DURATION || '3m',
  setupTimeout: '120s',
  thresholds: {
    http_req_failed: ['rate<0.05'],
    oracle_quick_duration: ['p(95)<2500'],
  },
};

export function setup() {
  const warm = [
    `${BASE}/health/live`,
    `${BASE}/oracle/BTC/quick?ux_mode=beginner&lang=en`,
    `${BASE}/oracle/ETH/quick?ux_mode=beginner&lang=en`,
  ];
  for (const url of warm) {
    http.get(url, { tags: { name: 'warmup' } });
  }
  sleep(0.5);
}

export default function () {
  const asset = ASSETS[Math.floor(Math.random() * ASSETS.length)];
  const lang = LANGS[Math.floor(Math.random() * LANGS.length)];
  const url = `${BASE}/oracle/${asset}/quick?ux_mode=beginner&lang=${lang}`;
  const res = http.get(url, { tags: { name: 'oracle_quick' } });
  oracleDuration.add(res.timings.duration);
  check(res, {
    'status 200': (r) => r.status === 200,
    'has score': (r) => {
      try {
        return r.json('opportunity_score') !== undefined;
      } catch (_) {
        return false;
      }
    },
  });
  try {
    const body = res.json();
    if (body.viral_cache === 'hit') {
      cacheHits.add(1);
    } else {
      cacheMisses.add(1);
    }
  } catch (_) {
    cacheMisses.add(1);
  }
  sleep(0.02);
}

export function handleSummary(data) {
  const hits = data.metrics.oracle_cache_hits?.values?.count || 0;
  const misses = data.metrics.oracle_cache_misses?.values?.count || 0;
  const total = hits + misses;
  const hitRate = total ? hits / total : 0;
  const p95 = data.metrics.oracle_quick_duration?.values?.['p(95)'] || 0;
  const out = {
    base: BASE,
    oracle_quick_p95_ms: p95,
    cache_hits: hits,
    cache_misses: misses,
    cache_hit_rate: hitRate,
    http_req_failed_rate: data.metrics.http_req_failed?.values?.rate || 0,
  };
  return {
    stdout: JSON.stringify(out, null, 2) + '\n',
    'docs/performance/k6_oracle_profiling_summary.json': JSON.stringify(out, null, 2),
  };
}
