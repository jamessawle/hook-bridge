"""Testing factories: build a `Context` in-process, no JSON, no harness.

These are the inputs a harness-free test feeds to `hook.dispatch(...)`. They
mirror the shape an Adapter would produce from a real Harness event, including
explicit Native data, so a test exercises the Hook through the exact same
Contract types the runner uses.
"""

from __future__ import annotations

from .contract import (
    ClaudeCode,
    ClaudeCodeTool,
    Codex,
    CodexTool,
    Json,
    ShellTool,
    TerminalObservation,
    Tool,
    ToolAfterContext,
    ToolBeforeContext,
    ToolError,
    ToolProjection,
    ToolResult,
)


def shell(command: str) -> ShellTool:
    """A shell tool carrying `command`."""
    return ShellTool(command=command)


def result(output: Json) -> ToolResult:
    """A normal Terminal observation carrying arbitrary JSON output."""
    return ToolResult(output=output)


def error(value: Json) -> ToolError:
    """An erroneous Terminal observation carrying arbitrary JSON error data."""
    return ToolError(error=value)


def claude_code_tool(
    data: dict[str, Json], projection: ToolProjection | None = None
) -> Tool:
    """A Tool carrying Claude Code Native data and an optional projection."""
    return Tool(ClaudeCode(), ClaudeCodeTool(data), projection)


def codex_tool(data: dict[str, Json], projection: ToolProjection | None = None) -> Tool:
    """A Tool carrying Codex Native data and an optional projection."""
    return Tool(Codex(), CodexTool(data), projection)


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
    observation: TerminalObservation,
    *,
    session_id: str = "test-session",
    cwd: str = ".",
) -> ToolAfterContext:
    """A `tool.after` Context wrapping `tool` and `observation`. The base
    fields default to harmless test values so a test need only supply the
    tool and result it cares about."""
    return ToolAfterContext(
        session_id=session_id, cwd=cwd, tool=tool, observation=observation
    )
