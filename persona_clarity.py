"""
BLACKDARK — Persona Clarity Layer (Differentiator D7 + growth wedge).

Translates one institutional decision into clear English guidance for:
  retail · pro · whale · fund · acquirer

Public site rule: English-only. Optional Arabic strings may remain in the
API payload for internal/docs use but are never the UI default.

Solves the real problem: giants drown users in indicators; we give one truth
per persona without inventing a second decision engine.
"""

from __future__ import annotations

from typing import Any


def _truth(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("net_edge_truth") or {}


def _half(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("opportunity_half_life") or {}


def _conflict(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("dimension_conflict") or {}


def _retail_texts(
    *,
    action: str,
    asset: str,
    score: float,
    reject: bool,
    veto: bool,
    net_profit_usdt: float,
) -> tuple[str, str]:
    if action == "I_DONT_KNOW":
        ar_suffix = "النظام لا يملك دليلاً كافياً لتكوين رأي اتجاهي — يعلن ذلك صراحة."
        en_suffix = "The system does not have enough evidence to form a directional view — it says so explicitly."
    elif reject:
        ar_suffix = "النظام رفض الإشارة لأنها غير مضمونة التنفيذ بعد التكاليف."
        en_suffix = "Rejected: not executable after real costs."
    elif veto:
        ar_suffix = "يوجد تعارض بين مصادر السوق — الأفضل عدم الدخول الآن."
        en_suffix = "Sources contradict — stay flat."
    else:
        ar_suffix = f"صافي تقديري بعد التكاليف حوالي ${net_profit_usdt:.2f}."
        en_suffix = f"Estimated net after costs ~${net_profit_usdt:.2f}."

    if action == "I_DONT_KNOW":
        lead_ar, lead_en = "لا نعرف", "I DON'T KNOW"
    elif action == "WAIT":
        lead_ar, lead_en = "انتظر", "Wait"
    else:
        lead_ar, lead_en = "فرصة واضحة", "Clear opportunity"
    retail_ar = f"{lead_ar} على {asset}: الدرجة {score:.0f}/100. " + ar_suffix
    retail_en = f"{lead_en} on {asset}: score {score:.0f}/100. " + en_suffix
    return retail_en, retail_ar


def _persona(en: str, ar: str, include_ar: bool) -> dict[str, str]:
    row = {"en": en, "text": en}
    if include_ar:
        row["ar"] = ar
    return row


def build_persona_clarity(
    *,
    asset: str,
    score: float,
    verdict: str,
    payload: dict[str, Any] | None = None,
    net_profit_usdt: float = 0.0,
    include_ar: bool = False,
) -> dict[str, Any]:
    p = payload or {}
    truth = _truth(p)
    half = _half(p)
    conflict = _conflict(p)
    regime = str(p.get("market_regime") or "neutral")
    truth_score = float(truth.get("truth_score") or 0)
    reject = bool(truth.get("reject"))
    veto = bool(conflict.get("veto") or conflict.get("abstain"))
    unknown = str(verdict).strip().upper().replace(" ", "_").replace("'", "") in {
        "I_DONT_KNOW",
        "INSUFFICIENT",
        "INSUFFICIENT_EVIDENCE",
    }
    if unknown or veto:
        action = "I_DONT_KNOW"
    elif reject or verdict == "Do Not Touch":
        action = "WAIT"
    else:
        action = "ACT"
    hl = half.get("expected_half_life_seconds")
    disappear = half.get("disappearance_probability")

    retail_en, retail_ar = _retail_texts(
        action=action,
        asset=asset,
        score=score,
        reject=reject,
        veto=veto,
        net_profit_usdt=net_profit_usdt,
    )

    pro_ar = (
        f"Verdict={verdict} | Truth={truth_score:.0f} | Regime={regime} | "
        f"Half-life≈{hl if hl is not None else 'n/a'}s | "
        f"P(disappear)={disappear if disappear is not None else 'n/a'}"
    )
    pro_en = pro_ar

    whale_ar = (
        f"{asset}: نافذة تنفيذ متبقية تقريباً {hl if hl is not None else '؟'} ثانية. "
        f"Truth Edge={'مرفوض' if reject else 'مقبول'} "
        f"(score {truth_score:.0f}). "
        f"ازدحام السوق محسوب — لا تطارد سعراً وهمياً."
    )
    whale_en = (
        f"{asset}: ~{hl if hl is not None else '?'}s execution window left. "
        f"Truth Edge={'REJECT' if reject else 'PASS'} ({truth_score:.0f}). "
        f"Crowd decay priced in — do not chase phantom prints."
    )

    fund_ar = (
        "قرار مؤسسي واحد مع بوابة Net-Edge + Contradiction Veto + سجل Signal Registry. "
        f"الإجراء={action}، النظام={regime}، صافي=${net_profit_usdt:.4f}."
    )
    fund_en = (
        "Single institutional decision with Net-Edge gate + Contradiction Veto + Signal Registry. "
        f"Action={action}, regime={regime}, net=${net_profit_usdt:.4f}."
    )

    acquirer_ar = (
        "أصل قابل للتدقيق: تنبؤ مُسجّل + Truth Score + Half-Life + سلسلة إثبات. "
        "ليس داشبورد مؤشرات — معجم إشارات مُسمّى وقابل للبيع."
    )
    acquirer_en = (
        "Auditable asset: registered prediction + Truth Score + Half-Life + proof chain. "
        "Not an indicator dashboard — a sellable labeled signal lexicon."
    )

    return {
        "action": action,
        "asset": asset,
        "score": score,
        "verdict": verdict,
        "regime": regime,
        "lang": "en",
        "personas": {
            "retail": _persona(retail_en, retail_ar, include_ar),
            "pro": _persona(pro_en, pro_ar, include_ar),
            "whale": _persona(whale_en, whale_ar, include_ar),
            "fund": _persona(fund_en, fund_ar, include_ar),
            "acquirer": _persona(acquirer_en, acquirer_ar, include_ar),
        },
        "hooks": {
            "problem_solved_retail": "one clear act/wait instead of 200 indicators",
            "problem_solved_pro": "truth + half-life + regime in one line",
            "problem_solved_whale": "time-to-death of edge before size hits book",
            "problem_solved_fund": "compliance-ready reject reasons + registry",
            "problem_solved_acquirer": "proof-native labeled corpus for data-room",
        },
    }
