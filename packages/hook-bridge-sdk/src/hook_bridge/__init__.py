"""hook-bridge-sdk — the thin typed authoring SDK for hook-bridge Hooks.

Write a Hook once against the generic Contract and test it with no harness
present. See the module docstrings in `contract`, `hook`, and `wire` for the
design rationale, and CONTEXT.md for the ubiquitous language.
"""

from __future__ import annotations

from .contract import (
    Context,
    ShellTool,
    Tool,
    ToolAfterContext,
    ToolAfterVerdict,
    ToolBeforeContext,
    ToolBeforeVerdict,
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
from .factories import result, shell, tool_after, tool_before
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
    "ToolBeforeContext",
    "ToolBeforeVerdict",
    "ToolAfterContext",
    "ToolAfterVerdict",
    "Verdict",
    "ShellTool",
    "Tool",
    "ToolResult",
    # Boundary (wire) validation
    "BoundaryError",
    "decode_context",
    "encode_verdict",
    # Testing factories
    "tool_before",
    "tool_after",
    "shell",
    "result",
]
