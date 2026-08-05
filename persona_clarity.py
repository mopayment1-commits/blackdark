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
    hl = half.get("expected_half_life_seconds")
    disappear = half.get("disappearance_probability")
    action = "WAIT" if (reject or veto or verdict == "Do Not Touch") else "ACT"

    retail_ar = (
        f"{'انتظر' if action == 'WAIT' else 'فرصة واضحة'} على {asset}: "
        f"الدرجة {score:.0f}/100. "
        + (
            "النظام رفض الإشارة لأنها غير مضمونة التنفيذ بعد التكاليف."
            if reject
            else (
                "يوجد تعارض بين مصادر السوق — الأفضل عدم الدخول الآن."
                if veto
                else f"صافي تقديري بعد التكاليف حوالي ${net_profit_usdt:.2f}."
            )
        )
    )
    retail_en = (
        f"{'Wait' if action == 'WAIT' else 'Clear opportunity'} on {asset}: "
        f"score {score:.0f}/100. "
        + (
            "Rejected: not executable after real costs."
            if reject
            else (
                "Sources contradict — stay flat."
                if veto
                else f"Estimated net after costs ~${net_profit_usdt:.2f}."
            )
        )
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

    def _persona(en: str, ar: str) -> dict[str, str]:
        row = {"en": en, "text": en}
        if include_ar:
            row["ar"] = ar
        return row

    return {
        "action": action,
        "asset": asset,
        "score": score,
        "verdict": verdict,
        "regime": regime,
        "lang": "en",
        "personas": {
            "retail": _persona(retail_en, retail_ar),
            "pro": _persona(pro_en, pro_ar),
            "whale": _persona(whale_en, whale_ar),
            "fund": _persona(fund_en, fund_ar),
            "acquirer": _persona(acquirer_en, acquirer_ar),
        },
        "hooks": {
            "problem_solved_retail": "one clear act/wait instead of 200 indicators",
            "problem_solved_pro": "truth + half-life + regime in one line",
            "problem_solved_whale": "time-to-death of edge before size hits book",
            "problem_solved_fund": "compliance-ready reject reasons + registry",
            "problem_solved_acquirer": "proof-native labeled corpus for data-room",
        },
    }
