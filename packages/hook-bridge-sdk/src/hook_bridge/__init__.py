"""hook-bridge-sdk — the thin typed authoring SDK for hook-bridge Hooks.

Write a Hook once against the generic Contract and test it with no harness
present. See the module docstrings in `contract`, `hook`, and `wire` for the
design rationale, and CONTEXT.md for the ubiquitous language.
"""

from __future__ import annotations

from .contract import (
    ClaudeCode,
    ClaudeCodeTool,
    Codex,
    CodexTool,
    Context,
    Harness,
    Json,
    NativeTool,
    ShellTool,
    TerminalObservation,
    Tool,
    ToolAfterContext,
    ToolAfterVerdict,
    ToolBeforeContext,
    ToolBeforeVerdict,
    ToolError,
    ToolProjection,
    ToolResult,
    Verdict,
    allow,
    annotate,
    ask,
    block,
    defer,
    deny,
    pass_,
)
from .factories import claude_code_tool, codex_tool, error, result, shell, tool_after, tool_before
from .hook import Hook, hook, run
from .wire import BoundaryError, decode_context, encode_verdict

__all__ = [
    # Authoring
    "hook",
    "run",
    "Hook",
    # tool.before Verdict helpers
    "allow",
    "deny",
    "ask",
    "defer",
    # tool.after Verdict helpers
    "pass_",
    "block",
    "annotate",
    # Contract types
    "Context",
    "Json",
    "Harness",
    "ClaudeCode",
    "Codex",
    "ToolBeforeContext",
    "ToolBeforeVerdict",
    "ToolAfterContext",
    "ToolAfterVerdict",
    "Verdict",
    "ShellTool",
    "Tool",
    "ToolProjection",
    "NativeTool",
    "ClaudeCodeTool",
    "CodexTool",
    "ToolResult",
    "ToolError",
    "TerminalObservation",
    # Boundary (wire) validation
    "BoundaryError",
    "decode_context",
    "encode_verdict",
    # Testing factories
    "tool_before",
    "tool_after",
    "shell",
    "result",
    "error",
    "claude_code_tool",
    "codex_tool",
]
