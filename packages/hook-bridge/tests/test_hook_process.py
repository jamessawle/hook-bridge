"""Unit tests on the Hook-subprocess boundary: a real `uv run` of small
dependency-free fixture scripts, exercising the health/exit-code contract
ADR-0001 and hook.py's `_run_io` already establish."""

from __future__ import annotations

from pathlib import Path

import pytest
from hook_bridge_runner.hook_process import HookProcessError, run_hook_process

FAKE_HOOK = str(Path(__file__).parent / "fixtures" / "fake_hook.py")
CRASHING_HOOK = str(Path(__file__).parent / "fixtures" / "crashing_hook.py")


def test_run_hook_process_returns_the_generic_verdict() -> None:
    context = {"event": "tool.before", "session_id": "s", "cwd": ".", "tool": {"kind": "shell", "command": "ls"}}
    assert run_hook_process(FAKE_HOOK, context) == {"outcome": "allow"}


def test_run_hook_process_raises_on_nonzero_exit() -> None:
    context = {"event": "tool.before", "session_id": "s", "cwd": ".", "tool": {"kind": "shell", "command": "ls"}}
    with pytest.raises(HookProcessError, match="boom"):
        run_hook_process(CRASHING_HOOK, context)
