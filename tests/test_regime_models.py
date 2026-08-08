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


def test_public_templates_bind_lang_dir():
    """Templates bind lang/dir for i18n (English default; Arabic rtl via context)."""
    from pathlib import Path
    import re

    root = Path(__file__).resolve().parents[1]
    for path in (root / "templates").glob("*.html"):
        text = path.read_text(encoding="utf-8")
        assert "lang=" in text, path.name
        # Forbid hard-locked <html … dir="rtl"> — rtl must come from {{ dir }}.
        # CSS selectors like html[dir="rtl"] are allowed.
        assert not re.search(r"<html[^>]*\bdir=[\"']rtl[\"']", text), path.name
