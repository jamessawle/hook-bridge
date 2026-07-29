"""PROTOTYPE: interactive scenario driver for annotation filtering."""

from __future__ import annotations

import dataclasses
import json
from typing import Any

from filtering import (
    ClaudeCode,
    ClaudeCodeTool,
    Codex,
    CodexTool,
    Context,
    FileEditTool,
    Hook,
    ShellTool,
    Tool,
    ToolAfterContext,
    ToolAfterVerdict,
    ToolBeforeContext,
    ToolBeforeVerdict,
    ToolError,
    ToolResult,
    dispatch_first,
    hook,
)

BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RESET = "\x1b[0m"


@hook
def deny_shell(ctx: ToolBeforeContext, tool: ShellTool) -> ToolBeforeVerdict:
    return ToolBeforeVerdict("deny", f"portable shell policy saw {tool.command!r}")


@hook
def ask_for_codex_edits(
    ctx: ToolBeforeContext, harness: Codex, tool: FileEditTool
) -> ToolBeforeVerdict:
    return ToolBeforeVerdict("ask", f"Codex wants to edit {tool.path}")


@hook
def inspect_claude_native(
    ctx: ToolBeforeContext, native: ClaudeCodeTool
) -> ToolBeforeVerdict:
    return ToolBeforeVerdict("allow", f"native tool name is {native.tool_name}")


@hook
def annotate_shell_result(
    ctx: ToolAfterContext, tool: ShellTool, result: ToolResult
) -> ToolAfterVerdict:
    return ToolAfterVerdict("annotate", f"shell returned {result.value!r}")


@hook
def block_codex_error(
    ctx: ToolAfterContext, harness: Codex, error: ToolError, native: CodexTool
) -> ToolAfterVerdict:
    return ToolAfterVerdict("block", f"{native.tool_name} failed: {error.error!r}")


@hook
def audit_any_terminal(ctx: ToolAfterContext, tool: Tool) -> ToolAfterVerdict:
    return ToolAfterVerdict("pass", f"observed {tool.native!r}")


BEFORE_HOOKS: tuple[Hook[Any, Any], ...] = (
    ask_for_codex_edits,
    deny_shell,
    inspect_claude_native,
)
AFTER_HOOKS: tuple[Hook[Any, Any], ...] = (
    block_codex_error,
    annotate_shell_result,
    audit_any_terminal,
)


@dataclasses.dataclass(frozen=True)
class Scenario:
    title: str
    note: str
    ctx: Context
    hooks: tuple[Hook[Any, Any], ...]


SCENARIOS = (
    Scenario(
        "portable tool.before projection",
        "ShellTool is injected with a precise type; Harness is irrelevant.",
        ToolBeforeContext(Tool(ClaudeCode(), ClaudeCodeTool("Bash", {"command": "rm draft"}), ShellTool("rm draft"))),
        BEFORE_HOOKS,
    ),
    Scenario(
        "combined Harness + Tool filter",
        "Both Codex and FileEditTool must match; filters compose as AND.",
        ToolBeforeContext(Tool(Codex(), CodexTool("apply_patch", {"patch": "..."}), FileEditTool("a.py", "..."))),
        BEFORE_HOOKS,
    ),
    Scenario(
        "unknown Tool with no projection",
        "Projection Hooks skip; the Claude Native escape-hatch Hook still matches.",
        ToolBeforeContext(Tool(ClaudeCode(), ClaudeCodeTool("FutureTool", {"x": 1}), None)),
        BEFORE_HOOKS,
    ),
    Scenario(
        "known Tool with projection suppressed",
        "A changed Bash schema remains observable as Native data without pretending ShellTool exists.",
        ToolBeforeContext(Tool(ClaudeCode(), ClaudeCodeTool("Bash", {"new_command_shape": ["pwd"]}), None)),
        BEFORE_HOOKS,
    ),
    Scenario(
        "portable tool.after Result",
        "Tool and observation filters both match and both parameters are precisely typed.",
        ToolAfterContext(
            Tool(ClaudeCode(), ClaudeCodeTool("Bash", {"command": "pwd"}), ShellTool("pwd")),
            ToolResult("/repo"),
        ),
        AFTER_HOOKS,
    ),
    Scenario(
        "Harness-specific terminal Error",
        "Harness, ToolError, and Native parameters combine; no portable projection is required.",
        ToolAfterContext(Tool(Codex(), CodexTool("mcp.call", {"server": "db"}), None), ToolError({"code": 500})),
        AFTER_HOOKS,
    ),
    Scenario(
        "unknown terminal Tool falls through",
        "A Tool envelope annotation catches every Tool; the neutral pass Verdict is explicit here.",
        ToolAfterContext(Tool(ClaudeCode(), ClaudeCodeTool("FutureTool", {}), None), ToolResult({"ok": True})),
        AFTER_HOOKS,
    ),
)


def _jsonable(value: object) -> object:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {field.name: _jsonable(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def render(index: int) -> None:
    scenario = SCENARIOS[index]
    result = dispatch_first(scenario.hooks, scenario.ctx)
    print("\x1b[2J\x1b[H", end="")
    print(f"{BOLD}PROTOTYPE — annotation-driven Hook filtering{RESET}")
    print(f"{BOLD}Scenario {index + 1}: {scenario.title}{RESET}")
    print(f"{DIM}{scenario.note}{RESET}\n")
    print(f"{BOLD}Context{RESET}")
    print(json.dumps(_jsonable(scenario.ctx), indent=2))
    print(f"\n{BOLD}Ordered composition trace{RESET}")
    for trace in result.traces:
        marker = "MATCH" if trace.match.matched else "skip"
        print(f"  {BOLD}{marker:5}{RESET} {trace.hook.signature}")
        for check in trace.match.checks:
            print(f"        {DIM}{check}{RESET}")
    print(f"\n{BOLD}Selected Hook{RESET}: {result.selected.name if result.selected else 'none (neutral fallback)'}")
    print(f"{BOLD}Injected runtime types{RESET}: {', '.join(result.injected_types) or 'none'}")
    print(f"{BOLD}Verdict{RESET}: {result.verdict!r}")
    keys = "  ".join(f"[{i + 1}] {item.title}" for i, item in enumerate(SCENARIOS))
    print(f"\n{DIM}{keys}{RESET}\n{BOLD}[q]{RESET} quit")


def main() -> None:
    index = 0
    while True:
        render(index)
        choice = input("> ").strip().lower()
        if choice == "q":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(SCENARIOS):
            index = int(choice) - 1


if __name__ == "__main__":
    main()
