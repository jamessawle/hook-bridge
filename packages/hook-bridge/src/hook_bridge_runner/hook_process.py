"""Spawns a Hook as a subprocess and pipes the generic wire JSON across the
process edge.

Per ADR-0001, hook-bridge invokes a Hook via `uv run <hook>`, passing the
generic Context as JSON on stdin and reading the Verdict from stdout / exit
code. This is exactly the stdin/stdout shell `hook.run()` already implements
in the SDK (#6, #9) — this module does not change that contract, it is the
other end of the same pipe. One spawn per event.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any


class HookProcessError(Exception):
    """The Hook subprocess failed: a nonzero exit (health only, per the SDK's
    `_run_io`) or stdout that isn't valid generic Verdict JSON."""


def run_hook_process(hook_path: str, context: dict[str, Any]) -> dict[str, Any]:
    result = subprocess.run(
        ["uv", "run", hook_path],
        input=json.dumps(context),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        reason = result.stderr.strip() or f"hook process exited {result.returncode}"
        raise HookProcessError(reason)
    try:
        verdict = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise HookProcessError(f"hook process did not print valid Verdict JSON: {exc}") from exc
    if not isinstance(verdict, dict):
        raise HookProcessError(
            f"hook process Verdict must be a JSON object, got {type(verdict).__name__}"
        )
    return verdict  # pyright: ignore[reportUnknownVariableType]
