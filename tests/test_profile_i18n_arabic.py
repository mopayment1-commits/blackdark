"""Profile page must honor ?lang=ar (html lang/dir + translated chrome)."""

from __future__ import annotations

import os

os.environ.setdefault("SOFT_LAUNCH", "1")

from fastapi.testclient import TestClient

from dashboard import app

client = TestClient(app)


def test_profile_arabic_html_lang_and_sections():
    from dashboard import templates
    from i18n_service import template_context
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/profile",
        "query_string": b"lang=ar",
        "headers": [],
    }
    req = Request(scope)
    ctx = template_context(req)
    ar = templates.env.get_template("profile.html").render(ctx)
    assert 'lang="ar"' in ar
    assert 'dir="rtl"' in ar
    assert "ملفك الشخصي" in ar
    assert "الملف الشخصي" in ar
    assert "الأمان" in ar
    assert "الخطة" in ar
    assert "حفظ الملف الشخصي" in ar
    assert "رفع" in ar
    assert "تسجيل الخروج من كل الجلسات" in ar
    assert "Your profile" not in ar
    assert "Save profile" not in ar
    assert 'data-bd-call="saveProfile"' in ar
    assert 'data-bd-call="logoutAll"' in ar

    gate = client.get("/profile?lang=ar").text
    assert 'lang="ar"' in gate
    assert "يلزم حساب" in gate


def test_pricing_arabic_shell():
    ar = client.get("/pricing?lang=ar").text
    assert 'lang="ar"' in ar
    assert "قارن الخطط" in ar
