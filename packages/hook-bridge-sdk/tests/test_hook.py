"""The `@hook` decorator, the pure `dispatch` seam, and the `run()` IO shell."""

from __future__ import annotations

import io
import json
from typing import Any

import pytest

from hook_bridge import (
    ToolBeforeContext,
    ToolBeforeVerdict,
    allow,
    deny,
    hook,
    run,
    shell,
    tool_before,
)


@hook
def guard(ctx: ToolBeforeContext) -> ToolBeforeVerdict:
    return deny("no force-push") if "--force" in ctx.tool.command else allow()


# --- the pure test seam --------------------------------------------------


def test_dispatch_runs_the_pure_handler() -> None:
    assert guard.dispatch(tool_before(shell("git status"))).is_allow
    assert guard.dispatch(tool_before(shell("git push --force"))).is_deny


def test_event_is_read_from_the_annotated_context_type() -> None:
    assert guard.event == "tool.before"


def test_unannotated_handler_is_rejected() -> None:
    def handler(ctx) -> ToolBeforeVerdict:  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
        return allow()

    with pytest.raises(TypeError):
        hook(handler)  # pyright: ignore[reportUnknownArgumentType]


def test_parameterless_handler_is_rejected() -> None:
    with pytest.raises(TypeError):
        hook(lambda: allow())  # pyright: ignore[reportUnknownLambdaType, reportArgumentType]


# --- the run() IO shell --------------------------------------------------


def _feed(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any] | str) -> None:
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    monkeypatch.setattr("sys.stdin", io.StringIO(raw))


def _context(command: str) -> dict[str, Any]:
    return {
        "event": "tool.before",
        "session_id": "s",
        "cwd": "/repo",
        "tool": {"kind": "shell", "command": command},
    }


def test_run_reads_stdin_and_writes_verdict_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _feed(monkeypatch, _context("git push --force"))
    guard.run()
    out = json.loads(capsys.readouterr().out)
    assert out == {"outcome": "deny", "reason": "no force-push"}


def test_run_exit_code_is_health_not_verdict(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # A deny is a normal, healthy outcome — the process still exits 0.
    _feed(monkeypatch, _context("git push --force"))
    guard.run()  # does not raise SystemExit
    assert capsys.readouterr().out.strip()


def test_run_fails_loud_on_malformed_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _feed(monkeypatch, "not json")
    with pytest.raises(SystemExit) as exc:
        guard.run()
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert captured.out.strip() == ""  # nothing on stdout
    assert captured.err.strip()  # reason on stderr


def test_run_fails_loud_on_boundary_violation(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _feed(monkeypatch, {"event": "tool.before", "session_id": "s"})  # missing cwd, tool
    with pytest.raises(SystemExit) as exc:
        guard.run()
    assert exc.value.code == 1
    assert capsys.readouterr().out.strip() == ""


# --- run(*hooks) compose -------------------------------------------------


def test_run_compose_dispatches_the_matching_hook(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _feed(monkeypatch, _context("git status"))
    run(guard)  # composes and selects by ctx.event
    assert json.loads(capsys.readouterr().out) == {"outcome": "allow"}


def test_run_compose_fails_when_no_hook_handles_the_event(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _feed(monkeypatch, _context("git status"))
    with pytest.raises(SystemExit) as exc:
        run()  # no hooks composed → no handler for tool.before
    assert exc.value.code == 1
    assert capsys.readouterr().out.strip() == ""
