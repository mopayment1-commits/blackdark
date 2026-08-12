"""D5 regime-conditional model registry — honest evidence status."""

from __future__ import annotations


def test_regime_model_registry_is_honest():
    from ml.regime_models import REGIMES, regime_model_registry

    reg = regime_model_registry()
    assert reg["differentiator"] == "D5"
    assert set(reg["regimes"].keys()) == set(REGIMES)
    assert reg["artifacts_expected"] == len(REGIMES)
    # Until trained artifacts exist, do not claim full per-regime models.
    if reg["artifacts_ready"] == 0:
        assert reg["per_regime_models"] is False
        assert reg["evidence_status"] == "weights_live"


def test_english_ui_covers_all_templates():
    from pathlib import Path

    def _has_english_default_lang(text: str) -> bool:
        return (
            'lang="en"' in text
            or "lang='en'" in text
            or "lang|default('en')" in text
            or 'lang|default("en")' in text
        )

    root = Path(__file__).resolve().parents[1]
    for path in (root / "templates").glob("*.html"):
        text = path.read_text(encoding="utf-8")
        assert _has_english_default_lang(text), path.name
        assert 'dir="rtl"' not in text, path.name
