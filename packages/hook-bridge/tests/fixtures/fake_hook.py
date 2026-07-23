# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Fixture Hook for hook-bridge-runner tests — not a real Hook.

Mimics the generic wire shell the SDK's `hook.run()` already provides (stdin
generic Context JSON in, stdout generic Verdict JSON out) without depending
on hook-bridge-sdk, so these tests can `uv run` it with no registry
resolution at all.
"""

import json
import sys


def main() -> None:
    ctx = json.loads(sys.stdin.read())
    command = ctx.get("tool", {}).get("command", "")
    if "rm -rf /" in command:
        verdict = {"outcome": "deny", "reason": "blocked"}
    else:
        verdict = {"outcome": "allow"}
    print(json.dumps(verdict))


if __name__ == "__main__":
    main()
