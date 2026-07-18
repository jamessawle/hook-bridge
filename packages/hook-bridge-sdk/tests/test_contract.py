"""The Contract types, verdict helpers, and testing factories."""

from __future__ import annotations

from hook_bridge import (
    ShellTool,
    ToolBeforeContext,
    ToolBeforeVerdict,
    allow,
    ask,
    defer,
    deny,
    shell,
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


def test_tool_before_factory_defaults_base_fields() -> None:
    ctx = tool_before(shell("git status"))
    assert isinstance(ctx, ToolBeforeContext)
    assert ctx.event == "tool.before"
    assert ctx.tool.command == "git status"
    assert ctx.session_id and ctx.cwd


def test_tool_before_factory_overrides_base_fields() -> None:
    ctx = tool_before(shell("git status"), session_id="abc", cwd="/repo")
    assert ctx.session_id == "abc"
    assert ctx.cwd == "/repo"


def test_event_is_a_type_level_constant() -> None:
    # The runner reads a Hook's event straight off the Context type.
    assert ToolBeforeContext.event == "tool.before"
