"""Interface tests for the claude-code `tool.before` Codec."""

from __future__ import annotations

from typing import Any

import pytest
from hook_bridge_runner.adapters.claude_code.tool_before import codec
from hook_bridge_runner.codec import RunnerError

_PRE_TOOL_USE = {
    "session_id": "s1",
    "cwd": "/repo",
    "hook_event_name": "PreToolUse",
    "tool_name": "Bash",
    "tool_input": {"command": "git status"},
}


def test_declares_its_native_and_contract_events() -> None:
    assert codec.native_event == "PreToolUse"
    assert codec.contract_event == "tool.before"


def test_decode_builds_the_generic_wire_context() -> None:
    assert codec.decode(_PRE_TOOL_USE) == {
        "event": "tool.before",
        "session_id": "s1",
        "cwd": "/repo",
        "tool": {"kind": "shell", "command": "git status"},
    }


def test_decode_requires_session_id_and_cwd() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "session_id": None})


def test_decode_rejects_a_misrouted_event() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "hook_event_name": "PostToolUse"})


def test_decode_rejects_an_unsupported_tool() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "tool_name": "WebFetch"})


def test_decode_requires_the_command_field() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "tool_input": {}})


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
