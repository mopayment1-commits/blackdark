# المراقبة والتنبيهات بعد النشر

## ما يوفره النظام

| المكوّن | الوظيفة |
|---------|---------|
| `/health/live` | فحص حياة فوري (<50ms) |
| `/health/ready` | جاهزية DB + Redis |
| `uptime_probe_loop.py` | تسجيل محلي كل 60ث |
| `ops/monitoring_alerting.py` | فحص live+ready، بطء، فشل متتالي، **تنبيه Telegram/webhook** |
| `/api/monitoring/status` | حالة 24h + إعداد التنبيه |
| `/api/monitoring/probe` | فحص يدوي بعد النشر |

## متغيرات البيئة (Staging/Production)

```bash
MONITORING_ENABLED=true
MONITORING_BASE_URL=https://your-staging.up.railway.app
MONITORING_INTERVAL_SEC=60
MONITORING_FAIL_THRESHOLD=2          # فشلان متتاليان → تنبيه
MONITORING_LATENCY_WARN_MS=2000
MONITORING_LATENCY_FAIL_MS=5000
MONITORING_ALERT_COOLDOWN_SEC=300

TELEGRAM_BOT_TOKEN=...
OPS_TELEGRAM_CHAT_ID=...             # قناة المشغّل
MONITORING_WEBHOOK_URL=...           # Slack/Discord/PagerDuty (اختياري)
```

## مراقبة خارجية (موصى بها)

1. **UptimeRobot** أو **Better Stack** → `GET /health/live` كل 60ث
2. قالب: `config/uptime_monitor.example.json`
3. تنبيه email/SMS من المزود الخارجي **بالإضافة** لتنبيه Telegram الداخلي

## بعد النشر على Railway

```bash
curl https://STAGING_URL/api/monitoring/probe
curl https://STAGING_URL/api/monitoring/status
```

تأكد أن `overall_ok: true` و`ops_telegram_configured: true`.

## Telemetry outage runbook

**Trigger / symptoms:** missing Sentry events, UptimeRobot down, `overall_ok: false`, or ops Telegram silence during incident.

**Diagnosis:** distinguish app down vs telemetry pipeline broken (`/health/live` ok but alerts absent).

**Actions:**
```bash
curl -s https://HOST/api/monitoring/probe
curl -s https://HOST/api/monitoring/status
python scripts/setup_monitoring.py --dry-run
```

**Decision:** if app unhealthy, follow incident response; if only telemetry, fail over to external uptime monitor + manual war-room.

**Verification:** test alert fires to Telegram/webhook; external monitor green.

**Recovery:** restore `MONITORING_*` env, redeploy if probe worker stuck.

**Escalation:** on-call pager + platform owner; external vendor status page.

**Evidence preservation:** probe JSON, alert delivery logs, timeline for postmortem.
