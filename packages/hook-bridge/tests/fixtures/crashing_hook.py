# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Fixture Hook that always fails health (nonzero exit) — proves hook-bridge
propagates a Hook process failure rather than swallowing it."""

import sys

if __name__ == "__main__":
    print("boom", file=sys.stderr)
    sys.exit(1)
