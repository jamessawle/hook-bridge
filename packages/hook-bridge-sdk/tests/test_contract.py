"""The Contract types, verdict helpers, and testing factories."""

from __future__ import annotations

from hook_bridge import (
    ShellTool,
    ToolAfterContext,
    ToolAfterVerdict,
    ToolBeforeContext,
    ToolBeforeVerdict,
    allow,
    annotate,
    ask,
    block,
    defer,
    deny,
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
    r = result("exit 0", exit_code=0)
    assert r.text == "exit 0"
    assert r.exit_code == 0


def test_tool_after_factory_defaults_base_fields() -> None:
    ctx = tool_after(shell("git status"), result("clean"))
    assert isinstance(ctx, ToolAfterContext)
    assert ctx.event == "tool.after"
    assert ctx.tool.command == "git status"
    assert ctx.result.text == "clean"
    assert ctx.result.exit_code == 0
    assert ctx.session_id and ctx.cwd


def test_tool_after_factory_overrides_base_fields() -> None:
    ctx = tool_after(shell("git status"), result("clean"), session_id="abc", cwd="/repo")
    assert ctx.session_id == "abc"
    assert ctx.cwd == "/repo"


def test_tool_after_event_is_a_type_level_constant() -> None:
    assert ToolAfterContext.event == "tool.after"
