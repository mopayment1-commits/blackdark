#!/usr/bin/env python3
"""Record CISA Secure by Design pledge submission URL (FINDING-01, executive)."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "docs" / "governance" / "SECURE_BY_DESIGN_PLEDGE_STATUS.md"
_URL_RE = re.compile(r"^https://", re.I)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pledge-url", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    url = args.pledge_url.strip()
    if not _URL_RE.match(url):
        print("pledge-url must be https://", file=sys.stderr)
        return 1
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    block = f"""
## Submission record

| Field | Value |
|-------|-------|
| Submitted | {stamp} |
| Portal URL | {url} |
| Recorded by | `scripts/record_pledge_submission.py` |

"""
    if not args.apply:
        print(block)
        print("dry-run: pass --apply to update SECURE_BY_DESIGN_PLEDGE_STATUS.md", file=sys.stderr)
        return 0
    text = STATUS.read_text(encoding="utf-8")
    if "## Submission record" in text:
        before, _, after = text.partition("## Submission record")
        text = before.rstrip() + "\n" + block
    else:
        text = text.rstrip() + "\n" + block
    STATUS.write_text(text, encoding="utf-8")
    print(f"Updated {STATUS}")
    print("Next: python scripts/transition_launch57_finding_status.py --finding FINDING-01 --pledge-url ... --apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
