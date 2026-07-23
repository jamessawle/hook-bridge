"""The `hook-bridge` CLI: the one process a Harness ever invokes.

`hook-bridge --harness <h> <hook>` reads the harness's native event off
stdin, selects the `Codec` for `(harness, native event)` by peeking that
event name (#8, #11 — see docs/adr/0003-runner-process-boundary.md),
`decode`s to the generic wire Context, runs the Hook as a subprocess, and
`encode`s the Hook's generic wire Verdict back into the harness's native
response + exit code.

hook-bridge owns all harness-specific translation; the Hook process itself
stays fully harness-ignorant (CONTEXT.md) — its own `hook.run()` shell is
unchanged by this module.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, NoReturn

from .adapters import ADAPTERS
from .codec import RunnerError
from .hook_process import HookProcessError, run_hook_process


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    try:
        raw = _read_stdin_json()
        body, exit_code = _bridge(args.harness, args.hook, raw)
    except (RunnerError, HookProcessError) as exc:
        _fail(str(exc))
    else:
        print(json.dumps(body))
        raise SystemExit(exit_code)


def _bridge(harness: str, hook_path: str, raw: dict[str, Any]) -> tuple[dict[str, Any], int]:
    adapter = ADAPTERS.get(harness)
    if adapter is None:
        raise RunnerError(f"unknown harness {harness!r}")
    native_event = adapter.native_event(raw)
    codec = adapter.codecs.get(native_event)
    if codec is None:
        raise RunnerError(f"harness {harness!r} has no codec for event {native_event!r}")
    context = codec.decode(raw)
    verdict = run_hook_process(hook_path, context)
    return codec.encode(verdict)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="hook-bridge")
    parser.add_argument(
        "--harness", required=True, help="the harness invoking this event, e.g. claude-code"
    )
    parser.add_argument("hook", help="path to the Hook's entry file, run via `uv run`")
    return parser.parse_args(argv)


def _read_stdin_json() -> dict[str, Any]:
    try:
        raw = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        raise RunnerError(f"could not parse native event JSON from stdin: {exc}") from exc
    if not isinstance(raw, dict):
        raise RunnerError(f"native event must be a JSON object, got {type(raw).__name__}")
    return raw  # pyright: ignore[reportUnknownVariableType]


def _fail(message: str) -> NoReturn:
    print(message, file=sys.stderr)
    raise SystemExit(1)
