"""Behavioral coverage for governance.launch57.generate_financial_security_closure helpers."""

from __future__ import annotations

import governance.launch57.generate_financial_security_closure as fin
from governance.launch57.literal_closure_documents import financial_recon_public_document


def test_git_sha_and_spec_sha():
    sha = fin._git_sha()
    assert isinstance(sha, str) and len(sha) >= 1
    spec = fin._spec_sha()
    assert isinstance(spec, str)


def test_financial_recon_document_matches_generator_import():
    doc = financial_recon_public_document(
        generated_at="t",
        implementation_sha=sha if (sha := fin._git_sha()) else "x",
        baseline_sha=fin._spec_sha(),
    )
    assert doc["public_private_leaks"] == []
