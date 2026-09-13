# المراقبة والتنبيهات + حدود مصادر البيانات المجانية

## المراقبة بعد النشر

### ما يعمل تلقائيًا

| المكون | الوظيفة |
|--------|---------|
| `ops/monitoring_alerting.py` | حلقة مراقبة كل 60 ثانية |
| `/health/live` + `/health/ready` | فحص uptime + latency |
| `runtime_verification.alert_status()` | تنبيه عند تجاوز معدل الأخطاء |
| `uptime_monitor.uptime_stats()` | تنبيه عند خرق SLA |
| `ops/vendor_rate_limit_watchdog.py` | تنبيه عند throttling من CoinGecko/Binance |
| Telegram `OPS_TELEGRAM_CHAT_ID` | تنبيه فوري للمشغّل |
| `MONITORING_WEBHOOK_URL` | PagerDuty / Slack / webhook عام |

### إعداد الإنتاج

```bash
# 1. نسخ المتغيرات من .env.production.example
MONITORING_ENABLED=true
MONITORING_BASE_URL=https://your-deploy-url
OPS_TELEGRAM_CHAT_ID=your_ops_chat_id
TELEGRAM_BOT_TOKEN=your_bot_token

# 2. التحقق
python3 scripts/setup_monitoring.py
curl https://your-deploy-url/api/monitoring/status
curl -X POST https://your-deploy-url/api/monitoring/probe

# 3. مراقبة خارجية (مطلوبة للإنتاج)
# UptimeRobot → GET /health/live كل 60 ثانية
# قالب: config/uptime_monitor.example.json
```

### نقاط API

| Endpoint | الوصف |
|----------|-------|
| `GET /api/monitoring/status` | حالة المراقبة + uptime + إشارات |
| `POST /api/monitoring/probe` | فحص فوري + تسجيل |
| `GET /api/monitoring/rate-limits` | حالة حدود APIs المجانية |

---

## حدود مصادر البيانات المجانية

### المراجعة قبل الإطلاق

```bash
LAUNCH_PROJECTED_USERS=100 python3 scripts/free_api_rate_limit_audit.py
```

**المخرجات:** `FREE_API_RATE_LIMIT_AUDIT.json`

| المصدر | الحد المجاني | مخاطر عند 100 مستخدم | ترقية مقترحة |
|--------|-------------|----------------------|--------------|
| CoinGecko | 10-30 req/min | **HIGH** بدون Pro key | `COINGECKO_API_KEY` (Pro) |
| Binance REST | 1200 weight/min/IP | MEDIUM | `BINANCE_WS_ENABLED=true` |
| Alternative.me | ~1 req/min | LOW | cache 15min+ |
| DefiLlama | reasonable use | MEDIUM للـ B2B | Pro إذا توزيع تجاري |
| Groq/Gemini | RPM/TPM | **HIGH** للـ Oracle | مفاتيح مدفوعة |

### توصيات الإطلاق

1. **قبل 50 مستخدم:** `COINGECKO_API_KEY` (Pro) أو `COINMARKETCAP_API_KEY`
2. **قبل 200 مستخدم:** `BINANCE_WS_ENABLED=true` + مراجعة IP weight
3. **قبل 20 مستخدم Oracle-heavy:** مفاتيح LLM مدفوعة
4. شغّل `GET /api/monitoring/rate-limits` بعد النشر لمراقبة throttling
