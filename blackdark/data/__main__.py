"""CLI entrypoint: python -m blackdark.data backfill ..."""

import sys

from blackdark.data.backfill import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
