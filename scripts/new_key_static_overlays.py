#!/usr/bin/env python3
"""Static overlays for new public-surface keys (when MT is rate-limited)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from i18n_service import EN, LOCALES

OVERLAYS: dict[str, dict[str, str]] = {
    "es": {
        "waitlist.title": "Obtén acceso anticipado a Trust OS",
        "waitlist.sub": "Únete a la lista de espera para novedades del lanzamiento. Sin contadores falsos — un camino claro hacia Prove.",
        "waitlist.email_aria": "Introduce tu correo",
        "waitlist.email_placeholder": "Introduce tu correo",
        "waitlist.submit": "Unirse a la lista",
        "waitlist.stats_aria": "Actividad de la plataforma",
        "waitlist.page.title": "Lista de espera",
        "waitlist.page.h1": "Únete a la lista de espera",
        "waitlist.page.body": "Novedades de Trust OS — sin contadores falsos. Los totales de la página principal vienen de /api/analytics/stats en vivo.",
        "waitlist.page.back": "← Volver al inicio",
        "waitlist.page.submit": "Unirse",
        "waitlist.msg.submitting": "Enviando…",
        "waitlist.msg.error": "No se pudo unir — inténtalo de nuevo.",
        "waitlist.msg.network": "Error de red — inténtalo de nuevo.",
        "waitlist.msg.generic": "Algo salió mal.",
        "waitlist.msg.welcome": "¡Bienvenido! Eres el #{position} en la lista de espera.",
        "tg.start_free_suffix": "Empezar gratis",
        "oracle.field.audience": "Público",
        "oracle.field.experience": "Experiencia",
        "oracle.field.symbol": "Símbolo",
        "oracle.mode.decision_pro": "Decision Pro",
        "oracle.title": "Oráculo BLACKDARK",
        "oracle.freshness.title": "Frescura de datos",
        "oracle.share.facebook": "Facebook",
        "oracle.share.instagram": "Instagram",
        "oracle.share.whatsapp": "WhatsApp",
        "oracle.share.telegram": "Telegram",
        "oracle.share.reddit": "Reddit",
    },
    "ar": {
        "waitlist.title": "احصل على وصول مبكر إلى Trust OS",
        "waitlist.sub": "انضم إلى قائمة الانتظار لتحديثات الإطلاق. بدون عدادات مقاعد وهمية — مسار واضح إلى Prove.",
        "waitlist.email_aria": "أدخل بريدك الإلكتروني",
        "waitlist.email_placeholder": "أدخل بريدك الإلكتروني",
        "waitlist.submit": "انضم إلى القائمة",
        "waitlist.stats_aria": "نشاط المنصة",
        "waitlist.page.title": "قائمة الانتظار",
        "waitlist.page.h1": "انضم إلى قائمة الانتظار",
        "waitlist.page.body": "تحديثات إطلاق Trust OS — بدون عدادات وهمية. الأرقام في الصفحة الرئيسية من /api/analytics/stats مباشرة.",
        "waitlist.page.back": "← العودة إلى الصفحة الرئيسية",
        "waitlist.page.submit": "انضم",
        "waitlist.msg.submitting": "جارٍ الإرسال…",
        "waitlist.msg.error": "تعذّر الانضمام — حاول مرة أخرى.",
        "waitlist.msg.network": "خطأ في الشبكة — حاول مرة أخرى.",
        "waitlist.msg.generic": "حدث خطأ ما.",
        "waitlist.msg.welcome": "مرحبًا! أنت رقم {position} في قائمة الانتظار.",
        "tg.start_free_suffix": "ابدأ مجانًا",
        "oracle.field.audience": "الجمهور",
        "oracle.field.experience": "التجربة",
        "oracle.field.symbol": "الرمز",
        "oracle.mode.decision_pro": "Decision Pro",
        "oracle.title": "أوراكل BLACKDARK",
        "oracle.freshness.title": "حداثة البيانات",
        "oracle.share.facebook": "Facebook",
        "oracle.share.instagram": "Instagram",
        "oracle.share.whatsapp": "WhatsApp",
        "oracle.share.telegram": "Telegram",
        "oracle.share.reddit": "Reddit",
    },
    "fr": {
        "waitlist.title": "Accès anticipé à Trust OS",
        "waitlist.sub": "Rejoignez la liste d’attente pour les nouveautés du lancement. Pas de faux compteurs — un chemin clair vers Prove.",
        "waitlist.email_aria": "Saisissez votre e-mail",
        "waitlist.email_placeholder": "Saisissez votre e-mail",
        "waitlist.submit": "Rejoindre la liste",
        "waitlist.stats_aria": "Activité de la plateforme",
        "waitlist.page.title": "Liste d’attente",
        "waitlist.page.h1": "Rejoindre la liste d’attente",
        "waitlist.page.body": "Nouveautés Trust OS — sans faux compteurs. Les chiffres de l’accueil viennent de /api/analytics/stats en direct.",
        "waitlist.page.back": "← Retour à l’accueil",
        "waitlist.page.submit": "Rejoindre",
        "waitlist.msg.submitting": "Envoi…",
        "waitlist.msg.error": "Impossible de rejoindre — réessayez.",
        "waitlist.msg.network": "Erreur réseau — réessayez.",
        "waitlist.msg.generic": "Une erreur s’est produite.",
        "waitlist.msg.welcome": "Bienvenue ! Vous êtes n°{position} sur la liste d’attente.",
        "tg.start_free_suffix": "Commencer gratuitement",
        "oracle.field.audience": "Public",
        "oracle.field.experience": "Expérience",
        "oracle.field.symbol": "Symbole",
        "oracle.mode.decision_pro": "Decision Pro",
        "oracle.title": "Oracle BLACKDARK",
        "oracle.freshness.title": "Fraîcheur des données",
        "oracle.share.facebook": "Facebook",
        "oracle.share.instagram": "Instagram",
        "oracle.share.whatsapp": "WhatsApp",
        "oracle.share.telegram": "Telegram",
        "oracle.share.reddit": "Reddit",
    },
}


def main() -> None:
    locales_dir = ROOT / "locales"
    extra_path = ROOT / "data" / "i18n_new_public_keys.json"
    extra: dict[str, dict[str, str]] = {}
    if extra_path.is_file():
        extra = json.loads(extra_path.read_text(encoding="utf-8"))
    merged = dict(extra)
    for code, overlay in OVERLAYS.items():
        merged.setdefault(code, {})
        merged[code].update(overlay)
    for code, overlay in merged.items():
        if code not in LOCALES:
            continue
        path = locales_dir / f"{code}.json"
        cat = json.loads(path.read_text(encoding="utf-8"))
        cat.update(overlay)
        for k in EN:
            cat.setdefault(k, EN[k])
        path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"patched {code}")


if __name__ == "__main__":
    main()
