"""Boundary schema validation on the wire Contract."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from hook_bridge import (
    BoundaryError,
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
    decode_context,
    defer,
    deny,
    encode_verdict,
    pass_,
)

Mutation = Callable[[dict[str, Any]], object]


def _valid_context() -> dict[str, Any]:
    return {
        "event": "tool.before",
        "session_id": "s",
        "cwd": "/repo",
        "tool": {
            "harness": "codex",
            "native": {"tool_name": "shell", "tool_input": {"command": "git status"}},
            "projection": {"kind": "shell", "command": "git status"},
        },
    }


# --- decode --------------------------------------------------------------


def test_decode_builds_typed_context() -> None:
    ctx = decode_context(_valid_context())
    assert isinstance(ctx, ToolBeforeContext)
    assert ctx.session_id == "s"
    assert ctx.cwd == "/repo"
    assert ctx.tool.harness.name == "codex"
    assert ctx.tool.native.data["tool_name"] == "shell"
    assert ctx.tool.projection is not None
    assert ctx.tool.projection.command == "git status"


_MALFORMED: list[tuple[str, Mutation]] = [
    ("missing-event", lambda d: d.pop("event")),
    ("missing-session_id", lambda d: d.pop("session_id")),
    ("missing-cwd", lambda d: d.pop("cwd")),
    ("missing-tool", lambda d: d.pop("tool")),
    ("unknown-event", lambda d: d.update(event="tool.other")),
    ("unknown-harness", lambda d: d["tool"].update(harness="other")),
    ("missing-native", lambda d: d["tool"].pop("native")),
    ("unknown-projection-kind", lambda d: d["tool"]["projection"].update(kind="python")),
    ("missing-command", lambda d: d["tool"]["projection"].pop("command")),
    ("non-string-session_id", lambda d: d.update(session_id=123)),
    ("non-string-command", lambda d: d["tool"]["projection"].update(command=None)),
    ("non-json-native", lambda d: d["tool"].update(native={"bad": object()})),
]


@pytest.mark.parametrize(
    "mutate", [m for _, m in _MALFORMED], ids=[i for i, _ in _MALFORMED]
)
def test_decode_rejects_malformed_context(mutate: Mutation) -> None:
    raw = _valid_context()
    mutate(raw)
    with pytest.raises(BoundaryError):
        decode_context(raw)


def test_decode_rejects_non_object() -> None:
    with pytest.raises(BoundaryError):
        decode_context("not an object")


# --- encode --------------------------------------------------------------


def test_encode_allow() -> None:
    assert encode_verdict(allow()) == {"outcome": "allow"}


def test_encode_defer() -> None:
    assert encode_verdict(defer()) == {"outcome": "defer"}


def test_encode_deny_includes_reason() -> None:
    assert encode_verdict(deny("blocked")) == {"outcome": "deny", "reason": "blocked"}


def test_encode_ask_includes_reason() -> None:
    assert encode_verdict(ask("confirm")) == {"outcome": "ask", "reason": "confirm"}


@pytest.mark.parametrize("outcome", ["deny", "ask"])
def test_encode_rejects_reasonless_deny_or_ask(outcome: str) -> None:
    with pytest.raises(BoundaryError):
        encode_verdict(ToolBeforeVerdict(outcome))  # pyright: ignore[reportArgumentType]


def test_encode_roundtrips_with_decode_shape() -> None:
    # A verdict encodes to a dict a harness Adapter can carry; a context decodes
    # from the dict shape a harness Adapter would emit. Both go through the same
    # boundary, so their shapes stay in lockstep.
    ctx = decode_context(_valid_context())
    assert ctx.event == "tool.before"
    assert encode_verdict(allow())["outcome"] == "allow"


# --- tool.after ------------------------------------------------------------


def _valid_tool_after_context() -> dict[str, Any]:
    return {
        "event": "tool.after",
        "session_id": "s",
        "cwd": "/repo",
        "tool": {
            "harness": "claude-code",
            "native": {
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "git status"},
                "tool_response": {"output": "clean", "exitCode": 0},
            },
            "projection": {"kind": "shell", "command": "git status"},
        },
        "observation": {
            "kind": "result",
            "output": {"output": "clean", "exitCode": 0},
        },
    }


def test_decode_builds_typed_tool_after_context() -> None:
    ctx = decode_context(_valid_tool_after_context())
    assert isinstance(ctx, ToolAfterContext)
    assert ctx.tool.projection is not None
    assert ctx.tool.projection.command == "git status"
    assert isinstance(ctx.observation, ToolResult)
    assert ctx.observation.output == {"output": "clean", "exitCode": 0}


_MALFORMED_TOOL_AFTER: list[tuple[str, Mutation]] = [
    ("missing-observation", lambda d: d.pop("observation")),
    ("missing-output", lambda d: d["observation"].pop("output")),
    ("unknown-observation-kind", lambda d: d["observation"].update(kind="maybe")),
    ("non-json-output", lambda d: d["observation"].update(output=object())),
]


@pytest.mark.parametrize(
    "mutate", [m for _, m in _MALFORMED_TOOL_AFTER], ids=[i for i, _ in _MALFORMED_TOOL_AFTER]
)
def test_decode_rejects_malformed_tool_after_context(mutate: Mutation) -> None:
    raw = _valid_tool_after_context()
    mutate(raw)
    with pytest.raises(BoundaryError):
        decode_context(raw)


def test_decode_builds_tool_error_with_any_json_value() -> None:
    raw = _valid_tool_after_context()
    raw["observation"] = {"kind": "error", "error": ["denied", {"code": 13}]}
    ctx = decode_context(raw)
    assert isinstance(ctx, ToolAfterContext)
    assert isinstance(ctx.observation, ToolError)
    assert ctx.observation.error == ["denied", {"code": 13}]


def test_decode_accepts_absent_projection_without_losing_native_tool() -> None:
    raw = _valid_context()
    raw["tool"]["projection"] = None
    ctx = decode_context(raw)
    assert isinstance(ctx, ToolBeforeContext)
    assert ctx.tool.projection is None
    assert ctx.tool.native.data["tool_name"] == "shell"


def test_encode_pass() -> None:
    assert encode_verdict(pass_()) == {"outcome": "pass"}


def test_encode_block_includes_message() -> None:
    assert encode_verdict(block("failed")) == {"outcome": "block", "message": "failed"}


def test_encode_annotate_includes_message() -> None:
    assert encode_verdict(annotate("fyi")) == {"outcome": "annotate", "message": "fyi"}


@pytest.mark.parametrize("outcome", ["block", "annotate"])
def test_encode_rejects_messageless_block_or_annotate(outcome: str) -> None:
    with pytest.raises(BoundaryError):
        encode_verdict(ToolAfterVerdict(outcome))  # pyright: ignore[reportArgumentType]
