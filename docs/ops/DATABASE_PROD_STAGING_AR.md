# قواعد البيانات — Staging vs Production (BLK-002)

## المشكلة (BLK-002)

التدقيق المحلي يستخدم **SQLite** (`data/blackdark.db`) افتراضيًا.  
الإنتاج **يجب** أن يستخدم **PostgreSQL منفصل** — لا يُسمح بنشر live على نفس قاعدة التطوير.

## الفصل الإلزامي

| البيئة | `DATABASE_URL` | الملف/الخدمة |
|--------|----------------|--------------|
| **Development** | غير مضبوط أو `sqlite:///...` | `data/blackdark.db` محلي |
| **Staging** | `postgresql://...@staging-host/blackdark_staging` | Railway Postgres plugin (خدمة staging) |
| **Production** | `postgresql://...@prod-host/blackdark_prod` | Railway Postgres plugin (خدمة prod منفصلة) |

## متغيرات Railway (لكل خدمة)

```bash
# Staging
ENVIRONMENT=staging
RAILWAY_ENVIRONMENT=staging
DATABASE_URL=${{Postgres.DATABASE_URL}}   # plugin منفصل لـ staging
REDIS_URL=${{Redis.REDIS_URL}}
SECRETS_MASTER_KEY=<generate-32b-hex>
STRIPE_WEBHOOK_SECRET=whsec_staging_...
LEMON_SQUEEZY_WEBHOOK_SECRET=...

# Production (منفصل تمامًا)
ENVIRONMENT=production
RAILWAY_ENVIRONMENT=production
DATABASE_URL=${{Postgres.DATABASE_URL}}   # plugin prod مختلف
```

## النسخ الاحتياطي (Backup)

```bash
# على cron يومي (staging + prod)
DATABASE_URL=postgresql://... python scripts/backup_postgres.py --out data/backups
```

المخرجات:
- `data/backups/blackdark_YYYYMMDDTHHMMSSZ.sql.gz`
- `data/backups/LATEST` → يشير لآخر نسخة
- SHA256 جنب كل ملف

الاستعادة: `scripts/restore_postgres.py`

## التحقق قبل النشر

```bash
python -c "from postgres_backend import use_postgres; import os; print(use_postgres(), os.getenv('DATABASE_URL','')[:20])"
python scripts/backup_postgres.py   # يفشل إذا لم يكن postgresql://
```

## بوابة BLK-002

| شرط | Staging | Production |
|-----|---------|------------|
| PostgreSQL URL | ✅ مطلوب | ✅ مطلوب |
| ≠ SQLite dev | ✅ | ✅ |
| Backup مجدول | موصى | **إلزامي** |
| `pre_launch_ready` | بعد اختبار staging كمستخدم | بعد PASS_LIVE evidence |
