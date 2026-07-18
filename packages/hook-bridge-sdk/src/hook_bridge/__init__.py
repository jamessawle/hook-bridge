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
    ToolBeforeContext,
    ToolBeforeVerdict,
    Verdict,
    allow,
    ask,
    defer,
    deny,
)
from .factories import shell, tool_before
from .hook import Hook, hook, run
from .wire import BoundaryError, decode_context, encode_verdict

__all__ = [
    # Authoring
    "hook",
    "run",
    "Hook",
    # Verdict helpers
    "allow",
    "deny",
    "ask",
    "defer",
    # Contract types
    "Context",
    "ToolBeforeContext",
    "ToolBeforeVerdict",
    "Verdict",
    "ShellTool",
    "Tool",
    # Boundary (wire) validation
    "BoundaryError",
    "decode_context",
    "encode_verdict",
    # Testing factories
    "tool_before",
    "shell",
]
