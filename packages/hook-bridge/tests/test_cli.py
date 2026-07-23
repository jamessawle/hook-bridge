"""End-to-end: `hook-bridge-runner --harness stub <fixture>` through a real `uv run`
subprocess — the CLI & IO plumbing this ticket (#11) builds. Uses the `stub`
Adapter (whose native wire is deliberately unlike the generic Contract) and a
dependency-free fixture Hook so no PyPI resolution is needed."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from hook_bridge_runner.cli import main

FAKE_HOOK = str(Path(__file__).parent / "fixtures" / "fake_hook.py")
CRASHING_HOOK = str(Path(__file__).parent / "fixtures" / "crashing_hook.py")


def _run(monkeypatch: pytest.MonkeyPatch, raw: dict[str, object], hook: str = FAKE_HOOK, harness: str = "stub") -> int:
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(raw)))
    with pytest.raises(SystemExit) as exc_info:
        main(["--harness", harness, hook])
    assert isinstance(exc_info.value.code, int)
    return exc_info.value.code


def test_allow_round_trips_through_the_hook_subprocess(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code = _run(monkeypatch, {"kind": "before-tool", "session": "s1", "directory": ".", "shell_command": "git status"})
    assert json.loads(capsys.readouterr().out) == {"decision": "proceed"}
    assert code == 0


def test_deny_round_trips_through_the_hook_subprocess(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code = _run(monkeypatch, {"kind": "before-tool", "session": "s1", "directory": ".", "shell_command": "rm -rf /"})
    assert json.loads(capsys.readouterr().out) == {"decision": "block", "why": "blocked"}
    assert code == 0


def test_unknown_harness_fails_loudly_before_any_payload_work(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code = _run(monkeypatch, {"kind": "before-tool", "shell_command": "git status"}, harness="cursor")
    assert code == 1
    assert "unknown harness" in capsys.readouterr().err


def test_no_codec_for_native_event_fails_loudly(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code = _run(monkeypatch, {"kind": "prompt-submitted", "prompt": "hi"})
    assert code == 1
    assert "no codec for event" in capsys.readouterr().err


def test_crashing_hook_process_is_propagated_not_swallowed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code = _run(monkeypatch, {"kind": "before-tool", "shell_command": "git status"}, hook=CRASHING_HOOK)
    assert code == 1
    assert "boom" in capsys.readouterr().err
