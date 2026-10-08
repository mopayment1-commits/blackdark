"""Profile Plan section — public tier names only (no PSP / legacy ladder copy)."""

from __future__ import annotations

from pathlib import Path


def test_profile_plan_section_public_copy():
    html = Path("templates/profile.html").read_text(encoding="utf-8")
    banned = (
        "DISCOVER",
        "ELITE",
        "WHALE",
        "19.99",
        "49.99",
        "Lemon",
        "Stripe",
        "KYC",
        "Option A",
        "social network",
        "card data",
        "provider keys",
        "DECIDE",
        "SEE THE EDGE",
    )
    for token in banned:
        assert token not in html
    assert "t('profile.plan.plus_cta')" in html
    assert "t('profile.plan.pro_cta')" in html
    assert "t('profile.section.plan')" in html
    assert "Enterprise" in html
    assert "publicPlanName" in html
    assert "data-bd-call=\"saveProfile\"" in html
    assert "data-bd-call=\"uploadAvatar\"" in html
    assert "data-bd-call=\"logoutAll\"" in html
