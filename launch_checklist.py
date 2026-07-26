"""
BLACKDARK — 5-day launch checklist (أسبوع عمل للإطلاق).

Tracks production readiness with auto-detection + manual gates.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

LaunchStatus = Literal["done", "progress", "blocked", "pending"]

ROOT = Path(__file__).resolve().parent.parent


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _file_exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def _run_pytest_quick() -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )
        tail = (proc.stdout or "").splitlines()[-1] if proc.stdout else ""
        return proc.returncode == 0, tail or f"exit {proc.returncode}"
    except Exception as exc:
        return False, str(exc)


def _checklist_rows() -> list[dict[str, Any]]:
    base_url = _env("APP_BASE_URL") or "http://localhost:8080"
    is_local = "localhost" in base_url or "127.0.0.1" in base_url
    tests_ok, tests_note = _run_pytest_quick()

    rows: list[dict[str, Any]] = [
        # ── Day 1: Production infra ──
        {
            "day": 1,
            "id": "d1_docker",
            "title": "Docker + Railway deploy ready",
            "status": "done" if _file_exists("Dockerfile") and _file_exists("railway.json") else "pending",
            "action": "docker compose up -d or Railway Deploy from GitHub",
            "endpoint": "/api/services/status",
        },
        {
            "day": 1,
            "id": "d1_secrets",
            "title": "Production secrets (SECRETS_MASTER_KEY, SESSION_TOKEN_PEPPER)",
            "status": "done" if _env("SECRETS_MASTER_KEY") or _env("SECRETS_VAULT_KEY") else "blocked",
            "action": "Generate 32-byte hex key in Railway Variables",
            "file": ".env.production.example",
        },
        {
            "day": 1,
            "id": "d1_admin",
            "title": "Admin API key + ADMIN_EMAILS",
            "status": "done" if _env("ADMIN_API_KEY") and _env("ADMIN_EMAILS") else "progress",
            "action": "Set ADMIN_API_KEY + ADMIN_EMAILS in .env",
        },
        {
            "day": 1,
            "id": "d1_verify",
            "title": "Buyer verification script passes",
            "status": "progress",
            "action": "python scripts/launch_verify.py",
        },
        # ── Day 2: Domain + Payments ──
        {
            "day": 2,
            "day_ar": "اليوم 2 — الدومين والدفع",
            "id": "d2_domain",
            "title": "Production domain + APP_BASE_URL",
            "title_ar": "دومين إنتاج + APP_BASE_URL",
            "status": "done" if not is_local and base_url.startswith("https") else "pending",
            "action": "Railway → Generate Domain → APP_BASE_URL=https://YOUR-DOMAIN",
        },
        {
            "day": 2,
            "id": "d2_stripe",
            "title": "Stripe live keys + webhook",
            "title_ar": "Stripe live + webhook",
            "status": "done" if _env("STRIPE_SECRET_KEY") and _env("STRIPE_WEBHOOK_SECRET") else "blocked",
            "action": "Stripe Dashboard → Webhook /webhook → STRIPE_WEBHOOK_SECRET",
        },
        {
            "day": 2,
            "id": "d2_billing",
            "title": "Billing checkout tested (free → pro trial)",
            "title_ar": "اختبار الاشتراك (free → pro)",
            "status": "progress",
            "action": "/api/billing/status + /login → upgrade flow",
            "endpoint": "/api/billing/status",
        },
        # ── Day 3: Alerts + Monitoring ──
        {
            "day": 3,
            "day_ar": "اليوم 3 — التنبيهات والمراقبة",
            "id": "d3_telegram",
            "title": "Telegram bot live (token + chat + webhook)",
            "title_ar": "بوت Telegram حي",
            "status": "done" if _env("TELEGRAM_BOT_TOKEN") and _env("TELEGRAM_CHAT_ID") else "progress",
            "action": "TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID + TELEGRAM_WEBHOOK_URL",
            "endpoint": "/api/alerts/telegram/status",
        },
        {
            "day": 3,
            "id": "d3_health",
            "title": "Health probes + uptime monitoring",
            "title_ar": "Health probes + مراقبة",
            "status": "done",
            "action": "UptimeRobot → /health/live (port+100 sidecar)",
            "endpoint": "/health/ready",
        },
        {
            "day": 3,
            "id": "d3_email",
            "title": "Email SMTP alerts (optional)",
            "title_ar": "تنبيهات Email (اختياري)",
            "status": "done" if _env("SMTP_HOST") and _env("SMTP_USER") else "pending",
            "action": "Set SMTP_* in .env or skip for v1 launch",
        },
        # ── Day 4: UX + Mobile + Legal ──
        {
            "day": 4,
            "day_ar": "اليوم 4 — UX + PWA + قانوني",
            "id": "d4_pwa",
            "title": "PWA icons + manifest + service worker",
            "title_ar": "PWA — أيقونات + manifest",
            "status": "done" if _file_exists("static/icon-192.png") and _file_exists("static/icon-512.png") else "progress",
            "action": "python scripts/generate_pwa_icons.py",
        },
        {
            "day": 4,
            "id": "d4_landing",
            "title": "Landing page CTA + pricing visible",
            "title_ar": "Landing + CTA + أسعار",
            "status": "done" if _file_exists("templates/landing.html") else "pending",
            "action": "/ → signup → /dashboard",
            "endpoint": "/",
        },
        {
            "day": 4,
            "id": "d4_legal",
            "title": "Terms + Privacy + Disclaimer pages",
            "title_ar": "صفحات قانونية",
            "status": "done",
            "action": "/terms · /privacy · /disclaimer",
            "endpoint": "/terms",
        },
        # ── Day 5: Go-live ──
        {
            "day": 5,
            "day_ar": "اليوم 5 — الإطلاق",
            "id": "d5_tests",
            "title": "Full test suite green",
            "title_ar": "كل الاختبارات خضراء",
            "status": "done" if tests_ok else "blocked",
            "action": tests_note,
        },
        {
            "day": 5,
            "id": "d5_keys",
            "title": "Platform API keys connected",
            "title_ar": "مفاتيح Platform Hub",
            "status": "progress",
            "action": "connect_keys.bat or /platform → Keys",
            "endpoint": "/api/platform/keys/status",
        },
        {
            "day": 5,
            "id": "d5_demo",
            "title": "B2B demo + public accuracy page",
            "title_ar": "B2B demo + Oracle accuracy",
            "status": "done",
            "action": "/b2b · /oracle/accuracy",
            "endpoint": "/api/oracle/accuracy/public",
        },
        {
            "day": 5,
            "id": "d5_golive",
            "title": "GO LIVE — announce + monitor 24h",
            "title_ar": "GO LIVE — إعلان + مراقبة 24س",
            "status": "pending",
            "action": "Deploy production → share URL → monitor /health",
        },
    ]
    return rows


def launch_checklist() -> dict[str, Any]:
    rows = [{k: v for k, v in r.items() if not k.endswith("_ar")} for r in _checklist_rows()]
    done = sum(1 for r in rows if r["status"] == "done")
    blocked = sum(1 for r in rows if r["status"] == "blocked")
    progress = sum(1 for r in rows if r["status"] == "progress")
    pending = sum(1 for r in rows if r["status"] == "pending")
    total = len(rows)

    by_day: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        by_day.setdefault(r["day"], []).append(r)

    days_summary = []
    for day in sorted(by_day.keys()):
        items = by_day[day]
        day_done = sum(1 for i in items if i["status"] == "done")
        days_summary.append({
            "day": day,
            "label": f"Day {day}",
            "total": len(items),
            "done": day_done,
            "percent": round(day_done / len(items) * 100, 1) if items else 0,
            "items": items,
        })

    launch_ready = blocked == 0 and done >= total - 2  # allow 2 pending for soft launch

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "launch_target": "5 business days",
        "total_tasks": total,
        "done_count": done,
        "progress_count": progress,
        "blocked_count": blocked,
        "pending_count": pending,
        "launch_percent": round(done / total * 100, 1) if total else 0,
        "launch_ready": launch_ready,
        "days": days_summary,
        "items": rows,
        "next_actions": [r for r in rows if r["status"] in {"blocked", "progress", "pending"}][:6],
        "roadmap_url": "/admin/roadmap",
        "plan_url": "/admin/plan",
    }


def save_checklist() -> dict[str, Any]:
    import json

    data = launch_checklist()
    path = ROOT / "data" / "launch_checklist.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    data["saved_to"] = str(path)
    return data
