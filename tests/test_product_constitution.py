"""Binding Product Constitution must exist and encode the adopted canon."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSTITUTION = ROOT / "docs" / "PRODUCT_CONSTITUTION_AR.md"


def test_product_constitution_exists():
    assert CONSTITUTION.is_file()


def test_product_constitution_encodes_core_and_differentiators():
    text = CONSTITUTION.read_text(encoding="utf-8")
    assert "دستور المنتج الملزم" in text or "Product Constitution" in text
    assert "لا يُمس" in text
    # Eight capabilities
    for capability in (
        "Unified Financial Oracle",
        "Executable Arbitrage Engine",
        "Net-Edge & Risk Gate",
        "Public Accuracy & Audit Chain",
        "Labeled Data Flywheel",
        "Whale / Microstructure / Macro Fusion",
        "Alert + Tiered Product",
        "B2B Evidence & API",
    ):
        assert capability in text
    # Differentiators D1–D8
    for marker in (
        "Proof-Native Oracle",
        "Contradiction Veto",
        "Net-Edge Truth",
        "Opportunity Half-Life",
        "Regime-Conditional Models",
        "Evidence Pack API",
        "English-first Persona Clarity UX",
        "Signal Registry",
    ):
        assert marker in text
    # Persona pain→solution map
    assert "Persona Clarity" in text or "افعل / انتظر" in text
    assert "واجب التنفيذ" in text


def test_related_docs_point_to_constitution():
    for rel in (
        "docs/UNIQUE_DIFFERENTIATORS_AR.md",
        "docs/AI_FINANCIAL_MODEL_DESIGN.md",
        "docs/AI_MODEL_TRANSFORMATION.md",
        "docs/INSTITUTIONAL_FEATURE_DD_AR.md",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "PRODUCT_CONSTITUTION_AR.md" in text


def test_heroes_strategy_binding_exists():
    path = ROOT / "docs" / "HEROES_STRATEGY_BINDING.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for marker in (
        "Six Heroes",
        "Locked Predictions",
        "Discipline Mirror",
        "Signal vs Noise",
        "Emerging Fund",
        "Compliance Footer",
        "Audience entry",
    ):
        assert marker in text
    constitution = (ROOT / "docs" / "PRODUCT_CONSTITUTION_AR.md").read_text(encoding="utf-8")
    assert "HEROES_STRATEGY_BINDING.md" in constitution
