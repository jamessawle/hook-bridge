"""Testing factories: build a `Context` in-process, no JSON, no harness.

These are the inputs a harness-free test feeds to `hook.dispatch(...)` — e.g.
`git_guard.dispatch(tool_before(shell("git push --force origin main")))`. They
mirror the shape an Adapter would produce from a real harness event, so a test
exercises the Hook through the exact same Contract types the runner uses.
"""

from __future__ import annotations

from .contract import ShellTool, Tool, ToolAfterContext, ToolBeforeContext, ToolResult


def shell(command: str) -> ShellTool:
    """A shell tool carrying `command`."""
    return ShellTool(command=command)


def result(text: str, exit_code: int = 0) -> ToolResult:
    """A tool result carrying `text` and `exit_code`."""
    return ToolResult(text=text, exit_code=exit_code)


def tool_before(
    tool: Tool,
    *,
    session_id: str = "test-session",
    cwd: str = ".",
) -> ToolBeforeContext:
    """A `tool.before` Context wrapping `tool`. The base fields default to
    harmless test values so a test need only supply the tool it cares about."""
    return ToolBeforeContext(session_id=session_id, cwd=cwd, tool=tool)


def tool_after(
    tool: Tool,
    tool_result: ToolResult,
    *,
    session_id: str = "test-session",
    cwd: str = ".",
) -> ToolAfterContext:
    """A `tool.after` Context wrapping `tool` and `tool_result`. The base
    fields default to harmless test values so a test need only supply the
    tool and result it cares about."""
    return ToolAfterContext(session_id=session_id, cwd=cwd, tool=tool, result=tool_result)
