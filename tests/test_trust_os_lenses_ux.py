"""Trust OS Prove / Operate / Desk / Room lens UX."""

from __future__ import annotations

from pathlib import Path


def test_lenses_manifest_story():
    from trust_os_lenses import lenses_manifest, normalize_lens, primary_entries_for_lens

    m = lenses_manifest()
    assert m["story"] == "Prove → Operate → Desk → Room"
    ids = [x["id"] for x in m["lenses"]]
    assert ids == ["prove", "operate", "desk", "room"]
    assert m["honesty"]["guaranteed_accuracy"] is False
    assert normalize_lens("whale") == "desk"
    assert normalize_lens("fund") == "room"
    prove_entries = primary_entries_for_lens("prove")
    by_id = {e["id"]: e for e in prove_entries}
    assert by_id["decide"]["available"] is True
    assert by_id["verify"]["available"] is True
    assert by_id["my_book"]["available"] is False
    assert by_id["alerts"]["available"] is False
    op = {e["id"]: e for e in primary_entries_for_lens("operate")}
    assert op["my_book"]["available"] is True


def test_audience_maps_to_lens():
    from audience_routing import audience_entry

    retail = audience_entry("retail")
    assert retail["lens"] == "prove"
    assert retail["lens_label"] == "Prove"
    whale = audience_entry("whale")
    assert whale["lens"] == "desk"
    fund = audience_entry("fund")
    assert fund["lens"] == "room"


def test_intent_router_primary_four():
    from intent_router import intent_router_manifest

    m = intent_router_manifest()
    primary_ids = [i["id"] for i in m["primary_entries"]]
    assert primary_ids == ["decide", "verify", "my_book", "alerts"]
    assert "Prove → Operate" in m["memory_line"]


def test_trust_os_manifest_includes_lenses():
    from trust_os import trust_os_manifest

    m = trust_os_manifest()
    assert m["ux_lenses"]["api"] == "/api/lenses"
    assert "docs/TRUST_OS_LENSES_UX.md" in m["binding_docs"]


def test_dashboard_and_landing_wire_lenses():
    dash = Path("templates/dashboard.html").read_text(encoding="utf-8")
    land = Path("templates/landing.html").read_text(encoding="utf-8")
    assert 'data-lens="prove"' in dash
    assert "entryRail" in dash
    assert "applyLens" in dash
    assert 'id="decide"' in dash
    assert 'id="alerts"' in dash
    assert "Prove → Operate → Desk → Room" in land or "lens=prove" in land
    # Landing uses i18n key; English string lives in i18n_service.
    assert "Open Proof" in land or "nav.open_proof" in land
    assert Path("docs/TRUST_OS_LENSES_UX.md").is_file()
