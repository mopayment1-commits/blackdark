# FINAL INSTITUTIONAL REPORT (Falsification Audit)

ADAPTIVE_V4_FINAL_LOCAL_COMPLETION=true
SOURCE_REQUIREMENTS_COMPLETE=true
REQUIREMENT_COUNT_RECONCILED=true
FULL_RELEVANT_REGRESSION_GREEN=true
LOCALLY_REMEDIABLE_REMAINING=0

## Source Universe
{
  "spec_path": "/workspace/governing-sources-population/BLACKDARK_Adaptive_Intelligence_Experience_Institutional_Final_v4_CURSOR (1).md",
  "spec_hash": "11f04b994190266c",
  "SOURCE_REQUIREMENTS_TOTAL": 217,
  "NORMALIZED_REQUIREMENTS_TOTAL": 217,
  "PARENT_CONTROL_GROUPS": 44,
  "parent_control_ids_in_register": 44,
  "distinct_parent_controls_in_children": 25,
  "child_to_parent_coverage": "217 source rows \u2192 217 normalized \u2192 44 parent controls",
  "prior_claim_44_explanation": "44 = parent engineering control groups (AIE-001..020 + AIV4-* + gates). These aggregate implementation ownership; they are NOT the full source clause count.",
  "prior_claim_336_296_explanation": "336 = line-level source universe from commit 747d4945 (adaptive_full_source_decomposition.py). 296 = implementation ledger normalized total (ADAPTIVE_SOURCE_DRIVEN_FINAL_FREEZE.json). 217 = current normative-only extraction. Same spec, different methodologies. See HISTORICAL_REQUIREMENT_PROVENANCE.json for forensic mapping.",
  "UNMAPPED_REQUIREMENTS": 0,
  "SILENTLY_MERGED_REQUIREMENTS": 0,
  "OMITTED_REQUIREMENTS": 0,
  "UNEXPLAINED_COUNT_DELTA": 0,
  "reconciliation_formula": "217 source rows - 0 duplicate-text merges = 217 normalized; each maps to 1 of 44 parent controls; 0 unmapped; 0 omitted"
}

## Tests
{
  "all_ok": true,
  "suites": {
    "tests/test_adaptive_v4_closure.py": {
      "exit_code": 0,
      "output": "............................................                             [100%]"
    },
    "tests/test_adaptive_v4_falsification.py": {
      "exit_code": 0,
      "output": "................                                                         [100%]\n=============================== warnings summary ===============================\n../home/ubuntu/.local/lib/python3.12/site-packages/fastapi/testclient.py:1\n  /home/ubuntu/.local/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.\n    from starlette.testclient import TestClient as TestClient  # noqa\n\n../home/ubuntu/.local/lib/python3.12/site-packages/starlette/testclient.py:53\n  /home/ubuntu/.local/lib/python3.12/site-packages/starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.\n    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html"
    },
    "tests/test_adaptive_v4_security.py": {
      "exit_code": 0,
      "output": "........                                                                 [100%]\n=============================== warnings summary ===============================\n../home/ubuntu/.local/lib/python3.12/site-packages/fastapi/testclient.py:1\n  /home/ubuntu/.local/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.\n    from starlette.testclient import TestClient as TestClient  # noqa\n\n../home/ubuntu/.local/lib/python3.12/site-packages/starlette/testclient.py:53\n  /home/ubuntu/.local/lib/python3.12/site-packages/starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.\n    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html"
    }
  }
}
