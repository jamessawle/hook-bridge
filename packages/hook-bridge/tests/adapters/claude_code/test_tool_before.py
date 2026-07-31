"""Interface tests for the claude-code `tool.before` Codec."""

from __future__ import annotations

from typing import Any

import pytest
from hook_bridge_runner.adapters.claude_code.tool_before import codec
from hook_bridge_runner.codec import RunnerError

_PRE_TOOL_USE = {
    "session_id": "s1",
    "transcript_path": "/tmp/transcript.jsonl",
    "cwd": "/repo",
    "hook_event_name": "PreToolUse",
    "tool_name": "Bash",
    "tool_input": {"command": "git status", "timeout": 30_000},
    "tool_use_id": "toolu_1",
}


def _tool(raw: dict[str, Any], projection: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "harness": "claude-code",
        "native": raw,
        "projection": projection,
    }


def test_declares_its_native_and_contract_events() -> None:
    assert codec.native_event == "PreToolUse"
    assert codec.contract_event == "tool.before"


def test_decode_preserves_native_data_and_projects_bash() -> None:
    assert codec.decode(_PRE_TOOL_USE) == {
        "event": "tool.before",
        "session_id": "s1",
        "cwd": "/repo",
        "tool": _tool(
            _PRE_TOOL_USE,
            {"kind": "shell", "command": "git status"},
        ),
    }


@pytest.mark.parametrize(
    "tool",
    [
        {"tool_name": "Edit", "tool_input": {"file_path": "a.py"}},
        {"tool_name": "mcp__server__remote", "tool_input": {"value": 1}},
        {"tool_name": "mcp__local__function", "tool_input": {"value": 2}},
        {"tool_name": "FutureBuiltIn", "tool_input": {"future": True}},
    ],
    ids=["built-in", "mcp", "local-function", "unknown"],
)
def test_decode_preserves_every_tool_without_inventing_a_projection(
    tool: dict[str, Any],
) -> None:
    raw = {**_PRE_TOOL_USE, **tool}
    decoded = codec.decode(raw)
    assert decoded["tool"] == _tool(raw, None)


def test_decode_suppresses_shell_projection_when_required_field_drifted() -> None:
    raw = {**_PRE_TOOL_USE, "tool_input": {"cmd": "git status"}}
    decoded = codec.decode(raw)
    assert decoded["tool"] == _tool(raw, None)


def test_decode_requires_session_id_and_cwd() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "session_id": None})


def test_decode_rejects_a_misrouted_event() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "hook_event_name": "PostToolUse"})


@pytest.mark.parametrize("field", ["tool_name", "tool_input", "tool_use_id"])
def test_decode_requires_the_native_tool_envelope(field: str) -> None:
    raw = dict(_PRE_TOOL_USE)
    raw.pop(field)
    with pytest.raises(RunnerError):
        codec.decode(raw)


def test_decode_rejects_non_json_native_data() -> None:
    with pytest.raises(RunnerError, match="must be JSON"):
        codec.decode({**_PRE_TOOL_USE, "future": object()})


_OUTCOMES: list[tuple[dict[str, str], tuple[dict[str, Any], int]]] = [
    (
        {"outcome": "allow"},
        (
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                }
            },
            0,
        ),
    ),
    ({"outcome": "defer"}, ({}, 0)),
    (
        {"outcome": "deny", "reason": "no"},
        (
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "no",
                }
            },
            0,
        ),
    ),
    (
        {"outcome": "ask", "reason": "confirm?"},
        (
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": "confirm?",
                }
            },
            0,
        ),
    ),
]


@pytest.mark.parametrize(("outcome", "expected"), _OUTCOMES)
def test_encode_maps_every_outcome(
    outcome: dict[str, str], expected: tuple[dict[str, Any], int]
) -> None:
    assert codec.encode(outcome) == expected


def test_encode_rejects_unknown_outcome() -> None:
    with pytest.raises(RunnerError):
        codec.encode({"outcome": "modify"})
