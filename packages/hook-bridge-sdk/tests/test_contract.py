"""The Contract types, verdict helpers, and testing factories."""

from __future__ import annotations

import pytest
from hook_bridge import (
    ClaudeCode,
    ClaudeCodeTool,
    Codex,
    CodexTool,
    ShellTool,
    Tool,
    ToolAfterContext,
    ToolAfterVerdict,
    ToolBeforeContext,
    ToolBeforeVerdict,
    ToolError,
    ToolResult,
    allow,
    annotate,
    ask,
    block,
    claude_code_tool,
    codex_tool,
    defer,
    deny,
    error,
    pass_,
    result,
    shell,
    tool_after,
    tool_before,
)


def test_allow_is_only_allow() -> None:
    v = allow()
    assert v.is_allow
    assert not (v.is_deny or v.is_ask or v.is_defer)
    assert v.reason is None


def test_deny_carries_reason() -> None:
    v = deny("nope")
    assert v.is_deny
    assert v.reason == "nope"


def test_ask_carries_reason() -> None:
    v = ask("confirm")
    assert v.is_ask
    assert v.reason == "confirm"


def test_defer_has_no_opinion() -> None:
    v = defer()
    assert v.is_defer
    assert not (v.is_allow or v.is_deny or v.is_ask)
    assert v.reason is None


def test_verdict_predicates_are_mutually_exclusive() -> None:
    verdicts: list[ToolBeforeVerdict] = [allow(), deny("x"), ask("y"), defer()]
    for v in verdicts:
        flags = [v.is_allow, v.is_deny, v.is_ask, v.is_defer]
        assert sum(flags) == 1


def test_shell_factory_builds_shell_tool() -> None:
    tool = shell("git status")
    assert isinstance(tool, ShellTool)
    assert tool.kind == "shell"
    assert tool.command == "git status"


def test_tool_envelope_requires_matching_harness_and_native_data() -> None:
    tool = claude_code_tool(
        {"tool_name": "Bash", "tool_input": {"command": "git status"}},
        shell("git status"),
    )
    assert isinstance(tool.harness, ClaudeCode)
    assert isinstance(tool.native, ClaudeCodeTool)
    assert tool.projection == shell("git status")

    with pytest.raises(ValueError):
        Tool(ClaudeCode(), CodexTool({}))


def test_unknown_tool_remains_available_without_projection() -> None:
    tool = codex_tool({"tool_name": "future_tool", "tool_input": {"x": 1}})
    assert isinstance(tool.harness, Codex)
    assert isinstance(tool.native, CodexTool)
    assert tool.projection is None


def test_tool_before_factory_defaults_base_fields() -> None:
    ctx = tool_before(codex_tool({"name": "shell"}, shell("git status")))
    assert isinstance(ctx, ToolBeforeContext)
    assert ctx.event == "tool.before"
    assert ctx.tool.projection == shell("git status")
    assert ctx.session_id and ctx.cwd


def test_tool_before_factory_overrides_base_fields() -> None:
    ctx = tool_before(codex_tool({}, shell("git status")), session_id="abc", cwd="/repo")
    assert ctx.session_id == "abc"
    assert ctx.cwd == "/repo"


def test_event_is_a_type_level_constant() -> None:
    # The runner reads a Hook's event straight off the Context type.
    assert ToolBeforeContext.event == "tool.before"


# --- tool.after ------------------------------------------------------------


def test_pass_is_only_pass() -> None:
    v = pass_()
    assert v.is_pass
    assert not (v.is_block or v.is_annotate)
    assert v.message is None


def test_block_carries_message() -> None:
    v = block("failed command")
    assert v.is_block
    assert v.message == "failed command"


def test_annotate_carries_message() -> None:
    v = annotate("saw an audit-worthy action")
    assert v.is_annotate
    assert v.message == "saw an audit-worthy action"


def test_tool_after_verdict_predicates_are_mutually_exclusive() -> None:
    verdicts: list[ToolAfterVerdict] = [pass_(), block("x"), annotate("y")]
    for v in verdicts:
        flags = [v.is_pass, v.is_block, v.is_annotate]
        assert sum(flags) == 1


def test_result_factory_builds_tool_result() -> None:
    r = result({"output": "clean", "exitCode": 0})
    assert r.output == {"output": "clean", "exitCode": 0}


def test_error_factory_builds_tool_error() -> None:
    observation = error(["permission denied", {"retryable": False}])
    assert isinstance(observation, ToolError)
    assert observation.error == ["permission denied", {"retryable": False}]


def test_tool_after_factory_defaults_base_fields() -> None:
    ctx = tool_after(codex_tool({"name": "shell"}, shell("git status")), result("clean"))
    assert isinstance(ctx, ToolAfterContext)
    assert ctx.event == "tool.after"
    assert ctx.tool.projection == shell("git status")
    assert isinstance(ctx.observation, ToolResult)
    assert ctx.observation.output == "clean"
    assert ctx.session_id and ctx.cwd


def test_tool_after_factory_overrides_base_fields() -> None:
    ctx = tool_after(
        codex_tool({}, shell("git status")),
        error("failed"),
        session_id="abc",
        cwd="/repo",
    )
    assert ctx.session_id == "abc"
    assert ctx.cwd == "/repo"


def test_tool_after_event_is_a_type_level_constant() -> None:
    assert ToolAfterContext.event == "tool.after"
