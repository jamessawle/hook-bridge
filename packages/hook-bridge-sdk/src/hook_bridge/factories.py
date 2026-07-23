"""Testing factories: build a `Context` in-process, no JSON, no harness.

These are the inputs a harness-free test feeds to `hook.dispatch(...)` — e.g.
`git_guard.dispatch(tool_before(shell("git push --force origin main")))`. They
mirror the shape an Adapter would produce from a real harness event, so a test
exercises the Hook through the exact same Contract types the runner uses.
"""

from __future__ import annotations

from .contract import ShellTool, Tool, ToolBeforeContext


def shell(command: str) -> ShellTool:
    """A shell tool carrying `command`."""
    return ShellTool(command=command)


def tool_before(
    tool: Tool,
    *,
    session_id: str = "test-session",
    cwd: str = ".",
) -> ToolBeforeContext:
    """A `tool.before` Context wrapping `tool`. The base fields default to
    harmless test values so a test need only supply the tool it cares about."""
    return ToolBeforeContext(session_id=session_id, cwd=cwd, tool=tool)
