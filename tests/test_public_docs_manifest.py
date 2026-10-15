"""Public /docs manifest: deduped prefixes, read list, and page-link policy."""

from __future__ import annotations

from public_api_docs import (
    PUBLIC_DOCS_READ_PREFIX_EXCLUDE,
    public_docs_manifest,
    public_docs_read_prefixes,
)


def test_allowed_prefixes_deduped_no_duplicate_oracle():
    prefixes = public_docs_read_prefixes()
    assert prefixes.count("/oracle/") == 1


def test_stealth_advisor_excluded_from_read_list():
    prefixes = public_docs_read_prefixes()
    assert "/api/whale/stealth-advisor" not in prefixes
    assert "/api/whale/stealth-advisor" in PUBLIC_DOCS_READ_PREFIX_EXCLUDE


def test_post_only_stealth_line_only_on_docs_page_manifest():
    api_manifest = public_docs_manifest()
    assert "post_only_public_prefixes" not in api_manifest
    docs_manifest = public_docs_manifest(include_post_only_public_prefixes=True)
    assert docs_manifest["post_only_public_prefixes"] == ["/api/whale/stealth-advisor"]


def test_prefix_rows_no_href_for_oracle_slash_prefix():
    manifest = public_docs_manifest()
    rows = {r["path"]: r for r in manifest["allowed_prefix_rows"]}
    assert "/oracle/" in rows
    assert "href" not in rows["/oracle/"]


def test_prefix_rows_href_for_known_get_ok_paths():
    manifest = public_docs_manifest()
    rows = {r["path"]: r for r in manifest["allowed_prefix_rows"]}
    assert rows["/api/oracle/accuracy"]["href"] == "/api/oracle/accuracy"
    assert rows["/api/trust-os"]["href"] == "/api/trust-os"
